import sys, os
sys.path.insert(0, os.path.abspath("."))
from datetime import datetime, timezone, timedelta
from app.db import get_pool
from app.repositories.booking_repo import BookingRepository

pool = get_pool()
conn = pool.acquire()
with conn.cursor() as cur:
    cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")

rtid = BookingRepository.get_room_type_id(conn, "STANDARD")
t1 = datetime.now(timezone.utc) + timedelta(days=5)
t2 = t1 + timedelta(days=2)
rms = BookingRepository.get_suggested_rooms(conn, rtid, t1, t2)
print("Found rooms for STANDARD:", len(rms))
for r in rms[:5]:
    print("Room:", r)
conn.close()
