-- =====================================================================
-- 99_drop_all.sql: gỡ toàn bộ đối tượng của schema (bước lùi của 01 đến 05). Chỉ dùng trên môi trường phát triển.
-- Xóa bảng kéo theo trigger của bảng; package và sequence xóa riêng.
-- =====================================================================
BEGIN
  FOR r IN (SELECT table_name FROM user_tables
             WHERE table_name IN ('HANG_DOI_EMAIL','CHI_TIET_HOA_DON','HOA_DON','BO_DEM_HOA_DON','HOAN_TIEN','GIAO_DICH_THANH_TOAN',
                                  'DAT_PHONG_DOAN','DAT_PHONG','GIAY_TO_KHACH','KHACH_HANG','PHONG','BANG_GIA','LOAI_PHONG_DICH',
                                  'LOAI_PHONG','NHAT_KY_KIEM_TOAN','NGUOI_DUNG','VAI_TRO','NOI_DUNG_DICH','CAU_HINH_HE_THONG',
                                  'TY_GIA','NGON_NGU')
             ORDER BY CASE table_name
                        WHEN 'HANG_DOI_EMAIL' THEN 1 WHEN 'CHI_TIET_HOA_DON' THEN 2 WHEN 'HOA_DON' THEN 3 ELSE 4 END) LOOP
    EXECUTE IMMEDIATE 'DROP TABLE ' || r.table_name || ' CASCADE CONSTRAINTS PURGE';
  END LOOP;
  FOR p IN (SELECT object_name FROM user_objects WHERE object_type = 'PACKAGE'
             AND object_name IN ('PKG_CAU_HINH','PKG_KIEM_TRA_TRUNG','PKG_NGU_CANH','PKG_NHAT_KY','PKG_HOA_DON','PKG_EMAIL','PKG_GIA','PKG_THANH_TOAN','PKG_PHONG','PKG_DAT_PHONG','PKG_BAO_CAO')) LOOP
    EXECUTE IMMEDIATE 'DROP PACKAGE ' || p.object_name;
  END LOOP;
  FOR j IN (SELECT job_name FROM user_scheduler_jobs WHERE job_name IN ('JOB_HET_HAN_GIU_CHO','JOB_TU_NO_SHOW')) LOOP
    DBMS_SCHEDULER.DROP_JOB(j.job_name);
  END LOOP;
  FOR s IN (SELECT sequence_name FROM user_sequences WHERE sequence_name = 'SEQ_MA_TRA_CUU') LOOP
    EXECUTE IMMEDIATE 'DROP SEQUENCE ' || s.sequence_name;
  END LOOP;
END;
/
