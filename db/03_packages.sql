-- =====================================================================
-- 03_packages.sql: các package dùng chung cho trigger và ứng dụng
--   PKG_CAU_HINH      đọc tham số có ngày hiệu lực
--   PKG_KIEM_TRA_TRUNG kiểm tra trùng phòng (BR-08 đến BR-11), khóa dòng phòng
--   PKG_NGU_CANH      người thực hiện, vai trò, kênh, IP của phiên (cho nhật ký BR-47)
--   PKG_NHAT_KY       ghi nhật ký kiểm toán
--   PKG_HOA_DON       cấp số hóa đơn liên tục (BR-44)
-- Mã lỗi nghiệp vụ trả về dạng 'MA_LOI|chi tiết' qua RAISE_APPLICATION_ERROR để API ánh xạ (FR-51):
--   -20001 ROOM_CONFLICT        -20002 ROOM_BUSY          -20003 BOOKING_STATE_INVALID
--   -20020 HOURLY_NOT_ALLOWED   -20021 PRICE_OVERLAP      -20022 PRICE_RULE_VIOLATION
--   -20023 CONFIG_OVERLAP       -20030 AUDIT_IMMUTABLE    -20031 INVOICE_IMMUTABLE
--   -20040 CONFIG_MISSING
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_cau_hinh AS
  -- Ngày hiện tại theo giờ Việt Nam (BR-07), không phụ thuộc múi giờ của máy chủ Docker
  FUNCTION ngay_vn RETURN DATE;
  FUNCTION lay_so  (p_ma IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN NUMBER;
  FUNCTION lay_chu (p_ma IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN VARCHAR2;
  -- Tham số dạng 'HH:MM' đổi thành phần của ngày (14:00 -> 0,58333...), để cộng vào một ngày
  FUNCTION lay_phan_ngay (p_ma IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN NUMBER;
END pkg_cau_hinh;
/
CREATE OR REPLACE PACKAGE BODY pkg_cau_hinh AS
  FUNCTION ngay_vn RETURN DATE IS
  BEGIN
    RETURN TRUNC(CAST(SYSTIMESTAMP AT TIME ZONE '+07:00' AS DATE));
  END ngay_vn;

  FUNCTION lay_so (p_ma IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN NUMBER IS
    v_tai DATE := NVL(p_tai, ngay_vn);
    v_kq  NUMBER;
  BEGIN
    SELECT gia_tri_so INTO v_kq
      FROM (SELECT gia_tri_so
              FROM cau_hinh_he_thong
             WHERE ma_tham_so = p_ma
               AND hieu_luc_tu <= v_tai
               AND (hieu_luc_den IS NULL OR hieu_luc_den >= v_tai)
             ORDER BY hieu_luc_tu DESC)
     WHERE ROWNUM = 1;
    RETURN v_kq;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20040, 'CONFIG_MISSING|' || p_ma);
  END lay_so;

  FUNCTION lay_chu (p_ma IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN VARCHAR2 IS
    v_tai DATE := NVL(p_tai, ngay_vn);
    v_kq  VARCHAR2(200 CHAR);
  BEGIN
    SELECT gia_tri_chu INTO v_kq
      FROM (SELECT gia_tri_chu
              FROM cau_hinh_he_thong
             WHERE ma_tham_so = p_ma
               AND hieu_luc_tu <= v_tai
               AND (hieu_luc_den IS NULL OR hieu_luc_den >= v_tai)
             ORDER BY hieu_luc_tu DESC)
     WHERE ROWNUM = 1;
    RETURN v_kq;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20040, 'CONFIG_MISSING|' || p_ma);
  END lay_chu;

  FUNCTION lay_phan_ngay (p_ma IN VARCHAR2, p_tai IN DATE DEFAULT NULL) RETURN NUMBER IS
    v_chu VARCHAR2(200 CHAR) := lay_chu(p_ma, p_tai);
  BEGIN
    RETURN TO_NUMBER(SUBSTR(v_chu, 1, 2)) / 24 + TO_NUMBER(SUBSTR(v_chu, 4, 2)) / 1440;
  END lay_phan_ngay;
END pkg_cau_hinh;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_kiem_tra_trung AS
  TYPE t_ds_so IS TABLE OF NUMBER INDEX BY PLS_INTEGER;

  -- Đơn có chiếm phòng không (BR-09): HOLD còn hạn, CONFIRMED, CHECKED_IN, CHECKED_OUT.
  -- Điều kiện này được lặp trong câu SQL của dem_xung_dot; sửa một nơi phải sửa cả hai.
  FUNCTION la_chiem_phong (p_trang_thai IN VARCHAR2, p_han_giu_cho IN TIMESTAMP WITH TIME ZONE) RETURN BOOLEAN;

  -- Số đoạn lưu trú xung đột với [p_tu, p_den) của một phòng (BR-08), không tính đoạn p_bo_qua_doan_id
  FUNCTION dem_xung_dot (p_phong_id IN NUMBER,
                         p_tu IN TIMESTAMP WITH TIME ZONE,
                         p_den IN TIMESTAMP WITH TIME ZONE,
                         p_bo_qua_doan_id IN NUMBER DEFAULT NULL) RETURN NUMBER;

  -- Số phút từ [p_tu, p_den) tới lượt liền kề gần nhất của phòng (BR-56); 1000000000 nếu phòng chưa có lượt nào gần
  FUNCTION khoang_cach_lan_can (p_phong_id IN NUMBER,
                                p_tu IN TIMESTAMP WITH TIME ZONE,
                                p_den IN TIMESTAMP WITH TIME ZONE) RETURN NUMBER;

  -- Khóa dòng phòng để các phiên cùng đặt một phòng phải xếp hàng (BR-11)
  PROCEDURE khoa_phong (p_phong_id IN NUMBER);

  -- Kiểm tra một đoạn lưu trú; ném ROOM_CONFLICT nếu trùng
  PROCEDURE kiem_tra_doan (p_doan_id IN NUMBER);

  -- Kiểm tra nhiều đoạn: khóa các phòng theo thứ tự tăng dần của phong_id rồi mới kiểm tra (tránh deadlock)
  PROCEDURE kiem_tra_cac_doan (p_doan IN t_ds_so);

  -- Kiểm tra mọi đoạn của một đơn (dùng khi đơn đổi sang trạng thái chiếm phòng trở lại)
  PROCEDURE kiem_tra_don (p_dat_phong_id IN NUMBER);
END pkg_kiem_tra_trung;
/
CREATE OR REPLACE PACKAGE BODY pkg_kiem_tra_trung AS

  FUNCTION la_chiem_phong (p_trang_thai IN VARCHAR2, p_han_giu_cho IN TIMESTAMP WITH TIME ZONE) RETURN BOOLEAN IS
  BEGIN
    RETURN p_trang_thai IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT')
        OR (p_trang_thai = 'HOLD' AND p_han_giu_cho > SYSTIMESTAMP);
  END la_chiem_phong;

  FUNCTION dem_xung_dot (p_phong_id IN NUMBER,
                         p_tu IN TIMESTAMP WITH TIME ZONE,
                         p_den IN TIMESTAMP WITH TIME ZONE,
                         p_bo_qua_doan_id IN NUMBER DEFAULT NULL) RETURN NUMBER IS
    v_dem   INTERVAL DAY TO SECOND := NUMTODSINTERVAL(pkg_cau_hinh.lay_so('KHOANG_DEM_PHUT'), 'MINUTE');
    v_so    NUMBER;
  BEGIN
    -- BR-08: A trùng B khi nhận A < trả B + đệm và nhận B < trả A + đệm.
    -- Viết lại phép cộng đệm sang phía tham số để dùng được chỉ mục (phong_id, tu_luc, den_luc).
    SELECT COUNT(*)
      INTO v_so
      FROM dat_phong_doan d
      JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
     WHERE d.phong_id = p_phong_id
       AND (p_bo_qua_doan_id IS NULL OR d.doan_id <> p_bo_qua_doan_id)
       AND (dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT')
            OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > SYSTIMESTAMP))
       AND d.tu_luc   < p_den + v_dem
       AND d.den_luc  > p_tu  - v_dem;
    RETURN v_so;
  END dem_xung_dot;

  FUNCTION khoang_cach_lan_can (p_phong_id IN NUMBER,
                                p_tu IN TIMESTAMP WITH TIME ZONE,
                                p_den IN TIMESTAMP WITH TIME ZONE) RETURN NUMBER IS
    v_truoc TIMESTAMP WITH TIME ZONE;
    v_sau   TIMESTAMP WITH TIME ZONE;
    v_pt    NUMBER := 1000000000;
    v_kc    INTERVAL DAY(9) TO SECOND;
  BEGIN
    SELECT MAX(d.den_luc), MIN(CASE WHEN d.tu_luc >= p_den THEN d.tu_luc END)
      INTO v_truoc, v_sau
      FROM dat_phong_doan d JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
     WHERE d.phong_id = p_phong_id
       AND (dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT')
            OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > SYSTIMESTAMP))
       AND (d.den_luc <= p_tu OR d.tu_luc >= p_den);
    IF v_truoc IS NOT NULL AND v_truoc <= p_tu THEN
      v_kc := p_tu - v_truoc;
      v_pt := LEAST(v_pt, EXTRACT(DAY FROM v_kc) * 1440 + EXTRACT(HOUR FROM v_kc) * 60 + EXTRACT(MINUTE FROM v_kc));
    END IF;
    IF v_sau IS NOT NULL THEN
      v_kc := v_sau - p_den;
      v_pt := LEAST(v_pt, EXTRACT(DAY FROM v_kc) * 1440 + EXTRACT(HOUR FROM v_kc) * 60 + EXTRACT(MINUTE FROM v_kc));
    END IF;
    RETURN v_pt;
  END khoang_cach_lan_can;

  PROCEDURE khoa_phong (p_phong_id IN NUMBER) IS
    v_id     NUMBER;
    e_het_gio EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_het_gio, -30006);   -- ORA-30006: hết thời gian chờ khóa
  BEGIN
    SELECT phong_id INTO v_id FROM phong WHERE phong_id = p_phong_id FOR UPDATE WAIT 10;
  EXCEPTION
    WHEN e_het_gio THEN
      RAISE_APPLICATION_ERROR(-20002, 'ROOM_BUSY|' || p_phong_id);
  END khoa_phong;

  PROCEDURE kiem_tra_doan (p_doan_id IN NUMBER) IS
    v_phong_id   NUMBER;
    v_tu         TIMESTAMP WITH TIME ZONE;
    v_den        TIMESTAMP WITH TIME ZONE;
    v_trang_thai VARCHAR2(20);
    v_han        TIMESTAMP WITH TIME ZONE;
  BEGIN
    SELECT d.phong_id, d.tu_luc, d.den_luc, dp.trang_thai, dp.han_giu_cho
      INTO v_phong_id, v_tu, v_den, v_trang_thai, v_han
      FROM dat_phong_doan d
      JOIN dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
     WHERE d.doan_id = p_doan_id;

    -- Đơn không chiếm phòng (CANCELLED, NO_SHOW, EXPIRED, HOLD hết hạn) thì không cần kiểm tra
    IF NOT la_chiem_phong(v_trang_thai, v_han) THEN
      RETURN;
    END IF;

    -- Khóa trước rồi mới đếm: câu đếm là câu lệnh mới nên thấy các dòng người khác vừa commit
    khoa_phong(v_phong_id);
    IF dem_xung_dot(v_phong_id, v_tu, v_den, p_doan_id) > 0 THEN
      RAISE_APPLICATION_ERROR(-20001, 'ROOM_CONFLICT|' || v_phong_id || '|' || p_doan_id);
    END IF;
  END kiem_tra_doan;

  PROCEDURE kiem_tra_cac_doan (p_doan IN t_ds_so) IS
    TYPE t_tap IS TABLE OF NUMBER INDEX BY VARCHAR2(40);
    v_phong t_tap;
    v_khoa  VARCHAR2(40);
    v_pid   NUMBER;
  BEGIN
    FOR i IN 1 .. p_doan.COUNT LOOP
      SELECT phong_id INTO v_pid FROM dat_phong_doan WHERE doan_id = p_doan(i);
      v_phong(LPAD(TO_CHAR(v_pid), 30, '0')) := v_pid;     -- khóa chuỗi sắp theo thứ tự tăng của phong_id
    END LOOP;
    v_khoa := v_phong.FIRST;
    WHILE v_khoa IS NOT NULL LOOP
      khoa_phong(v_phong(v_khoa));
      v_khoa := v_phong.NEXT(v_khoa);
    END LOOP;
    FOR i IN 1 .. p_doan.COUNT LOOP
      kiem_tra_doan(p_doan(i));
    END LOOP;
  END kiem_tra_cac_doan;

  PROCEDURE kiem_tra_don (p_dat_phong_id IN NUMBER) IS
    v_ds t_ds_so;
  BEGIN
    FOR r IN (SELECT doan_id FROM dat_phong_doan WHERE dat_phong_id = p_dat_phong_id ORDER BY doan_id) LOOP
      v_ds(v_ds.COUNT + 1) := r.doan_id;
    END LOOP;
    kiem_tra_cac_doan(v_ds);
  END kiem_tra_don;

