import logging
import secrets
import string
from datetime import datetime
from typing import Optional, Any
import oracledb

from app.errors import BusinessException
from app.schemas.user import UserItem
from app.security import hash_password, AuthUser

logger = logging.getLogger(__name__)


def generate_temp_password(length: int = 12) -> str:
    """Generates cryptographically secure temporary password."""
    special = "!@#$%^&*"
    chars = string.ascii_letters + string.digits + special
    while True:
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        if (any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in special for c in pwd)):
            return pwd


def set_audit_context(
    conn: oracledb.Connection,
    user: AuthUser,
    ly_do: str,
    ip: Optional[str] = None
) -> None:
    """Sets session audit context in pkg_ngu_canh."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                BEGIN
                    pkg_ngu_canh.dat(
                        p_nguoi_id => :uid,
                        p_vai_tro  => :role,
                        p_kenh     => 'WEB',
                        p_ip       => :ip,
                        p_ly_do    => :ly_do
                    );
                END;
                """,
                uid=user.user_id,
                role=user.role,
                ip=ip or "127.0.0.1",
                ly_do=ly_do[:500]
            )
    except Exception as e:
        logger.warning(f"Failed to set audit context via pkg_ngu_canh: {e}")


def count_active_managers(conn: oracledb.Connection) -> int:
    """Counts active users having QUAN_LY role."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
              FROM nguoi_dung u
              JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
             WHERE v.ma_vai_tro = 'QUAN_LY'
               AND u.trang_thai = 'HOAT_DONG'
            """
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def get_role_id_by_code(conn: oracledb.Connection, role_code: str) -> int:
    """Translates role string (LE_TAN, BUONG_PHONG, QUAN_LY) to vai_tro_id."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT vai_tro_id FROM vai_tro WHERE ma_vai_tro = :role_code",
            role_code=role_code.upper().strip()
        )
        row = cur.fetchone()
        if not row:
            raise BusinessException(code="VALIDATION_ERROR", detail=f"Vai trò {role_code} không hợp lệ")
        return int(row[0])


def get_user_by_id(conn: oracledb.Connection, user_id: int) -> Optional[UserItem]:
    """Fetches user details by user_id."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.nguoi_dung_id, u.ten_dang_nhap, u.ho_ten, v.ma_vai_tro,
                   u.trang_thai, u.so_lan_sai, u.phai_doi_mat_khau, u.ngay_tao
              FROM nguoi_dung u
              JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
             WHERE u.nguoi_dung_id = :user_id
            """,
            user_id=user_id
        )
        row = cur.fetchone()
        if not row:
            return None
        return UserItem(
            id=row[0],
            tenDangNhap=row[1],
            hoTen=row[2],
            vaiTro=row[3],
            trangThai=row[4],
            soLanSai=row[5] or 0,
            phaiDoiMatKhau=bool(row[6]),
            ngayTao=row[7].isoformat() if row[7] else None
        )


def list_users(
    conn: oracledb.Connection,
    vai_tro: Optional[str] = None,
    trang_thai: Optional[str] = None,
    q: Optional[str] = None
) -> list[UserItem]:
    """Lists staff accounts with filtering (F17)."""
    clauses = ["1=1"]
    params: dict[str, Any] = {}

    if vai_tro and vai_tro.strip():
        clauses.append("v.ma_vai_tro = :vai_tro")
        params["vai_tro"] = vai_tro.strip().upper()

    if trang_thai and trang_thai.strip():
        clauses.append("u.trang_thai = :trang_thai")
        params["trang_thai"] = trang_thai.strip().upper()

    if q and q.strip():
        clauses.append("(LOWER(u.ten_dang_nhap) LIKE :q OR LOWER(u.ho_ten) LIKE :q)")
        params["q"] = f"%{q.strip().lower()}%"

    sql = f"""
        SELECT u.nguoi_dung_id, u.ten_dang_nhap, u.ho_ten, v.ma_vai_tro,
               u.trang_thai, u.so_lan_sai, u.phai_doi_mat_khau, u.ngay_tao
          FROM nguoi_dung u
          JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
         WHERE {" AND ".join(clauses)}
         ORDER BY u.nguoi_dung_id ASC
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        UserItem(
            id=r[0],
            tenDangNhap=r[1],
            hoTen=r[2],
            vaiTro=r[3],
            trangThai=r[4],
            soLanSai=r[5] or 0,
            phaiDoiMatKhau=bool(r[6]),
            ngayTao=r[7].isoformat() if r[7] else None
        )
        for r in rows
    ]


def create_user(
    conn: oracledb.Connection,
    username: str,
    full_name: str,
    role: str,
    password: Optional[str],
    current_user: AuthUser,
    ip: Optional[str] = None
) -> tuple[UserItem, str]:
    """
    Creates new staff account.
    Rule 3: Unique username, lowercase, no space.
    Rule 5: Sets phai_doi_mat_khau = TRUE.
    Generates strong temp password if not provided.
    """
    username = username.strip().lower()
    full_name = full_name.strip()
    role = role.strip().upper()

    role_id = get_role_id_by_code(conn, role)

    with conn.cursor() as cur:
        # Check duplicate username
        cur.execute(
            "SELECT COUNT(*) FROM nguoi_dung WHERE LOWER(ten_dang_nhap) = :username",
            username=username
        )
        if cur.fetchone()[0] > 0:
            raise BusinessException(code="USERNAME_EXISTS", detail=f"Tên đăng nhập '{username}' đã tồn tại")

        # Prepare password
        temp_password = password if (password and password.strip()) else generate_temp_password(12)
        pwd_hash = hash_password(temp_password)

        # Audit context
        set_audit_context(conn, current_user, f"Tạo tài khoản {username} ({role})", ip)

        # Insert user
        new_id_var = cur.var(oracledb.DB_TYPE_NUMBER)
        cur.execute(
            """
            INSERT INTO nguoi_dung (
                ten_dang_nhap, mat_khau_bam, ho_ten, vai_tro_id, trang_thai,
                so_lan_sai, khoa_den, phai_doi_mat_khau, ngay_tao
            ) VALUES (
                :username, :pwd_hash, :full_name, :role_id, 'HOAT_DONG',
                0, NULL, TRUE, SYSTIMESTAMP
            ) RETURNING nguoi_dung_id INTO :new_id
            """,
            username=username,
            pwd_hash=pwd_hash,
            full_name=full_name,
            role_id=role_id,
            new_id=new_id_var
        )
        new_id = int(new_id_var.getvalue()[0])

    created_user = get_user_by_id(conn, new_id)
    if not created_user:
        raise BusinessException(code="INTERNAL_SERVER_ERROR", detail="Không thể tạo người dùng")

    return created_user, temp_password


