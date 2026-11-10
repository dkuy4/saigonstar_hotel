-- =====================================================================
-- 08_pkg_nghiep_vu.sql: package nghiệp vụ (SRS mục 9.2)
--   PKG_EMAIL        xếp email vào hàng đợi (BR-29)
--   PKG_GIA          tính giá, VAT, tiền ở quá giờ (BR-04, BR-33, BR-39, BR-42, BR-57, BR-58)
--   PKG_THANH_TOAN   thanh toán, thanh toán về muộn, hoàn tiền, đối soát (BR-18, BR-19, BR-24 đến BR-26, FR-34 đến FR-39)
--   PKG_PHONG        sơ đồ phòng, dọn phòng, bảo trì (BR-40, BR-41, FR-12, FR-24, FR-32)
--   PKG_DAT_PHONG    tạo, đổi, hủy đơn, check-in, gia hạn, đổi phòng sự cố, check-out, tác vụ nền (FR-04 đến FR-23)
--   PKG_BAO_CAO      doanh thu, công suất, hủy và no-show, ADR, RevPAR (FR-40 đến FR-44)
-- Quy ước: không procedure nào COMMIT hay ROLLBACK toàn giao dịch; API commit sau khi gọi xong. Tham số cờ dùng NUMBER 1 hoặc 0.
-- Trước mỗi giao dịch API gọi PKG_NGU_CANH.DAT để nhật ký ghi đúng người thực hiện.
-- Mã lỗi thêm ngoài 03_packages.sql:
--   -20050 PENDING_LIMIT_EXCEEDED  -20051 NO_AVAILABILITY    -20052 CANCEL_NOT_ALLOWED  -20053 CHECKIN_TOO_EARLY
--   -20054 ROOM_NOT_READY          -20055 EXTEND_CONFLICT    -20056 REFUND_EXCEEDS_PAID -20060 VALIDATION_ERROR
--   -20041 PRICE_MISSING           -20061 BOOKING_NOT_FOUND  -20062 HOLD_EXPIRED        -20063 PAYMENT_NOT_FOUND
--   -20064 REFUND_STATE_INVALID    -20065 ROOM_STATE_INVALID -20066 MAINTENANCE_HAS_BOOKINGS
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_email AS
  PROCEDURE xep (p_dat_phong_id IN NUMBER, p_loai_email IN VARCHAR2);
END pkg_email;
/
CREATE OR REPLACE PACKAGE BODY pkg_email AS
  -- Loại email theo phụ lục C của BRD: XAC_NHAN, THAY_DOI_DON, HUY_HOAN_TIEN, HET_HAN_GIU_CHO, THANH_TOAN_VE_MUON.
  -- Ngôn ngữ lấy từ đơn (BR-51). Tiến trình gửi lấy từ HANG_DOI_EMAIL, thử lại khi lỗi (FR-53).
  PROCEDURE xep (p_dat_phong_id IN NUMBER, p_loai_email IN VARCHAR2) IS
  BEGIN
    INSERT INTO hang_doi_email (dat_phong_id, loai_email, ngon_ngu)
    SELECT dat_phong_id, p_loai_email, ngon_ngu FROM dat_phong WHERE dat_phong_id = p_dat_phong_id;
  END xep;
