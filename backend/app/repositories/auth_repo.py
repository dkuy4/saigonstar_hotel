import logging
from typing import Optional, Any
from datetime import datetime
import oracledb

logger = logging.getLogger(__name__)

class AuthUserData:
    def __init__(
        self,
        user_id: int,
        username: str,
        password_hash: str,
        full_name: str,
        role: str,
        status: str,
        failed_attempts: int,
        locked_until: Optional[datetime],
        phai_doi_mat_khau: bool = False
    ):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role
        self.status = status
        self.failed_attempts = failed_attempts
        self.locked_until = locked_until
        self.phai_doi_mat_khau = phai_doi_mat_khau

def get_user_by_username(conn: oracledb.Connection, username: str) -> Optional[AuthUserData]:
    """Retrieves user by username with role details."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.nguoi_dung_id, u.ten_dang_nhap, u.mat_khau_bam, u.ho_ten,
                   v.ma_vai_tro, u.trang_thai, u.so_lan_sai, u.khoa_den, u.phai_doi_mat_khau
              FROM nguoi_dung u
              JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
             WHERE LOWER(u.ten_dang_nhap) = LOWER(:username)
            """,
            username=username.strip()
        )
        row = cur.fetchone()
        if not row:
            return None
        return AuthUserData(
            user_id=row[0],
            username=row[1],
            password_hash=row[2],
            full_name=row[3],
            role=row[4],
            status=row[5],
            failed_attempts=row[6] or 0,
            locked_until=row[7],
            phai_doi_mat_khau=bool(row[8])
        )

def get_user_by_id(conn: oracledb.Connection, user_id: int) -> Optional[AuthUserData]:
    """Retrieves user by ID."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.nguoi_dung_id, u.ten_dang_nhap, u.mat_khau_bam, u.ho_ten,
                   v.ma_vai_tro, u.trang_thai, u.so_lan_sai, u.khoa_den, u.phai_doi_mat_khau
              FROM nguoi_dung u
              JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
             WHERE u.nguoi_dung_id = :user_id
            """,
            user_id=user_id
        )
        row = cur.fetchone()
        if not row:
            return None
        return AuthUserData(
            user_id=row[0],
            username=row[1],
            password_hash=row[2],
            full_name=row[3],
            role=row[4],
            status=row[5],
            failed_attempts=row[6] or 0,
            locked_until=row[7],
            phai_doi_mat_khau=bool(row[8])
        )

def get_login_config_params(conn: oracledb.Connection) -> tuple[int, int]:
    """Fetches SO_LAN_DANG_NHAP_SAI_TOI_DA and PHUT_KHOA_TAM from system config."""
    with conn.cursor() as cur:
        try:
            max_attempts = cur.callfunc("pkg_cau_hinh.lay_so", oracledb.DB_TYPE_NUMBER, ["SO_LAN_DANG_NHAP_SAI_TOI_DA"])
        except Exception:
            max_attempts = 5
        try:
            lock_minutes = cur.callfunc("pkg_cau_hinh.lay_so", oracledb.DB_TYPE_NUMBER, ["PHUT_KHOA_TAM"])
        except Exception:
            lock_minutes = 15
        return int(max_attempts or 5), int(lock_minutes or 15)

def record_failed_attempt(
    conn: oracledb.Connection,
    user_id: int,
    current_attempts: int,
    max_attempts: int,
    lock_minutes: int
) -> bool:
    """
    Increments failed attempts count.
    If limit reached, sets temporary lock (khoa_den).
    Returns True if user became locked.
    """
    new_attempts = current_attempts + 1
    with conn.cursor() as cur:
        if new_attempts >= max_attempts:
            cur.execute(
                """
                UPDATE nguoi_dung
                   SET so_lan_sai = :attempts,
                       khoa_den = SYSTIMESTAMP + NUMTODSINTERVAL(:mins, 'MINUTE')
                 WHERE nguoi_dung_id = :user_id
                """,
                attempts=new_attempts,
                mins=lock_minutes,
                user_id=user_id
            )
            return True
        else:
            cur.execute(
                """
                UPDATE nguoi_dung
                   SET so_lan_sai = :attempts
                 WHERE nguoi_dung_id = :user_id
                """,
                attempts=new_attempts,
                user_id=user_id
            )
            return False

def reset_failed_attempts(conn: oracledb.Connection, user_id: int) -> None:
    """Resets failed attempts and unlocks user."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE nguoi_dung
               SET so_lan_sai = 0,
                   khoa_den = NULL
             WHERE nguoi_dung_id = :user_id
            """,
            user_id=user_id
        )

def update_password_hash(conn: oracledb.Connection, user_id: int, new_hash: str) -> None:
    """Updates password hash for user and clears phai_doi_mat_khau flag."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE nguoi_dung
               SET mat_khau_bam = :new_hash,
                   phai_doi_mat_khau = FALSE,
                   so_lan_sai = 0,
                   khoa_den = NULL
             WHERE nguoi_dung_id = :user_id
            """,
            new_hash=new_hash,
            user_id=user_id
        )