END pkg_kiem_tra_trung;
/

-- ---------------------------------------------------------------------
-- Ngữ cảnh phiên: API gọi PKG_NGU_CANH.DAT ở đầu mỗi giao dịch (kết nối từ pool dùng lại giữa các yêu cầu)
CREATE OR REPLACE PACKAGE pkg_ngu_canh AS
  PROCEDURE dat (p_nguoi_id IN NUMBER, p_vai_tro IN VARCHAR2, p_kenh IN VARCHAR2,
                 p_ip IN VARCHAR2 DEFAULT NULL, p_ly_do IN VARCHAR2 DEFAULT NULL);
  PROCEDURE dat_ly_do (p_ly_do IN VARCHAR2);
  PROCEDURE xoa;
  FUNCTION nguoi_id RETURN NUMBER;
  FUNCTION vai_tro  RETURN VARCHAR2;
  FUNCTION kenh     RETURN VARCHAR2;
  FUNCTION ip       RETURN VARCHAR2;
  FUNCTION ly_do    RETURN VARCHAR2;
END pkg_ngu_canh;
/
CREATE OR REPLACE PACKAGE BODY pkg_ngu_canh AS
  g_nguoi_id NUMBER;
  g_vai_tro  VARCHAR2(20) := 'HE_THONG';
  g_kenh     VARCHAR2(20) := 'HE_THONG';
  g_ip       VARCHAR2(45);
  g_ly_do    VARCHAR2(500 CHAR);

  PROCEDURE dat (p_nguoi_id IN NUMBER, p_vai_tro IN VARCHAR2, p_kenh IN VARCHAR2,
                 p_ip IN VARCHAR2 DEFAULT NULL, p_ly_do IN VARCHAR2 DEFAULT NULL) IS
  BEGIN
    g_nguoi_id := p_nguoi_id;
    g_vai_tro  := p_vai_tro;
    g_kenh     := p_kenh;
    g_ip       := p_ip;
    g_ly_do    := p_ly_do;
  END dat;

  PROCEDURE dat_ly_do (p_ly_do IN VARCHAR2) IS
  BEGIN
    g_ly_do := p_ly_do;
  END dat_ly_do;

  PROCEDURE xoa IS
  BEGIN
    g_nguoi_id := NULL; g_vai_tro := 'HE_THONG'; g_kenh := 'HE_THONG'; g_ip := NULL; g_ly_do := NULL;
  END xoa;

  FUNCTION nguoi_id RETURN NUMBER   IS BEGIN RETURN g_nguoi_id; END nguoi_id;
  FUNCTION vai_tro  RETURN VARCHAR2 IS BEGIN RETURN g_vai_tro;  END vai_tro;
  FUNCTION kenh     RETURN VARCHAR2 IS BEGIN RETURN g_kenh;     END kenh;
  FUNCTION ip       RETURN VARCHAR2 IS BEGIN RETURN g_ip;       END ip;
  FUNCTION ly_do    RETURN VARCHAR2 IS BEGIN RETURN g_ly_do;    END ly_do;