END pkg_email;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_gia AS
  TYPE t_gia IS RECORD (
    don_gia       NUMBER,   -- đơn giá áp dụng cho đơn: giá ngày với đơn theo ngày, giá giờ với đơn theo giờ
    don_gia_ngay  NUMBER,   -- giá ngày cùng thời điểm (đơn giờ cần để tính lại khi vượt ngưỡng giờ)
    tien_phong    NUMBER,
    thue_suat     NUMBER,
    tien_vat      NUMBER,
    tong_tien     NUMBER);

  FUNCTION bay_gio RETURN TIMESTAMP WITH TIME ZONE;                    -- thời điểm hiện tại, bỏ phần lẻ giây
  FUNCTION lam_tron_vnd (p_so IN NUMBER) RETURN NUMBER;               -- làm tròn tới đồng, 0,5 làm tròn lên
  FUNCTION so_phut (p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) RETURN NUMBER;
  FUNCTION so_dem (p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) RETURN NUMBER;
  FUNCTION don_gia (p_loai_phong_id IN NUMBER, p_loai_gia IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN NUMBER;
  FUNCTION thue_suat (p_tai IN DATE DEFAULT NULL) RETURN NUMBER;
  FUNCTION tien_theo_gio (p_so_gio IN NUMBER, p_don_gia_gio IN NUMBER, p_don_gia_ngay IN NUMBER) RETURN NUMBER;
  FUNCTION tien_phong (p_loai_dat IN VARCHAR2, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                       p_don_gia IN NUMBER, p_don_gia_ngay IN NUMBER) RETURN NUMBER;
  FUNCTION tinh_vat (p_tien IN NUMBER, p_thue_suat IN NUMBER) RETURN NUMBER;
  FUNCTION chot_gia (p_loai_phong_id IN NUMBER, p_loai_dat IN VARCHAR2,
                     p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) RETURN t_gia;
  FUNCTION tien_qua_gio (p_loai_dat IN VARCHAR2, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                         p_tra_thuc_te IN TIMESTAMP WITH TIME ZONE, p_don_gia IN NUMBER, p_don_gia_ngay IN NUMBER) RETURN NUMBER;
END pkg_gia;
/
CREATE OR REPLACE PACKAGE BODY pkg_gia AS

  FUNCTION bay_gio RETURN TIMESTAMP WITH TIME ZONE IS
    v TIMESTAMP(0) WITH TIME ZONE := SYSTIMESTAMP;
  BEGIN
    RETURN v;
  END bay_gio;

  -- Quy ước làm tròn VAT: tới đồng, 0,5 làm tròn lên. BRD chưa nêu; đổi ở đây nếu kế toán yêu cầu khác.
  FUNCTION lam_tron_vnd (p_so IN NUMBER) RETURN NUMBER IS
  BEGIN
    RETURN ROUND(p_so, 0);
  END lam_tron_vnd;

  FUNCTION so_phut (p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) RETURN NUMBER IS
    v INTERVAL DAY(9) TO SECOND := p_den - p_tu;
  BEGIN
    RETURN EXTRACT(DAY FROM v) * 1440 + EXTRACT(HOUR FROM v) * 60 + EXTRACT(MINUTE FROM v) + EXTRACT(SECOND FROM v) / 60;
  END so_phut;

  -- Số đêm của đơn theo ngày: chênh lệch ngày lịch giờ Việt Nam giữa ngày trả và ngày nhận
  FUNCTION so_dem (p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) RETURN NUMBER IS
  BEGIN
    RETURN TRUNC(CAST(p_den AT TIME ZONE '+07:00' AS DATE)) - TRUNC(CAST(p_tu AT TIME ZONE '+07:00' AS DATE));
  END so_dem;

  FUNCTION don_gia (p_loai_phong_id IN NUMBER, p_loai_gia IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN NUMBER IS
    v_tai DATE := NVL(p_tai, pkg_cau_hinh.ngay_vn);
    v_kq  NUMBER;
  BEGIN
    SELECT dg INTO v_kq
      FROM (SELECT b.don_gia AS dg
              FROM bang_gia b
             WHERE b.loai_phong_id = p_loai_phong_id AND b.loai_gia = p_loai_gia
               AND b.hieu_luc_tu <= v_tai AND (b.hieu_luc_den IS NULL OR b.hieu_luc_den >= v_tai)
             ORDER BY b.hieu_luc_tu DESC)
     WHERE ROWNUM = 1;
    RETURN v_kq;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20041, 'PRICE_MISSING|' || p_loai_phong_id || '|' || p_loai_gia);
  END don_gia;

  FUNCTION thue_suat (p_tai IN DATE DEFAULT NULL) RETURN NUMBER IS
  BEGIN
    RETURN pkg_cau_hinh.lay_so('THUE_SUAT_VAT', p_tai);
  END thue_suat;

  -- BR-04: từ 1 đến ngưỡng giờ (5) tính số giờ nhân giá giờ; vượt ngưỡng tính đúng một giá ngày cho cả đơn
  FUNCTION tien_theo_gio (p_so_gio IN NUMBER, p_don_gia_gio IN NUMBER, p_don_gia_ngay IN NUMBER) RETURN NUMBER IS
  BEGIN
    IF p_so_gio <= pkg_cau_hinh.lay_so('NGUONG_GIO_TINH_NGAY') THEN
      RETURN p_so_gio * p_don_gia_gio;
    END IF;
    RETURN p_don_gia_ngay;
  END tien_theo_gio;

  FUNCTION tien_phong (p_loai_dat IN VARCHAR2, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                       p_don_gia IN NUMBER, p_don_gia_ngay IN NUMBER) RETURN NUMBER IS
    v_phut NUMBER;
  BEGIN
    IF p_loai_dat = 'NGAY' THEN
      RETURN so_dem(p_tu, p_den) * p_don_gia_ngay;
    END IF;
    v_phut := so_phut(p_tu, p_den);
    IF v_phut <= 0 OR MOD(v_phut, 60) <> 0 THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|SO_GIO');
    END IF;
    RETURN tien_theo_gio(v_phut / 60, p_don_gia, p_don_gia_ngay);
  END tien_phong;

  FUNCTION tinh_vat (p_tien IN NUMBER, p_thue_suat IN NUMBER) RETURN NUMBER IS
  BEGIN
    RETURN lam_tron_vnd(p_tien * p_thue_suat);
  END tinh_vat;

  -- BR-42: chốt đơn giá, giá ngày và thuế suất theo bảng giá và cấu hình có hiệu lực lúc tạo đơn
  FUNCTION chot_gia (p_loai_phong_id IN NUMBER, p_loai_dat IN VARCHAR2,
                     p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE) RETURN t_gia IS
    r t_gia;
  BEGIN
    r.don_gia_ngay := don_gia(p_loai_phong_id, 'NGAY');
    r.don_gia      := CASE WHEN p_loai_dat = 'GIO' THEN don_gia(p_loai_phong_id, 'GIO') ELSE r.don_gia_ngay END;
    r.tien_phong   := tien_phong(p_loai_dat, p_tu, p_den, r.don_gia, r.don_gia_ngay);
    r.thue_suat    := thue_suat;
    r.tien_vat     := tinh_vat(r.tien_phong, r.thue_suat);
    r.tong_tien    := r.tien_phong + r.tien_vat;
    RETURN r;
  END chot_gia;

  -- BR-39: tiền ở quá giờ trả, sau ân hạn. Đơn theo ngày: mỗi ngày bắt đầu tính một đêm theo giá đã chốt.
  -- Đơn theo giờ: thêm theo giờ nguyên, vượt ngưỡng giờ thì tính lại thành một giá ngày (BR-33).
  FUNCTION tien_qua_gio (p_loai_dat IN VARCHAR2, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                         p_tra_thuc_te IN TIMESTAMP WITH TIME ZONE, p_don_gia IN NUMBER, p_don_gia_ngay IN NUMBER) RETURN NUMBER IS
    v_qua     NUMBER := so_phut(p_den, p_tra_thuc_te);
    v_gio_dat NUMBER;
    v_them    NUMBER;
  BEGIN
    IF v_qua <= pkg_cau_hinh.lay_so('PHUT_AN_HAN_QUA_GIO') THEN
      RETURN 0;
    END IF;
    IF p_loai_dat = 'NGAY' THEN
      RETURN CEIL(v_qua / 1440) * p_don_gia_ngay;
    END IF;
    v_gio_dat := so_phut(p_tu, p_den) / 60;
    v_them    := CEIL(v_qua / 60);
    RETURN tien_theo_gio(v_gio_dat + v_them, p_don_gia, p_don_gia_ngay) - tien_theo_gio(v_gio_dat, p_don_gia, p_don_gia_ngay);
  END tien_qua_gio;

END pkg_gia;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_thanh_toan AS
  FUNCTION tong_thu (p_dat_phong_id IN NUMBER) RETURN NUMBER;            -- tổng giao dịch THANH_CONG
  FUNCTION tong_hoan (p_dat_phong_id IN NUMBER) RETURN NUMBER;           -- tổng hoàn chưa bị từ chối
  FUNCTION tinh_da_thanh_toan (p_dat_phong_id IN NUMBER) RETURN NUMBER;  -- thu trừ hoàn
  FUNCTION da_thanh_toan_truoc (p_dat_phong_id IN NUMBER) RETURN NUMBER; -- 1 nếu có ít nhất một giao dịch THANH_CONG

  PROCEDURE ghi_nhan_quay (p_dat_phong_id IN NUMBER, p_phuong_thuc IN VARCHAR2, p_so_tien IN NUMBER,
                           p_giao_dich_id OUT NUMBER);
  PROCEDURE tao_giao_dich_cong (p_dat_phong_id IN NUMBER, p_ma_tham_chieu IN VARCHAR2, p_giao_dich_id OUT NUMBER);
  -- Kết quả: XAC_NHAN, XAC_NHAN_MUON, HOAN_TIEN, THAT_BAI, DA_XU_LY (callback lặp)
  PROCEDURE xu_ly_ket_qua_cong (p_ma_tham_chieu IN VARCHAR2, p_thanh_cong IN NUMBER, p_ket_qua OUT VARCHAR2);

  PROCEDURE tao_hoan (p_dat_phong_id IN NUMBER, p_so_tien IN NUMBER, p_ly_do IN VARCHAR2,
                      p_nguoi_de_nghi_id IN NUMBER DEFAULT NULL, p_nguoi_duyet_id IN NUMBER DEFAULT NULL);
  PROCEDURE duyet_hoan_tien (p_hoan_tien_id IN NUMBER, p_nguoi_duyet_id IN NUMBER, p_dong_y IN NUMBER);
  PROCEDURE xac_nhan_da_hoan (p_hoan_tien_id IN NUMBER);
  PROCEDURE hoan_ngoai_le (p_dat_phong_id IN NUMBER, p_so_tien IN NUMBER, p_ly_do IN VARCHAR2, p_quan_ly_id IN NUMBER);
  FUNCTION doi_soat_ngay (p_ngay IN DATE) RETURN SYS_REFCURSOR;
END pkg_thanh_toan;
/
CREATE OR REPLACE PACKAGE BODY pkg_thanh_toan AS

  FUNCTION tong_thu (p_dat_phong_id IN NUMBER) RETURN NUMBER IS
    v NUMBER;
  BEGIN
    SELECT NVL(SUM(so_tien), 0) INTO v FROM giao_dich_thanh_toan
     WHERE dat_phong_id = p_dat_phong_id AND trang_thai = 'THANH_CONG';
    RETURN v;
  END tong_thu;

  FUNCTION tong_hoan (p_dat_phong_id IN NUMBER) RETURN NUMBER IS
    v NUMBER;
  BEGIN
    SELECT NVL(SUM(h.so_tien), 0) INTO v
      FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
     WHERE g.dat_phong_id = p_dat_phong_id AND h.trang_thai <> 'TU_CHOI';
    RETURN v;
  END tong_hoan;

  FUNCTION tinh_da_thanh_toan (p_dat_phong_id IN NUMBER) RETURN NUMBER IS
  BEGIN
    RETURN tong_thu(p_dat_phong_id) - tong_hoan(p_dat_phong_id);
  END tinh_da_thanh_toan;

  FUNCTION da_thanh_toan_truoc (p_dat_phong_id IN NUMBER) RETURN NUMBER IS
  BEGIN
    RETURN CASE WHEN tong_thu(p_dat_phong_id) > 0 THEN 1 ELSE 0 END;
  END da_thanh_toan_truoc;

  -- FR-34, BR-45: thu tại quầy (tiền mặt, chuyển khoản, thẻ); một đơn có nhiều giao dịch
  PROCEDURE ghi_nhan_quay (p_dat_phong_id IN NUMBER, p_phuong_thuc IN VARCHAR2, p_so_tien IN NUMBER,
                           p_giao_dich_id OUT NUMBER) IS
    v_tt dat_phong.trang_thai%TYPE;
  BEGIN
    IF p_phuong_thuc NOT IN ('TIEN_MAT', 'CHUYEN_KHOAN', 'THE') OR p_so_tien IS NULL OR p_so_tien <= 0 THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|THANH_TOAN');
    END IF;
    SELECT trang_thai INTO v_tt FROM dat_phong WHERE dat_phong_id = p_dat_phong_id FOR UPDATE;
    IF v_tt NOT IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT') THEN
      RAISE_APPLICATION_ERROR(-20003, 'BOOKING_STATE_INVALID|' || v_tt);
    END IF;
    INSERT INTO giao_dich_thanh_toan (dat_phong_id, kenh, phuong_thuc, so_tien, trang_thai)
    VALUES (p_dat_phong_id, 'QUAY', p_phuong_thuc, p_so_tien, 'THANH_CONG')
    RETURNING giao_dich_id INTO p_giao_dich_id;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20061, 'BOOKING_NOT_FOUND|' || p_dat_phong_id);
  END ghi_nhan_quay;

  -- FR-07, FR-35: tạo giao dịch chờ xử lý cho đơn HOLD; số tiền là 100% tổng tiền (D-34)
  PROCEDURE tao_giao_dich_cong (p_dat_phong_id IN NUMBER, p_ma_tham_chieu IN VARCHAR2, p_giao_dich_id OUT NUMBER) IS
    d dat_phong%ROWTYPE;
  BEGIN
    SELECT * INTO d FROM dat_phong WHERE dat_phong_id = p_dat_phong_id FOR UPDATE;
    IF d.trang_thai <> 'HOLD' OR d.han_giu_cho <= SYSTIMESTAMP THEN
      RAISE_APPLICATION_ERROR(-20062, 'HOLD_EXPIRED|' || p_dat_phong_id);
    END IF;
    INSERT INTO giao_dich_thanh_toan (dat_phong_id, kenh, phuong_thuc, so_tien, trang_thai, ma_tham_chieu_cong)
    VALUES (p_dat_phong_id, 'CONG', 'ONLINE', d.tong_tien, 'CHO_XU_LY', p_ma_tham_chieu)
    RETURNING giao_dich_id INTO p_giao_dich_id;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20061, 'BOOKING_NOT_FOUND|' || p_dat_phong_id);
  END tao_giao_dich_cong;

  -- FR-35, FR-36, BR-18, BR-19: xử lý kết quả cổng. Gọi lặp với cùng mã tham chiếu thì không làm gì thêm (idempotent).
  PROCEDURE xu_ly_ket_qua_cong (p_ma_tham_chieu IN VARCHAR2, p_thanh_cong IN NUMBER, p_ket_qua OUT VARCHAR2) IS
    g giao_dich_thanh_toan%ROWTYPE;
    d dat_phong%ROWTYPE;
  BEGIN
    BEGIN
      SELECT * INTO g FROM giao_dich_thanh_toan WHERE ma_tham_chieu_cong = p_ma_tham_chieu FOR UPDATE;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20063, 'PAYMENT_NOT_FOUND|' || p_ma_tham_chieu);
    END;
    IF g.trang_thai <> 'CHO_XU_LY' THEN
      p_ket_qua := 'DA_XU_LY';
      RETURN;
    END IF;
    SELECT * INTO d FROM dat_phong WHERE dat_phong_id = g.dat_phong_id FOR UPDATE;

    IF p_thanh_cong = 0 THEN
      UPDATE giao_dich_thanh_toan SET trang_thai = 'THAT_BAI' WHERE giao_dich_id = g.giao_dich_id;
      IF d.trang_thai = 'HOLD' THEN
        UPDATE dat_phong SET trang_thai = 'EXPIRED' WHERE dat_phong_id = d.dat_phong_id;     -- BR-18: thanh toán thất bại
        pkg_email.xep(d.dat_phong_id, 'HET_HAN_GIU_CHO');
      END IF;
      p_ket_qua := 'THAT_BAI';
      RETURN;
    END IF;

    UPDATE giao_dich_thanh_toan SET trang_thai = 'THANH_CONG', ngay_giao_dich = SYSTIMESTAMP WHERE giao_dich_id = g.giao_dich_id;

    IF d.trang_thai = 'HOLD' AND d.han_giu_cho > SYSTIMESTAMP THEN
      UPDATE dat_phong SET trang_thai = 'CONFIRMED' WHERE dat_phong_id = d.dat_phong_id;       -- BR-18
      pkg_email.xep(d.dat_phong_id, 'XAC_NHAN');
      p_ket_qua := 'XAC_NHAN';
    ELSIF d.trang_thai IN ('HOLD', 'EXPIRED') THEN
      -- BR-19: về muộn. Phòng còn trống thì xác nhận; nếu đã có người đặt, trigger TRG_DAT_PHONG_CHIEM_LAI ném ROOM_CONFLICT
      SAVEPOINT sp_ve_muon;
      BEGIN
        UPDATE dat_phong SET trang_thai = 'CONFIRMED' WHERE dat_phong_id = d.dat_phong_id;
        pkg_email.xep(d.dat_phong_id, 'THANH_TOAN_VE_MUON');
        p_ket_qua := 'XAC_NHAN_MUON';
      EXCEPTION
        WHEN OTHERS THEN
          IF SQLCODE = -20001 THEN
            ROLLBACK TO SAVEPOINT sp_ve_muon;
            IF d.trang_thai = 'HOLD' THEN
              UPDATE dat_phong SET trang_thai = 'EXPIRED' WHERE dat_phong_id = d.dat_phong_id;
            END IF;
            tao_hoan(d.dat_phong_id, g.so_tien, 'Thanh toán về muộn, phòng đã có người đặt (BR-19)');
            pkg_email.xep(d.dat_phong_id, 'THANH_TOAN_VE_MUON');
            p_ket_qua := 'HOAN_TIEN';
          ELSE
            RAISE;
          END IF;
      END;
    ELSE
      -- Đơn đã CONFIRMED, CANCELLED, NO_SHOW...: không còn chờ thanh toán này, hoàn lại toàn bộ
      tao_hoan(d.dat_phong_id, g.so_tien, 'Đơn không còn chờ thanh toán, trạng thái ' || d.trang_thai);
      pkg_email.xep(d.dat_phong_id, 'THANH_TOAN_VE_MUON');
      p_ket_qua := 'HOAN_TIEN';
    END IF;
  END xu_ly_ket_qua_cong;

  -- BR-25: hoàn về đúng phương thức đã trả, bắt đầu từ giao dịch mới nhất. Cổng: hệ thống hoàn (DA_DUYET).
  -- Quầy: lễ tân chi trả, quản lý duyệt (CHO_DUYET), trừ khi có p_nguoi_duyet_id (hoàn ngoại lệ do quản lý, BR-26).
  PROCEDURE tao_hoan (p_dat_phong_id IN NUMBER, p_so_tien IN NUMBER, p_ly_do IN VARCHAR2,
                      p_nguoi_de_nghi_id IN NUMBER DEFAULT NULL, p_nguoi_duyet_id IN NUMBER DEFAULT NULL) IS
    v_con   NUMBER := NVL(p_so_tien, 0);
    v_da    NUMBER;
    v_hoan  NUMBER;
  BEGIN
    IF v_con <= 0 THEN
      RETURN;
    END IF;
    IF v_con > tinh_da_thanh_toan(p_dat_phong_id) THEN        -- kiểm tra trước khi ghi, để lỗi không để lại bản ghi hoàn dở
      RAISE_APPLICATION_ERROR(-20056, 'REFUND_EXCEEDS_PAID|' || (v_con - tinh_da_thanh_toan(p_dat_phong_id)));
    END IF;
    FOR g IN (SELECT giao_dich_id, kenh, so_tien
                FROM giao_dich_thanh_toan
               WHERE dat_phong_id = p_dat_phong_id AND trang_thai = 'THANH_CONG'
               ORDER BY ngay_giao_dich DESC, giao_dich_id DESC) LOOP
      EXIT WHEN v_con <= 0;
      SELECT NVL(SUM(so_tien), 0) INTO v_da FROM hoan_tien WHERE giao_dich_id = g.giao_dich_id AND trang_thai <> 'TU_CHOI';
      IF g.so_tien - v_da > 0 THEN
        v_hoan := LEAST(v_con, g.so_tien - v_da);
        INSERT INTO hoan_tien (giao_dich_id, so_tien, ly_do, trang_thai, nguoi_de_nghi_id, nguoi_duyet_id)
        VALUES (g.giao_dich_id, v_hoan, p_ly_do,
                CASE WHEN p_nguoi_duyet_id IS NOT NULL OR g.kenh = 'CONG' THEN 'DA_DUYET' ELSE 'CHO_DUYET' END,
                p_nguoi_de_nghi_id, p_nguoi_duyet_id);
        v_con := v_con - v_hoan;
      END IF;
    END LOOP;
    IF v_con > 0 THEN
      RAISE_APPLICATION_ERROR(-20056, 'REFUND_EXCEEDS_PAID|' || v_con);
    END IF;
  END tao_hoan;

  PROCEDURE duyet_hoan_tien (p_hoan_tien_id IN NUMBER, p_nguoi_duyet_id IN NUMBER, p_dong_y IN NUMBER) IS
    v_tt hoan_tien.trang_thai%TYPE;
  BEGIN
    SELECT trang_thai INTO v_tt FROM hoan_tien WHERE hoan_tien_id = p_hoan_tien_id FOR UPDATE;
    IF v_tt <> 'CHO_DUYET' THEN
      RAISE_APPLICATION_ERROR(-20064, 'REFUND_STATE_INVALID|' || v_tt);
    END IF;
    UPDATE hoan_tien
       SET trang_thai = CASE WHEN p_dong_y = 1 THEN 'DA_DUYET' ELSE 'TU_CHOI' END, nguoi_duyet_id = p_nguoi_duyet_id
     WHERE hoan_tien_id = p_hoan_tien_id;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20064, 'REFUND_STATE_INVALID|NOT_FOUND');
  END duyet_hoan_tien;

  -- Gọi khi lễ tân đã chi trả (quầy) hoặc cổng báo đã hoàn (trực tuyến, FR-37)
  PROCEDURE xac_nhan_da_hoan (p_hoan_tien_id IN NUMBER) IS
    v_tt hoan_tien.trang_thai%TYPE;
  BEGIN
    SELECT trang_thai INTO v_tt FROM hoan_tien WHERE hoan_tien_id = p_hoan_tien_id FOR UPDATE;
    IF v_tt <> 'DA_DUYET' THEN
      RAISE_APPLICATION_ERROR(-20064, 'REFUND_STATE_INVALID|' || v_tt);
    END IF;
    UPDATE hoan_tien SET trang_thai = 'DA_HOAN' WHERE hoan_tien_id = p_hoan_tien_id;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20064, 'REFUND_STATE_INVALID|NOT_FOUND');
  END xac_nhan_da_hoan;

  -- BR-26: quản lý hoàn tiền ngoại lệ ngoài BR-24, bắt buộc có lý do; nhật ký lưu lý do qua PKG_NGU_CANH
  PROCEDURE hoan_ngoai_le (p_dat_phong_id IN NUMBER, p_so_tien IN NUMBER, p_ly_do IN VARCHAR2, p_quan_ly_id IN NUMBER) IS
  BEGIN
    IF p_ly_do IS NULL OR TRIM(p_ly_do) IS NULL THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|LY_DO');
    END IF;
    pkg_ngu_canh.dat_ly_do(p_ly_do);
    tao_hoan(p_dat_phong_id, p_so_tien, p_ly_do, p_quan_ly_id, p_quan_ly_id);
  END hoan_ngoai_le;

  -- FR-39: tổng thu theo phương thức trong một ngày (giờ Việt Nam). Ngày hoàn tính theo ngày tạo yêu cầu hoàn,
  -- vì HOAN_TIEN chưa có cột thời điểm hoàn xong.
  FUNCTION doi_soat_ngay (p_ngay IN DATE) RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT phuong_thuc, kenh,
             SUM(CASE loai WHEN 'THU' THEN so_tien ELSE 0 END)  AS tong_thu,
             SUM(CASE loai WHEN 'HOAN' THEN so_tien ELSE 0 END) AS tong_hoan,
             SUM(CASE loai WHEN 'THU' THEN so_tien ELSE -so_tien END) AS thuc_thu
        FROM (SELECT g.phuong_thuc, g.kenh, 'THU' AS loai, g.so_tien
                FROM giao_dich_thanh_toan g
               WHERE g.trang_thai = 'THANH_CONG'
                 AND TRUNC(CAST(g.ngay_giao_dich AT TIME ZONE '+07:00' AS DATE)) = p_ngay
              UNION ALL
              SELECT g.phuong_thuc, g.kenh, 'HOAN', h.so_tien
                FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
               WHERE h.trang_thai = 'DA_HOAN'
                 AND TRUNC(CAST(h.ngay_tao AT TIME ZONE '+07:00' AS DATE)) = p_ngay)
       GROUP BY phuong_thuc, kenh
       ORDER BY phuong_thuc, kenh;
    RETURN c;
  END doi_soat_ngay;

