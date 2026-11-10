-- =====================================================================
-- 00_run_all.sql: dựng toàn bộ cơ sở dữ liệu rồi chạy kiểm thử.
-- Kết nối vào schema của ứng dụng trong PDB FREEPDB1 rồi chạy:  @00_run_all.sql
--   SQLcl:    sql hotel_owner/<mat_khau>@localhost:1521/FREEPDB1 @00_run_all.sql
-- Làm lại từ đầu: @99_drop_all.sql trước.
-- (10_jobs.sql tạo tác vụ nền DBMS_SCHEDULER, chạy riêng sau khi kiểm thử đạt.)
-- Thứ tự quan trọng: seed chạy trước package và trigger để dữ liệu khởi tạo không đi qua trigger kiểm tra giá
-- và không sinh nhật ký; package phải có trước trigger vì trigger gọi package.
-- =====================================================================
SET DEFINE OFF
SET SERVEROUTPUT ON SIZE UNLIMITED
@01_schema.sql
@02_seed.sql
@03_packages.sql
@04_triggers.sql
@05_trigger_nhat_ky.sql
@08_pkg_nghiep_vu.sql
@06_tests.sql
@09_tests_nghiep_vu.sql
-- Kiểm tra đối tượng lỗi biên dịch (kết quả phải rỗng):
SELECT object_name, object_type, status FROM user_objects WHERE status <> 'VALID';
SELECT name, type, line, text FROM user_errors ORDER BY name, sequence;
