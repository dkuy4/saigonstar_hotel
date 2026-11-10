-- =====================================================================
-- 10_jobs.sql: tác vụ nền bằng DBMS_SCHEDULER (FR-52). Chạy sau 08_pkg_nghiep_vu.sql, bằng chủ schema.
-- [CẦN KIỂM TRA] DBMS_SCHEDULER chưa được chạy thử trên Oracle 23ai Free. Nếu CREATE_JOB báo lỗi quyền hoặc không hỗ trợ,
-- gọi hai thủ tục PKG_DAT_PHONG.JOB_HET_HAN_GIU_CHO và JOB_NO_SHOW từ tiến trình nền của API theo chu kỳ tương tự (SRS mục 9.3).
-- =====================================================================
BEGIN
  DBMS_SCHEDULER.CREATE_JOB(
    job_name        => 'JOB_HET_HAN_GIU_CHO',
    job_type        => 'STORED_PROCEDURE',
    job_action      => 'PKG_DAT_PHONG.JOB_HET_HAN_GIU_CHO',
    repeat_interval => 'FREQ=MINUTELY;INTERVAL=1',
    enabled         => TRUE,
    comments        => 'BR-18: HOLD hết hạn thành EXPIRED');
  DBMS_SCHEDULER.CREATE_JOB(
    job_name        => 'JOB_TU_NO_SHOW',
    job_type        => 'STORED_PROCEDURE',
    job_action      => 'PKG_DAT_PHONG.JOB_NO_SHOW',
    repeat_interval => 'FREQ=MINUTELY;INTERVAL=5',
    enabled         => TRUE,
    comments        => 'BR-27, BR-28: tự chuyển NO_SHOW');
END;
/
-- Gỡ job:  BEGIN DBMS_SCHEDULER.DROP_JOB('JOB_HET_HAN_GIU_CHO'); DBMS_SCHEDULER.DROP_JOB('JOB_TU_NO_SHOW'); END; /
