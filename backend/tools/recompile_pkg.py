import re
import oracledb

with open('D:/HQT-CSDL/hotel/db/08_pkg_nghiep_vu.sql', 'r', encoding='utf-8') as f:
    sql_text = f.read()

conn = oracledb.connect(user='hotel_owner', password='HotelOwner123#', dsn='localhost:1521/FREEPDB1')
with conn.cursor() as cur:
    raw_blocks = sql_text.split('\n/\n')
    for block in raw_blocks:
        b = block.strip()
        if not b:
            continue
        # Remove comments before the first CREATE
        match = re.search(r'\bCREATE\b', b, re.IGNORECASE)
        if match:
            b = b[match.start():]
            try:
                cur.execute(b)
            except Exception as e:
                print('Error on block:\n', b[:120], '\n->', e)
                raise
    print('All blocks in 08_pkg_nghiep_vu.sql compiled successfully!')

    cur.execute("SELECT name, type, line, position, text FROM user_errors WHERE name = 'PKG_DAT_PHONG'")
    errs = cur.fetchall()
    if errs:
        for err in errs:
            print(err)
    else:
        print('PKG_DAT_PHONG has 0 compilation errors!')
conn.close()