END pkg_thanh_toan;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_phong AS
  -- Sơ đồ phòng tại một thời điểm (FR-12, BR-40): trạng thái lưu của phòng, lượt đang chiếm phòng tại thời điểm xem
  -- (kể cả đệm) và lượt kế tiếp. Giao diện tô màu theo các cột này.
  FUNCTION so_do (p_tai IN TIMESTAMP WITH TIME ZONE DEFAULT NULL) RETURN SYS_REFCURSOR;
  PROCEDURE bat_dau_don (p_phong_id IN NUMBER);
  PROCEDURE don_xong (p_phong_id IN NUMBER);
  -- BR-41: đơn tương lai bị ảnh hưởng nếu đưa phòng vào bảo trì
  FUNCTION don_bi_anh_huong (p_phong_id IN NUMBER) RETURN SYS_REFCURSOR;
  PROCEDURE bat_bao_tri (p_phong_id IN NUMBER, p_ly_do IN VARCHAR2, p_bo_qua_don_anh_huong IN NUMBER DEFAULT 0);
  PROCEDURE ket_thuc_bao_tri (p_phong_id IN NUMBER);
  -- BR-40: quản lý sửa trực tiếp trạng thái trái luồng, bắt buộc có lý do
  PROCEDURE doi_trang_thai_thu_cong (p_phong_id IN NUMBER, p_trang_thai_moi IN VARCHAR2, p_ly_do IN VARCHAR2);
  -- NFR-03: phòng lệch giữa trạng thái lưu và lịch đơn
  FUNCTION doi_soat_phong_lich RETURN SYS_REFCURSOR;
