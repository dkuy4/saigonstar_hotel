-- =====================================================================
-- 07_user_ung_dung.sql (tùy chọn): tài khoản ứng dụng quyền tối thiểu cho NFR-04, NFR-12, NFR-26.
-- Chạy bằng tài khoản DBA trong PDB (FREEPDB1). Không để mật khẩu trong script: nhập khi chạy.
-- Ứng dụng kết nối bằng HOTEL_APP, đặt ALTER SESSION SET CURRENT_SCHEMA = <chủ schema> sau khi kết nối.
-- Nhật ký chỉ ghi qua trigger và PKG_NHAT_KY (chạy quyền chủ schema), nên ứng dụng chỉ cần SELECT trên bảng nhật ký.
-- =====================================================================
DEFINE chu_schema = HOTEL_OWNER
ACCEPT mat_khau CHAR PROMPT 'Mật khẩu cho HOTEL_APP: ' HIDE

CREATE USER hotel_app IDENTIFIED BY "&mat_khau" DEFAULT TABLESPACE users QUOTA 0 ON users;
GRANT CREATE SESSION TO hotel_app;

BEGIN
  FOR r IN (SELECT table_name FROM all_tables WHERE owner = UPPER('&chu_schema')) LOOP
    IF r.table_name = 'NHAT_KY_KIEM_TOAN' THEN
      EXECUTE IMMEDIATE 'GRANT SELECT ON &chu_schema..' || r.table_name || ' TO hotel_app';
    ELSIF r.table_name IN ('HOA_DON', 'CHI_TIET_HOA_DON') THEN
      EXECUTE IMMEDIATE 'GRANT SELECT, INSERT ON &chu_schema..' || r.table_name || ' TO hotel_app';
    ELSIF r.table_name IN ('GIAY_TO_KHACH', 'LOAI_PHONG_DICH', 'NOI_DUNG_DICH') THEN
      -- xóa giấy tờ khi khách yêu cầu (NFR-15); xóa bản dịch khi quản lý đổi nội dung
      EXECUTE IMMEDIATE 'GRANT SELECT, INSERT, UPDATE, DELETE ON &chu_schema..' || r.table_name || ' TO hotel_app';
    ELSE
      EXECUTE IMMEDIATE 'GRANT SELECT, INSERT, UPDATE ON &chu_schema..' || r.table_name || ' TO hotel_app';
    END IF;
  END LOOP;
  FOR p IN (SELECT object_name FROM all_objects WHERE owner = UPPER('&chu_schema') AND object_type = 'PACKAGE') LOOP
    EXECUTE IMMEDIATE 'GRANT EXECUTE ON &chu_schema..' || p.object_name || ' TO hotel_app';
  END LOOP;
END;
/
