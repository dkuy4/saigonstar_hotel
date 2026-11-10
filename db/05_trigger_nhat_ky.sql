-- =====================================================================
-- 05_trigger_nhat_ky.sql: trigger ghi nhật ký kiểm toán tự động (FR-45, BR-46, BR-47)
-- FILE SINH TỰ ĐỘNG bởi tools/gen_audit.py từ 01_schema.sql. Không sửa tay; đổi schema thì sinh lại.
-- Người thực hiện, vai trò, kênh, IP, lý do lấy từ PKG_NGU_CANH (API gọi PKG_NGU_CANH.DAT đầu mỗi giao dịch).
-- Cột mat_khau_bam của NGUOI_DUNG không đưa vào nhật ký.
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_dat_phong
AFTER INSERT OR UPDATE OR DELETE ON dat_phong
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.dat_phong_id);
    SELECT JSON_OBJECT(
        'dat_phong_id' VALUE :NEW.dat_phong_id,
        'ma_tra_cuu' VALUE :NEW.ma_tra_cuu,
        'khach_hang_id' VALUE :NEW.khach_hang_id,
        'loai_dat' VALUE :NEW.loai_dat,
        'kenh_dat' VALUE :NEW.kenh_dat,
        'trang_thai' VALUE :NEW.trang_thai,
        'tu_luc' VALUE :NEW.tu_luc,
        'den_luc' VALUE :NEW.den_luc,
        'han_giu_cho' VALUE :NEW.han_giu_cho,
        'so_khach' VALUE :NEW.so_khach,
        'don_gia_ap_dung' VALUE :NEW.don_gia_ap_dung,
        'don_gia_ngay_ap_dung' VALUE :NEW.don_gia_ngay_ap_dung,
        'tien_phong' VALUE :NEW.tien_phong,
        'thue_suat' VALUE :NEW.thue_suat,
        'tien_vat' VALUE :NEW.tien_vat,
        'tong_tien' VALUE :NEW.tong_tien,
        'ngon_ngu' VALUE :NEW.ngon_ngu,
        'dong_y_chinh_sach_luc' VALUE :NEW.dong_y_chinh_sach_luc,
        'nhan_thuc_te' VALUE :NEW.nhan_thuc_te,
        'tra_thuc_te' VALUE :NEW.tra_thuc_te,
        'ly_do_huy' VALUE :NEW.ly_do_huy,
        'nguoi_tao_id' VALUE :NEW.nguoi_tao_id,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.dat_phong_id);
    SELECT JSON_OBJECT(
        'dat_phong_id' VALUE :OLD.dat_phong_id,
        'ma_tra_cuu' VALUE :OLD.ma_tra_cuu,
        'khach_hang_id' VALUE :OLD.khach_hang_id,
        'loai_dat' VALUE :OLD.loai_dat,
        'kenh_dat' VALUE :OLD.kenh_dat,
        'trang_thai' VALUE :OLD.trang_thai,
        'tu_luc' VALUE :OLD.tu_luc,
        'den_luc' VALUE :OLD.den_luc,
        'han_giu_cho' VALUE :OLD.han_giu_cho,
        'so_khach' VALUE :OLD.so_khach,
        'don_gia_ap_dung' VALUE :OLD.don_gia_ap_dung,
        'don_gia_ngay_ap_dung' VALUE :OLD.don_gia_ngay_ap_dung,
        'tien_phong' VALUE :OLD.tien_phong,
        'thue_suat' VALUE :OLD.thue_suat,
        'tien_vat' VALUE :OLD.tien_vat,
        'tong_tien' VALUE :OLD.tong_tien,
        'ngon_ngu' VALUE :OLD.ngon_ngu,
        'dong_y_chinh_sach_luc' VALUE :OLD.dong_y_chinh_sach_luc,
        'nhan_thuc_te' VALUE :OLD.nhan_thuc_te,
        'tra_thuc_te' VALUE :OLD.tra_thuc_te,
        'ly_do_huy' VALUE :OLD.ly_do_huy,
        'nguoi_tao_id' VALUE :OLD.nguoi_tao_id,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := CASE WHEN :NEW.trang_thai <> :OLD.trang_thai THEN 'DOI_TRANG_THAI' ELSE 'SUA' END;
    v_khoa := TO_CHAR(:NEW.dat_phong_id);
    SELECT JSON_OBJECT(
        'dat_phong_id' VALUE :OLD.dat_phong_id,
        'ma_tra_cuu' VALUE :OLD.ma_tra_cuu,
        'khach_hang_id' VALUE :OLD.khach_hang_id,
        'loai_dat' VALUE :OLD.loai_dat,
        'kenh_dat' VALUE :OLD.kenh_dat,
        'trang_thai' VALUE :OLD.trang_thai,
        'tu_luc' VALUE :OLD.tu_luc,
        'den_luc' VALUE :OLD.den_luc,
        'han_giu_cho' VALUE :OLD.han_giu_cho,
        'so_khach' VALUE :OLD.so_khach,
        'don_gia_ap_dung' VALUE :OLD.don_gia_ap_dung,
        'don_gia_ngay_ap_dung' VALUE :OLD.don_gia_ngay_ap_dung,
        'tien_phong' VALUE :OLD.tien_phong,
        'thue_suat' VALUE :OLD.thue_suat,
        'tien_vat' VALUE :OLD.tien_vat,
        'tong_tien' VALUE :OLD.tong_tien,
        'ngon_ngu' VALUE :OLD.ngon_ngu,
        'dong_y_chinh_sach_luc' VALUE :OLD.dong_y_chinh_sach_luc,
        'nhan_thuc_te' VALUE :OLD.nhan_thuc_te,
        'tra_thuc_te' VALUE :OLD.tra_thuc_te,
        'ly_do_huy' VALUE :OLD.ly_do_huy,
        'nguoi_tao_id' VALUE :OLD.nguoi_tao_id,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'dat_phong_id' VALUE :NEW.dat_phong_id,
        'ma_tra_cuu' VALUE :NEW.ma_tra_cuu,
        'khach_hang_id' VALUE :NEW.khach_hang_id,
        'loai_dat' VALUE :NEW.loai_dat,
        'kenh_dat' VALUE :NEW.kenh_dat,
        'trang_thai' VALUE :NEW.trang_thai,
        'tu_luc' VALUE :NEW.tu_luc,
        'den_luc' VALUE :NEW.den_luc,
        'han_giu_cho' VALUE :NEW.han_giu_cho,
        'so_khach' VALUE :NEW.so_khach,
        'don_gia_ap_dung' VALUE :NEW.don_gia_ap_dung,
        'don_gia_ngay_ap_dung' VALUE :NEW.don_gia_ngay_ap_dung,
        'tien_phong' VALUE :NEW.tien_phong,
        'thue_suat' VALUE :NEW.thue_suat,
        'tien_vat' VALUE :NEW.tien_vat,
        'tong_tien' VALUE :NEW.tong_tien,
        'ngon_ngu' VALUE :NEW.ngon_ngu,
        'dong_y_chinh_sach_luc' VALUE :NEW.dong_y_chinh_sach_luc,
        'nhan_thuc_te' VALUE :NEW.nhan_thuc_te,
        'tra_thuc_te' VALUE :NEW.tra_thuc_te,
        'ly_do_huy' VALUE :NEW.ly_do_huy,
        'nguoi_tao_id' VALUE :NEW.nguoi_tao_id,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('DAT_PHONG', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_dat_phong;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_dat_phong_doan
AFTER INSERT OR UPDATE OR DELETE ON dat_phong_doan
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.doan_id);
    SELECT JSON_OBJECT(
        'doan_id' VALUE :NEW.doan_id,
        'dat_phong_id' VALUE :NEW.dat_phong_id,
        'phong_id' VALUE :NEW.phong_id,
        'tu_luc' VALUE :NEW.tu_luc,
        'den_luc' VALUE :NEW.den_luc,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.doan_id);
    SELECT JSON_OBJECT(
        'doan_id' VALUE :OLD.doan_id,
        'dat_phong_id' VALUE :OLD.dat_phong_id,
        'phong_id' VALUE :OLD.phong_id,
        'tu_luc' VALUE :OLD.tu_luc,
        'den_luc' VALUE :OLD.den_luc,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := 'SUA';
    v_khoa := TO_CHAR(:NEW.doan_id);
    SELECT JSON_OBJECT(
        'doan_id' VALUE :OLD.doan_id,
        'dat_phong_id' VALUE :OLD.dat_phong_id,
        'phong_id' VALUE :OLD.phong_id,
        'tu_luc' VALUE :OLD.tu_luc,
        'den_luc' VALUE :OLD.den_luc,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'doan_id' VALUE :NEW.doan_id,
        'dat_phong_id' VALUE :NEW.dat_phong_id,
        'phong_id' VALUE :NEW.phong_id,
        'tu_luc' VALUE :NEW.tu_luc,
        'den_luc' VALUE :NEW.den_luc,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('DAT_PHONG_DOAN', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_dat_phong_doan;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_phong
AFTER INSERT OR UPDATE OR DELETE ON phong
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.phong_id);
    SELECT JSON_OBJECT(
        'phong_id' VALUE :NEW.phong_id,
        'ma_phong' VALUE :NEW.ma_phong,
        'so_tang' VALUE :NEW.so_tang,
        'loai_phong_id' VALUE :NEW.loai_phong_id,
        'trang_thai' VALUE :NEW.trang_thai,
        'dang_hoat_dong' VALUE :NEW.dang_hoat_dong,
        'ghi_chu' VALUE :NEW.ghi_chu,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.phong_id);
    SELECT JSON_OBJECT(
        'phong_id' VALUE :OLD.phong_id,
        'ma_phong' VALUE :OLD.ma_phong,
        'so_tang' VALUE :OLD.so_tang,
        'loai_phong_id' VALUE :OLD.loai_phong_id,
        'trang_thai' VALUE :OLD.trang_thai,
        'dang_hoat_dong' VALUE :OLD.dang_hoat_dong,
        'ghi_chu' VALUE :OLD.ghi_chu,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := CASE WHEN :NEW.trang_thai <> :OLD.trang_thai THEN 'DOI_TRANG_THAI' ELSE 'SUA' END;
    v_khoa := TO_CHAR(:NEW.phong_id);
    SELECT JSON_OBJECT(
        'phong_id' VALUE :OLD.phong_id,
        'ma_phong' VALUE :OLD.ma_phong,
        'so_tang' VALUE :OLD.so_tang,
        'loai_phong_id' VALUE :OLD.loai_phong_id,
        'trang_thai' VALUE :OLD.trang_thai,
        'dang_hoat_dong' VALUE :OLD.dang_hoat_dong,
        'ghi_chu' VALUE :OLD.ghi_chu,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'phong_id' VALUE :NEW.phong_id,
        'ma_phong' VALUE :NEW.ma_phong,
        'so_tang' VALUE :NEW.so_tang,
        'loai_phong_id' VALUE :NEW.loai_phong_id,
        'trang_thai' VALUE :NEW.trang_thai,
        'dang_hoat_dong' VALUE :NEW.dang_hoat_dong,
        'ghi_chu' VALUE :NEW.ghi_chu,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('PHONG', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_phong;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_giao_dich_thanh_toan
AFTER INSERT OR UPDATE OR DELETE ON giao_dich_thanh_toan
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.giao_dich_id);
    SELECT JSON_OBJECT(
        'giao_dich_id' VALUE :NEW.giao_dich_id,
        'dat_phong_id' VALUE :NEW.dat_phong_id,
        'kenh' VALUE :NEW.kenh,
        'phuong_thuc' VALUE :NEW.phuong_thuc,
        'so_tien' VALUE :NEW.so_tien,
        'trang_thai' VALUE :NEW.trang_thai,
        'ma_tham_chieu_cong' VALUE :NEW.ma_tham_chieu_cong,
        'ngay_giao_dich' VALUE :NEW.ngay_giao_dich,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.giao_dich_id);
    SELECT JSON_OBJECT(
        'giao_dich_id' VALUE :OLD.giao_dich_id,
        'dat_phong_id' VALUE :OLD.dat_phong_id,
        'kenh' VALUE :OLD.kenh,
        'phuong_thuc' VALUE :OLD.phuong_thuc,
        'so_tien' VALUE :OLD.so_tien,
        'trang_thai' VALUE :OLD.trang_thai,
        'ma_tham_chieu_cong' VALUE :OLD.ma_tham_chieu_cong,
        'ngay_giao_dich' VALUE :OLD.ngay_giao_dich,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := CASE WHEN :NEW.trang_thai <> :OLD.trang_thai THEN 'DOI_TRANG_THAI' ELSE 'SUA' END;
    v_khoa := TO_CHAR(:NEW.giao_dich_id);
    SELECT JSON_OBJECT(
        'giao_dich_id' VALUE :OLD.giao_dich_id,
        'dat_phong_id' VALUE :OLD.dat_phong_id,
        'kenh' VALUE :OLD.kenh,
        'phuong_thuc' VALUE :OLD.phuong_thuc,
        'so_tien' VALUE :OLD.so_tien,
        'trang_thai' VALUE :OLD.trang_thai,
        'ma_tham_chieu_cong' VALUE :OLD.ma_tham_chieu_cong,
        'ngay_giao_dich' VALUE :OLD.ngay_giao_dich,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'giao_dich_id' VALUE :NEW.giao_dich_id,
        'dat_phong_id' VALUE :NEW.dat_phong_id,
        'kenh' VALUE :NEW.kenh,
        'phuong_thuc' VALUE :NEW.phuong_thuc,
        'so_tien' VALUE :NEW.so_tien,
        'trang_thai' VALUE :NEW.trang_thai,
        'ma_tham_chieu_cong' VALUE :NEW.ma_tham_chieu_cong,
        'ngay_giao_dich' VALUE :NEW.ngay_giao_dich,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('GIAO_DICH_THANH_TOAN', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_giao_dich_thanh_toan;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_hoan_tien
AFTER INSERT OR UPDATE OR DELETE ON hoan_tien
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.hoan_tien_id);
    SELECT JSON_OBJECT(
        'hoan_tien_id' VALUE :NEW.hoan_tien_id,
        'giao_dich_id' VALUE :NEW.giao_dich_id,
        'so_tien' VALUE :NEW.so_tien,
        'ly_do' VALUE :NEW.ly_do,
        'trang_thai' VALUE :NEW.trang_thai,
        'nguoi_de_nghi_id' VALUE :NEW.nguoi_de_nghi_id,
        'nguoi_duyet_id' VALUE :NEW.nguoi_duyet_id,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.hoan_tien_id);
    SELECT JSON_OBJECT(
        'hoan_tien_id' VALUE :OLD.hoan_tien_id,
        'giao_dich_id' VALUE :OLD.giao_dich_id,
        'so_tien' VALUE :OLD.so_tien,
        'ly_do' VALUE :OLD.ly_do,
        'trang_thai' VALUE :OLD.trang_thai,
        'nguoi_de_nghi_id' VALUE :OLD.nguoi_de_nghi_id,
        'nguoi_duyet_id' VALUE :OLD.nguoi_duyet_id,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := CASE WHEN :NEW.trang_thai <> :OLD.trang_thai THEN 'DOI_TRANG_THAI' ELSE 'SUA' END;
    v_khoa := TO_CHAR(:NEW.hoan_tien_id);
    SELECT JSON_OBJECT(
        'hoan_tien_id' VALUE :OLD.hoan_tien_id,
        'giao_dich_id' VALUE :OLD.giao_dich_id,
        'so_tien' VALUE :OLD.so_tien,
        'ly_do' VALUE :OLD.ly_do,
        'trang_thai' VALUE :OLD.trang_thai,
        'nguoi_de_nghi_id' VALUE :OLD.nguoi_de_nghi_id,
        'nguoi_duyet_id' VALUE :OLD.nguoi_duyet_id,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'hoan_tien_id' VALUE :NEW.hoan_tien_id,
        'giao_dich_id' VALUE :NEW.giao_dich_id,
        'so_tien' VALUE :NEW.so_tien,
        'ly_do' VALUE :NEW.ly_do,
        'trang_thai' VALUE :NEW.trang_thai,
        'nguoi_de_nghi_id' VALUE :NEW.nguoi_de_nghi_id,
        'nguoi_duyet_id' VALUE :NEW.nguoi_duyet_id,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('HOAN_TIEN', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_hoan_tien;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_bang_gia
AFTER INSERT OR UPDATE OR DELETE ON bang_gia
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.bang_gia_id);
    SELECT JSON_OBJECT(
        'bang_gia_id' VALUE :NEW.bang_gia_id,
        'loai_phong_id' VALUE :NEW.loai_phong_id,
        'loai_gia' VALUE :NEW.loai_gia,
        'don_gia' VALUE :NEW.don_gia,
        'hieu_luc_tu' VALUE :NEW.hieu_luc_tu,
        'hieu_luc_den' VALUE :NEW.hieu_luc_den,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.bang_gia_id);
    SELECT JSON_OBJECT(
        'bang_gia_id' VALUE :OLD.bang_gia_id,
        'loai_phong_id' VALUE :OLD.loai_phong_id,
        'loai_gia' VALUE :OLD.loai_gia,
        'don_gia' VALUE :OLD.don_gia,
        'hieu_luc_tu' VALUE :OLD.hieu_luc_tu,
        'hieu_luc_den' VALUE :OLD.hieu_luc_den,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := 'SUA';
    v_khoa := TO_CHAR(:NEW.bang_gia_id);
    SELECT JSON_OBJECT(
        'bang_gia_id' VALUE :OLD.bang_gia_id,
        'loai_phong_id' VALUE :OLD.loai_phong_id,
        'loai_gia' VALUE :OLD.loai_gia,
        'don_gia' VALUE :OLD.don_gia,
        'hieu_luc_tu' VALUE :OLD.hieu_luc_tu,
        'hieu_luc_den' VALUE :OLD.hieu_luc_den,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'bang_gia_id' VALUE :NEW.bang_gia_id,
        'loai_phong_id' VALUE :NEW.loai_phong_id,
        'loai_gia' VALUE :NEW.loai_gia,
        'don_gia' VALUE :NEW.don_gia,
        'hieu_luc_tu' VALUE :NEW.hieu_luc_tu,
        'hieu_luc_den' VALUE :NEW.hieu_luc_den,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('BANG_GIA', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_bang_gia;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_loai_phong
AFTER INSERT OR UPDATE OR DELETE ON loai_phong
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.loai_phong_id);
    SELECT JSON_OBJECT(
        'loai_phong_id' VALUE :NEW.loai_phong_id,
        'ma_hang' VALUE :NEW.ma_hang,
        'suc_chua' VALUE :NEW.suc_chua,
        'cho_thue_gio' VALUE :NEW.cho_thue_gio,
        'anh_url' VALUE :NEW.anh_url,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.loai_phong_id);
    SELECT JSON_OBJECT(
        'loai_phong_id' VALUE :OLD.loai_phong_id,
        'ma_hang' VALUE :OLD.ma_hang,
        'suc_chua' VALUE :OLD.suc_chua,
        'cho_thue_gio' VALUE :OLD.cho_thue_gio,
        'anh_url' VALUE :OLD.anh_url,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := 'SUA';
    v_khoa := TO_CHAR(:NEW.loai_phong_id);
    SELECT JSON_OBJECT(
        'loai_phong_id' VALUE :OLD.loai_phong_id,
        'ma_hang' VALUE :OLD.ma_hang,
        'suc_chua' VALUE :OLD.suc_chua,
        'cho_thue_gio' VALUE :OLD.cho_thue_gio,
        'anh_url' VALUE :OLD.anh_url,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'loai_phong_id' VALUE :NEW.loai_phong_id,
        'ma_hang' VALUE :NEW.ma_hang,
        'suc_chua' VALUE :NEW.suc_chua,
        'cho_thue_gio' VALUE :NEW.cho_thue_gio,
        'anh_url' VALUE :NEW.anh_url,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('LOAI_PHONG', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_loai_phong;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_cau_hinh_he_thong
AFTER INSERT OR UPDATE OR DELETE ON cau_hinh_he_thong
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := :NEW.ma_tham_so || '@' || TO_CHAR(:NEW.hieu_luc_tu, 'YYYY-MM-DD');
    SELECT JSON_OBJECT(
        'ma_tham_so' VALUE :NEW.ma_tham_so,
        'hieu_luc_tu' VALUE :NEW.hieu_luc_tu,
        'hieu_luc_den' VALUE :NEW.hieu_luc_den,
        'gia_tri_so' VALUE :NEW.gia_tri_so,
        'gia_tri_chu' VALUE :NEW.gia_tri_chu,
        'mo_ta' VALUE :NEW.mo_ta,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := :OLD.ma_tham_so || '@' || TO_CHAR(:OLD.hieu_luc_tu, 'YYYY-MM-DD');
    SELECT JSON_OBJECT(
        'ma_tham_so' VALUE :OLD.ma_tham_so,
        'hieu_luc_tu' VALUE :OLD.hieu_luc_tu,
        'hieu_luc_den' VALUE :OLD.hieu_luc_den,
        'gia_tri_so' VALUE :OLD.gia_tri_so,
        'gia_tri_chu' VALUE :OLD.gia_tri_chu,
        'mo_ta' VALUE :OLD.mo_ta,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := 'SUA';
    v_khoa := :NEW.ma_tham_so || '@' || TO_CHAR(:NEW.hieu_luc_tu, 'YYYY-MM-DD');
    SELECT JSON_OBJECT(
        'ma_tham_so' VALUE :OLD.ma_tham_so,
        'hieu_luc_tu' VALUE :OLD.hieu_luc_tu,
        'hieu_luc_den' VALUE :OLD.hieu_luc_den,
        'gia_tri_so' VALUE :OLD.gia_tri_so,
        'gia_tri_chu' VALUE :OLD.gia_tri_chu,
        'mo_ta' VALUE :OLD.mo_ta,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'ma_tham_so' VALUE :NEW.ma_tham_so,
        'hieu_luc_tu' VALUE :NEW.hieu_luc_tu,
        'hieu_luc_den' VALUE :NEW.hieu_luc_den,
        'gia_tri_so' VALUE :NEW.gia_tri_so,
        'gia_tri_chu' VALUE :NEW.gia_tri_chu,
        'mo_ta' VALUE :NEW.mo_ta,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('CAU_HINH_HE_THONG', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_cau_hinh_he_thong;
/

CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_nguoi_dung
AFTER INSERT OR UPDATE OR DELETE ON nguoi_dung
FOR EACH ROW
DECLARE
  v_cu   CLOB;
  v_moi  CLOB;
  v_khoa VARCHAR2(100);
  v_act  VARCHAR2(30);
BEGIN
  IF INSERTING THEN
    v_act := 'TAO';
    v_khoa := TO_CHAR(:NEW.nguoi_dung_id);
    SELECT JSON_OBJECT(
        'nguoi_dung_id' VALUE :NEW.nguoi_dung_id,
        'ten_dang_nhap' VALUE :NEW.ten_dang_nhap,
        'ho_ten' VALUE :NEW.ho_ten,
        'vai_tro_id' VALUE :NEW.vai_tro_id,
        'trang_thai' VALUE :NEW.trang_thai,
        'so_lan_sai' VALUE :NEW.so_lan_sai,
        'khoa_den' VALUE :NEW.khoa_den,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  ELSIF DELETING THEN
    v_act := 'XOA';
    v_khoa := TO_CHAR(:OLD.nguoi_dung_id);
    SELECT JSON_OBJECT(
        'nguoi_dung_id' VALUE :OLD.nguoi_dung_id,
        'ten_dang_nhap' VALUE :OLD.ten_dang_nhap,
        'ho_ten' VALUE :OLD.ho_ten,
        'vai_tro_id' VALUE :OLD.vai_tro_id,
        'trang_thai' VALUE :OLD.trang_thai,
        'so_lan_sai' VALUE :OLD.so_lan_sai,
        'khoa_den' VALUE :OLD.khoa_den,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
  ELSE
    v_act := CASE WHEN :NEW.trang_thai <> :OLD.trang_thai THEN 'DOI_TRANG_THAI' ELSE 'SUA' END;
    v_khoa := TO_CHAR(:NEW.nguoi_dung_id);
    SELECT JSON_OBJECT(
        'nguoi_dung_id' VALUE :OLD.nguoi_dung_id,
        'ten_dang_nhap' VALUE :OLD.ten_dang_nhap,
        'ho_ten' VALUE :OLD.ho_ten,
        'vai_tro_id' VALUE :OLD.vai_tro_id,
        'trang_thai' VALUE :OLD.trang_thai,
        'so_lan_sai' VALUE :OLD.so_lan_sai,
        'khoa_den' VALUE :OLD.khoa_den,
        'ngay_tao' VALUE :OLD.ngay_tao
        RETURNING CLOB)
      INTO v_cu FROM dual;
    SELECT JSON_OBJECT(
        'nguoi_dung_id' VALUE :NEW.nguoi_dung_id,
        'ten_dang_nhap' VALUE :NEW.ten_dang_nhap,
        'ho_ten' VALUE :NEW.ho_ten,
        'vai_tro_id' VALUE :NEW.vai_tro_id,
        'trang_thai' VALUE :NEW.trang_thai,
        'so_lan_sai' VALUE :NEW.so_lan_sai,
        'khoa_den' VALUE :NEW.khoa_den,
        'ngay_tao' VALUE :NEW.ngay_tao
        RETURNING CLOB)
      INTO v_moi FROM dual;
  END IF;
  pkg_nhat_ky.ghi('NGUOI_DUNG', v_khoa, v_act, v_cu, v_moi);
END trg_ghi_nhat_ky_nguoi_dung;
/