END pkg_phong;
/
CREATE OR REPLACE PACKAGE BODY pkg_phong AS

  FUNCTION so_do (p_tai IN TIMESTAMP WITH TIME ZONE DEFAULT NULL) RETURN SYS_REFCURSOR IS
    c     SYS_REFCURSOR;
    v_tai TIMESTAMP WITH TIME ZONE := NVL(p_tai, SYSTIMESTAMP);
    v_dem INTERVAL DAY TO SECOND := NUMTODSINTERVAL(pkg_cau_hinh.lay_so('KHOANG_DEM_PHUT'), 'MINUTE');
  BEGIN
    OPEN c FOR
      SELECT p.phong_id, p.ma_phong, p.so_tang, lp.ma_hang, p.trang_thai, CASE WHEN p.dang_hoat_dong THEN 1 ELSE 0 END AS dang_hoat_dong,
             hn.ma_tra_cuu AS ma_don_hien_tai, hn.trang_thai_don, hn.tu_luc AS luot_tu, hn.den_luc AS luot_den,
             kt.ma_tra_cuu AS ma_don_ke_tiep, kt.tu_luc AS ke_tiep_tu
        FROM phong p
        JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
        OUTER APPLY (SELECT dp.ma_tra_cuu, dp.trang_thai AS trang_thai_don, d.tu_luc, d.den_luc
                       FROM dat_phong_doan d JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
                      WHERE d.phong_id = p.phong_id
                        AND (dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT')
                             OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > SYSTIMESTAMP))
                        AND d.tu_luc <= v_tai AND d.den_luc + v_dem > v_tai
                      ORDER BY d.tu_luc
                      FETCH FIRST 1 ROW ONLY) hn
        OUTER APPLY (SELECT dp.ma_tra_cuu, d.tu_luc
                       FROM dat_phong_doan d JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
                      WHERE d.phong_id = p.phong_id
                        AND (dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN')
                             OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > SYSTIMESTAMP))
                        AND d.tu_luc > v_tai
                      ORDER BY d.tu_luc
                      FETCH FIRST 1 ROW ONLY) kt
       ORDER BY p.so_tang, p.ma_phong;
    RETURN c;
  END so_do;

  PROCEDURE bat_dau_don (p_phong_id IN NUMBER) IS
    v_tt phong.trang_thai%TYPE;
  BEGIN
    SELECT trang_thai INTO v_tt FROM phong WHERE phong_id = p_phong_id FOR UPDATE;
    IF v_tt <> 'DANG_DON' THEN
      RAISE_APPLICATION_ERROR(-20065, 'ROOM_STATE_INVALID|' || v_tt);
    END IF;
    -- Trạng thái vẫn là DANG_DON; việc bắt đầu dọn chỉ để lại dấu vết trong nhật ký (FR-24)
    pkg_nhat_ky.ghi('PHONG', TO_CHAR(p_phong_id), 'BAT_DAU_DON');
  END bat_dau_don;

  PROCEDURE don_xong (p_phong_id IN NUMBER) IS
    v_tt phong.trang_thai%TYPE;
  BEGIN
    SELECT trang_thai INTO v_tt FROM phong WHERE phong_id = p_phong_id FOR UPDATE;
    IF v_tt <> 'DANG_DON' THEN
      RAISE_APPLICATION_ERROR(-20065, 'ROOM_STATE_INVALID|' || v_tt);
    END IF;
    UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = p_phong_id;
  END don_xong;

  FUNCTION don_bi_anh_huong (p_phong_id IN NUMBER) RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, d.tu_luc, d.den_luc, kh.ho_ten, kh.sdt, kh.email
        FROM dat_phong_doan d
        JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
        JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
       WHERE d.phong_id = p_phong_id AND d.den_luc > SYSTIMESTAMP
         AND (dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN') OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > SYSTIMESTAMP))
       ORDER BY d.tu_luc;
    RETURN c;
  END don_bi_anh_huong;

  -- BR-41: có đơn tương lai thì phải xử lý (đổi sang phòng cùng hạng) trước; API gọi lại với p_bo_qua_don_anh_huong = 1
  -- khi quản lý đã xử lý hoặc chấp nhận. Phòng đang có khách (DANG_O) đi qua PKG_DAT_PHONG.DOI_PHONG_SU_CO.
  PROCEDURE bat_bao_tri (p_phong_id IN NUMBER, p_ly_do IN VARCHAR2, p_bo_qua_don_anh_huong IN NUMBER DEFAULT 0) IS
    v_tt  phong.trang_thai%TYPE;
    v_dem NUMBER;
  BEGIN
    IF p_ly_do IS NULL OR TRIM(p_ly_do) IS NULL THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|LY_DO');
    END IF;
    SELECT trang_thai INTO v_tt FROM phong WHERE phong_id = p_phong_id FOR UPDATE;
    IF v_tt NOT IN ('TRONG', 'DANG_DON') THEN
      RAISE_APPLICATION_ERROR(-20065, 'ROOM_STATE_INVALID|' || v_tt);
    END IF;
    SELECT COUNT(*) INTO v_dem
      FROM dat_phong_doan d JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
     WHERE d.phong_id = p_phong_id AND d.den_luc > SYSTIMESTAMP
       AND (dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN') OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > SYSTIMESTAMP));
    IF v_dem > 0 AND p_bo_qua_don_anh_huong <> 1 THEN
      RAISE_APPLICATION_ERROR(-20066, 'MAINTENANCE_HAS_BOOKINGS|' || v_dem);
    END IF;
    pkg_ngu_canh.dat_ly_do(p_ly_do);
    UPDATE phong SET trang_thai = 'BAO_TRI', ghi_chu = SUBSTR(p_ly_do, 1, 500) WHERE phong_id = p_phong_id;
  END bat_bao_tri;

  -- Hết bảo trì: phòng về TRONG (BRD chưa nêu; nếu cần dọn sau bảo trì thì quản lý chuyển DANG_DON thủ công)
  PROCEDURE ket_thuc_bao_tri (p_phong_id IN NUMBER) IS
    v_tt phong.trang_thai%TYPE;
  BEGIN
    SELECT trang_thai INTO v_tt FROM phong WHERE phong_id = p_phong_id FOR UPDATE;
    IF v_tt <> 'BAO_TRI' THEN
      RAISE_APPLICATION_ERROR(-20065, 'ROOM_STATE_INVALID|' || v_tt);
    END IF;
    UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = p_phong_id;
  END ket_thuc_bao_tri;

  PROCEDURE doi_trang_thai_thu_cong (p_phong_id IN NUMBER, p_trang_thai_moi IN VARCHAR2, p_ly_do IN VARCHAR2) IS
  BEGIN
    IF p_ly_do IS NULL OR TRIM(p_ly_do) IS NULL THEN
      RAISE_APPLICATION_ERROR(-20060, 'VALIDATION_ERROR|LY_DO');
    END IF;
    pkg_ngu_canh.dat_ly_do(p_ly_do);
    UPDATE phong SET trang_thai = p_trang_thai_moi WHERE phong_id = p_phong_id;
  END doi_trang_thai_thu_cong;

  FUNCTION doi_soat_phong_lich RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT p.phong_id, p.ma_phong, p.trang_thai,
             CASE WHEN p.trang_thai = 'DANG_O' AND n.dat_phong_id IS NULL THEN 'DANG_O_NHUNG_KHONG_CO_DON_CHECKED_IN'
                  WHEN p.trang_thai <> 'DANG_O' AND n.dat_phong_id IS NOT NULL THEN 'CO_DON_CHECKED_IN_NHUNG_PHONG_KHONG_DANG_O'
             END AS lech
        FROM phong p
        LEFT JOIN (SELECT d.phong_id, MIN(dp.dat_phong_id) AS dat_phong_id
                     FROM dat_phong_doan d JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
                    WHERE dp.trang_thai = 'CHECKED_IN' AND d.tu_luc <= SYSTIMESTAMP AND d.den_luc >= SYSTIMESTAMP - INTERVAL '1' DAY
                    GROUP BY d.phong_id) n ON n.phong_id = p.phong_id
       WHERE (p.trang_thai = 'DANG_O' AND n.dat_phong_id IS NULL)
          OR (p.trang_thai <> 'DANG_O' AND n.dat_phong_id IS NOT NULL);
    RETURN c;
  END doi_soat_phong_lich;

END pkg_phong;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_dat_phong AS
  -- FR-04 đến FR-06, FR-13, BR-01 đến BR-05, BR-12, BR-17, BR-20, BR-21, BR-56.
  -- p_phong_id rỗng: hệ thống gán phòng theo hạng (khách đặt trực tuyến). Có p_phong_id: lễ tân chọn phòng cụ thể.
  -- p_thanh_toan: TRUC_TUYEN (đơn HOLD khi kênh WEB hoặc API) hoặc KHI_NHAN_PHONG (CONFIRMED ngay). Kênh QUAY luôn CONFIRMED.
  PROCEDURE tao_don (p_ho_ten IN VARCHAR2, p_sdt IN VARCHAR2, p_email IN VARCHAR2, p_quoc_tich IN VARCHAR2,
                     p_ngon_ngu IN VARCHAR2, p_loai_dat IN VARCHAR2, p_kenh_dat IN VARCHAR2,
                     p_ma_hang IN VARCHAR2, p_phong_id IN NUMBER,
                     p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                     p_so_khach IN NUMBER, p_thanh_toan IN VARCHAR2, p_dong_y_luc IN TIMESTAMP WITH TIME ZONE,
                     p_dat_phong_id OUT NUMBER, p_ma_tra_cuu OUT VARCHAR2, p_trang_thai OUT VARCHAR2,
                     p_phong_id_gan OUT NUMBER, p_tien_phong OUT NUMBER, p_tien_vat OUT NUMBER,
                     p_tong_tien OUT NUMBER, p_han_giu_cho OUT TIMESTAMP WITH TIME ZONE);

  -- Số tiền hoàn nếu hủy ngay bây giờ (BR-24), để hiển thị trước khi khách xác nhận (FR-09)
  FUNCTION hoan_du_kien (p_dat_phong_id IN NUMBER) RETURN NUMBER;
  PROCEDURE huy_don (p_dat_phong_id IN NUMBER, p_ly_do IN VARCHAR2, p_so_tien_hoan OUT NUMBER);
  -- BR-15, D-29: đổi ngày, giờ hoặc phòng của đơn CONFIRMED
  PROCEDURE doi_lich (p_dat_phong_id IN NUMBER, p_tu_moi IN TIMESTAMP WITH TIME ZONE, p_den_moi IN TIMESTAMP WITH TIME ZONE,
                      p_phong_moi_id IN NUMBER DEFAULT NULL, p_chenh_lech OUT NUMBER, p_so_tien_hoan OUT NUMBER);
  PROCEDURE check_in (p_dat_phong_id IN NUMBER, p_loai_giay_to IN VARCHAR2, p_so_giay_to IN VARCHAR2,
                      p_quoc_tich IN VARCHAR2, p_anh_url IN VARCHAR2 DEFAULT NULL, p_phong_id OUT NUMBER);
  PROCEDURE gia_han (p_dat_phong_id IN NUMBER, p_so_don_vi IN NUMBER, p_tien_them OUT NUMBER);
  PROCEDURE doi_phong_su_co (p_dat_phong_id IN NUMBER, p_phong_moi_id IN NUMBER, p_ly_do IN VARCHAR2);
  PROCEDURE check_out (p_dat_phong_id IN NUMBER, p_nguoi_lap_id IN NUMBER,
                       p_phu_thu_tien IN NUMBER DEFAULT 0, p_phu_thu_mo_ta IN VARCHAR2 DEFAULT NULL,
                       p_giam_gia IN NUMBER DEFAULT 0, p_giam_gia_ly_do IN VARCHAR2 DEFAULT NULL,
                       p_hoa_don_id OUT NUMBER, p_tong_hoa_don OUT NUMBER, p_con_phai_thu OUT NUMBER);
  PROCEDURE no_show_thu_cong (p_dat_phong_id IN NUMBER);
  -- Phòng cùng hạng còn trống đúng khoảng [p_tu, p_den): gợi ý khi trùng phòng hoặc không gia hạn được (BR-11, BR-33)
  FUNCTION goi_y_phong (p_loai_phong_id IN NUMBER, p_tu IN TIMESTAMP WITH TIME ZONE,
                        p_den IN TIMESTAMP WITH TIME ZONE) RETURN SYS_REFCURSOR;
  -- FR-02, FR-03, FR-10, FR-11: tìm các hạng còn phòng trong khoảng [p_tu, p_den), kèm giá đã chốt
  FUNCTION tim_hang_con_phong (p_loai_dat IN VARCHAR2,
                               p_tu IN TIMESTAMP WITH TIME ZONE,
                               p_den IN TIMESTAMP WITH TIME ZONE,
                               p_so_khach IN NUMBER DEFAULT NULL) RETURN SYS_REFCURSOR;
  -- Tác vụ nền (FR-52). Hai thủ tục job_* không tham số để DBMS_SCHEDULER gọi.
  PROCEDURE het_han_giu_cho (p_so_don OUT NUMBER);
  PROCEDURE tu_no_show (p_so_don OUT NUMBER);
  PROCEDURE job_het_han_giu_cho;
  PROCEDURE job_no_show;
END pkg_dat_phong;
/
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
    v_dem        NUMBER;
    v_tt         VARCHAR2(20);
    v_han        TIMESTAMP WITH TIME ZONE;
    v_phong_gan  NUMBER;
  BEGIN
    IF p_loai_dat NOT IN ('NGAY', 'GIO') THEN loi_du_lieu('LOAI_DAT'); END IF;
    IF p_kenh_dat NOT IN ('WEB', 'QUAY', 'API') THEN loi_du_lieu('KENH_DAT'); END IF;
    IF p_thanh_toan NOT IN ('TRUC_TUYEN', 'KHI_NHAN_PHONG') THEN loi_du_lieu('THANH_TOAN'); END IF;
    IF p_ho_ten IS NULL OR p_sdt IS NULL OR v_email IS NULL THEN loi_du_lieu('KHACH'); END IF;
    IF p_so_khach IS NULL OR p_so_khach < 1 OR p_so_khach <> TRUNC(p_so_khach) THEN loi_du_lieu('SO_KHACH'); END IF;

    -- Hạng phòng (BR-02, BR-56)
    IF p_phong_id IS NOT NULL THEN
      BEGIN
        SELECT lp.loai_phong_id, lp.ma_hang, lp.cho_thue_gio, lp.suc_chua, p.dang_hoat_dong
          INTO v_loai_phong, v_ma_hang, v_cho_gio, v_suc_chua, v_hoat_dong
          FROM phong p JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
         WHERE p.phong_id = p_phong_id;
      EXCEPTION
        WHEN NO_DATA_FOUND THEN loi_du_lieu('PHONG');
      END;
      IF NOT v_hoat_dong THEN loi_du_lieu('PHONG_NGUNG_DUNG'); END IF;
    ELSE
      BEGIN
        SELECT loai_phong_id, ma_hang, cho_thue_gio, suc_chua
          INTO v_loai_phong, v_ma_hang, v_cho_gio, v_suc_chua
          FROM loai_phong WHERE ma_hang = p_ma_hang;
      EXCEPTION
        WHEN NO_DATA_FOUND THEN loi_du_lieu('HANG_PHONG');
      END;
    END IF;
    IF p_loai_dat = 'GIO' AND NOT v_cho_gio THEN
      RAISE_APPLICATION_ERROR(-20020, 'HOURLY_NOT_ALLOWED|' || v_ma_hang);
    END IF;
    IF v_suc_chua IS NOT NULL AND p_so_khach > v_suc_chua THEN loi_du_lieu('SO_KHACH'); END IF;

    kiem_tra_thoi_gian(p_loai_dat, p_tu, p_den);
    v_gia := pkg_gia.chot_gia(v_loai_phong, p_loai_dat, p_tu, p_den);        -- BR-42, BR-57, BR-58

    -- Khách: dùng lại dòng khách có cùng email và SĐT, nếu chưa có thì tạo
    BEGIN
      SELECT khach_hang_id INTO v_khach FROM khach_hang
       WHERE email = v_email AND sdt = p_sdt AND ROWNUM = 1;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        INSERT INTO khach_hang (ho_ten, sdt, email, quoc_tich, ngon_ngu_uu_tien)
        VALUES (p_ho_ten, p_sdt, v_email, p_quoc_tich, NVL(p_ngon_ngu, 'vi'))
        RETURNING khach_hang_id INTO v_khach;
    END;

    -- BR-21: số đơn CONFIRMED chưa thanh toán trên một email hoặc SĐT
    IF p_thanh_toan = 'KHI_NHAN_PHONG' THEN
      SELECT COUNT(*) INTO v_dem
        FROM dat_phong dp JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
       WHERE (kh.email = v_email OR kh.sdt = p_sdt) AND dp.trang_thai = 'CONFIRMED'
         AND NOT EXISTS (SELECT 1 FROM giao_dich_thanh_toan g
                          WHERE g.dat_phong_id = dp.dat_phong_id AND g.trang_thai = 'THANH_CONG');
      IF v_dem >= pkg_cau_hinh.lay_so('SO_DON_CHUA_TT_TOI_DA') THEN
        RAISE_APPLICATION_ERROR(-20050, 'PENDING_LIMIT_EXCEEDED|' || v_dem);
      END IF;
    END IF;

    -- BR-17, BR-20: thanh toán trực tuyến qua HOLD; còn lại CONFIRMED ngay
    IF p_thanh_toan = 'TRUC_TUYEN' AND p_kenh_dat <> 'QUAY' THEN
      v_tt  := 'HOLD';
      v_han := pkg_gia.bay_gio + NUMTODSINTERVAL(pkg_cau_hinh.lay_so('PHUT_GIU_CHO'), 'MINUTE');
    ELSE
      v_tt  := 'CONFIRMED';
      v_han := NULL;
    END IF;

    SAVEPOINT sp_tao_don;
    INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, han_giu_cho, so_khach,
                           don_gia_ap_dung, don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien,
                           ngon_ngu, dong_y_chinh_sach_luc, nguoi_tao_id)
    VALUES (v_khach, p_loai_dat, p_kenh_dat, v_tt, p_tu, p_den, v_han, p_so_khach,
            v_gia.don_gia, v_gia.don_gia_ngay, v_gia.tien_phong, v_gia.thue_suat, v_gia.tien_vat, v_gia.tong_tien,
            NVL(p_ngon_ngu, 'vi'), p_dong_y_luc, pkg_ngu_canh.nguoi_id)
    RETURNING dat_phong_id, ma_tra_cuu INTO p_dat_phong_id, p_ma_tra_cuu;

    -- Gán phòng. Mỗi lần INSERT đoạn lưu trú đi qua TRG_DAT_PHONG_DOAN_TRUNG, nên đây cũng là bước kiểm tra trùng (BR-10)
    IF p_phong_id IS NOT NULL THEN
      BEGIN
        INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc) VALUES (p_dat_phong_id, p_phong_id, p_tu, p_den);
        v_phong_gan := p_phong_id;
      EXCEPTION
        WHEN OTHERS THEN
          ROLLBACK TO SAVEPOINT sp_tao_don;
          RAISE;
      END;
    ELSE
      -- BR-56: ưu tiên phòng có lượt liền kề gần nhất; thử lần lượt vì phiên khác có thể giành mất phòng giữa chừng
      FOR c IN (SELECT p.phong_id
                  FROM phong p
                 WHERE p.loai_phong_id = v_loai_phong AND p.dang_hoat_dong = TRUE AND p.trang_thai <> 'BAO_TRI'
                   AND pkg_kiem_tra_trung.dem_xung_dot(p.phong_id, p_tu, p_den) = 0
                 ORDER BY pkg_kiem_tra_trung.khoang_cach_lan_can(p.phong_id, p_tu, p_den), p.ma_phong) LOOP
        BEGIN
          INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc) VALUES (p_dat_phong_id, c.phong_id, p_tu, p_den);
          v_phong_gan := c.phong_id;
          EXIT;
        EXCEPTION
          WHEN OTHERS THEN
            IF SQLCODE <> -20001 THEN
              RAISE;
            END IF;
        END;
      END LOOP;
      IF v_phong_gan IS NULL THEN
        ROLLBACK TO SAVEPOINT sp_tao_don;
        RAISE_APPLICATION_ERROR(-20051, 'NO_AVAILABILITY|' || v_ma_hang);   -- BR-12: chỉ báo hết phòng
      END IF;
    END IF;

    IF v_tt = 'CONFIRMED' THEN
      pkg_email.xep(p_dat_phong_id, 'XAC_NHAN');
    END IF;
    p_trang_thai   := v_tt;
    p_phong_id_gan := v_phong_gan;
    p_tien_phong   := v_gia.tien_phong;
    p_tien_vat     := v_gia.tien_vat;
    p_tong_tien    := v_gia.tong_tien;
    p_han_giu_cho  := v_han;
  END tao_don;

  -- ---------- hủy đơn ----------
  FUNCTION hoan_du_kien (p_dat_phong_id IN NUMBER) RETURN NUMBER IS
    r dat_phong%ROWTYPE;
  BEGIN
    SELECT * INTO r FROM dat_phong WHERE dat_phong_id = p_dat_phong_id;
    IF r.trang_thai <> 'CONFIRMED' THEN
      RETURN 0;
    END IF;
    -- BR-24: còn từ 24 giờ trở lên đến giờ nhận thì hoàn 100% số đã thanh toán, dưới 24 giờ không hoàn
    IF pkg_gia.so_phut(SYSTIMESTAMP, r.tu_luc) / 60 >= pkg_cau_hinh.lay_so('GIO_HUY_MIEN_PHI') THEN
      RETURN pkg_thanh_toan.tinh_da_thanh_toan(p_dat_phong_id);
    END IF;
    RETURN 0;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20061, 'BOOKING_NOT_FOUND|' || p_dat_phong_id);
  END hoan_du_kien;

  PROCEDURE huy_don (p_dat_phong_id IN NUMBER, p_ly_do IN VARCHAR2, p_so_tien_hoan OUT NUMBER) IS
    r dat_phong%ROWTYPE;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    p_so_tien_hoan := 0;
    IF r.trang_thai IN ('CHECKED_IN', 'CHECKED_OUT') THEN
      RAISE_APPLICATION_ERROR(-20052, 'CANCEL_NOT_ALLOWED|' || r.trang_thai);      -- BR-14, mọi vai trò
    ELSIF r.trang_thai = 'HOLD' THEN
      UPDATE dat_phong SET trang_thai = 'EXPIRED', ly_do_huy = p_ly_do WHERE dat_phong_id = p_dat_phong_id;   -- BR-18: khách hủy
    ELSIF r.trang_thai = 'CONFIRMED' THEN
      p_so_tien_hoan := hoan_du_kien(p_dat_phong_id);
      UPDATE dat_phong SET trang_thai = 'CANCELLED', ly_do_huy = p_ly_do WHERE dat_phong_id = p_dat_phong_id;
      IF p_so_tien_hoan > 0 THEN
        pkg_thanh_toan.tao_hoan(p_dat_phong_id, p_so_tien_hoan, 'Hủy đơn theo chính sách (BR-24)', pkg_ngu_canh.nguoi_id);
      END IF;
      pkg_email.xep(p_dat_phong_id, 'HUY_HOAN_TIEN');
    ELSE
      sai_trang_thai(r.trang_thai);
    END IF;
  END huy_don;

  -- ---------- đổi lịch, đổi phòng ----------
  PROCEDURE doi_lich (p_dat_phong_id IN NUMBER, p_tu_moi IN TIMESTAMP WITH TIME ZONE, p_den_moi IN TIMESTAMP WITH TIME ZONE,
                      p_phong_moi_id IN NUMBER DEFAULT NULL, p_chenh_lech OUT NUMBER, p_so_tien_hoan OUT NUMBER) IS
    r            dat_phong%ROWTYPE;
    v_doan       NUMBER;
    v_phong_cu   NUMBER;
    v_tu_cu      TIMESTAMP WITH TIME ZONE;
    v_den_cu     TIMESTAMP WITH TIME ZONE;
    v_phong_moi  NUMBER;
    v_hang_cu    NUMBER;
    v_hang_moi   NUMBER;
    v_cho_gio    BOOLEAN;
    v_gia        pkg_gia.t_gia;
    v_da_tt      NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CONFIRMED' THEN
      sai_trang_thai(r.trang_thai);                 -- BR-15: đơn CHECKED_IN chỉ gia hạn hoặc đổi phòng sự cố
    END IF;
    doan_cuoi(p_dat_phong_id, v_doan, v_phong_cu, v_tu_cu, v_den_cu);
    v_phong_moi := NVL(p_phong_moi_id, v_phong_cu);
    SELECT loai_phong_id INTO v_hang_cu FROM phong WHERE phong_id = v_phong_cu;
    BEGIN
      SELECT p.loai_phong_id, lp.cho_thue_gio INTO v_hang_moi, v_cho_gio
        FROM phong p JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
       WHERE p.phong_id = v_phong_moi AND p.dang_hoat_dong = TRUE;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN loi_du_lieu('PHONG');
    END;
    IF r.loai_dat = 'GIO' AND NOT v_cho_gio THEN
      RAISE_APPLICATION_ERROR(-20020, 'HOURLY_NOT_ALLOWED|' || v_phong_moi);
    END IF;
    kiem_tra_thoi_gian(r.loai_dat, p_tu_moi, p_den_moi);

    IF v_hang_moi = v_hang_cu THEN
      -- D-29: cùng hạng giữ giá, giá ngày và thuế suất đã chốt
      v_gia.don_gia      := r.don_gia_ap_dung;
      v_gia.don_gia_ngay := r.don_gia_ngay_ap_dung;
      v_gia.thue_suat    := r.thue_suat;
      v_gia.tien_phong   := pkg_gia.tien_phong(r.loai_dat, p_tu_moi, p_den_moi, r.don_gia_ap_dung, r.don_gia_ngay_ap_dung);
      v_gia.tien_vat     := pkg_gia.tinh_vat(v_gia.tien_phong, r.thue_suat);
      v_gia.tong_tien    := v_gia.tien_phong + v_gia.tien_vat;
    ELSE
      -- D-29: sang hạng khác thì tính theo giá hiện hành của hạng mới
      v_gia := pkg_gia.chot_gia(v_hang_moi, r.loai_dat, p_tu_moi, p_den_moi);
    END IF;

    -- Đoạn lưu trú đi trước để trigger kiểm tra trùng chạy; trùng thì đơn giữ nguyên (BR-15)
    UPDATE dat_phong_doan SET phong_id = v_phong_moi, tu_luc = p_tu_moi, den_luc = p_den_moi WHERE doan_id = v_doan;
    UPDATE dat_phong
       SET tu_luc = p_tu_moi, den_luc = p_den_moi, don_gia_ap_dung = v_gia.don_gia, don_gia_ngay_ap_dung = v_gia.don_gia_ngay,
           tien_phong = v_gia.tien_phong, thue_suat = v_gia.thue_suat, tien_vat = v_gia.tien_vat, tong_tien = v_gia.tong_tien
     WHERE dat_phong_id = p_dat_phong_id;

    p_chenh_lech   := v_gia.tong_tien - r.tong_tien;
    p_so_tien_hoan := 0;
    v_da_tt := pkg_thanh_toan.tinh_da_thanh_toan(p_dat_phong_id);
    IF v_da_tt > v_gia.tong_tien THEN
      p_so_tien_hoan := v_da_tt - v_gia.tong_tien;                              -- hoàn phần chênh lệch (D-29)
      pkg_thanh_toan.tao_hoan(p_dat_phong_id, p_so_tien_hoan, 'Chênh lệch khi đổi lịch hoặc phòng (D-29)', pkg_ngu_canh.nguoi_id);
    END IF;
    pkg_email.xep(p_dat_phong_id, 'THAY_DOI_DON');
  END doi_lich;

  -- ---------- check-in ----------
  PROCEDURE check_in (p_dat_phong_id IN NUMBER, p_loai_giay_to IN VARCHAR2, p_so_giay_to IN VARCHAR2,
                      p_quoc_tich IN VARCHAR2, p_anh_url IN VARCHAR2 DEFAULT NULL, p_phong_id OUT NUMBER) IS
    r       dat_phong%ROWTYPE;
    v_tt    phong.trang_thai%TYPE;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CONFIRMED' THEN
      sai_trang_thai(r.trang_thai);
    END IF;
    IF pkg_gia.bay_gio < r.tu_luc THEN
      RAISE_APPLICATION_ERROR(-20053, 'CHECKIN_TOO_EARLY|' || p_dat_phong_id);   -- BR-32, không có ngoại lệ
    END IF;
    IF p_loai_giay_to IS NULL OR p_so_giay_to IS NULL OR p_quoc_tich IS NULL THEN
      loi_du_lieu('GIAY_TO');                                                    -- BR-30
    END IF;
    SELECT phong_id INTO p_phong_id FROM (SELECT phong_id FROM dat_phong_doan WHERE dat_phong_id = p_dat_phong_id ORDER BY doan_id) WHERE ROWNUM = 1;
    SELECT trang_thai INTO v_tt FROM phong WHERE phong_id = p_phong_id FOR UPDATE;
    IF v_tt <> 'TRONG' THEN
      RAISE_APPLICATION_ERROR(-20054, 'ROOM_NOT_READY|' || v_tt);                -- BR-31
    END IF;
    INSERT INTO giay_to_khach (khach_hang_id, loai_giay_to, so_giay_to, anh_url)
    VALUES (r.khach_hang_id, p_loai_giay_to, p_so_giay_to, p_anh_url);
    UPDATE khach_hang SET quoc_tich = p_quoc_tich WHERE khach_hang_id = r.khach_hang_id;
    UPDATE dat_phong SET trang_thai = 'CHECKED_IN', nhan_thuc_te = pkg_gia.bay_gio WHERE dat_phong_id = p_dat_phong_id;
    UPDATE phong SET trang_thai = 'DANG_O' WHERE phong_id = p_phong_id;
  END check_in;

  -- ---------- gia hạn ----------
  PROCEDURE gia_han (p_dat_phong_id IN NUMBER, p_so_don_vi IN NUMBER, p_tien_them OUT NUMBER) IS
    r          dat_phong%ROWTYPE;
    v_doan     NUMBER;
    v_phong    NUMBER;
    v_tu       TIMESTAMP WITH TIME ZONE;
    v_den      TIMESTAMP WITH TIME ZONE;
    v_den_moi  TIMESTAMP WITH TIME ZONE;
    v_tien     NUMBER;
    v_vat      NUMBER;
    v_gio      NUMBER;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CHECKED_IN' THEN
      sai_trang_thai(r.trang_thai);
    END IF;
    IF p_so_don_vi IS NULL OR p_so_don_vi < 1 OR p_so_don_vi <> TRUNC(p_so_don_vi) THEN
      loi_du_lieu('SO_DON_VI');                                                  -- BR-33: số đêm nguyên hoặc số giờ nguyên
    END IF;
    doan_cuoi(p_dat_phong_id, v_doan, v_phong, v_tu, v_den);
    IF r.loai_dat = 'NGAY' THEN
      v_den_moi := r.den_luc + NUMTODSINTERVAL(p_so_don_vi, 'DAY');
      v_tien    := r.tien_phong + p_so_don_vi * r.don_gia_ngay_ap_dung;         -- BR-34: giá đã chốt của đơn
    ELSE
      v_den_moi := r.den_luc + NUMTODSINTERVAL(p_so_don_vi, 'HOUR');
      v_gio     := pkg_gia.so_phut(r.tu_luc, v_den_moi) / 60;
      IF v_gio > pkg_cau_hinh.lay_so('SO_GIO_TOI_DA_DON_GIO') THEN
        loi_du_lieu('SO_GIO');
      END IF;
      v_tien    := pkg_gia.tien_theo_gio(v_gio, r.don_gia_ap_dung, r.don_gia_ngay_ap_dung);   -- vượt 5 giờ: một giá ngày (BR-33)
    END IF;
    v_vat := pkg_gia.tinh_vat(v_tien, r.thue_suat);
    BEGIN
      UPDATE dat_phong_doan SET den_luc = v_den_moi WHERE doan_id = v_doan;
    EXCEPTION
      WHEN OTHERS THEN
        IF SQLCODE = -20001 THEN
          RAISE_APPLICATION_ERROR(-20055, 'EXTEND_CONFLICT|' || v_phong);        -- vướng lượt kế tiếp, kể cả đệm
        END IF;
        RAISE;
    END;
    UPDATE dat_phong SET den_luc = v_den_moi, tien_phong = v_tien, tien_vat = v_vat, tong_tien = v_tien + v_vat
     WHERE dat_phong_id = p_dat_phong_id;
    p_tien_them := (v_tien + v_vat) - (r.tien_phong + r.tien_vat);
    pkg_email.xep(p_dat_phong_id, 'THAY_DOI_DON');
  END gia_han;

  -- ---------- đổi phòng do sự cố ----------
  PROCEDURE doi_phong_su_co (p_dat_phong_id IN NUMBER, p_phong_moi_id IN NUMBER, p_ly_do IN VARCHAR2) IS
    r          dat_phong%ROWTYPE;
    v_doan     NUMBER;
    v_phong_cu NUMBER;
    v_tu       TIMESTAMP WITH TIME ZONE;
    v_den      TIMESTAMP WITH TIME ZONE;
    v_bay_gio  TIMESTAMP WITH TIME ZONE;
    v_tt       phong.trang_thai%TYPE;
    v_cho_gio  BOOLEAN;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CHECKED_IN' THEN
      sai_trang_thai(r.trang_thai);
    END IF;
    IF p_ly_do IS NULL OR TRIM(p_ly_do) IS NULL THEN
      loi_du_lieu('LY_DO');                                                      -- BR-35: bắt buộc nhập lý do sự cố
    END IF;
    doan_cuoi(p_dat_phong_id, v_doan, v_phong_cu, v_tu, v_den);
    IF p_phong_moi_id = v_phong_cu THEN loi_du_lieu('PHONG'); END IF;
    BEGIN
      SELECT p.trang_thai, lp.cho_thue_gio INTO v_tt, v_cho_gio
        FROM phong p JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
       WHERE p.phong_id = p_phong_moi_id AND p.dang_hoat_dong = TRUE FOR UPDATE OF p.trang_thai;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN loi_du_lieu('PHONG');
    END;
    IF r.loai_dat = 'GIO' AND NOT v_cho_gio THEN
      RAISE_APPLICATION_ERROR(-20020, 'HOURLY_NOT_ALLOWED|' || p_phong_moi_id);  -- BR-35: đơn theo giờ chỉ đổi sang Standard
    END IF;
    IF v_tt <> 'TRONG' THEN
      RAISE_APPLICATION_ERROR(-20054, 'ROOM_NOT_READY|' || v_tt);
    END IF;
    v_bay_gio := pkg_gia.bay_gio;
    IF v_bay_gio <= v_tu OR v_bay_gio >= v_den THEN
      loi_du_lieu('THOI_GIAN');
    END IF;

    pkg_ngu_canh.dat_ly_do(p_ly_do);
    SAVEPOINT sp_doi_phong;
    BEGIN
      UPDATE dat_phong_doan SET den_luc = v_bay_gio WHERE doan_id = v_doan;     -- đoạn cũ kết thúc ngay bây giờ
      INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc)
      VALUES (p_dat_phong_id, p_phong_moi_id, v_bay_gio, v_den);                -- phần còn lại sang phòng mới (kiểm tra trùng, kể cả đệm)
    EXCEPTION
      WHEN OTHERS THEN
        ROLLBACK TO SAVEPOINT sp_doi_phong;
        RAISE;
    END;
    UPDATE phong SET trang_thai = 'BAO_TRI', ghi_chu = SUBSTR(p_ly_do, 1, 500) WHERE phong_id = v_phong_cu;   -- phòng cũ sang BAO_TRI ngay
    UPDATE phong SET trang_thai = 'DANG_O' WHERE phong_id = p_phong_moi_id;
    pkg_email.xep(p_dat_phong_id, 'THAY_DOI_DON');                              -- BR-36: giá của đơn không đổi
  END doi_phong_su_co;

  -- ---------- check-out ----------
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
    IF NVL(p_phu_thu_tien, 0) > 0 AND p_phu_thu_mo_ta IS NULL THEN loi_du_lieu('PHU_THU'); END IF;           -- BR-38
    IF NVL(p_giam_gia, 0) > 0 AND p_giam_gia_ly_do IS NULL THEN loi_du_lieu('GIAM_GIA'); END IF;

    v_qua       := pkg_gia.tien_qua_gio(r.loai_dat, r.tu_luc, r.den_luc, v_ra, r.don_gia_ap_dung, r.don_gia_ngay_ap_dung);   -- BR-39
    v_chiu_thue := r.tien_phong + v_qua + NVL(p_phu_thu_tien, 0) - NVL(p_giam_gia, 0);
    IF v_chiu_thue < 0 THEN loi_du_lieu('GIAM_GIA'); END IF;
    v_vat  := pkg_gia.tinh_vat(v_chiu_thue, r.thue_suat);      -- VAT tính trên toàn bộ khoản chịu thuế của hóa đơn (giả định, chờ kế toán xác nhận)
    v_tong := v_chiu_thue + v_vat;

    -- BR-37, D-33: trả sớm thì mở lại phần thời gian dư để bán lại (không hoàn tiền)
    doan_cuoi(p_dat_phong_id, v_doan, v_phong, v_tu, v_den);
    IF v_ra > v_tu AND v_ra < v_den THEN
      UPDATE dat_phong_doan SET den_luc = v_ra WHERE doan_id = v_doan;
    END IF;
    UPDATE dat_phong SET trang_thai = 'CHECKED_OUT', tra_thuc_te = v_ra WHERE dat_phong_id = p_dat_phong_id;
    UPDATE phong SET trang_thai = 'DANG_DON' WHERE phong_id = v_phong;

    -- BR-44: hóa đơn nội bộ, số liên tục, không sửa sau khi lập
    v_so_hd := pkg_hoa_don.cap_so;       -- gọi ngoài câu INSERT: hàm này có DML (khóa và tăng bộ đếm)
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
  END check_out;

  PROCEDURE no_show_thu_cong (p_dat_phong_id IN NUMBER) IS
    r dat_phong%ROWTYPE;
  BEGIN
    r := khoa_don(p_dat_phong_id);
    IF r.trang_thai <> 'CONFIRMED' THEN
      sai_trang_thai(r.trang_thai);
    END IF;
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
    v_res t_hang_con_phong_tab := t_hang_con_phong_tab();
    v_gia pkg_gia.t_gia;
    v_so_con NUMBER;
  BEGIN
    -- Kiểm tra thời gian theo quy tắc nghiệp vụ BR-01, BR-03, BR-05
    kiem_tra_thoi_gian(p_loai_dat, p_tu, p_den);

    FOR r IN (
      SELECT lp.loai_phong_id, lp.ma_hang, lp.suc_chua, lp.cho_thue_gio, lp.anh_url
        FROM loai_phong lp
       WHERE (p_loai_dat = 'NGAY' OR lp.cho_thue_gio = TRUE)
         AND (p_so_khach IS NULL OR lp.suc_chua IS NULL OR lp.suc_chua >= p_so_khach)
       ORDER BY lp.loai_phong_id
    ) LOOP
      -- Đếm số phòng còn trống không xung đột trong khoảng [p_tu, p_den)
      SELECT COUNT(*) INTO v_so_con
        FROM phong p
       WHERE p.loai_phong_id = r.loai_phong_id
         AND p.dang_hoat_dong = TRUE
         AND p.trang_thai <> 'BAO_TRI'
         AND pkg_kiem_tra_trung.dem_xung_dot(p.phong_id, p_tu, p_den) = 0;

      -- Chỉ trả về hạng còn ít nhất 1 phòng trống
      IF v_so_con > 0 THEN
        v_gia := pkg_gia.chot_gia(r.loai_phong_id, p_loai_dat, p_tu, p_den);
        v_res.EXTEND;
        v_res(v_res.COUNT) := t_hang_con_phong(
          r.loai_phong_id,
          r.ma_hang,
          v_so_con,
          v_gia.don_gia,
          v_gia.don_gia_ngay,
          v_gia.tien_phong,
          v_gia.thue_suat,
          v_gia.tien_vat,
          v_gia.tong_tien,
          r.suc_chua,
          CASE WHEN r.cho_thue_gio THEN 'TRUE' ELSE 'FALSE' END,
          r.anh_url
        );
      END IF;
    END LOOP;

    OPEN c FOR SELECT * FROM TABLE(v_res);
    RETURN c;
  END tim_hang_con_phong;

  -- ---------- tác vụ nền ----------
  -- BR-18: HOLD hết hạn thành EXPIRED, nhả phòng, gửi email. SKIP LOCKED để chạy song song với thanh toán đang xử lý.
  PROCEDURE het_han_giu_cho (p_so_don OUT NUMBER) IS
  BEGIN
    p_so_don := 0;
    FOR r IN (SELECT dat_phong_id FROM dat_phong
               WHERE CASE WHEN trang_thai = 'HOLD' THEN han_giu_cho END <= SYSTIMESTAMP
                 FOR UPDATE SKIP LOCKED) LOOP
      UPDATE dat_phong SET trang_thai = 'EXPIRED' WHERE dat_phong_id = r.dat_phong_id;
      pkg_email.xep(r.dat_phong_id, 'HET_HAN_GIU_CHO');
      p_so_don := p_so_don + 1;
    END LOOP;
  END het_han_giu_cho;

  -- BR-27, BR-28, D-28: tự chuyển NO_SHOW.
  --   Chưa thanh toán: đơn theo ngày sau GIO_CHO_NO_SHOW giờ kể từ giờ nhận; đơn theo giờ sau PHUT_CHO_NO_SHOW_DON_GIO phút.
  --   Đã thanh toán: đơn theo ngày đến 12:00 ngày hôm sau ngày nhận; đơn theo giờ đến hết khung giờ đã đặt. Không hoàn tiền.
  PROCEDURE tu_no_show (p_so_don OUT NUMBER) IS
    v_cho_gio  NUMBER := pkg_cau_hinh.lay_so('GIO_CHO_NO_SHOW');
    v_cho_phut NUMBER := pkg_cau_hinh.lay_so('PHUT_CHO_NO_SHOW_DON_GIO');
    v_gio_tra  NUMBER := pkg_cau_hinh.lay_phan_ngay('GIO_TRA_PHONG');
  BEGIN
    p_so_don := 0;
    FOR r IN (SELECT dp.dat_phong_id
                FROM dat_phong dp
               WHERE dp.trang_thai = 'CONFIRMED'
                 AND ((NOT EXISTS (SELECT 1 FROM giao_dich_thanh_toan g WHERE g.dat_phong_id = dp.dat_phong_id AND g.trang_thai = 'THANH_CONG')
                       AND ((dp.loai_dat = 'NGAY' AND SYSTIMESTAMP >= dp.tu_luc + NUMTODSINTERVAL(v_cho_gio, 'HOUR'))
                         OR (dp.loai_dat = 'GIO'  AND SYSTIMESTAMP >= dp.tu_luc + NUMTODSINTERVAL(v_cho_phut, 'MINUTE'))))
                   OR (EXISTS (SELECT 1 FROM giao_dich_thanh_toan g WHERE g.dat_phong_id = dp.dat_phong_id AND g.trang_thai = 'THANH_CONG')
                       AND ((dp.loai_dat = 'GIO' AND SYSTIMESTAMP >= dp.den_luc)
                         OR (dp.loai_dat = 'NGAY'
                             AND SYSTIMESTAMP >= FROM_TZ(CAST(TRUNC(CAST(dp.tu_luc AT TIME ZONE '+07:00' AS DATE)) + 1 + v_gio_tra AS TIMESTAMP), '+07:00')))))
                 FOR UPDATE OF dp.trang_thai SKIP LOCKED) LOOP
      UPDATE dat_phong SET trang_thai = 'NO_SHOW' WHERE dat_phong_id = r.dat_phong_id;
      p_so_don := p_so_don + 1;
    END LOOP;
  END tu_no_show;

  PROCEDURE job_het_han_giu_cho IS
    v NUMBER;
  BEGIN
    het_han_giu_cho(v);
    COMMIT;
  END job_het_han_giu_cho;

  PROCEDURE job_no_show IS
    v NUMBER;
  BEGIN
    tu_no_show(v);
    COMMIT;
  END job_no_show;

