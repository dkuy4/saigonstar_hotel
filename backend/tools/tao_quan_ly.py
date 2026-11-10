import os
import sys
import oracledb

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.security import hash_password

def seed_initial_staff():
    """
    Seeds initial staff accounts for the 3 roles:
    1. QUAN_LY (Manager)
    2. LE_TAN (Receptionist)
    3. BUONG_PHONG (Housekeeping)
    Passwords are read from environment variables or defaults, and hashed using backend bcrypt.
    """
    admin_user = os.getenv("ADMIN_USERNAME", "quanly")
    admin_pass = os.getenv("ADMIN_PASSWORD", "QuanLy123#")
    admin_name = os.getenv("ADMIN_NAME", "Quản lý Nguyễn Văn A")

    letan_user = os.getenv("LETAN_USERNAME", "letan")
    letan_pass = os.getenv("LETAN_PASSWORD", "LeTan123#")
    letan_name = os.getenv("LETAN_NAME", "Lễ tân Trần Thị B")

    housekeeping_user = os.getenv("BUONGPHONG_USERNAME", "buongphong")
    housekeeping_pass = os.getenv("BUONGPHONG_PASSWORD", "BuongPhong123#")
    housekeeping_name = os.getenv("BUONGPHONG_NAME", "Buồng phòng Lê Văn C")

    users_to_create = [
        {"username": admin_user, "password": admin_pass, "name": admin_name, "role": "QUAN_LY"},
        {"username": letan_user, "password": letan_pass, "name": letan_name, "role": "LE_TAN"},
        {"username": housekeeping_user, "password": housekeeping_pass, "name": housekeeping_name, "role": "BUONG_PHONG"}
    ]

    print(f"Connecting to Oracle at {settings.ORA_DSN} as {settings.ORA_USER}...")
    conn = oracledb.connect(
        user=settings.ORA_USER,
        password=settings.ORA_PASSWORD,
        dsn=settings.ORA_DSN
    )

    with conn.cursor() as cur:
        if settings.ORA_SCHEMA:
            cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {settings.ORA_SCHEMA}")

        # Fetch role IDs
        cur.execute("SELECT vai_tro_id, ma_vai_tro FROM vai_tro")
        role_map = {row[1]: row[0] for row in cur.fetchall()}
        print("Role map:", role_map)

        for u in users_to_create:
            role_id = role_map.get(u["role"])
            if not role_id:
                print(f"Error: Role {u['role']} not found!")
                continue

            pw_hash = hash_password(u["password"])
            
            # Check if user already exists
            cur.execute("SELECT nguoi_dung_id FROM nguoi_dung WHERE LOWER(ten_dang_nhap) = LOWER(:u)", u=u["username"])
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    """
                    UPDATE nguoi_dung
                       SET mat_khau_bam = :pw,
                           ho_ten = :name,
                           vai_tro_id = :role_id,
                           trang_thai = 'HOAT_DONG',
                           so_lan_sai = 0,
                           khoa_den = NULL
                     WHERE nguoi_dung_id = :id
                    """,
                    pw=pw_hash,
                    name=u["name"],
                    role_id=role_id,
                    id=existing[0]
                )
                print(f"Updated user: {u['username']} ({u['role']})")
            else:
                cur.execute(
                    """
                    INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_bam, ho_ten, vai_tro_id, trang_thai)
                    VALUES (:username, :pw, :name, :role_id, 'HOAT_DONG')
                    """,
                    username=u["username"],
                    pw=pw_hash,
                    name=u["name"],
                    role_id=role_id
                )
                print(f"Created user: {u['username']} ({u['role']})")

        conn.commit()
    conn.close()
    print("Staff accounts successfully initialized!")

if __name__ == "__main__":
    seed_initial_staff()
