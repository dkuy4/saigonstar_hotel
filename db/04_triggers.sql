-- =====================================================================
-- 04_triggers.sql: trigger nghiệp vụ
--   TRG_DAT_PHONG_DOAN_TRUNG      compound trigger chống trùng phòng (BR-08 đến BR-11, NFR-01)
--   TRG_DAT_PHONG_CHIEM_LAI       kiểm tra lại khi đơn trở lại trạng thái chiếm phòng (BR-19)
--   TRG_DAT_PHONG_TRANG_THAI      mã tra cứu, trạng thái hợp lệ, đơn kết thúc không sửa (BR-16)
--   TRG_NHAT_KY_CHAN_SUA_XOA      nhật ký chỉ thêm (BR-48, NFR-04)
--   TRG_HOA_DON_CHAN_SUA, TRG_CHI_TIET_HOA_DON_CHAN_SUA   hóa đơn không sửa sau khi lập (BR-44)
--   TRG_BANG_GIA_RANG_BUOC        giá giờ chỉ cho hạng cho thuê giờ, không chồng hiệu lực, 5 lần giá giờ <= giá ngày
--   TRG_CAU_HINH_TRUNG_HIEU_LUC   tham số không chồng hiệu lực
-- Trigger ghi nhật ký tự động nằm ở 05_trigger_nhat_ky.sql (sinh bằng tools/gen_audit.py).
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- ---------------------------------------------------------------------
-- Chống trùng phòng. Compound trigger gom các đoạn bị ghi trong câu lệnh, rồi kiểm tra ở AFTER STATEMENT:
-- lúc đó bảng không còn "mutating" nên đọc được chính DAT_PHONG_DOAN. Các bước ở PKG_KIEM_TRA_TRUNG:
--   1. khóa dòng PHONG (theo thứ tự tăng của phong_id) để hai phiên cùng đặt một phòng phải xếp hàng;
--   2. đếm đoạn xung đột bằng câu lệnh mới, nhờ đó thấy các đoạn phiên khác vừa commit;
--   3. có xung đột thì ném -20001 ROOM_CONFLICT, câu lệnh INSERT/UPDATE bị hủy.
-- Mọi kênh (web, quầy, API) đi qua trigger này nên không có đường ghi nào bỏ qua kiểm tra (BR-10).
CREATE OR REPLACE TRIGGER trg_dat_phong_doan_trung
FOR INSERT OR UPDATE OF phong_id, tu_luc, den_luc ON dat_phong_doan
COMPOUND TRIGGER
  g_doan pkg_kiem_tra_trung.t_ds_so;

  AFTER EACH ROW IS
  BEGIN
    g_doan(g_doan.COUNT + 1) := :NEW.doan_id;
  END AFTER EACH ROW;

  AFTER STATEMENT IS
  BEGIN
    IF g_doan.COUNT > 0 THEN
      pkg_kiem_tra_trung.kiem_tra_cac_doan(g_doan);
    END IF;
  END AFTER STATEMENT;
END trg_dat_phong_doan_trung;
/

-- Đơn đang không chiếm phòng (EXPIRED, hoặc HOLD đã quá hạn) mà quay lại chiếm phòng, ví dụ thanh toán về muộn
-- (BR-19, AC-08): kiểm tra lại các đoạn của đơn, vì trong lúc đó phòng có thể đã có người đặt.
CREATE OR REPLACE TRIGGER trg_dat_phong_chiem_lai
FOR UPDATE OF trang_thai, han_giu_cho ON dat_phong
COMPOUND TRIGGER
  g_don pkg_kiem_tra_trung.t_ds_so;

  AFTER EACH ROW IS
  BEGIN
    IF pkg_kiem_tra_trung.la_chiem_phong(:NEW.trang_thai, :NEW.han_giu_cho)
       AND NOT pkg_kiem_tra_trung.la_chiem_phong(:OLD.trang_thai, :OLD.han_giu_cho) THEN
      g_don(g_don.COUNT + 1) := :NEW.dat_phong_id;
    END IF;
  END AFTER EACH ROW;

  AFTER STATEMENT IS
  BEGIN
    FOR i IN 1 .. g_don.COUNT LOOP
      pkg_kiem_tra_trung.kiem_tra_don(g_don(i));
    END LOOP;
  END AFTER STATEMENT;
END trg_dat_phong_chiem_lai;
/