END pkg_dat_phong;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_bao_cao AS
  -- Báo cáo trả về SYS_REFCURSOR; API đọc và xuất Excel (FR-43). Ngày tính theo giờ Việt Nam. Khoảng [p_tu, p_den] gồm cả hai đầu.
  -- Doanh thu tính theo tiền thực thu: giao dịch THANH_CONG trừ hoàn DA_HOAN (FR-40).
  FUNCTION doanh_thu (p_tu IN DATE, p_den IN DATE, p_don_vi IN VARCHAR2 DEFAULT 'NGAY',
                      p_ma_hang IN VARCHAR2 DEFAULT NULL, p_phuong_thuc IN VARCHAR2 DEFAULT NULL) RETURN SYS_REFCURSOR;
  -- Công suất theo hạng, tính theo giờ-phòng và loại trừ giờ bảo trì (FR-41). Giờ bảo trì suy ra từ nhật ký kiểm toán của PHONG.
  FUNCTION cong_suat (p_tu IN DATE, p_den IN DATE) RETURN SYS_REFCURSOR;
  -- Tỷ lệ hủy, no-show, hết hạn giữ chỗ trên các đơn tạo trong kỳ (FR-42)
  FUNCTION ty_le_huy (p_tu IN DATE, p_den IN DATE) RETURN SYS_REFCURSOR;
  -- ADR = doanh thu phòng / số phòng-đêm đã bán; RevPAR = doanh thu phòng / số phòng-đêm khả dụng (FR-44, mức C).
  -- Một phòng-đêm là 24 giờ-phòng. Doanh thu phòng là tiền phòng của đơn chia theo tỷ lệ giờ nằm trong kỳ, đơn CONFIRMED, CHECKED_IN, CHECKED_OUT.
  FUNCTION adr_revpar (p_tu IN DATE, p_den IN DATE) RETURN SYS_REFCURSOR;