END pkg_ngu_canh;
/

-- ---------------------------------------------------------------------
CREATE OR REPLACE PACKAGE pkg_nhat_ky AS
  PROCEDURE ghi (p_bang IN VARCHAR2, p_khoa_dong IN VARCHAR2, p_hanh_dong IN VARCHAR2,
                 p_cu IN CLOB DEFAULT NULL, p_moi IN CLOB DEFAULT NULL);
END pkg_nhat_ky;
/
CREATE OR REPLACE PACKAGE BODY pkg_nhat_ky AS
  PROCEDURE ghi (p_bang IN VARCHAR2, p_khoa_dong IN VARCHAR2, p_hanh_dong IN VARCHAR2,
                 p_cu IN CLOB DEFAULT NULL, p_moi IN CLOB DEFAULT NULL) IS
  BEGIN
    INSERT INTO nhat_ky_kiem_toan
           (bang, khoa_dong, hanh_dong, gia_tri_cu, gia_tri_moi, ly_do, nguoi_thuc_hien_id, vai_tro, kenh, dia_chi_ip)
    VALUES (p_bang, p_khoa_dong, p_hanh_dong, p_cu, p_moi, pkg_ngu_canh.ly_do, pkg_ngu_canh.nguoi_id,
            pkg_ngu_canh.vai_tro, pkg_ngu_canh.kenh, pkg_ngu_canh.ip);
  END ghi;
END pkg_nhat_ky;
/

-- ---------------------------------------------------------------------
-- Cấp số hóa đơn liên tục: khóa dòng bộ đếm đến hết giao dịch, hủy giao dịch thì số không bị mất (không hở số)
CREATE OR REPLACE PACKAGE pkg_hoa_don AS
  FUNCTION cap_so RETURN NUMBER;
END pkg_hoa_don;
/
CREATE OR REPLACE PACKAGE BODY pkg_hoa_don AS
  FUNCTION cap_so RETURN NUMBER IS
    v_so NUMBER;
  BEGIN
    SELECT gia_tri_cuoi INTO v_so FROM bo_dem_hoa_don WHERE loai = 'HOA_DON' FOR UPDATE;
    v_so := v_so + 1;
    UPDATE bo_dem_hoa_don SET gia_tri_cuoi = v_so WHERE loai = 'HOA_DON';
    RETURN v_so;
  END cap_so;
END pkg_hoa_don;
/
