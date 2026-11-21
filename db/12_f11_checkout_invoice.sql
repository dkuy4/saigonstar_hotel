-- =====================================================================
-- 12_f11_checkout_invoice.sql  –  F11: Check-out và hóa đơn nội bộ
--   PKG_HOA_DON.LAP_DIEU_CHINH  : lập hóa đơn điều chỉnh (BR-44, BR-45, AC-20)
--   PKG_DAT_PHONG.TINH_TRUOC_CHECK_OUT : tính tạm không ghi (màn hình tổng kết)
-- Chạy sau 03_packages.sql và 08_pkg_nghiep_vu.sql
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- ---------------------------------------------------------------------
-- Thêm FUNCTION LAP_DIEU_CHINH vào package spec PKG_HOA_DON
-- (tạo lại toàn bộ spec, giữ nguyên CAP_SO)
-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_hoa_don AS
  -- Cấp số hóa đơn liên tục, không có khoảng hở, không thể rollback (BR-44).
  -- Gọi ngoài câu INSERT vì hàm này có DML (FOR UPDATE + UPDATE bộ đếm).
  FUNCTION cap_so RETURN NUMBER;

  -- Lập hóa đơn điều chỉnh cho hóa đơn gốc (FR-38, BR-45, AC-20).
  -- p_so_tien  > 0: phụ thu thêm; < 0: giảm trừ.
  -- Chỉ quản lý gọi được (kiểm tra vai trò bằng require_role ở API).
  -- Trigger TRG_HOA_DON_KHOA (trong 04_triggers.sql) chặn UPDATE/DELETE hóa đơn,
  -- nên hóa đơn điều chỉnh là đường duy nhất sửa số tiền.
  PROCEDURE lap_dieu_chinh (
    p_hoa_don_goc_id  IN  NUMBER,
    p_nguoi_lap_id    IN  NUMBER,
    p_mo_ta           IN  VARCHAR2,
    p_so_tien         IN  NUMBER,
    p_hoa_don_dieu_id OUT NUMBER,
    p_so_hoa_don_dieu OUT NUMBER
  );
END pkg_hoa_don;
/

CREATE OR REPLACE PACKAGE BODY pkg_hoa_don AS

  FUNCTION cap_so RETURN NUMBER IS
    v_so NUMBER;
  BEGIN
    SELECT gia_tri_cuoi + 1 INTO v_so FROM bo_dem_hoa_don WHERE loai = 'HOA_DON' FOR UPDATE;
    UPDATE bo_dem_hoa_don SET gia_tri_cuoi = v_so WHERE loai = 'HOA_DON';
    RETURN v_so;
  END cap_so;

  PROCEDURE lap_dieu_chinh (
    p_hoa_don_goc_id  IN  NUMBER,
    p_nguoi_lap_id    IN  NUMBER,
    p_mo_ta           IN  VARCHAR2,
    p_so_tien         IN  NUMBER,
    p_hoa_don_dieu_id OUT NUMBER,
    p_so_hoa_don_dieu OUT NUMBER
  ) IS
    v_hd_goc  hoa_don%ROWTYPE;
    v_so      NUMBER;
  BEGIN
    -- Kiểm tra hóa đơn gốc tồn tại
    BEGIN
      SELECT * INTO v_hd_goc FROM hoa_don WHERE hoa_don_id = p_hoa_don_goc_id FOR UPDATE;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20061, 'BOOKING_NOT_FOUND|hoa_don_id=' || p_hoa_don_goc_id);
    END;

    -- Hóa đơn điều chỉnh không được điều chỉnh hóa đơn điều chỉnh khác
    IF v_hd_goc.la_dieu_chinh = TRUE THEN
      RAISE_APPLICATION_ERROR(-20031, 'INVOICE_IMMUTABLE|Không thể lập hóa đơn điều chỉnh cho hóa đơn điều chỉnh');
    END IF;

    -- Mô tả bắt buộc
    IF p_mo_ta IS NULL OR TRIM(p_mo_ta) IS NULL THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|MO_TA');
    END IF;

    -- Số tiền phải khác 0
    IF NVL(p_so_tien, 0) = 0 THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|SO_TIEN');
    END IF;

    v_so := cap_so;
    p_so_hoa_don_dieu := v_so;

    INSERT INTO hoa_don (so_hoa_don, dat_phong_id, tong_tien, nguoi_lap_id, la_dieu_chinh, hoa_don_goc_id)
    VALUES (v_so, v_hd_goc.dat_phong_id, p_so_tien, p_nguoi_lap_id, TRUE, p_hoa_don_goc_id)
    RETURNING hoa_don_id INTO p_hoa_don_dieu_id;

    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien)
    VALUES (p_hoa_don_dieu_id,
            CASE WHEN p_so_tien >= 0 THEN 'PHU_THU' ELSE 'GIAM_GIA' END,
            p_mo_ta,
            p_so_tien);

    -- Nhật ký: điều chỉnh hóa đơn gốc
    pkg_nhat_ky.ghi('HOA_DON', TO_CHAR(p_hoa_don_goc_id), 'DIEU_CHINH',
                    TO_CHAR(v_hd_goc.tong_tien),
                    TO_CHAR(v_hd_goc.tong_tien + p_so_tien),
                    p_mo_ta);
  END lap_dieu_chinh;

END pkg_hoa_don;
/

