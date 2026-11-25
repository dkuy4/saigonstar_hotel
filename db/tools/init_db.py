import oracledb
import subprocess

def main():
    conn = oracledb.connect(user='system', password='Oracle123', dsn='localhost:1521/FREEPDB1')
    cur = conn.cursor()

    try:
        cur.execute("DROP USER hotel_app CASCADE")
        print("Dropped old hotel_app")
    except Exception:
        pass

    try:
        cur.execute("DROP USER hotel_owner CASCADE")
        print("Dropped old hotel_owner")
    except Exception:
        pass

    cur.execute("CREATE USER hotel_owner IDENTIFIED BY HotelOwner123# DEFAULT TABLESPACE users QUOTA UNLIMITED ON users")
    cur.execute("GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE PROCEDURE, CREATE TRIGGER, CREATE JOB, CREATE VIEW, CREATE SYNONYM TO hotel_owner")
    print("Created hotel_owner successfully!")
    conn.close()

if __name__ == '__main__':
    main()
