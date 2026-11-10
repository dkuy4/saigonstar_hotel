-- =====================================================================
-- 09_tests_nghiep_vu.sql: kiểm thử package nghiệp vụ trên Oracle (một phiên). Chạy sau 01 đến 05 và 08.
-- Toàn bộ dữ liệu thử nằm trong một giao dịch và bị ROLLBACK ở cuối. Đơn theo ngày dùng ngày năm 2031 để không đụng dữ liệu thật;
-- đơn theo giờ dùng thời điểm hiện tại (cần cho check-in, hủy dưới 24 giờ, no-show).
-- Các ví dụ V1 đến V10 là phụ lục B của BRD. Thuế suất lấy từ PKG_GIA nên kết quả không phụ thuộc ngày chạy.
-- =====================================================================
SET SERVEROUTPUT ON SIZE UNLIMITED
WHENEVER SQLERROR CONTINUE

DECLARE
  v_dat   PLS_INTEGER := 0;
  v_loi   PLS_INTEGER := 0;
  v_seq   PLS_INTEGER := 0;
  v_nd    NUMBER;
  v_id    NUMBER;
  v_id2   NUMBER;
  v_so    NUMBER;
  v_n     NUMBER;
  v_n2    NUMBER;
  v_ma    VARCHAR2(20);
  v_tt    VARCHAR2(20);
  v_ph    NUMBER;
  v_tien  NUMBER;
  v_vat   NUMBER;
  v_tong  NUMBER;
  v_han   TIMESTAMP WITH TIME ZONE;
  v_ket   VARCHAR2(30);
  v_gd    NUMBER;
  v_hd    NUMBER;
  v_tongh NUMBER;
  v_con   NUMBER;
  v_chenh NUMBER;
  v_hoan  NUMBER;
  v_t     NUMBER;
  v_c     SYS_REFCURSOR;
  v_d0    DATE := DATE '2031-05-10';
  v_now15 TIMESTAMP WITH TIME ZONE;
  v_dd    DATE;
  v_lp    NUMBER;
  v_x     XMLTYPE;
  v_tt2   NUMBER;

  PROCEDURE kiem (p_ten IN VARCHAR2, p_dat IN BOOLEAN) IS
  BEGIN
    IF p_dat THEN v_dat := v_dat + 1; DBMS_OUTPUT.PUT_LINE('PASS  ' || p_ten);
    ELSE v_loi := v_loi + 1; DBMS_OUTPUT.PUT_LINE('FAIL  ' || p_ten);
    END IF;
  END kiem;

  FUNCTION ngay (p_d IN DATE, p_gio IN NUMBER) RETURN TIMESTAMP WITH TIME ZONE IS
  BEGIN
    RETURN FROM_TZ(CAST(p_d + p_gio / 24 AS TIMESTAMP), '+07:00');
  END ngay;

  FUNCTION phut (p_p IN NUMBER) RETURN INTERVAL DAY TO SECOND IS
  BEGIN
    RETURN NUMTODSINTERVAL(p_p, 'MINUTE');
  END phut;

  FUNCTION phong (p_ma IN VARCHAR2) RETURN NUMBER IS
    v NUMBER;
  BEGIN
    SELECT phong_id INTO v FROM phong WHERE ma_phong = p_ma;
    RETURN v;
  END phong;

  FUNCTION dem_dong (p_c IN SYS_REFCURSOR) RETURN NUMBER IS
    x XMLTYPE;
    n NUMBER;
  BEGIN
    x := XMLTYPE(p_c);
    SELECT XMLCAST(XMLQUERY('count(/ROWSET/ROW)' PASSING x RETURNING CONTENT) AS NUMBER) INTO n FROM dual;
    RETURN n;
  EXCEPTION
    WHEN VALUE_ERROR THEN
      RETURN 0;
  END dem_dong;

  -- Gọi PKG_DAT_PHONG.TAO_DON; kết quả phụ để ở các biến v_ma, v_tt, v_ph, v_tien, v_vat, v_tong, v_han
  FUNCTION dat (p_ma_hang IN VARCHAR2, p_phong IN NUMBER, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                p_loai IN VARCHAR2, p_kenh IN VARCHAR2, p_thanh_toan IN VARCHAR2,
                p_email IN VARCHAR2 DEFAULT NULL, p_sdt IN VARCHAR2 DEFAULT NULL) RETURN NUMBER IS
    v_i NUMBER;
  BEGIN
    v_seq := v_seq + 1;
    pkg_dat_phong.tao_don('Khách thử', NVL(p_sdt, '09' || LPAD(v_seq, 8, '0')), NVL(p_email, 'u' || v_seq || '@example.com'),
                          'VN', 'vi', p_loai, p_kenh, p_ma_hang, p_phong, p_tu, p_den, 1, p_thanh_toan, SYSTIMESTAMP,
                          v_i, v_ma, v_tt, v_ph, v_tien, v_vat, v_tong, v_han);
    RETURN v_i;
  END dat;

  FUNCTION trang_thai_don (p_id IN NUMBER) RETURN VARCHAR2 IS
    v VARCHAR2(20);
  BEGIN
    SELECT trang_thai INTO v FROM dat_phong WHERE dat_phong_id = p_id;
    RETURN v;
  END trang_thai_don;

  FUNCTION trang_thai_phong (p_ma IN VARCHAR2) RETURN VARCHAR2 IS
    v VARCHAR2(20);
  BEGIN
    SELECT trang_thai INTO v FROM phong WHERE ma_phong = p_ma;
    RETURN v;
  END trang_thai_phong;

  FUNCTION so_email (p_id IN NUMBER, p_loai IN VARCHAR2) RETURN NUMBER IS
    v NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v FROM hang_doi_email WHERE dat_phong_id = p_id AND loai_email = p_loai;
    RETURN v;
  END so_email;

  -- Chèn thẳng một đơn để thử tác vụ nền (đi vòng kiểm tra "không ở quá khứ" của TAO_DON)
  FUNCTION don_truc_tiep (p_phong IN NUMBER, p_loai IN VARCHAR2, p_tu IN TIMESTAMP WITH TIME ZONE,
                          p_den IN TIMESTAMP WITH TIME ZONE, p_da_tt IN NUMBER) RETURN NUMBER IS
    v_k NUMBER; v_i NUMBER;
  BEGIN
    v_seq := v_seq + 1;
    INSERT INTO khach_hang (ho_ten, sdt, email) VALUES ('Khách trực tiếp', '08' || LPAD(v_seq, 8, '0'), 'd' || v_seq || '@example.com')
      RETURNING khach_hang_id INTO v_k;
    INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, so_khach, don_gia_ap_dung,
                           don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu)
    VALUES (v_k, p_loai, 'QUAY', 'CONFIRMED', p_tu, p_den, 1, 550000, 550000, 550000, 0.08, 44000, 594000, 'vi')
    RETURNING dat_phong_id INTO v_i;
    INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc) VALUES (v_i, p_phong, p_tu, p_den);
    IF p_da_tt = 1 THEN
      INSERT INTO giao_dich_thanh_toan (dat_phong_id, kenh, phuong_thuc, so_tien, trang_thai)
      VALUES (v_i, 'QUAY', 'TIEN_MAT', 594000, 'THANH_CONG');
    END IF;
    RETURN v_i;
  END don_truc_tiep;