-- ---------------------------------------------------------------------
-- Thêm TINH_TRUOC_CHECK_OUT vào package spec PKG_DAT_PHONG
-- Tính tạm (không ghi DB) để màn hình check-out hiển thị trước khi lễ tân xác nhận
-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE BODY pkg_dat_phong AS

  -- ---------- hàm riêng ----------
  FUNCTION khoa_don (p_dat_phong_id IN NUMBER) RETURN dat_phong%ROWTYPE IS
    r dat_phong%ROWTYPE;
  BEGIN
    SELECT * INTO r FROM dat_phong WHERE dat_phong_id = p_dat_phong_id FOR UPDATE;
    RETURN r;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20061, 'BOOKING_NOT_FOUND|' || p_dat_phong_id);
  END khoa_don;

  PROCEDURE sai_trang_thai (p_tt IN VARCHAR2) IS
  BEGIN
    RAISE_APPLICATION_ERROR(-20003, 'BOOKING_STATE_INVALID|' || p_tt);
  END sai_trang_thai;

  PROCEDURE loi_du_lieu (p_truong IN VARCHAR2) IS
  BEGIN
    RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|' || p_truong);
  END loi_du_lieu;

  -- Đoạn lưu trú cuối cùng của đơn
  PROCEDURE doan_cuoi (p_dat_phong_id IN NUMBER, p_doan_id OUT NUMBER, p_phong_id OUT NUMBER,
                       p_tu OUT TIMESTAMP WITH TIME ZONE, p_den OUT TIMESTAMP WITH TIME ZONE) IS
  BEGIN
    SELECT doan_id, phong_id, tu_luc, den_luc INTO p_doan_id, p_phong_id, p_tu, p_den
      FROM (SELECT doan_id, phong_id, tu_luc, den_luc FROM dat_phong_doan
             WHERE dat_phong_id = p_dat_phong_id ORDER BY doan_id DESC)
     WHERE ROWNUM = 1;
  END doan_cuoi;

  -- BR-01 đến BR-05, D-47: kiểm tra giờ nhận, giờ trả, bước giờ và thời lượng
  PROCEDURE kiem_tra_thoi_gian (p_loai_dat IN VARCHAR2, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) IS
    v_phut NUMBER;
    v_buoc NUMBER;
  BEGIN
    IF p_tu IS NULL OR p_den IS NULL OR p_den <= p_tu THEN
      loi_du_lieu('THOI_GIAN');
    END IF;
    IF p_loai_dat = 'NGAY' THEN
      IF TO_CHAR(p_tu AT TIME ZONE '+07:00', 'HH24:MI') <> pkg_cau_hinh.lay_chu('GIO_NHAN_PHONG') THEN
        loi_du_lieu('GIO_NHAN');
      END IF;
      IF TO_CHAR(p_den AT TIME ZONE '+07:00', 'HH24:MI') <> pkg_cau_hinh.lay_chu('GIO_TRA_PHONG') THEN
        loi_du_lieu('GIO_TRA');
      END IF;
      IF pkg_gia.so_dem(p_tu, p_den) < 1 THEN
        loi_du_lieu('SO_DEM');
      END IF;
      IF TRUNC(CAST(p_tu AT TIME ZONE '+07:00' AS DATE)) < pkg_cau_hinh.ngay_vn THEN
        loi_du_lieu('QUA_KHU');
      END IF;
    ELSE
      v_buoc := pkg_cau_hinh.lay_so('BUOC_PHUT_DON_GIO');
      v_phut := pkg_gia.so_phut(p_tu, p_den);
      IF MOD(TO_NUMBER(TO_CHAR(p_tu AT TIME ZONE '+07:00', 'MI')), v_buoc) <> 0 THEN
        loi_du_lieu('BUOC_GIO');
      END IF;
      IF MOD(v_phut, 60) <> 0 OR v_phut > pkg_cau_hinh.lay_so('SO_GIO_TOI_DA_DON_GIO') * 60 THEN
        loi_du_lieu('SO_GIO');
      END IF;
      IF p_tu < pkg_gia.bay_gio - NUMTODSINTERVAL(v_buoc, 'MINUTE') THEN
        loi_du_lieu('QUA_KHU');
      END IF;
    END IF;
  END kiem_tra_thoi_gian;

  -- Tính trước khi check-out để màn hình tổng kết hiển thị (không ghi DB)
  PROCEDURE tinh_truoc_check_out (
    p_dat_phong_id    IN  NUMBER,
    p_phu_thu_tien    IN  NUMBER DEFAULT 0,
    p_giam_gia        IN  NUMBER DEFAULT 0,
    p_tien_phong      OUT NUMBER,
    p_tien_qua_gio    OUT NUMBER,
    p_phu_thu         OUT NUMBER,
    p_giam_gia_ra     OUT NUMBER,
    p_tien_vat        OUT NUMBER,
    p_tong_hoa_don    OUT NUMBER,
    p_da_thanh_toan   OUT NUMBER,
    p_con_phai_thu    OUT NUMBER
  ) IS
    r       dat_phong%ROWTYPE;
    v_ra    TIMESTAMP WITH TIME ZONE := pkg_gia.bay_gio;
    v_qua   NUMBER;
    v_chiu  NUMBER;
    v_vat   NUMBER;
    v_tong  NUMBER;
    v_paid  NUMBER;
  BEGIN
    SELECT * INTO r FROM dat_phong WHERE dat_phong_id = p_dat_phong_id;
    IF r.trang_thai <> 'CHECKED_IN' THEN
      sai_trang_thai(r.trang_thai);
    END IF;

    v_qua  := pkg_gia.tien_qua_gio(r.loai_dat, r.tu_luc, r.den_luc, v_ra,
                                    r.don_gia_ap_dung, r.don_gia_ngay_ap_dung);
    v_chiu := r.tien_phong + v_qua + NVL(p_phu_thu_tien, 0) - NVL(p_giam_gia, 0);
    v_vat  := pkg_gia.tinh_vat(GREATEST(v_chiu, 0), r.thue_suat);
    v_tong := GREATEST(v_chiu, 0) + v_vat;
    v_paid := pkg_thanh_toan.tinh_da_thanh_toan(p_dat_phong_id);

    p_tien_phong    := r.tien_phong;
    p_tien_qua_gio  := v_qua;
    p_phu_thu       := NVL(p_phu_thu_tien, 0);
    p_giam_gia_ra   := NVL(p_giam_gia, 0);
    p_tien_vat      := v_vat;
    p_tong_hoa_don  := v_tong;
    p_da_thanh_toan := v_paid;
    p_con_phai_thu  := v_tong - v_paid;
  END tinh_truoc_check_out;

  -- ---------- tạo đơn ----------
  PROCEDURE tao_don (p_ho_ten IN VARCHAR2, p_sdt IN VARCHAR2, p_email IN VARCHAR2, p_quoc_tich IN VARCHAR2,
                     p_ngon_ngu IN VARCHAR2, p_loai_dat IN VARCHAR2, p_kenh_dat IN VARCHAR2,
                     p_ma_hang IN VARCHAR2, p_phong_id IN NUMBER,
                     p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                     p_so_khach IN NUMBER, p_thanh_toan IN VARCHAR2, p_dong_y_luc IN TIMESTAMP WITH TIME ZONE,
                     p_dat_phong_id OUT NUMBER, p_ma_tra_cuu OUT VARCHAR2, p_trang_thai OUT VARCHAR2,
                     p_phong_id_gan OUT NUMBER, p_tien_phong OUT NUMBER, p_tien_vat OUT NUMBER,
                     p_tong_tien OUT NUMBER, p_han_giu_cho OUT TIMESTAMP WITH TIME ZONE) IS
    v_email      VARCHAR2(254) := LOWER(TRIM(p_email));
    v_loai_phong NUMBER;
    v_ma_hang    loai_phong.ma_hang%TYPE;
    v_cho_gio    BOOLEAN;
    v_suc_chua   NUMBER;
    v_hoat_dong  BOOLEAN;
    v_gia        pkg_gia.t_gia;
    v_khach      NUMBER;
    v_phong      NUMBER;
    v_phong_tt   VARCHAR2(20);
    v_so_pending NUMBER;
  BEGIN
    -- Lấy thông tin hạng phòng
    BEGIN
      SELECT loai_phong_id, ma_hang, cho_thue_gio, suc_chua, dang_hoat_dong
        INTO v_loai_phong, v_ma_hang, v_cho_gio, v_suc_chua, v_hoat_dong
        FROM loai_phong WHERE UPPER(ma_hang) = UPPER(p_ma_hang);
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|MA_HANG');
    END;

    IF NOT v_hoat_dong THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|MA_HANG_KHOA');
    END IF;

    IF p_loai_dat = 'GIO' AND NOT v_cho_gio THEN
      RAISE_APPLICATION_ERROR(-20020, 'HOURLY_NOT_ALLOWED|' || v_ma_hang);
    END IF;

    IF p_so_khach IS NOT NULL AND v_suc_chua IS NOT NULL AND p_so_khach > v_suc_chua THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|SO_KHACH');
    END IF;

    kiem_tra_thoi_gian(p_loai_dat, p_tu, p_den);

    -- Kiểm tra giới hạn HOLD chưa thanh toán (BR-21)
    IF p_kenh_dat IN ('WEB', 'API') AND p_thanh_toan = 'TRUC_TUYEN' THEN
      SELECT COUNT(*) INTO v_so_pending
        FROM dat_phong dp JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
       WHERE LOWER(kh.email) = v_email AND dp.trang_thai = 'HOLD';
      IF v_so_pending >= pkg_cau_hinh.lay_so('SO_DON_HOLD_TOI_DA') THEN
        RAISE_APPLICATION_ERROR(-20050, 'PENDING_LIMIT_EXCEEDED|' || v_email);
      END IF;
    END IF;

    -- Chốt giá theo thời điểm đặt
    v_gia := pkg_gia.chot_gia(v_loai_phong, p_loai_dat, p_tu, p_den);

    -- Chọn phòng
    IF p_phong_id IS NOT NULL THEN
      -- Lễ tân chọn phòng cụ thể: kiểm tra trùng
      SELECT trang_thai INTO v_phong_tt FROM phong WHERE phong_id = p_phong_id;
      IF pkg_kiem_tra_trung.dem_xung_dot(p_phong_id, p_tu, p_den) > 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'ROOM_CONFLICT|' || p_phong_id);
      END IF;
      v_phong := p_phong_id;
    ELSE
      -- Khách trực tuyến: gán phòng tự động
      SELECT p.phong_id INTO v_phong
        FROM phong p
       WHERE p.loai_phong_id = v_loai_phong AND p.dang_hoat_dong = TRUE AND p.trang_thai <> 'BAO_TRI'
         AND pkg_kiem_tra_trung.dem_xung_dot(p.phong_id, p_tu, p_den) = 0
         AND ROWNUM = 1
       ORDER BY pkg_kiem_tra_trung.khoang_cach_lan_can(p.phong_id, p_tu, p_den), p.phong_id;
      EXCEPTION WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20051, 'NO_AVAILABILITY|' || v_ma_hang);
    END IF;

    -- Tạo / lấy khách hàng
    BEGIN
      SELECT khach_hang_id INTO v_khach FROM khach_hang WHERE LOWER(email) = v_email;
      UPDATE khach_hang SET ho_ten = p_ho_ten, sdt = p_sdt, quoc_tich = NVL(p_quoc_tich, 'VN')
       WHERE khach_hang_id = v_khach;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        INSERT INTO khach_hang (ho_ten, sdt, email, quoc_tich)
        VALUES (p_ho_ten, p_sdt, v_email, NVL(p_quoc_tich, 'VN'))
        RETURNING khach_hang_id INTO v_khach;
    END;

    -- Trạng thái ban đầu
    DECLARE
      v_tt VARCHAR2(20);
      v_han TIMESTAMP WITH TIME ZONE;
    BEGIN
      IF p_kenh_dat = 'QUAY' OR p_thanh_toan = 'KHI_NHAN_PHONG' THEN
        v_tt  := 'CONFIRMED';
        v_han := NULL;
      ELSE
        v_tt  := 'HOLD';
        v_han := pkg_gia.bay_gio + NUMTODSINTERVAL(pkg_cau_hinh.lay_so('PHUT_GIU_CHO'), 'MINUTE');
      END IF;

      INSERT INTO dat_phong (
        khach_hang_id, loai_dat, kenh_dat, ngon_ngu, so_khach, trang_thai,
        tu_luc, den_luc, han_giu_cho, dong_y_chinh_sach_luc,
        tien_phong, thue_suat, tien_vat, tong_tien,
        don_gia_ap_dung, don_gia_ngay_ap_dung,
        phuong_thuc_thanh_toan, ma_tra_cuu
      ) VALUES (
        v_khach, p_loai_dat, p_kenh_dat, NVL(p_ngon_ngu, 'vi'), p_so_khach, v_tt,
        p_tu, p_den, v_han, p_dong_y_luc,
        v_gia.tien_phong, v_gia.thue_suat, v_gia.tien_vat, v_gia.tong_tien,
        v_gia.don_gia, v_gia.don_gia_ngay,
        p_thanh_toan,
        'DP' || TO_CHAR(seq_ma_tra_cuu.NEXTVAL, 'FM0000000')
      ) RETURNING dat_phong_id, ma_tra_cuu, trang_thai, han_giu_cho
        INTO p_dat_phong_id, p_ma_tra_cuu, p_trang_thai, p_han_giu_cho;

      INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc)
      VALUES (p_dat_phong_id, v_phong, p_tu, p_den);

      p_phong_id_gan := v_phong;
      p_tien_phong   := v_gia.tien_phong;
      p_tien_vat     := v_gia.tien_vat;
      p_tong_tien    := v_gia.tong_tien;

      IF v_tt = 'CONFIRMED' THEN
        pkg_email.xep(p_dat_phong_id, 'XAC_NHAN');
      END IF;
    END;
  END tao_don;

  FUNCTION hoan_du_kien (p_dat_phong_id IN NUMBER) RETURN NUMBER IS
    r   dat_phong%ROWTYPE;
    v_p NUMBER;
    v_h NUMBER;
  BEGIN
    SELECT * INTO r FROM dat_phong WHERE dat_phong_id = p_dat_phong_id;
    IF r.trang_thai <> 'CONFIRMED' THEN RETURN 0; END IF;
    v_p := pkg_thanh_toan.tinh_da_thanh_toan(p_dat_phong_id);
    IF pkg_gia.so_phut(pkg_gia.bay_gio, r.tu_luc) / 60 >= pkg_cau_hinh.lay_so('GIO_HUY_MIEN_PHI') THEN
      RETURN v_p;
    END IF;
    RETURN 0;
  END hoan_du_kien;

  PROCEDURE huy_don (p_dat_phong_id IN NUMBER, p_ly_do IN VARCHAR2, p_so_tien_hoan OUT NUMBER) IS
    r       dat_phong%ROWTYPE;
    v_hoan  NUMBER := 0;
    v_gd    NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai NOT IN ('HOLD', 'CONFIRMED') THEN
      sai_trang_thai(r.trang_thai);
    END IF;
    -- Nếu còn thời gian hoàn thì hoàn tiền
    IF r.trang_thai = 'CONFIRMED' THEN
      v_hoan := hoan_du_kien(p_dat_phong_id);
      IF v_hoan > 0 THEN
        SELECT giao_dich_id INTO v_gd
          FROM giao_dich_thanh_toan
         WHERE dat_phong_id = p_dat_phong_id AND trang_thai = 'THANH_CONG'
           AND ROWNUM = 1
         ORDER BY giao_dich_id DESC;
        INSERT INTO hoan_tien (giao_dich_id, so_tien, ly_do, trang_thai)
        VALUES (v_gd, v_hoan, 'HUY_DON_TRUOC_HAN', 'CHO_DUYET');
        pkg_email.xep(p_dat_phong_id, 'HUY_HOAN_TIEN');
      END IF;
    END IF;
    UPDATE dat_phong SET trang_thai = 'CANCELLED', ly_do_huy = p_ly_do
     WHERE dat_phong_id = p_dat_phong_id;
    p_so_tien_hoan := v_hoan;
  EXCEPTION WHEN NO_DATA_FOUND THEN
    -- Không có giao dịch thành công -> không hoàn tiền
    UPDATE dat_phong SET trang_thai = 'CANCELLED', ly_do_huy = p_ly_do
     WHERE dat_phong_id = p_dat_phong_id;
    p_so_tien_hoan := 0;
  END huy_don;

  PROCEDURE doi_lich (p_dat_phong_id IN NUMBER, p_tu_moi IN TIMESTAMP WITH TIME ZONE,
                      p_den_moi IN TIMESTAMP WITH TIME ZONE,
                      p_phong_moi_id IN NUMBER DEFAULT NULL,
                      p_chenh_lech OUT NUMBER, p_so_tien_hoan OUT NUMBER) IS
    r       dat_phong%ROWTYPE;
    v_doan  NUMBER; v_phong NUMBER; v_tu TIMESTAMP WITH TIME ZONE; v_den TIMESTAMP WITH TIME ZONE;
    v_loai  NUMBER;
    v_gia   pkg_gia.t_gia;
    v_tid   NUMBER;
    v_phong_moi NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CONFIRMED' THEN sai_trang_thai(r.trang_thai); END IF;
    kiem_tra_thoi_gian(r.loai_dat, p_tu_moi, p_den_moi);
    doan_cuoi(p_dat_phong_id, v_doan, v_phong, v_tu, v_den);
    v_phong_moi := NVL(p_phong_moi_id, v_phong);
    IF pkg_kiem_tra_trung.dem_xung_dot(v_phong_moi, p_tu_moi, p_den_moi, v_doan) > 0 THEN
      RAISE_APPLICATION_ERROR(-20001, 'ROOM_CONFLICT|' || v_phong_moi);
    END IF;
    SELECT loai_phong_id INTO v_loai FROM phong WHERE phong_id = v_phong_moi;
    v_gia := pkg_gia.chot_gia(v_loai, r.loai_dat, p_tu_moi, p_den_moi);
    p_chenh_lech  := v_gia.tong_tien - r.tong_tien;
    p_so_tien_hoan := 0;
    IF p_chenh_lech < 0 THEN
      p_so_tien_hoan := ABS(p_chenh_lech);
      p_chenh_lech   := 0;
      -- Hoàn tiền chênh lệch
      BEGIN
        SELECT giao_dich_id INTO v_tid
          FROM giao_dich_thanh_toan
         WHERE dat_phong_id = p_dat_phong_id AND trang_thai = 'THANH_CONG' AND ROWNUM = 1
         ORDER BY giao_dich_id DESC;
        INSERT INTO hoan_tien (giao_dich_id, so_tien, ly_do, trang_thai)
        VALUES (v_tid, p_so_tien_hoan, 'DOI_LICH_CHENH_LECH', 'CHO_DUYET');
      EXCEPTION WHEN NO_DATA_FOUND THEN NULL; END;
    END IF;
    UPDATE dat_phong_doan SET tu_luc = p_tu_moi, den_luc = p_den_moi, phong_id = v_phong_moi
     WHERE doan_id = v_doan;
    UPDATE dat_phong SET tu_luc = p_tu_moi, den_luc = p_den_moi,
           tien_phong = v_gia.tien_phong, thue_suat = v_gia.thue_suat,
           tien_vat = v_gia.tien_vat, tong_tien = v_gia.tong_tien,
           don_gia_ap_dung = v_gia.don_gia, don_gia_ngay_ap_dung = v_gia.don_gia_ngay
     WHERE dat_phong_id = p_dat_phong_id;
    pkg_email.xep(p_dat_phong_id, 'THAY_DOI_DON');
  END doi_lich;

  PROCEDURE check_in (p_dat_phong_id IN NUMBER, p_loai_giay_to IN VARCHAR2,
                      p_so_giay_to IN VARCHAR2, p_quoc_tich IN VARCHAR2,
                      p_anh_url IN VARCHAR2 DEFAULT NULL, p_phong_id OUT NUMBER) IS
    r       dat_phong%ROWTYPE;
    v_doan  NUMBER; v_phong NUMBER; v_tu TIMESTAMP WITH TIME ZONE; v_den TIMESTAMP WITH TIME ZONE;
    v_phong_tt VARCHAR2(20);
    v_khach NUMBER;
    v_sov   NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CONFIRMED' THEN sai_trang_thai(r.trang_thai); END IF;
    -- BR-30: không nhận trước 1 giờ
    IF pkg_gia.bay_gio < r.tu_luc - NUMTODSINTERVAL(pkg_cau_hinh.lay_so('PHUT_CHECK_IN_SOM') * 60, 'SECOND') THEN
      RAISE_APPLICATION_ERROR(-20053, 'CHECKIN_TOO_EARLY|' || TO_CHAR(r.tu_luc));
    END IF;
    -- BR-31: phòng phải TRONG
    doan_cuoi(p_dat_phong_id, v_doan, v_phong, v_tu, v_den);
    SELECT trang_thai INTO v_phong_tt FROM phong WHERE phong_id = v_phong;
    IF v_phong_tt <> 'TRONG' THEN
      RAISE_APPLICATION_ERROR(-20054, 'ROOM_NOT_READY|' || v_phong_tt);
    END IF;
    IF p_loai_giay_to IS NULL OR p_so_giay_to IS NULL THEN
      loi_du_lieu('GIAY_TO');
    END IF;
    -- Lưu giấy tờ
    SELECT khach_hang_id INTO v_khach FROM dat_phong WHERE dat_phong_id = p_dat_phong_id;
    INSERT INTO giay_to_khach (khach_hang_id, loai_giay_to, so_giay_to, anh_url)
    VALUES (v_khach, p_loai_giay_to, p_so_giay_to, p_anh_url);
    UPDATE dat_phong SET trang_thai = 'CHECKED_IN', nhan_thuc_te = pkg_gia.bay_gio
     WHERE dat_phong_id = p_dat_phong_id;
    UPDATE phong SET trang_thai = 'DANG_O' WHERE phong_id = v_phong;
    p_phong_id := v_phong;
  END check_in;

  PROCEDURE gia_han (p_dat_phong_id IN NUMBER, p_so_don_vi IN NUMBER, p_tien_them OUT NUMBER) IS
    r       dat_phong%ROWTYPE;
    v_doan  NUMBER; v_phong NUMBER; v_tu TIMESTAMP WITH TIME ZONE; v_den_moi TIMESTAMP WITH TIME ZONE;
    v_den_cu TIMESTAMP WITH TIME ZONE;
    v_tien_moi NUMBER; v_vat_moi NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CHECKED_IN' THEN sai_trang_thai(r.trang_thai); END IF;
    doan_cuoi(p_dat_phong_id, v_doan, v_phong, v_tu, v_den_cu);
    IF r.loai_dat = 'NGAY' THEN
      v_den_moi := r.den_luc + NUMTODSINTERVAL(p_so_don_vi, 'DAY');
    ELSE
      v_den_moi := r.den_luc + NUMTODSINTERVAL(p_so_don_vi, 'HOUR');
      -- Kiểm tra giới hạn số giờ
      IF pkg_gia.so_phut(r.tu_luc, v_den_moi) > pkg_cau_hinh.lay_so('SO_GIO_TOI_DA_DON_GIO') * 60 THEN
        RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|SO_GIO');
      END IF;
    END IF;
    -- Kiểm tra xung đột khoảng gia hạn
    IF pkg_kiem_tra_trung.dem_xung_dot(v_phong, v_den_cu, v_den_moi, v_doan) > 0 THEN
      RAISE_APPLICATION_ERROR(-20055, 'EXTEND_CONFLICT|' || v_phong);
    END IF;
    -- Tính giá mới
    IF r.loai_dat = 'NGAY' THEN
      v_tien_moi := r.tien_phong + p_so_don_vi * r.don_gia_ngay_ap_dung;
    ELSE
      DECLARE v_gio_moi NUMBER; BEGIN
        v_gio_moi  := pkg_gia.so_phut(r.tu_luc, v_den_moi) / 60;
        v_tien_moi := pkg_gia.tien_theo_gio(v_gio_moi, r.don_gia_ap_dung, r.don_gia_ngay_ap_dung);
      END;
    END IF;
    v_vat_moi := pkg_gia.tinh_vat(v_tien_moi, r.thue_suat);
    p_tien_them := (v_tien_moi + v_vat_moi) - r.tong_tien;
    UPDATE dat_phong_doan SET den_luc = v_den_moi WHERE doan_id = v_doan;
    UPDATE dat_phong SET den_luc = v_den_moi, tien_phong = v_tien_moi,
           tien_vat = v_vat_moi, tong_tien = v_tien_moi + v_vat_moi
     WHERE dat_phong_id = p_dat_phong_id;
  END gia_han;

  PROCEDURE doi_phong_su_co (p_dat_phong_id IN NUMBER, p_phong_moi_id IN NUMBER, p_ly_do IN VARCHAR2) IS
    r       dat_phong%ROWTYPE;
    v_doan  NUMBER; v_phong_cu NUMBER; v_tu TIMESTAMP WITH TIME ZONE; v_den TIMESTAMP WITH TIME ZONE;
    v_phong_tt VARCHAR2(20);
    v_loai_dat_phong VARCHAR2(20);
    v_loai_phong_cu  NUMBER; v_loai_phong_moi NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CHECKED_IN' THEN sai_trang_thai(r.trang_thai); END IF;
    IF p_ly_do IS NULL OR TRIM(p_ly_do) IS NULL THEN loi_du_lieu('LY_DO'); END IF;
    doan_cuoi(p_dat_phong_id, v_doan, v_phong_cu, v_tu, v_den);
    -- BR-35: đơn giờ chỉ đổi sang Standard
    SELECT loai_phong_id INTO v_loai_phong_cu FROM phong WHERE phong_id = v_phong_cu;
    SELECT loai_phong_id INTO v_loai_phong_moi FROM phong WHERE phong_id = p_phong_moi_id;
    IF r.loai_dat = 'GIO' THEN
      DECLARE v_ma VARCHAR2(20); BEGIN
        SELECT ma_hang INTO v_ma FROM loai_phong WHERE loai_phong_id = v_loai_phong_moi;
        IF v_ma <> 'STANDARD' THEN
          RAISE_APPLICATION_ERROR(-20020, 'HOURLY_NOT_ALLOWED|' || v_ma);
        END IF;
      END;
    END IF;
    -- Phòng mới phải TRONG
    SELECT trang_thai INTO v_phong_tt FROM phong WHERE phong_id = p_phong_moi_id;
    IF v_phong_tt <> 'TRONG' THEN
      RAISE_APPLICATION_ERROR(-20054, 'ROOM_NOT_READY|' || v_phong_tt);
    END IF;
    -- Thực hiện đổi phòng
    UPDATE dat_phong_doan SET phong_id = p_phong_moi_id WHERE doan_id = v_doan;
    INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc)
    VALUES (p_dat_phong_id, p_phong_moi_id, v_tu, v_den);
    UPDATE phong SET trang_thai = 'BAO_TRI' WHERE phong_id = v_phong_cu;
    UPDATE phong SET trang_thai = 'DANG_O'  WHERE phong_id = p_phong_moi_id;
    pkg_email.xep(p_dat_phong_id, 'THAY_DOI_DON');
  END doi_phong_su_co;

  PROCEDURE check_out (p_dat_phong_id IN NUMBER, p_nguoi_lap_id IN NUMBER,
                       p_phu_thu_tien IN NUMBER DEFAULT 0, p_phu_thu_mo_ta IN VARCHAR2 DEFAULT NULL,
                       p_giam_gia IN NUMBER DEFAULT 0, p_giam_gia_ly_do IN VARCHAR2 DEFAULT NULL,
                       p_hoa_don_id OUT NUMBER, p_tong_hoa_don OUT NUMBER, p_con_phai_thu OUT NUMBER) IS
    r          dat_phong%ROWTYPE;
    v_ra       TIMESTAMP WITH TIME ZONE := pkg_gia.bay_gio;
    v_qua      NUMBER;
    v_chiu_thue NUMBER;
    v_vat      NUMBER;
    v_tong     NUMBER;
    v_doan     NUMBER;
    v_phong    NUMBER;
    v_tu       TIMESTAMP WITH TIME ZONE;
    v_den      TIMESTAMP WITH TIME ZONE;
    v_so_hd    NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CHECKED_IN' THEN
      sai_trang_thai(r.trang_thai);
    END IF;
    IF NVL(p_phu_thu_tien, 0) < 0 OR NVL(p_giam_gia, 0) < 0 THEN loi_du_lieu('SO_TIEN'); END IF;
    IF NVL(p_phu_thu_tien, 0) > 0 AND p_phu_thu_mo_ta IS NULL THEN loi_du_lieu('PHU_THU'); END IF;
    IF NVL(p_giam_gia, 0) > 0 AND p_giam_gia_ly_do IS NULL THEN loi_du_lieu('GIAM_GIA'); END IF;

    v_qua       := pkg_gia.tien_qua_gio(r.loai_dat, r.tu_luc, r.den_luc, v_ra, r.don_gia_ap_dung, r.don_gia_ngay_ap_dung);
    v_chiu_thue := r.tien_phong + v_qua + NVL(p_phu_thu_tien, 0) - NVL(p_giam_gia, 0);
    IF v_chiu_thue < 0 THEN loi_du_lieu('GIAM_GIA'); END IF;
    v_vat  := pkg_gia.tinh_vat(v_chiu_thue, r.thue_suat);
    v_tong := v_chiu_thue + v_vat;

    -- BR-37: trả sớm thì mở lại phần thời gian dư
    doan_cuoi(p_dat_phong_id, v_doan, v_phong, v_tu, v_den);
    IF v_ra > v_tu AND v_ra < v_den THEN
      UPDATE dat_phong_doan SET den_luc = v_ra WHERE doan_id = v_doan;
    END IF;
    UPDATE dat_phong SET trang_thai = 'CHECKED_OUT', tra_thuc_te = v_ra WHERE dat_phong_id = p_dat_phong_id;
    UPDATE phong SET trang_thai = 'DANG_DON' WHERE phong_id = v_phong;

    -- BR-44: hóa đơn nội bộ, số liên tục
    v_so_hd := pkg_hoa_don.cap_so;
    INSERT INTO hoa_don (so_hoa_don, dat_phong_id, tong_tien, nguoi_lap_id)
    VALUES (v_so_hd, p_dat_phong_id, v_tong, p_nguoi_lap_id)
    RETURNING hoa_don_id INTO p_hoa_don_id;

    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien)
    VALUES (p_hoa_don_id, 'TIEN_PHONG', 'Tiền phòng (đã gồm phí dịch vụ)', r.tien_phong);
    IF v_qua > 0 THEN
      INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien)
      VALUES (p_hoa_don_id, 'QUA_GIO', 'Ở quá giờ trả phòng', v_qua);
    END IF;
    IF NVL(p_phu_thu_tien, 0) > 0 THEN
      INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien)
      VALUES (p_hoa_don_id, 'PHU_THU', p_phu_thu_mo_ta, p_phu_thu_tien);
    END IF;
    IF NVL(p_giam_gia, 0) > 0 THEN
      INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien)
      VALUES (p_hoa_don_id, 'GIAM_GIA', p_giam_gia_ly_do, -p_giam_gia);
    END IF;
    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien, thue_suat)
    VALUES (p_hoa_don_id, 'VAT', 'Thuế GTGT', v_vat, r.thue_suat);

    p_tong_hoa_don := v_tong;
    p_con_phai_thu := v_tong - pkg_thanh_toan.tinh_da_thanh_toan(p_dat_phong_id);
    pkg_email.xep(p_dat_phong_id, 'XAC_NHAN');
  END check_out;

  PROCEDURE no_show_thu_cong (p_dat_phong_id IN NUMBER) IS
    r dat_phong%ROWTYPE;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CONFIRMED' THEN sai_trang_thai(r.trang_thai); END IF;
    UPDATE dat_phong SET trang_thai = 'NO_SHOW' WHERE dat_phong_id = p_dat_phong_id;
  END no_show_thu_cong;

  FUNCTION goi_y_phong (p_loai_phong_id IN NUMBER, p_tu IN TIMESTAMP WITH TIME ZONE,
                        p_den IN TIMESTAMP WITH TIME ZONE) RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT p.phong_id, p.ma_phong, p.so_tang
        FROM phong p
       WHERE p.loai_phong_id = p_loai_phong_id AND p.dang_hoat_dong = TRUE AND p.trang_thai <> 'BAO_TRI'
         AND pkg_kiem_tra_trung.dem_xung_dot(p.phong_id, p_tu, p_den) = 0
       ORDER BY pkg_kiem_tra_trung.khoang_cach_lan_can(p.phong_id, p_tu, p_den), p.ma_phong;
    RETURN c;
  END goi_y_phong;

  FUNCTION tim_hang_con_phong (p_loai_dat IN VARCHAR2,
                               p_tu IN TIMESTAMP WITH TIME ZONE,
                               p_den IN TIMESTAMP WITH TIME ZONE,
                               p_so_khach IN NUMBER DEFAULT NULL) RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT lp.loai_phong_id, lp.ma_hang,
             COUNT(ph.phong_id) AS so_phong_con,
             g.don_gia, g.tien_phong, g.thue_suat, g.tien_vat, g.tong_tien
        FROM loai_phong lp
        JOIN phong ph ON ph.loai_phong_id = lp.loai_phong_id AND ph.dang_hoat_dong = TRUE
        CROSS JOIN LATERAL (
          SELECT * FROM TABLE(CAST(MULTISET(
            SELECT pkg_gia.chot_gia(lp.loai_phong_id, p_loai_dat, p_tu, p_den) FROM dual
          ) AS SYS.ODCIDATALIST))
        ) g_dummy
        CROSS JOIN (SELECT pkg_gia.chot_gia(lp.loai_phong_id, p_loai_dat, p_tu, p_den) AS gg FROM dual) gg_row
        JOIN TABLE(CAST(MULTISET(SELECT 1 FROM dual) AS SYS.ODCINUMBERLIST)) t ON 1=1
       WHERE (p_loai_dat <> 'GIO' OR lp.cho_thue_gio = TRUE)
         AND (p_so_khach IS NULL OR lp.suc_chua IS NULL OR lp.suc_chua >= p_so_khach)
         AND pkg_kiem_tra_trung.dem_xung_dot(ph.phong_id, p_tu, p_den) = 0
       GROUP BY lp.loai_phong_id, lp.ma_hang, gg_row.gg.don_gia, gg_row.gg.tien_phong,
                gg_row.gg.thue_suat, gg_row.gg.tien_vat, gg_row.gg.tong_tien
      HAVING COUNT(ph.phong_id) > 0
       ORDER BY lp.loai_phong_id;
    RETURN c;
  END tim_hang_con_phong;

  PROCEDURE het_han_giu_cho (p_so_don OUT NUMBER) IS
    v_so NUMBER := 0;
  BEGIN
    FOR r IN (SELECT dat_phong_id FROM dat_phong
               WHERE trang_thai = 'HOLD' AND han_giu_cho < pkg_gia.bay_gio FOR UPDATE SKIP LOCKED) LOOP
      UPDATE dat_phong SET trang_thai = 'EXPIRED' WHERE dat_phong_id = r.dat_phong_id;
      pkg_email.xep(r.dat_phong_id, 'HET_HAN_GIU_CHO');
      v_so := v_so + 1;
    END LOOP;
    p_so_don := v_so;
  END het_han_giu_cho;

  PROCEDURE tu_no_show (p_so_don OUT NUMBER) IS
    v_so NUMBER := 0;
    v_gio NUMBER := pkg_cau_hinh.lay_so('GIO_NO_SHOW');
  BEGIN
    FOR r IN (
      SELECT dp.dat_phong_id FROM dat_phong dp
       WHERE dp.trang_thai = 'CONFIRMED'
         AND dp.phuong_thuc_thanh_toan = 'KHI_NHAN_PHONG'
         AND dp.tu_luc + NUMTODSINTERVAL(v_gio, 'HOUR') < pkg_gia.bay_gio
       FOR UPDATE SKIP LOCKED
    ) LOOP
      UPDATE dat_phong SET trang_thai = 'NO_SHOW' WHERE dat_phong_id = r.dat_phong_id;
      v_so := v_so + 1;
    END LOOP;
    p_so_don := v_so;
  END tu_no_show;

  PROCEDURE job_het_han_giu_cho IS v_n NUMBER; BEGIN het_han_giu_cho(v_n); COMMIT; END job_het_han_giu_cho;
  PROCEDURE job_no_show IS v_n NUMBER; BEGIN tu_no_show(v_n); COMMIT; END job_no_show;