-- ---------------------------------------------------------------------
-- Trạng thái đơn (BR-16, BR-14, BR-18, BR-19):
--   HOLD -> CONFIRMED | EXPIRED;  EXPIRED -> CONFIRMED (thanh toán về muộn);
--   CONFIRMED -> CHECKED_IN | CANCELLED | NO_SHOW;  CHECKED_IN -> CHECKED_OUT.
-- Đơn tạo mới chỉ được bắt đầu ở HOLD hoặc CONFIRMED. CHECKED_IN không hủy được (BR-14).
CREATE OR REPLACE TRIGGER trg_dat_phong_trang_thai
BEFORE INSERT OR UPDATE ON dat_phong
FOR EACH ROW
DECLARE
  FUNCTION hop_le (p_cu IN VARCHAR2, p_moi IN VARCHAR2) RETURN BOOLEAN IS
  BEGIN
    RETURN (p_cu = 'HOLD'       AND p_moi IN ('CONFIRMED', 'EXPIRED'))
        OR (p_cu = 'EXPIRED'    AND p_moi = 'CONFIRMED')
        OR (p_cu = 'CONFIRMED'  AND p_moi IN ('CHECKED_IN', 'CANCELLED', 'NO_SHOW'))
        OR (p_cu = 'CHECKED_IN' AND p_moi = 'CHECKED_OUT');
  END hop_le;
BEGIN
  IF INSERTING THEN
    IF :NEW.trang_thai NOT IN ('HOLD', 'CONFIRMED') THEN
      RAISE_APPLICATION_ERROR(-20003, 'BOOKING_STATE_INVALID|NEW>' || :NEW.trang_thai);
    END IF;
    IF :NEW.ma_tra_cuu IS NULL THEN
      :NEW.ma_tra_cuu := 'DP' || LPAD(TO_CHAR(seq_ma_tra_cuu.NEXTVAL), 7, '0');
    END IF;
  ELSE
    IF :NEW.trang_thai <> :OLD.trang_thai THEN
      IF NOT hop_le(:OLD.trang_thai, :NEW.trang_thai) THEN
        RAISE_APPLICATION_ERROR(-20003, 'BOOKING_STATE_INVALID|' || :OLD.trang_thai || '>' || :NEW.trang_thai);
      END IF;
    ELSIF :OLD.trang_thai IN ('CHECKED_OUT', 'CANCELLED', 'NO_SHOW') THEN
      -- Trạng thái kết thúc: không sửa nội dung và tiền (BR-16). Sai sót về tiền xử lý bằng hóa đơn điều chỉnh (BR-44).
      IF :NEW.tu_luc <> :OLD.tu_luc OR :NEW.den_luc <> :OLD.den_luc
         OR :NEW.khach_hang_id <> :OLD.khach_hang_id OR :NEW.loai_dat <> :OLD.loai_dat
         OR :NEW.don_gia_ap_dung <> :OLD.don_gia_ap_dung OR :NEW.tien_phong <> :OLD.tien_phong
         OR :NEW.thue_suat <> :OLD.thue_suat OR :NEW.tien_vat <> :OLD.tien_vat
         OR :NEW.tong_tien <> :OLD.tong_tien THEN
        RAISE_APPLICATION_ERROR(-20003, 'BOOKING_STATE_INVALID|LOCKED>' || :OLD.trang_thai);
      END IF;
    END IF;
  END IF;
END trg_dat_phong_trang_thai;
/

-- ---------------------------------------------------------------------
-- Nhật ký chỉ thêm (BR-48, NFR-04). Người dùng ứng dụng còn bị thu quyền UPDATE, DELETE ở 07_user_ung_dung.sql.
CREATE OR REPLACE TRIGGER trg_nhat_ky_chan_sua_xoa
BEFORE UPDATE OR DELETE ON nhat_ky_kiem_toan
BEGIN
  RAISE_APPLICATION_ERROR(-20030, 'AUDIT_IMMUTABLE');
END trg_nhat_ky_chan_sua_xoa;
/

-- Hóa đơn đã lập không sửa, không xóa (BR-44). Sai sót xử lý bằng hóa đơn điều chỉnh (LA_DIEU_CHINH, HOA_DON_GOC_ID).
CREATE OR REPLACE TRIGGER trg_hoa_don_chan_sua
BEFORE UPDATE OR DELETE ON hoa_don
BEGIN
  RAISE_APPLICATION_ERROR(-20031, 'INVOICE_IMMUTABLE');
END trg_hoa_don_chan_sua;
/
CREATE OR REPLACE TRIGGER trg_chi_tiet_hoa_don_chan_sua
BEFORE UPDATE OR DELETE ON chi_tiet_hoa_don
BEGIN
  RAISE_APPLICATION_ERROR(-20031, 'INVOICE_IMMUTABLE');
END trg_chi_tiet_hoa_don_chan_sua;
/

