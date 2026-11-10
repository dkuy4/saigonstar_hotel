import oracledb
from typing import Optional

def set_db_context(
    conn: oracledb.Connection,
    nguoi_id: Optional[int] = None,
    vai_tro: str = "KHACH",
    kenh: str = "WEB",
    ip: Optional[str] = None,
    ly_do: Optional[str] = None
) -> None:
    """
    Sets the session context in Oracle via PKG_NGU_CANH.DAT (BR-47).
    This ensures audit triggers automatically record the correct user, role, channel and IP.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            BEGIN
                pkg_ngu_canh.dat(
                    p_nguoi_id => :nguoi_id,
                    p_vai_tro  => :vai_tro,
                    p_kenh     => :kenh,
                    p_ip       => :ip,
                    p_ly_do    => :ly_do
                );
            END;
            """,
            nguoi_id=nguoi_id,
            vai_tro=vai_tro,
            kenh=kenh,
            ip=ip,
            ly_do=ly_do
        )

def clear_db_context(conn: oracledb.Connection) -> None:
    """Resets session context in Oracle via PKG_NGU_CANH.XOA."""
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN pkg_ngu_canh.xoa; END;")
    except Exception:
        pass