BEGIN
  INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_bam, ho_ten, vai_tro_id)
    VALUES ('test_pkg', 'khong-phai-mat-khau-that', 'Lễ tân thử', (SELECT vai_tro_id FROM vai_tro WHERE ma_vai_tro = 'LE_TAN'))
    RETURNING nguoi_dung_id INTO v_nd;
  pkg_ngu_canh.dat(v_nd, 'LE_TAN', 'QUAY', '127.0.0.1', 'kiem thu package');

  -- mốc "bây giờ" làm tròn xuống bội của 15 phút, giờ Việt Nam
  v_dd := CAST(SYSTIMESTAMP AT TIME ZONE '+07:00' AS DATE);
  v_dd := TRUNC(v_dd, 'HH24') + FLOOR(TO_NUMBER(TO_CHAR(v_dd, 'MI')) / 15) * 15 / 1440;
  v_now15 := FROM_TZ(CAST(v_dd AS TIMESTAMP), '+07:00');

  DBMS_OUTPUT.PUT_LINE('--- PKG_GIA: ví dụ phụ lục B (giá giờ 80.000, giá ngày 550.000) ---');
  kiem('V1: 3 giờ = 240.000',  pkg_gia.tien_theo_gio(3, 80000, 550000) = 240000);
  kiem('V2: 5 giờ = 400.000',  pkg_gia.tien_theo_gio(5, 80000, 550000) = 400000);
  kiem('V3: 6 giờ tính một giá ngày 550.000, không cộng dồn', pkg_gia.tien_theo_gio(6, 80000, 550000) = 550000);
  kiem('V4: Superior 2 đêm = 1.900.000',
       pkg_gia.tien_phong('NGAY', ngay(v_d0, 14), ngay(v_d0 + 2, 12), 950000, 950000) = 1900000);
  kiem('V8: 4 giờ gia hạn thêm 2 giờ thu thêm 230.000',
       pkg_gia.tien_theo_gio(6, 80000, 550000) - pkg_gia.tien_theo_gio(4, 80000, 550000) = 230000);
  kiem('V9: VAT 8% của 1.900.000 = 152.000', pkg_gia.tinh_vat(1900000, 0.08) = 152000);
  kiem('làm tròn VAT: 1.006 x 8% = 80,48 thành 80', pkg_gia.tinh_vat(1006, 0.08) = 80);
  kiem('làm tròn VAT: 1.007 x 8% = 80,56 thành 81', pkg_gia.tinh_vat(1007, 0.08) = 81);
  kiem('V10: ở quá 3 giờ tính thêm 1 đêm 950.000',
       pkg_gia.tien_qua_gio('NGAY', ngay(v_d0, 14), ngay(v_d0 + 2, 12), ngay(v_d0 + 2, 15), 950000, 950000) = 950000);
  kiem('V10: VAT của đêm thêm 950.000 là 76.000', pkg_gia.tinh_vat(950000, 0.08) = 76000);
  kiem('ở quá 20 phút nằm trong ân hạn 30 phút: không tính',
       pkg_gia.tien_qua_gio('NGAY', ngay(v_d0, 14), ngay(v_d0 + 2, 12), ngay(v_d0 + 2, 12) + phut(20), 950000, 950000) = 0);
  kiem('ở quá 25 giờ tính 2 đêm',
       pkg_gia.tien_qua_gio('NGAY', ngay(v_d0, 14), ngay(v_d0 + 2, 12), ngay(v_d0 + 2, 12) + phut(1500), 950000, 950000) = 1900000);
  kiem('đơn giờ 4 giờ ở quá 2 giờ 30 phút: 7 giờ thành giá ngày, thu thêm 230.000',
       pkg_gia.tien_qua_gio('GIO', ngay(v_d0, 10), ngay(v_d0, 14), ngay(v_d0, 14) + phut(150), 80000, 550000) = 230000);
  kiem('đơn giờ 4 giờ ở quá 40 phút: 5 giờ, thu thêm 80.000',
       pkg_gia.tien_qua_gio('GIO', ngay(v_d0, 10), ngay(v_d0, 14), ngay(v_d0, 14) + phut(40), 80000, 550000) = 80000);
  kiem('2 đêm giờ Việt Nam', pkg_gia.so_dem(ngay(v_d0, 14), ngay(v_d0 + 2, 12)) = 2);

  DBMS_OUTPUT.PUT_LINE('--- PKG_DAT_PHONG.TAO_DON ---');
  v_id := dat('SUPERIOR', NULL, ngay(v_d0, 14), ngay(v_d0 + 2, 12), 'NGAY', 'WEB', 'TRUC_TUYEN');
  kiem('đơn web trực tuyến vào HOLD', v_tt = 'HOLD');
  kiem('tiền phòng 2 đêm Superior = 1.900.000', v_tien = 1900000);
  kiem('VAT và tổng khớp PKG_GIA', v_vat = pkg_gia.tinh_vat(1900000, pkg_gia.thue_suat) AND v_tong = v_tien + v_vat);
  kiem('hạn giữ chỗ khoảng 15 phút', v_han > SYSTIMESTAMP + phut(13) AND v_han <= SYSTIMESTAMP + phut(16));
  SELECT COUNT(*) INTO v_n FROM phong p JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
   WHERE p.phong_id = v_ph AND lp.ma_hang = 'SUPERIOR';
  kiem('hệ thống gán một phòng Superior', v_n = 1);
  kiem('đơn HOLD chưa gửi email xác nhận', so_email(v_id, 'XAC_NHAN') = 0);

  v_id := dat('STANDARD', NULL, ngay(v_d0 + 10, 14), ngay(v_d0 + 11, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  v_n := v_ph;
  kiem('kênh quầy vào CONFIRMED ngay và có email xác nhận', v_tt = 'CONFIRMED' AND so_email(v_id, 'XAC_NHAN') = 1);
  v_id2 := dat('STANDARD', NULL, ngay(v_d0 + 11, 14), ngay(v_d0 + 12, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  kiem('BR-56: đơn ngay sau được gán đúng phòng có lượt liền kề', v_ph = v_n);

  BEGIN
    v_id := dat('SUPERIOR', NULL, ngay(v_d0, 14), ngay(v_d0 + 1, 12), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
    kiem('thuê giờ cho Superior phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('thuê giờ cho Superior bị chặn (BR-02)', SQLCODE = -20020);
  END;
  BEGIN
    v_id := dat('STANDARD', NULL, ngay(v_d0 + 20, 10), ngay(v_d0 + 21, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
    kiem('nhận phòng 10:00 đơn theo ngày phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('nhận phòng sai giờ chuẩn bị chặn (BR-01)', SQLCODE = -20060 AND SQLERRM LIKE '%GIO_NHAN%');
  END;
  BEGIN
    v_id := dat('STANDARD', NULL, v_now15 + phut(105) + phut(7), v_now15 + phut(105) + phut(67), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
    kiem('giờ bắt đầu lệch bước 15 phút phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('giờ bắt đầu lệch bước 15 phút bị chặn (D-47)', SQLCODE = -20060 AND SQLERRM LIKE '%BUOC_GIO%');
  END;
  BEGIN
    v_id := dat('STANDARD', NULL, ngay(DATE '2020-01-01', 14), ngay(DATE '2020-01-02', 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
    kiem('đặt vào quá khứ phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đặt vào quá khứ bị chặn', SQLCODE = -20060 AND SQLERRM LIKE '%QUA_KHU%');
  END;

  -- BR-12: hết phòng thì chỉ báo hết phòng. Suite có 5 phòng.
  FOR i IN 1 .. 5 LOOP
    v_id := dat('SUITE', NULL, ngay(v_d0 + 30, 14), ngay(v_d0 + 31, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  END LOOP;
  v_han := ngay(v_d0 + 30, 14);
  SELECT COUNT(DISTINCT d.phong_id) INTO v_n FROM dat_phong_doan d JOIN phong p ON p.phong_id = d.phong_id
   WHERE p.ma_phong LIKE '5%' AND d.tu_luc = v_han;
  kiem('5 đơn Suite cùng khung giờ gán được 5 phòng khác nhau', v_n = 5);
  BEGIN
    v_id := dat('SUITE', NULL, ngay(v_d0 + 30, 14), ngay(v_d0 + 31, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
    kiem('đơn Suite thứ 6 phải báo hết phòng', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đơn Suite thứ 6 báo hết phòng (NO_AVAILABILITY)', SQLCODE = -20051);
  END;

  -- BR-21: tối đa 3 đơn CONFIRMED chưa thanh toán trên một email hoặc SĐT
  FOR i IN 1 .. 3 LOOP
    v_id := dat('DELUXE', NULL, ngay(v_d0 + 40 + i * 3, 14), ngay(v_d0 + 41 + i * 3, 12), 'NGAY', 'WEB', 'KHI_NHAN_PHONG',
                'gioihan@example.com', '0911111111');
  END LOOP;
  BEGIN
    v_id := dat('DELUXE', NULL, ngay(v_d0 + 60, 14), ngay(v_d0 + 61, 12), 'NGAY', 'WEB', 'KHI_NHAN_PHONG',
                'gioihan@example.com', '0911111111');
    kiem('đơn chưa thanh toán thứ 4 phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đơn chưa thanh toán thứ 4 trên cùng email bị chặn (BR-21)', SQLCODE = -20050);
  END;

  DBMS_OUTPUT.PUT_LINE('--- PKG_THANH_TOAN: cổng, thanh toán về muộn (BR-18, BR-19) ---');
  v_id := dat('SUPERIOR', NULL, ngay(v_d0 + 70, 14), ngay(v_d0 + 71, 12), 'NGAY', 'WEB', 'TRUC_TUYEN');
  pkg_thanh_toan.tao_giao_dich_cong(v_id, 'TEST-OK-' || v_id, v_gd);
  pkg_thanh_toan.xu_ly_ket_qua_cong('TEST-OK-' || v_id, 1, v_ket);
  kiem('thanh toán trong hạn: đơn CONFIRMED', v_ket = 'XAC_NHAN' AND trang_thai_don(v_id) = 'CONFIRMED');
  kiem('thanh toán trong hạn: có email xác nhận', so_email(v_id, 'XAC_NHAN') = 1);
  pkg_thanh_toan.xu_ly_ket_qua_cong('TEST-OK-' || v_id, 1, v_ket);
  kiem('callback lặp không xử lý lần hai (idempotent)', v_ket = 'DA_XU_LY');
  SELECT SUM(so_tien) INTO v_n FROM giao_dich_thanh_toan WHERE dat_phong_id = v_id AND trang_thai = 'THANH_CONG';
  SELECT tong_tien INTO v_tt2 FROM dat_phong WHERE dat_phong_id = v_id;
  kiem('thanh toán trực tuyến bằng 100% tổng tiền (D-34)', v_n = v_tt2);

  v_id := dat('SUPERIOR', NULL, ngay(v_d0 + 72, 14), ngay(v_d0 + 73, 12), 'NGAY', 'WEB', 'TRUC_TUYEN');
  pkg_thanh_toan.tao_giao_dich_cong(v_id, 'TEST-FAIL-' || v_id, v_gd);
  pkg_thanh_toan.xu_ly_ket_qua_cong('TEST-FAIL-' || v_id, 0, v_ket);
  kiem('thanh toán thất bại: đơn EXPIRED', v_ket = 'THAT_BAI' AND trang_thai_don(v_id) = 'EXPIRED');

  -- về muộn, phòng còn trống: tự xác nhận
  v_id := dat('SUPERIOR', NULL, ngay(v_d0 + 74, 14), ngay(v_d0 + 75, 12), 'NGAY', 'WEB', 'TRUC_TUYEN');
  pkg_thanh_toan.tao_giao_dich_cong(v_id, 'TEST-LATE1-' || v_id, v_gd);
  v_han := SYSTIMESTAMP - phut(5);
  UPDATE dat_phong SET han_giu_cho = v_han WHERE dat_phong_id = v_id;
  pkg_thanh_toan.xu_ly_ket_qua_cong('TEST-LATE1-' || v_id, 1, v_ket);
  kiem('BR-19: về muộn, phòng còn trống thì xác nhận', v_ket = 'XAC_NHAN_MUON' AND trang_thai_don(v_id) = 'CONFIRMED');
  kiem('BR-19: có email thanh toán về muộn', so_email(v_id, 'THANH_TOAN_VE_MUON') = 1);

  -- về muộn, phòng đã có người đặt: hoàn 100%
  v_id := dat('STANDARD', phong('110'), ngay(v_d0 + 80, 14), ngay(v_d0 + 81, 12), 'NGAY', 'WEB', 'TRUC_TUYEN');
  pkg_thanh_toan.tao_giao_dich_cong(v_id, 'TEST-LATE2-' || v_id, v_gd);
  v_han := SYSTIMESTAMP - phut(5);
  UPDATE dat_phong SET han_giu_cho = v_han WHERE dat_phong_id = v_id;
  v_id2 := dat('STANDARD', phong('110'), ngay(v_d0 + 80, 14), ngay(v_d0 + 81, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  pkg_thanh_toan.xu_ly_ket_qua_cong('TEST-LATE2-' || v_id, 1, v_ket);
  kiem('BR-19, AC-08: về muộn khi phòng đã có người đặt thì hoàn tiền', v_ket = 'HOAN_TIEN' AND trang_thai_don(v_id) = 'EXPIRED');
  SELECT COUNT(*), NVL(SUM(h.so_tien), 0) INTO v_n, v_n2
    FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id WHERE g.dat_phong_id = v_id AND h.trang_thai = 'DA_DUYET';
  SELECT tong_tien INTO v_tt2 FROM dat_phong WHERE dat_phong_id = v_id;
  kiem('AC-08: hoàn đúng 100% về cổng', v_n = 1 AND v_n2 = v_tt2);

  DBMS_OUTPUT.PUT_LINE('--- Hủy đơn và hoàn tiền (BR-14, BR-24, BR-25, BR-26) ---');
  v_id := dat('STANDARD', NULL, ngay(v_d0 + 90, 14), ngay(v_d0 + 91, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  pkg_thanh_toan.ghi_nhan_quay(v_id, 'TIEN_MAT', v_tong, v_gd);
  kiem('hoàn dự kiến khi còn hơn 24 giờ = số đã thanh toán', pkg_dat_phong.hoan_du_kien(v_id) = v_tong);
  pkg_dat_phong.huy_don(v_id, 'Khách đổi kế hoạch', v_hoan);
  kiem('AC-09: hủy từ 24 giờ trở lên hoàn 100%', v_hoan = v_tong AND trang_thai_don(v_id) = 'CANCELLED');
  SELECT h.trang_thai INTO v_tt FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id WHERE g.dat_phong_id = v_id;
  kiem('hoàn tại quầy chờ quản lý duyệt (BR-25)', v_tt = 'CHO_DUYET');
  SELECT h.hoan_tien_id INTO v_n FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id WHERE g.dat_phong_id = v_id;
  pkg_thanh_toan.duyet_hoan_tien(v_n, v_nd, 1);
  pkg_thanh_toan.xac_nhan_da_hoan(v_n);
  SELECT trang_thai INTO v_tt FROM hoan_tien WHERE hoan_tien_id = v_n;
  kiem('duyệt rồi xác nhận đã hoàn: DA_HOAN', v_tt = 'DA_HOAN');
  kiem('hủy xong có email hủy và hoàn tiền', so_email(v_id, 'HUY_HOAN_TIEN') = 1);

  v_id := dat('STANDARD', phong('109'), v_now15, v_now15 + phut(60), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
  pkg_thanh_toan.ghi_nhan_quay(v_id, 'THE', v_tong, v_gd);
  pkg_dat_phong.huy_don(v_id, 'Hủy sát giờ', v_hoan);
  kiem('AC-09: hủy dưới 24 giờ không hoàn', v_hoan = 0 AND trang_thai_don(v_id) = 'CANCELLED');
  BEGIN
    pkg_thanh_toan.hoan_ngoai_le(v_id, 50000, 'Khách phàn nàn dịch vụ', v_nd);
    SELECT COUNT(*) INTO v_n FROM hoan_tien h JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
     WHERE g.dat_phong_id = v_id AND h.trang_thai = 'DA_DUYET' AND h.nguoi_duyet_id = v_nd;
    kiem('BR-26: quản lý hoàn ngoại lệ, tự duyệt, có lý do', v_n = 1);
  EXCEPTION WHEN OTHERS THEN
    kiem('BR-26: quản lý hoàn ngoại lệ (lỗi ' || SQLERRM || ')', FALSE);
  END;
  BEGIN
    pkg_thanh_toan.hoan_ngoai_le(v_id, 99999999, 'Quá số đã thu', v_nd);
    kiem('hoàn vượt số đã thu phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('hoàn vượt số đã thu bị chặn', SQLCODE = -20056);
  END;
  BEGIN
    pkg_thanh_toan.hoan_ngoai_le(v_id, 1000, '   ', v_nd);
    kiem('hoàn ngoại lệ không có lý do phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('hoàn ngoại lệ bắt buộc có lý do', SQLCODE = -20060);
  END;

  DBMS_OUTPUT.PUT_LINE('--- Check-in, gia hạn, đổi phòng, check-out (BR-31 đến BR-39) ---');
  -- Đơn theo giờ bắt đầu từ bây giờ trên phòng 201, có đơn kế tiếp lúc +90 phút
  v_id := dat('STANDARD', phong('201'), v_now15, v_now15 + phut(60), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
  v_id2 := dat('STANDARD', phong('201'), v_now15 + phut(90), v_now15 + phut(150), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
  BEGIN
    pkg_dat_phong.check_in(v_id, 'CCCD', 'ban-ma-hoa', NULL, NULL, v_ph);
    kiem('check-in thiếu quốc tịch phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('check-in thiếu giấy tờ hoặc quốc tịch bị chặn (BR-30)', SQLCODE = -20060);
  END;
  pkg_dat_phong.check_in(v_id, 'CCCD', 'ban-ma-hoa', 'VN', NULL, v_ph);
  kiem('check-in: đơn CHECKED_IN, phòng DANG_O', trang_thai_don(v_id) = 'CHECKED_IN' AND trang_thai_phong('201') = 'DANG_O');
  SELECT COUNT(*) INTO v_n FROM giay_to_khach g JOIN dat_phong dp ON dp.khach_hang_id = g.khach_hang_id WHERE dp.dat_phong_id = v_id;
  kiem('check-in lưu giấy tờ khách', v_n = 1);
  BEGIN
    pkg_dat_phong.gia_han(v_id, 1, v_tien);
    kiem('gia hạn vướng đơn kế tiếp phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('AC-12: gia hạn vướng lượt kế tiếp (kể cả đệm) bị chặn', SQLCODE = -20055);
  END;
  BEGIN
    pkg_dat_phong.huy_don(v_id, 'thử hủy đơn đang ở', v_hoan);
    kiem('hủy đơn CHECKED_IN phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('AC-10: hủy đơn CHECKED_IN bị chặn', SQLCODE = -20052);
  END;
  v_id2 := dat('STANDARD', phong('202'), v_now15, v_now15 + phut(60), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
  pkg_dat_phong.check_in(v_id2, 'CCCD', 'ban-ma-hoa-2', 'VN', NULL, v_ph);
  pkg_dat_phong.gia_han(v_id2, 2, v_tien);
  SELECT tien_phong, thue_suat INTO v_n, v_n2 FROM dat_phong WHERE dat_phong_id = v_id2;
  kiem('AC-12: gia hạn 2 giờ, tổng 3 giờ = 240.000', v_n = 240000);
  kiem('gia hạn trả đúng số tiền thêm gồm VAT', v_tien = (240000 + pkg_gia.tinh_vat(240000, v_n2)) - (80000 + pkg_gia.tinh_vat(80000, v_n2)));
  pkg_dat_phong.gia_han(v_id2, 3, v_tien);
  SELECT tien_phong INTO v_n FROM dat_phong WHERE dat_phong_id = v_id2;
  kiem('BR-33: gia hạn lên 6 giờ tính lại một giá ngày 550.000', v_n = 550000);

  -- đổi phòng do sự cố: 202 sang 203
  BEGIN
    pkg_dat_phong.doi_phong_su_co(v_id2, phong('301'), 'Hỏng điều hòa');
    kiem('đơn giờ đổi sang Superior phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('BR-35: đơn theo giờ chỉ đổi sang Standard', SQLCODE = -20020);
  END;
  UPDATE phong SET trang_thai = 'DANG_DON' WHERE ma_phong = '204';
  BEGIN
    pkg_dat_phong.doi_phong_su_co(v_id2, phong('204'), 'Hỏng điều hòa');
    kiem('đổi sang phòng chưa dọn phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đổi sang phòng DANG_DON bị chặn (ROOM_NOT_READY)', SQLCODE = -20054);
  END;
  SELECT tien_phong INTO v_n FROM dat_phong WHERE dat_phong_id = v_id2;
  pkg_dat_phong.doi_phong_su_co(v_id2, phong('203'), 'Hỏng điều hòa');
  SELECT tien_phong INTO v_n2 FROM dat_phong WHERE dat_phong_id = v_id2;
  kiem('AC-13: phòng cũ sang BAO_TRI, phòng mới DANG_O', trang_thai_phong('202') = 'BAO_TRI' AND trang_thai_phong('203') = 'DANG_O');
  SELECT COUNT(*) INTO v_t FROM dat_phong_doan WHERE dat_phong_id = v_id2;
  kiem('AC-13: giá đơn giữ nguyên, đơn có hai đoạn lưu trú', v_n2 = v_n AND v_t = 2);
  v_ph := phong('202');
  SELECT COUNT(*) INTO v_n FROM nhat_ky_kiem_toan WHERE bang = 'PHONG' AND hanh_dong = 'DOI_TRANG_THAI'
     AND ly_do = 'Hỏng điều hòa' AND khoa_dong = TO_CHAR(v_ph);
  kiem('AC-13: nhật ký ghi lý do sự cố', v_n >= 1);

  -- check-out có phụ thu và giảm giá (đơn 201), rồi check-out đơn 202/203
  pkg_dat_phong.check_out(v_id, v_nd, 50000, 'Minibar', 20000, 'Khuyến mãi', v_hd, v_tongh, v_con);
  SELECT thue_suat, tien_phong INTO v_n2, v_n FROM dat_phong WHERE dat_phong_id = v_id;
  kiem('check-out: tổng hóa đơn = (tiền phòng + phụ thu - giảm giá) cộng VAT',
       v_tongh = (v_n + 50000 - 20000) + pkg_gia.tinh_vat(v_n + 50000 - 20000, v_n2));
  SELECT SUM(so_tien) INTO v_t FROM chi_tiet_hoa_don WHERE hoa_don_id = v_hd;
  kiem('tổng các dòng chi tiết bằng tổng hóa đơn', v_t = v_tongh);
  kiem('chưa thanh toán nên còn phải thu bằng tổng hóa đơn', v_con = v_tongh);
  kiem('check-out: đơn CHECKED_OUT, phòng DANG_DON', trang_thai_don(v_id) = 'CHECKED_OUT' AND trang_thai_phong('201') = 'DANG_DON');
  v_han := SYSTIMESTAMP + phut(1);
  SELECT COUNT(*) INTO v_n FROM dat_phong_doan WHERE dat_phong_id = v_id AND den_luc <= v_han;
  kiem('BR-37: trả sớm rút đoạn lưu trú về giờ trả thực tế để bán lại', v_n = 1);
  pkg_dat_phong.check_out(v_id2, v_nd, 0, NULL, 0, NULL, v_hd, v_tongh, v_con);
  SELECT tien_phong, thue_suat INTO v_n, v_n2 FROM dat_phong WHERE dat_phong_id = v_id2;
  kiem('check-out đơn đã gia hạn: tiền phòng 550.000 cộng VAT', v_n = 550000 AND v_tongh = 550000 + pkg_gia.tinh_vat(550000, v_n2));
  kiem('check-out ở phòng cuối cùng của đơn: 203 sang DANG_DON', trang_thai_phong('203') = 'DANG_DON');
  BEGIN
    pkg_dat_phong.check_out(v_id2, v_nd, 0, NULL, 0, NULL, v_hd, v_tongh, v_con);
    kiem('check-out lần hai phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('check-out đơn đã CHECKED_OUT bị chặn', SQLCODE = -20003);
  END;

  -- check-in quá sớm (BR-32) và phòng chưa sẵn sàng (BR-31)
  v_id := dat('STANDARD', phong('101'), ngay(v_d0 + 100, 14), ngay(v_d0 + 101, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  BEGIN
    pkg_dat_phong.check_in(v_id, 'CCCD', 'x', 'VN', NULL, v_ph);
    kiem('check-in trước giờ nhận phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('BR-32: check-in trước giờ nhận bị chặn (CHECKIN_TOO_EARLY)', SQLCODE = -20053);
  END;
  v_id := dat('STANDARD', phong('205'), v_now15, v_now15 + phut(60), 'GIO', 'QUAY', 'KHI_NHAN_PHONG');
  UPDATE phong SET trang_thai = 'DANG_DON' WHERE ma_phong = '205';
  BEGIN
    pkg_dat_phong.check_in(v_id, 'CCCD', 'x', 'VN', NULL, v_ph);
    kiem('check-in vào phòng đang dọn phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('BR-31: check-in vào phòng DANG_DON bị chặn (ROOM_NOT_READY)', SQLCODE = -20054);
  END;

  DBMS_OUTPUT.PUT_LINE('--- Đổi lịch (BR-15, D-29) ---');
  v_id := dat('STANDARD', phong('105'), ngay(v_d0 + 110, 14), ngay(v_d0 + 111, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  pkg_thanh_toan.ghi_nhan_quay(v_id, 'TIEN_MAT', v_tong, v_gd);
  pkg_dat_phong.doi_lich(v_id, ngay(v_d0 + 112, 14), ngay(v_d0 + 114, 12), NULL, v_chenh, v_hoan);
  SELECT tien_phong INTO v_n FROM dat_phong WHERE dat_phong_id = v_id;
  kiem('cùng hạng giữ giá đã chốt: 2 đêm x 550.000', v_n = 1100000);
  kiem('đổi sang 2 đêm thì phải thu thêm, không hoàn', v_chenh > 0 AND v_hoan = 0);
  pkg_dat_phong.doi_lich(v_id, ngay(v_d0 + 112, 14), ngay(v_d0 + 113, 12), NULL, v_chenh, v_hoan);
  kiem('giảm về 1 đêm: chênh lệch âm (D-29)', v_chenh < 0);
  v_id2 := dat('STANDARD', phong('106'), ngay(v_d0 + 112, 14), ngay(v_d0 + 113, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  BEGIN
    pkg_dat_phong.doi_lich(v_id, ngay(v_d0 + 112, 14), ngay(v_d0 + 113, 12), phong('106'), v_chenh, v_hoan);
    kiem('đổi sang phòng đã có đơn trong khung giờ đó phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đổi lịch đi qua kiểm tra trùng như đặt mới (BR-15)', SQLCODE = -20001);
  END;
  v_id2 := dat('SUPERIOR', NULL, ngay(v_d0 + 120, 14), ngay(v_d0 + 121, 12), 'NGAY', 'QUAY', 'KHI_NHAN_PHONG');
  pkg_dat_phong.doi_lich(v_id2, ngay(v_d0 + 120, 14), ngay(v_d0 + 121, 12), phong('401'), v_chenh, v_hoan);
  SELECT don_gia_ap_dung INTO v_n FROM dat_phong WHERE dat_phong_id = v_id2;
  kiem('đổi phòng cùng hạng Superior vẫn giữ giá đã chốt', v_n = 950000);
  pkg_dat_phong.doi_lich(v_id2, ngay(v_d0 + 120, 14), ngay(v_d0 + 121, 12), phong('501'), v_chenh, v_hoan);
  SELECT don_gia_ap_dung INTO v_n FROM dat_phong WHERE dat_phong_id = v_id2;
  kiem('D-29: sang Deluxe tính giá hiện hành 1.450.000 và phải thu thêm', v_n = 1450000 AND v_chenh > 0);

  DBMS_OUTPUT.PUT_LINE('--- Tác vụ nền (BR-18, BR-27, BR-28) ---');
  v_id := dat('SUPERIOR', NULL, ngay(v_d0 + 130, 14), ngay(v_d0 + 131, 12), 'NGAY', 'WEB', 'TRUC_TUYEN');
  v_han := SYSTIMESTAMP - phut(1);
  UPDATE dat_phong SET han_giu_cho = v_han WHERE dat_phong_id = v_id;
  pkg_dat_phong.het_han_giu_cho(v_n);
  kiem('AC-06: HOLD hết hạn thành EXPIRED, có email', v_n >= 1 AND trang_thai_don(v_id) = 'EXPIRED' AND so_email(v_id, 'HET_HAN_GIU_CHO') = 1);

  v_id  := don_truc_tiep(phong('301'), 'NGAY', SYSTIMESTAMP - phut(180), SYSTIMESTAMP + phut(1200), 0);
  v_id2 := don_truc_tiep(phong('302'), 'NGAY', SYSTIMESTAMP - phut(60),  SYSTIMESTAMP + phut(1200), 0);
  pkg_dat_phong.tu_no_show(v_n);
  kiem('AC-11a: chưa thanh toán, quá 2 giờ thì NO_SHOW', trang_thai_don(v_id) = 'NO_SHOW');
  kiem('AC-11a: chưa thanh toán nhưng mới quá 1 giờ thì giữ CONFIRMED', trang_thai_don(v_id2) = 'CONFIRMED');
  v_id  := don_truc_tiep(phong('303'), 'NGAY', SYSTIMESTAMP - phut(2 * 1440), SYSTIMESTAMP + phut(600), 1);
  v_id2 := don_truc_tiep(phong('304'), 'NGAY', SYSTIMESTAMP - phut(60), SYSTIMESTAMP + phut(1200), 1);
  pkg_dat_phong.tu_no_show(v_n);
  kiem('AC-11b: đã thanh toán, qua 12:00 hôm sau ngày nhận thì NO_SHOW', trang_thai_don(v_id) = 'NO_SHOW');
  kiem('AC-11b: đã thanh toán, chưa tới 12:00 hôm sau thì giữ CONFIRMED', trang_thai_don(v_id2) = 'CONFIRMED');
  v_id := don_truc_tiep(phong('305'), 'GIO', SYSTIMESTAMP - phut(240), SYSTIMESTAMP - phut(60), 1);
  v_id2 := don_truc_tiep(phong('306'), 'GIO', SYSTIMESTAMP - phut(20), SYSTIMESTAMP + phut(160), 0);
  pkg_dat_phong.tu_no_show(v_n);
  kiem('đơn giờ đã thanh toán: NO_SHOW khi hết khung giờ đã đặt', trang_thai_don(v_id) = 'NO_SHOW');
  kiem('đơn giờ chưa thanh toán: chờ 30 phút, mới 20 phút thì giữ CONFIRMED', trang_thai_don(v_id2) = 'CONFIRMED');
  pkg_dat_phong.no_show_thu_cong(v_id2);
  kiem('lễ tân đóng NO_SHOW thủ công', trang_thai_don(v_id2) = 'NO_SHOW');

  DBMS_OUTPUT.PUT_LINE('--- PKG_PHONG ---');
  v_c := pkg_phong.so_do;
  kiem('sơ đồ phòng trả 50 phòng', dem_dong(v_c) = 50);
  v_c := pkg_phong.so_do(SYSTIMESTAMP + phut(30));
  kiem('sơ đồ phòng chọn thời điểm khác vẫn trả 50 phòng', dem_dong(v_c) = 50);
  SELECT loai_phong_id INTO v_lp FROM loai_phong WHERE ma_hang = 'SUITE';
  v_c := pkg_dat_phong.goi_y_phong(v_lp, ngay(v_d0 + 30, 14), ngay(v_d0 + 31, 12));
  kiem('gợi ý phòng: không còn Suite trống đúng khung đã kín', dem_dong(v_c) = 0);
  v_c := pkg_dat_phong.goi_y_phong(v_lp, ngay(v_d0 + 200, 14), ngay(v_d0 + 201, 12));
  kiem('gợi ý phòng: khung trống có đủ 5 Suite', dem_dong(v_c) = 5);
  BEGIN
    pkg_phong.bat_bao_tri(phong('501'), 'Sơn lại tường', 0);
    kiem('bảo trì phòng có đơn tương lai phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('BR-41: bảo trì phòng có đơn tương lai phải xử lý trước (-20066)', SQLCODE = -20066);
  END;
  pkg_phong.bat_bao_tri(phong('501'), 'Sơn lại tường', 1);
  kiem('bảo trì sau khi xác nhận: phòng BAO_TRI', trang_thai_phong('501') = 'BAO_TRI');
  pkg_phong.ket_thuc_bao_tri(phong('501'));
  kiem('hết bảo trì: phòng TRONG', trang_thai_phong('501') = 'TRONG');
  BEGIN
    pkg_phong.bat_bao_tri(phong('203'), 'x', 1);
    kiem('bảo trì phòng DANG_DON phải được phép', trang_thai_phong('203') = 'BAO_TRI');
  EXCEPTION WHEN OTHERS THEN
    kiem('bảo trì phòng DANG_DON (lỗi ' || SQLERRM || ')', FALSE);
  END;
  pkg_phong.ket_thuc_bao_tri(phong('203'));
  UPDATE phong SET trang_thai = 'DANG_DON' WHERE ma_phong = '206';
  pkg_phong.bat_dau_don(phong('206'));
  pkg_phong.don_xong(phong('206'));
  kiem('FR-24: dọn xong thì phòng TRONG', trang_thai_phong('206') = 'TRONG');
  BEGIN
    pkg_phong.don_xong(phong('207'));
    kiem('dọn xong phòng không ở DANG_DON phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('dọn xong phòng không ở DANG_DON bị chặn', SQLCODE = -20065);
  END;
  BEGIN
    pkg_phong.doi_trang_thai_thu_cong(phong('207'), 'BAO_TRI', NULL);
    kiem('sửa trạng thái thủ công không có lý do phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('BR-40: sửa trạng thái thủ công bắt buộc có lý do', SQLCODE = -20060);
  END;
  v_c := pkg_phong.doi_soat_phong_lich;
  kiem('đối soát phòng và lịch chạy được', dem_dong(v_c) >= 0);

  DBMS_OUTPUT.PUT_LINE('--- PKG_THANH_TOAN.DOI_SOAT_NGAY và PKG_BAO_CAO ---');
  v_c := pkg_thanh_toan.doi_soat_ngay(TRUNC(CAST(SYSTIMESTAMP AT TIME ZONE '+07:00' AS DATE)));
  kiem('FR-39: đối soát cuối ngày có dòng tiền mặt hôm nay', dem_dong(v_c) >= 1);
  v_c := pkg_bao_cao.doanh_thu(TRUNC(SYSDATE) - 1, TRUNC(SYSDATE) + 1, 'NGAY');
  kiem('FR-40: doanh thu theo ngày chạy được', dem_dong(v_c) >= 1);
  v_c := pkg_bao_cao.doanh_thu(TRUNC(SYSDATE) - 1, TRUNC(SYSDATE) + 1, 'THANG', 'STANDARD', 'TIEN_MAT');
  kiem('FR-40: doanh thu theo tháng, lọc hạng và phương thức', dem_dong(v_c) >= 0);
  v_c := pkg_bao_cao.cong_suat(v_d0 + 30, v_d0 + 30);
  v_x := XMLTYPE(v_c);
  SELECT XMLCAST(XMLQUERY('count(/ROWSET/ROW)' PASSING v_x RETURNING CONTENT) AS NUMBER) INTO v_n FROM dual;
  kiem('FR-41: công suất trả 4 hạng', v_n = 4);
  -- Suite: 5 phòng, mỗi đơn từ 14:00 ngày 09/06/2031 sang 12:00 hôm sau; trong ngày 09/06 mỗi phòng bán 10 giờ
  SELECT XMLCAST(XMLQUERY('/ROWSET/ROW[MA_HANG="SUITE"]/GIO_PHONG_BAN' PASSING v_x RETURNING CONTENT) AS NUMBER) INTO v_n FROM dual;
  kiem('AC-17: Suite ngày 09/06/2031 bán 5 phòng x 10 giờ = 50 giờ-phòng', v_n = 50);
  v_c := pkg_bao_cao.ty_le_huy(TRUNC(SYSDATE) - 1, TRUNC(SYSDATE) + 1);
  kiem('FR-42: tỷ lệ hủy, no-show chạy được', dem_dong(v_c) = 1);
  v_c := pkg_bao_cao.adr_revpar(v_d0 + 30, v_d0 + 30);
  kiem('FR-44: ADR và RevPAR trả 4 hạng', dem_dong(v_c) = 4);

  DBMS_OUTPUT.PUT_LINE('=== ' || v_dat || ' đạt, ' || v_loi || ' lỗi ===');
  pkg_ngu_canh.xoa;
  ROLLBACK;
  IF v_loi > 0 THEN
    RAISE_APPLICATION_ERROR(-20999, v_loi || ' ca kiểm thử thất bại');
  END IF;
END;
/