-- ---------------------------------------------------------------------
-- Ràng buộc bảng giá (BR-02, BR-04, FR-28). Dùng compound trigger vì phải đọc chính BANG_GIA để so sánh các dòng.
CREATE OR REPLACE TRIGGER trg_bang_gia_rang_buoc
FOR INSERT OR UPDATE ON bang_gia
COMPOUND TRIGGER
  TYPE t_so IS TABLE OF NUMBER INDEX BY PLS_INTEGER;
  g_ids t_so;

  AFTER EACH ROW IS
  BEGIN
    g_ids(g_ids.COUNT + 1) := :NEW.bang_gia_id;
  END AFTER EACH ROW;

  AFTER STATEMENT IS
    v_dem    NUMBER;
    v_nguong NUMBER;
  BEGIN
    IF g_ids.COUNT > 0 THEN
      v_nguong := pkg_cau_hinh.lay_so('NGUONG_GIO_TINH_NGAY');
    END IF;

    FOR i IN 1 .. g_ids.COUNT LOOP
      -- 1. Giá giờ chỉ dành cho hạng cho thuê theo giờ (BR-02)
      SELECT COUNT(*) INTO v_dem
        FROM bang_gia b JOIN loai_phong lp ON lp.loai_phong_id = b.loai_phong_id
       WHERE b.bang_gia_id = g_ids(i) AND b.loai_gia = 'GIO' AND lp.cho_thue_gio = FALSE;
      IF v_dem > 0 THEN
        RAISE_APPLICATION_ERROR(-20020, 'HOURLY_NOT_ALLOWED|' || g_ids(i));
      END IF;

      -- 2. Cùng hạng và cùng loại giá không được chồng ngày hiệu lực
      SELECT COUNT(*) INTO v_dem
        FROM bang_gia a JOIN bang_gia b
          ON b.loai_phong_id = a.loai_phong_id AND b.loai_gia = a.loai_gia AND b.bang_gia_id <> a.bang_gia_id
       WHERE a.bang_gia_id = g_ids(i)
         AND a.hieu_luc_tu <= NVL(b.hieu_luc_den, DATE '9999-12-31')
         AND b.hieu_luc_tu <= NVL(a.hieu_luc_den, DATE '9999-12-31');
      IF v_dem > 0 THEN
        RAISE_APPLICATION_ERROR(-20021, 'PRICE_OVERLAP|' || g_ids(i));
      END IF;

      -- 3. Ngưỡng giờ nhân giá giờ không vượt giá ngày khi hai dòng cùng hiệu lực (BR-04, FR-28)
      SELECT COUNT(*) INTO v_dem
        FROM bang_gia g JOIN bang_gia o
          ON o.loai_phong_id = g.loai_phong_id AND o.loai_gia <> g.loai_gia
       WHERE g.bang_gia_id = g_ids(i)
         AND g.hieu_luc_tu <= NVL(o.hieu_luc_den, DATE '9999-12-31')
         AND o.hieu_luc_tu <= NVL(g.hieu_luc_den, DATE '9999-12-31')
         AND ((g.loai_gia = 'GIO'  AND g.don_gia * v_nguong > o.don_gia)
           OR (g.loai_gia = 'NGAY' AND o.don_gia * v_nguong > g.don_gia));
      IF v_dem > 0 THEN
        RAISE_APPLICATION_ERROR(-20022, 'PRICE_RULE_VIOLATION|' || g_ids(i));
      END IF;
    END LOOP;
  END AFTER STATEMENT;
END trg_bang_gia_rang_buoc;
/

-- Tham số cùng mã không được chồng ngày hiệu lực (BR-58: thuế suất đổi bằng cách đóng dòng cũ, thêm dòng mới)
CREATE OR REPLACE TRIGGER trg_cau_hinh_trung_hieu_luc
FOR INSERT OR UPDATE ON cau_hinh_he_thong
COMPOUND TRIGGER
  TYPE t_chu  IS TABLE OF VARCHAR2(50) INDEX BY PLS_INTEGER;
  TYPE t_ngay IS TABLE OF DATE INDEX BY PLS_INTEGER;
  g_ma t_chu;
  g_tu t_ngay;

  AFTER EACH ROW IS
  BEGIN
    g_ma(g_ma.COUNT + 1) := :NEW.ma_tham_so;
    g_tu(g_tu.COUNT + 1) := :NEW.hieu_luc_tu;
  END AFTER EACH ROW;

  AFTER STATEMENT IS
    v_dem NUMBER;
  BEGIN
    FOR i IN 1 .. g_ma.COUNT LOOP
      SELECT COUNT(*) INTO v_dem
        FROM cau_hinh_he_thong a JOIN cau_hinh_he_thong b
          ON b.ma_tham_so = a.ma_tham_so AND b.hieu_luc_tu <> a.hieu_luc_tu
       WHERE a.ma_tham_so = g_ma(i) AND a.hieu_luc_tu = g_tu(i)
         AND a.hieu_luc_tu <= NVL(b.hieu_luc_den, DATE '9999-12-31')
         AND b.hieu_luc_tu <= NVL(a.hieu_luc_den, DATE '9999-12-31');
      IF v_dem > 0 THEN
        RAISE_APPLICATION_ERROR(-20023, 'CONFIG_OVERLAP|' || g_ma(i));
      END IF;
    END LOOP;
  END AFTER STATEMENT;
END trg_cau_hinh_trung_hieu_luc;
/