END pkg_bao_cao;
/
CREATE OR REPLACE PACKAGE BODY pkg_bao_cao AS

  FUNCTION dau_ky (p_ngay IN DATE) RETURN TIMESTAMP WITH TIME ZONE IS
  BEGIN
    RETURN FROM_TZ(CAST(TRUNC(p_ngay) AS TIMESTAMP), '+07:00');
  END dau_ky;

  FUNCTION cuoi_ky (p_ngay IN DATE) RETURN TIMESTAMP WITH TIME ZONE IS
  BEGIN
    RETURN FROM_TZ(CAST(TRUNC(p_ngay) + 1 AS TIMESTAMP), '+07:00');   -- hết ngày p_ngay, loại trừ
  END cuoi_ky;

  FUNCTION doanh_thu (p_tu IN DATE, p_den IN DATE, p_don_vi IN VARCHAR2 DEFAULT 'NGAY',
                      p_ma_hang IN VARCHAR2 DEFAULT NULL, p_phuong_thuc IN VARCHAR2 DEFAULT NULL) RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT ky, SUM(thu) AS thu, SUM(hoan) AS hoan, SUM(thu) - SUM(hoan) AS thuc_thu
        FROM (SELECT CASE WHEN p_don_vi = 'THANG' THEN TRUNC(ngay, 'MM') ELSE ngay END AS ky, thu, hoan
                FROM (SELECT TRUNC(CAST(g.ngay_giao_dich AT TIME ZONE '+07:00' AS DATE)) AS ngay,
                             g.so_tien AS thu, 0 AS hoan, g.phuong_thuc,
                             (SELECT lp.ma_hang FROM dat_phong_doan d
                                JOIN phong p ON p.phong_id = d.phong_id
                                JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                               WHERE d.dat_phong_id = g.dat_phong_id ORDER BY d.doan_id FETCH FIRST 1 ROW ONLY) AS ma_hang
                        FROM giao_dich_thanh_toan g
                       WHERE g.trang_thai = 'THANH_CONG'
                      UNION ALL
                      SELECT TRUNC(CAST(h.ngay_tao AT TIME ZONE '+07:00' AS DATE)), 0, h.so_tien, g.phuong_thuc,
                             (SELECT lp.ma_hang FROM dat_phong_doan d
                                JOIN phong p ON p.phong_id = d.phong_id
                                JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                               WHERE d.dat_phong_id = g.dat_phong_id ORDER BY d.doan_id FETCH FIRST 1 ROW ONLY)
                        FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
                       WHERE h.trang_thai = 'DA_HOAN')
               WHERE ngay BETWEEN TRUNC(p_tu) AND TRUNC(p_den)
                 AND (p_phuong_thuc IS NULL OR phuong_thuc = p_phuong_thuc)
                 AND (p_ma_hang IS NULL OR ma_hang = p_ma_hang))
       GROUP BY ky
       ORDER BY ky;
    RETURN c;
  END doanh_thu;

  FUNCTION cong_suat (p_tu IN DATE, p_den IN DATE) RETURN SYS_REFCURSOR IS
    c         SYS_REFCURSOR;
    v_dau     TIMESTAMP WITH TIME ZONE := dau_ky(p_tu);
    v_cuoi    TIMESTAMP WITH TIME ZONE := cuoi_ky(p_den);
    v_gio_ky  NUMBER := pkg_gia.so_phut(dau_ky(p_tu), cuoi_ky(p_den)) / 60;
  BEGIN
    OPEN c FOR
      WITH ev AS (
        SELECT khoa_dong, thoi_diem, nhat_ky_id, JSON_VALUE(gia_tri_moi, '$.trang_thai') AS tt
          FROM nhat_ky_kiem_toan
         WHERE bang = 'PHONG' AND hanh_dong IN ('TAO', 'DOI_TRANG_THAI')),
      iv AS (
        SELECT TO_NUMBER(khoa_dong) AS phong_id, tt, thoi_diem AS tu,
               NVL(LEAD(thoi_diem) OVER (PARTITION BY khoa_dong ORDER BY thoi_diem, nhat_ky_id), SYSTIMESTAMP) AS den
          FROM ev),
      bt AS (
        SELECT p.loai_phong_id,
               SUM(pkg_gia.so_phut(GREATEST(i.tu, v_dau), LEAST(i.den, v_cuoi))) / 60 AS gio
          FROM iv i JOIN phong p ON p.phong_id = i.phong_id
         WHERE i.tt = 'BAO_TRI' AND i.tu < v_cuoi AND i.den > v_dau
         GROUP BY p.loai_phong_id),
      ban AS (
        SELECT p.loai_phong_id,
               SUM(pkg_gia.so_phut(GREATEST(d.tu_luc, v_dau), LEAST(d.den_luc, v_cuoi))) / 60 AS gio
          FROM dat_phong_doan d
          JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
          JOIN phong p ON p.phong_id = d.phong_id
         WHERE dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT')
           AND d.tu_luc < v_cuoi AND d.den_luc > v_dau
         GROUP BY p.loai_phong_id),
      tong AS (
        SELECT lp.ma_hang,
               (SELECT COUNT(*) FROM phong p WHERE p.loai_phong_id = lp.loai_phong_id AND p.dang_hoat_dong = TRUE) AS so_phong,
               NVL(bt.gio, 0) AS gio_bao_tri, NVL(ban.gio, 0) AS gio_ban
          FROM loai_phong lp
          LEFT JOIN bt  ON bt.loai_phong_id  = lp.loai_phong_id
          LEFT JOIN ban ON ban.loai_phong_id = lp.loai_phong_id)
      SELECT ma_hang, so_phong,
             so_phong * v_gio_ky - gio_bao_tri AS gio_phong_kha_dung,
             gio_ban AS gio_phong_ban,
             ROUND(100 * gio_ban / NULLIF(so_phong * v_gio_ky - gio_bao_tri, 0), 2) AS cong_suat_phan_tram
        FROM tong
       ORDER BY ma_hang;
    RETURN c;
  END cong_suat;

  FUNCTION ty_le_huy (p_tu IN DATE, p_den IN DATE) RETURN SYS_REFCURSOR IS
    c SYS_REFCURSOR;
  BEGIN
    OPEN c FOR
      SELECT COUNT(*) AS tong_don,
             COUNT(CASE WHEN trang_thai = 'CANCELLED' THEN 1 END) AS huy,
             COUNT(CASE WHEN trang_thai = 'NO_SHOW'   THEN 1 END) AS no_show,
             COUNT(CASE WHEN trang_thai = 'EXPIRED'   THEN 1 END) AS het_han_giu_cho,
             ROUND(100 * COUNT(CASE WHEN trang_thai = 'CANCELLED' THEN 1 END) / NULLIF(COUNT(*), 0), 2) AS ty_le_huy,
             ROUND(100 * COUNT(CASE WHEN trang_thai = 'NO_SHOW'   THEN 1 END) / NULLIF(COUNT(*), 0), 2) AS ty_le_no_show,
             ROUND(100 * COUNT(CASE WHEN trang_thai = 'EXPIRED'   THEN 1 END) / NULLIF(COUNT(*), 0), 2) AS ty_le_het_han
        FROM dat_phong
       WHERE TRUNC(CAST(ngay_tao AT TIME ZONE '+07:00' AS DATE)) BETWEEN TRUNC(p_tu) AND TRUNC(p_den);
    RETURN c;
  END ty_le_huy;

  FUNCTION adr_revpar (p_tu IN DATE, p_den IN DATE) RETURN SYS_REFCURSOR IS
    c         SYS_REFCURSOR;
    v_dau     TIMESTAMP WITH TIME ZONE := dau_ky(p_tu);
    v_cuoi    TIMESTAMP WITH TIME ZONE := cuoi_ky(p_den);
    v_gio_ky  NUMBER := pkg_gia.so_phut(dau_ky(p_tu), cuoi_ky(p_den)) / 60;
  BEGIN
    OPEN c FOR
      WITH ev AS (
        SELECT khoa_dong, thoi_diem, nhat_ky_id, JSON_VALUE(gia_tri_moi, '$.trang_thai') AS tt
          FROM nhat_ky_kiem_toan
         WHERE bang = 'PHONG' AND hanh_dong IN ('TAO', 'DOI_TRANG_THAI')),
      iv AS (
        SELECT TO_NUMBER(khoa_dong) AS phong_id, tt, thoi_diem AS tu,
               NVL(LEAD(thoi_diem) OVER (PARTITION BY khoa_dong ORDER BY thoi_diem, nhat_ky_id), SYSTIMESTAMP) AS den
          FROM ev),
      bt AS (
        SELECT p.loai_phong_id,
               SUM(pkg_gia.so_phut(GREATEST(i.tu, v_dau), LEAST(i.den, v_cuoi))) / 60 AS gio
          FROM iv i JOIN phong p ON p.phong_id = i.phong_id
         WHERE i.tt = 'BAO_TRI' AND i.tu < v_cuoi AND i.den > v_dau
         GROUP BY p.loai_phong_id),
      ban AS (
        SELECT p.loai_phong_id,
               SUM(pkg_gia.so_phut(GREATEST(d.tu_luc, v_dau), LEAST(d.den_luc, v_cuoi))) / 60 AS gio,
               SUM(dp.tien_phong * pkg_gia.so_phut(GREATEST(d.tu_luc, v_dau), LEAST(d.den_luc, v_cuoi))
                   / pkg_gia.so_phut(dp.tu_luc, dp.den_luc)) AS doanh_thu_phong
          FROM dat_phong_doan d
          JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
          JOIN phong p ON p.phong_id = d.phong_id
         WHERE dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT')
           AND d.tu_luc < v_cuoi AND d.den_luc > v_dau
         GROUP BY p.loai_phong_id),
      tong AS (
        SELECT lp.ma_hang,
               (SELECT COUNT(*) FROM phong p WHERE p.loai_phong_id = lp.loai_phong_id AND p.dang_hoat_dong = TRUE) AS so_phong,
               NVL(bt.gio, 0) AS gio_bao_tri, NVL(ban.gio, 0) AS gio_ban, NVL(ban.doanh_thu_phong, 0) AS doanh_thu_phong
          FROM loai_phong lp
          LEFT JOIN bt  ON bt.loai_phong_id  = lp.loai_phong_id
          LEFT JOIN ban ON ban.loai_phong_id = lp.loai_phong_id)
      SELECT ma_hang, ROUND(doanh_thu_phong, 0) AS doanh_thu_phong,
             ROUND(gio_ban / 24, 2) AS phong_dem_ban,
             ROUND((so_phong * v_gio_ky - gio_bao_tri) / 24, 2) AS phong_dem_kha_dung,
             ROUND(doanh_thu_phong / NULLIF(gio_ban / 24, 0), 0) AS adr,
             ROUND(doanh_thu_phong / NULLIF((so_phong * v_gio_ky - gio_bao_tri) / 24, 0), 0) AS revpar
        FROM tong
       ORDER BY ma_hang;
    RETURN c;
  END adr_revpar;

END pkg_bao_cao;
/
