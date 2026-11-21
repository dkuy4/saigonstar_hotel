import oracledb

conn = oracledb.connect(user='hotel_owner', password='HotelOwner123#', dsn='localhost:1521/FREEPDB1')
cur = conn.cursor()
cur.execute("SELECT user, sys_context('USERENV','CON_NAME') FROM dual")
print("Connected successfully as:", cur.fetchone())
conn.close()
