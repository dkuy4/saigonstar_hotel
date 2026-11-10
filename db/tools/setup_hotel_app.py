import oracledb

conn = oracledb.connect(user='system', password='1', dsn='localhost:1521/FREEPDB1')
cur = conn.cursor()

# Drop hotel_app if exists
try:
    cur.execute("DROP USER hotel_app CASCADE")
    print("Dropped old hotel_app")
except Exception as e:
    pass

# Create hotel_app
cur.execute('CREATE USER hotel_app IDENTIFIED BY "HotelApp123#" DEFAULT TABLESPACE users QUOTA 0 ON users')
cur.execute('GRANT CREATE SESSION TO hotel_app')
print("Created hotel_app user")

# Grant table privileges
chu_schema = 'HOTEL_OWNER'
cur.execute(f"SELECT table_name FROM all_tables WHERE owner = '{chu_schema}'")
tables = [r[0] for r in cur.fetchall()]
print(f"Granting on {len(tables)} tables...")

for t in tables:
    if t == 'NHAT_KY_KIEM_TOAN':
        cur.execute(f"GRANT SELECT ON {chu_schema}.{t} TO hotel_app")
    elif t in ('HOA_DON', 'CHI_TIET_HOA_DON'):
        cur.execute(f"GRANT SELECT, INSERT ON {chu_schema}.{t} TO hotel_app")
    elif t in ('GIAY_TO_KHACH', 'LOAI_PHONG_DICH', 'NOI_DUNG_DICH'):
        cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {chu_schema}.{t} TO hotel_app")
    else:
        cur.execute(f"GRANT SELECT, INSERT, UPDATE ON {chu_schema}.{t} TO hotel_app")

# Grant execute on packages
cur.execute(f"SELECT object_name FROM all_objects WHERE owner = '{chu_schema}' AND object_type = 'PACKAGE'")
packages = [r[0] for r in cur.fetchall()]
print(f"Granting EXECUTE on {len(packages)} packages...")

for p in packages:
    cur.execute(f"GRANT EXECUTE ON {chu_schema}.{p} TO hotel_app")

# Grant select on sequences
cur.execute(f"SELECT sequence_name FROM all_sequences WHERE sequence_owner = '{chu_schema}'")
sequences = [r[0] for r in cur.fetchall()]
for s in sequences:
    cur.execute(f"GRANT SELECT ON {chu_schema}.{s} TO hotel_app")

print("All permissions granted to hotel_app!")
conn.close()

# Test connecting as hotel_app and querying through synonym or current_schema
conn2 = oracledb.connect(user='hotel_app', password='HotelApp123#', dsn='localhost:1521/FREEPDB1')
cur2 = conn2.cursor()
cur2.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
cur2.execute("SELECT COUNT(*) FROM phong")
print("hotel_app test query count(phong):", cur2.fetchone()[0])
conn2.close()