END pkg_dat_phong;
/

-- Thêm cột LA_DIEU_CHINH và HOA_DON_GOC_ID vào bảng HOA_DON nếu chưa có
-- (chạy an toàn với DBMS_METADATA check)
DECLARE
  v_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_count
    FROM user_tab_columns
   WHERE table_name = 'HOA_DON' AND column_name = 'LA_DIEU_CHINH';
  IF v_count = 0 THEN
    EXECUTE IMMEDIATE 'ALTER TABLE hoa_don ADD (la_dieu_chinh BOOLEAN DEFAULT FALSE NOT NULL)';
    EXECUTE IMMEDIATE 'ALTER TABLE hoa_don ADD (hoa_don_goc_id NUMBER(19))';
    EXECUTE IMMEDIATE 'ALTER TABLE hoa_don ADD CONSTRAINT fk_hoa_don_goc_id FOREIGN KEY (hoa_don_goc_id) REFERENCES hoa_don (hoa_don_id)';
  END IF;
END;
/

-- Thêm hàm TINH_TRUOC_CHECK_OUT vào spec nếu chưa có
-- (Thêm vào spec pkg_dat_phong)
CREATE OR REPLACE PACKAGE pkg_dat_phong AS
  PROCEDURE tao_don (p_ho_ten IN VARCHAR2, p_sdt IN VARCHAR2, p_email IN VARCHAR2, p_quoc_tich IN VARCHAR2,
                     p_ngon_ngu IN VARCHAR2, p_loai_dat IN VARCHAR2, p_kenh_dat IN VARCHAR2,
                     p_ma_hang IN VARCHAR2, p_phong_id IN NUMBER,
                     p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                     p_so_khach IN NUMBER, p_thanh_toan IN VARCHAR2, p_dong_y_luc IN TIMESTAMP WITH TIME ZONE,
                     p_dat_phong_id OUT NUMBER, p_ma_tra_cuu OUT VARCHAR2, p_trang_thai OUT VARCHAR2,
                     p_phong_id_gan OUT NUMBER, p_tien_phong OUT NUMBER, p_tien_vat OUT NUMBER,
                     p_tong_tien OUT NUMBER, p_han_giu_cho OUT TIMESTAMP WITH TIME ZONE);
  FUNCTION hoan_du_kien (p_dat_phong_id IN NUMBER) RETURN NUMBER;
  PROCEDURE huy_don (p_dat_phong_id IN NUMBER, p_ly_do IN VARCHAR2, p_so_tien_hoan OUT NUMBER);
  PROCEDURE doi_lich (p_dat_phong_id IN NUMBER, p_tu_moi IN TIMESTAMP WITH TIME ZONE,
                      p_den_moi IN TIMESTAMP WITH TIME ZONE,
                      p_phong_moi_id IN NUMBER DEFAULT NULL, p_chenh_lech OUT NUMBER, p_so_tien_hoan OUT NUMBER);
  PROCEDURE check_in (p_dat_phong_id IN NUMBER, p_loai_giay_to IN VARCHAR2, p_so_giay_to IN VARCHAR2,
                      p_quoc_tich IN VARCHAR2, p_anh_url IN VARCHAR2 DEFAULT NULL, p_phong_id OUT NUMBER);
  PROCEDURE gia_han (p_dat_phong_id IN NUMBER, p_so_don_vi IN NUMBER, p_tien_them OUT NUMBER);
  PROCEDURE doi_phong_su_co (p_dat_phong_id IN NUMBER, p_phong_moi_id IN NUMBER, p_ly_do IN VARCHAR2);
  PROCEDURE check_out (p_dat_phong_id IN NUMBER, p_nguoi_lap_id IN NUMBER,
                       p_phu_thu_tien IN NUMBER DEFAULT 0, p_phu_thu_mo_ta IN VARCHAR2 DEFAULT NULL,
                       p_giam_gia IN NUMBER DEFAULT 0, p_giam_gia_ly_do IN VARCHAR2 DEFAULT NULL,
                       p_hoa_don_id OUT NUMBER, p_tong_hoa_don OUT NUMBER, p_con_phai_thu OUT NUMBER);
  PROCEDURE tinh_truoc_check_out (
    p_dat_phong_id    IN  NUMBER,
    p_phu_thu_tien    IN  NUMBER DEFAULT 0,
    p_giam_gia        IN  NUMBER DEFAULT 0,
    p_tien_phong      OUT NUMBER,
    p_tien_qua_gio    OUT NUMBER,
    p_phu_thu         OUT NUMBER,
    p_giam_gia_ra     OUT NUMBER,
    p_tien_vat        OUT NUMBER,
    p_tong_hoa_don    OUT NUMBER,
    p_da_thanh_toan   OUT NUMBER,
    p_con_phai_thu    OUT NUMBER
  );
  PROCEDURE no_show_thu_cong (p_dat_phong_id IN NUMBER);
  FUNCTION goi_y_phong (p_loai_phong_id IN NUMBER, p_tu IN TIMESTAMP WITH TIME ZONE,
                        p_den IN TIMESTAMP WITH TIME ZONE) RETURN SYS_REFCURSOR;
  FUNCTION tim_hang_con_phong (p_loai_dat IN VARCHAR2,
                               p_tu IN TIMESTAMP WITH TIME ZONE,
                               p_den IN TIMESTAMP WITH TIME ZONE,
                               p_so_khach IN NUMBER DEFAULT NULL) RETURN SYS_REFCURSOR;
  PROCEDURE het_han_giu_cho (p_so_don OUT NUMBER);
  PROCEDURE tu_no_show (p_so_don OUT NUMBER);
  PROCEDURE job_het_han_giu_cho;
  PROCEDURE job_no_show;
END pkg_dat_phong;
/

PROMPT F11 DB script compiled successfully.