def update_user(
    conn: oracledb.Connection,
    user_id: int,
    full_name: str,
    new_role: str,
    current_user: AuthUser,
    ip: Optional[str] = None
) -> UserItem:
    """
    Updates staff full name and role.
    Rule 1: Cannot demote or change self role.
    Rule 2: Cannot demote last active manager.
    """
    target = get_user_by_id(conn, user_id)
    if not target:
        raise BusinessException(code="USER_NOT_FOUND", detail="Không tìm thấy tài khoản người dùng")

    new_role = new_role.strip().upper()
    full_name = full_name.strip()
    new_role_id = get_role_id_by_code(conn, new_role)

    # Rule 1: Self role change check
    if current_user.user_id == user_id and target.vaiTro != new_role:
        raise BusinessException(code="SELF_ROLE_CHANGE_NOT_ALLOWED", detail="Không thể tự thay đổi vai trò của chính mình")

    # Rule 2: Last manager demotion check
    if target.vaiTro == "QUAN_LY" and new_role != "QUAN_LY" and target.trangThai == "HOAT_DONG":
        active_mgrs = count_active_managers(conn)
        if active_mgrs <= 1:
            raise BusinessException(code="LAST_MANAGER", detail="Không thể hạ vai trò quản lý đang hoạt động cuối cùng của hệ thống")

    set_audit_context(
        conn,
        current_user,
        f"Cập nhật tài khoản ID {user_id} ({target.tenDangNhap}): họ tên '{full_name}', vai trò {new_role}",
        ip
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE nguoi_dung
               SET ho_ten = :full_name,
                   vai_tro_id = :role_id
             WHERE nguoi_dung_id = :user_id
            """,
            full_name=full_name,
            role_id=new_role_id,
            user_id=user_id
        )

    updated = get_user_by_id(conn, user_id)
    return updated


def toggle_lock(
    conn: oracledb.Connection,
    user_id: int,
    khoa: bool,
    current_user: AuthUser,
    ip: Optional[str] = None
) -> UserItem:
    """
    Locks or unlocks staff account.
    Rule 1: Cannot lock own account.
    Rule 2: Cannot lock last active manager.
    """
    target = get_user_by_id(conn, user_id)
    if not target:
        raise BusinessException(code="USER_NOT_FOUND", detail="Không tìm thấy tài khoản người dùng")

    # Rule 1: Self lock check
    if current_user.user_id == user_id and khoa:
        raise BusinessException(code="SELF_LOCK_NOT_ALLOWED", detail="Không thể tự khóa tài khoản của chính mình")

    # Rule 2: Last manager lock check
    if khoa and target.vaiTro == "QUAN_LY" and target.trangThai == "HOAT_DONG":
        active_mgrs = count_active_managers(conn)
        if active_mgrs <= 1:
            raise BusinessException(code="LAST_MANAGER", detail="Không thể khóa quản lý đang hoạt động cuối cùng của hệ thống")

    action_label = "Khóa" if khoa else "Mở khóa"
    new_status = "KHOA" if khoa else "HOAT_DONG"

    set_audit_context(
        conn,
        current_user,
        f"{action_label} tài khoản ID {user_id} ({target.tenDangNhap})",
        ip
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE nguoi_dung
               SET trang_thai = :st,
                   so_lan_sai = CASE WHEN :st = 'HOAT_DONG' THEN 0 ELSE so_lan_sai END,
                   khoa_den = CASE WHEN :st = 'HOAT_DONG' THEN NULL ELSE khoa_den END
             WHERE nguoi_dung_id = :user_id
            """,
            st=new_status,
            user_id=user_id
        )

    return get_user_by_id(conn, user_id)


def reset_password(
    conn: oracledb.Connection,
    user_id: int,
    current_user: AuthUser,
    ip: Optional[str] = None
) -> str:
    """
    Resets user password to random temp password and sets phai_doi_mat_khau = TRUE.
    Resets failed attempts and unlocks temporary lock.
    """
    target = get_user_by_id(conn, user_id)
    if not target:
        raise BusinessException(code="USER_NOT_FOUND", detail="Không tìm thấy tài khoản người dùng")

    temp_password = generate_temp_password(12)
    pwd_hash = hash_password(temp_password)

    set_audit_context(
        conn,
        current_user,
        f"Đặt lại mật khẩu cho tài khoản ID {user_id} ({target.tenDangNhap})",
        ip
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE nguoi_dung
               SET mat_khau_bam = :pwd_hash,
                   phai_doi_mat_khau = TRUE,
                   so_lan_sai = 0,
                   khoa_den = NULL
             WHERE nguoi_dung_id = :user_id
            """,
            pwd_hash=pwd_hash,
            user_id=user_id
        )

    return temp_password
