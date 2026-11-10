-- =====================================================================
-- 06_tests.sql: kiểm thử trigger và ràng buộc trên Oracle (một phiên). Chạy sau 01 đến 05.
-- Mọi dữ liệu thử nằm trong một giao dịch và bị ROLLBACK ở cuối; dữ liệu seed không bị đụng.
-- Kiểm thử đồng thời nhiều phiên (AC-01, AC-02) nằm ở ac02_concurrency.py.
-- =====================================================================
SET SERVEROUTPUT ON SIZE UNLIMITED
WHENEVER SQLERROR CONTINUE

DECLARE
  v_dat    PLS_INTEGER := 0;
  v_loi    PLS_INTEGER := 0;
  v_khach  NUMBER;
  v_nd     NUMBER;
  v_don    NUMBER;
  v_don2   NUMBER;
  v_hd     NUMBER;
  v_so1    NUMBER;
  v_so2    NUMBER;
  v_dem    NUMBER;
  v_ma     VARCHAR2(20);
  v_t0     TIMESTAMP WITH TIME ZONE := TIMESTAMP '2031-03-01 10:00:00 +07:00';
  v_tuan   TIMESTAMP WITH TIME ZONE := TIMESTAMP '2031-03-08 10:00:00 +07:00';
  v_tuan_t TIMESTAMP WITH TIME ZONE := TIMESTAMP '2031-03-08 09:00:00 +07:00';   -- trước v_tuan 60 phút
  v_tuan_s TIMESTAMP WITH TIME ZONE := TIMESTAMP '2031-03-08 11:00:00 +07:00';   -- sau v_tuan 60 phút
  v_han    TIMESTAMP WITH TIME ZONE;
  v_p      NUMBER;

  PROCEDURE kiem (p_ten IN VARCHAR2, p_dat IN BOOLEAN) IS
  BEGIN
    IF p_dat THEN
      v_dat := v_dat + 1;  DBMS_OUTPUT.PUT_LINE('PASS  ' || p_ten);
    ELSE
      v_loi := v_loi + 1;  DBMS_OUTPUT.PUT_LINE('FAIL  ' || p_ten);
    END IF;
  END kiem;

  FUNCTION phong (p_ma IN VARCHAR2) RETURN NUMBER IS
    v NUMBER;
  BEGIN
    SELECT phong_id INTO v FROM phong WHERE ma_phong = p_ma;
    RETURN v;
  END phong;

  FUNCTION phut (p_p IN NUMBER) RETURN INTERVAL DAY TO SECOND IS
  BEGIN
    RETURN NUMTODSINTERVAL(p_p, 'MINUTE');
  END phut;

  -- Tạo một đơn theo giờ và đoạn lưu trú của nó. Lỗi trigger trùng phòng nổ ở lệnh INSERT thứ hai.
  FUNCTION tao_don (p_phong IN NUMBER, p_tu IN TIMESTAMP WITH TIME ZONE, p_den IN TIMESTAMP WITH TIME ZONE,
                    p_trang_thai IN VARCHAR2 DEFAULT 'CONFIRMED',
                    p_han IN TIMESTAMP WITH TIME ZONE DEFAULT NULL) RETURN NUMBER IS
    v_id NUMBER;
  BEGIN
    INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, han_giu_cho,
                           so_khach, don_gia_ap_dung, don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu)
    VALUES (v_khach, 'GIO', 'QUAY', p_trang_thai, p_tu, p_den, p_han, 1, 80000, 550000, 240000, 0.08, 19200, 259200, 'vi')
    RETURNING dat_phong_id INTO v_id;
    INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc) VALUES (v_id, p_phong, p_tu, p_den);
    RETURN v_id;
  END tao_don;
BEGIN
  INSERT INTO khach_hang (ho_ten, sdt, email) VALUES ('Khách thử', '0900000000', 'thu@example.com')
    RETURNING khach_hang_id INTO v_khach;
  INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_bam, ho_ten, vai_tro_id)
    VALUES ('test_tmp', 'khong-phai-mat-khau-that', 'Lễ tân thử', (SELECT vai_tro_id FROM vai_tro WHERE ma_vai_tro = 'LE_TAN'))
    RETURNING nguoi_dung_id INTO v_nd;
  pkg_ngu_canh.dat(v_nd, 'LE_TAN', 'QUAY', '127.0.0.1', 'kiem thu');

  DBMS_OUTPUT.PUT_LINE('--- Chống trùng phòng (BR-06, BR-08, BR-09, BR-11) ---');
  -- AC-03: đơn theo giờ 10:00-13:00 trên phòng 101
  v_don := tao_don(phong('101'), v_t0, v_t0 + phut(180));
  kiem('đơn 10:00-13:00 tạo được', v_don IS NOT NULL);
  BEGIN
    v_don2 := tao_don(phong('101'), v_t0 + phut(200), v_t0 + phut(300));          -- 13:20 còn trong đệm
    kiem('AC-03: đơn bắt đầu 13:20 phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('AC-03: đơn bắt đầu 13:20 bị chặn (-20001 ROOM_CONFLICT)', SQLCODE = -20001 AND SQLERRM LIKE '%ROOM_CONFLICT%');
  END;
  BEGIN
    v_don2 := tao_don(phong('101'), v_t0 + phut(210), v_t0 + phut(300));          -- 13:30 đúng lúc hết đệm
    kiem('AC-03: đơn bắt đầu 13:30 được nhận', v_don2 IS NOT NULL);
  EXCEPTION WHEN OTHERS THEN
    kiem('AC-03: đơn bắt đầu 13:30 được nhận (lỗi ' || SQLERRM || ')', FALSE);
  END;
  BEGIN
    v_don2 := tao_don(phong('101'), v_t0 - phut(120), v_t0 - phut(30));           -- 08:00-09:30, A bắt đầu 10:00
    kiem('kết thúc 09:30 trước đơn 10:00: không trùng', v_don2 IS NOT NULL);
  EXCEPTION WHEN OTHERS THEN
    kiem('kết thúc 09:30 trước đơn 10:00: không trùng (lỗi ' || SQLERRM || ')', FALSE);
  END;
  BEGIN
    v_don2 := tao_don(phong('101'), v_t0 - phut(180), v_t0 - phut(20));           -- 07:00-09:40, còn trong đệm của A
    kiem('kết thúc 09:40 sát đơn 10:00 phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('kết thúc 09:40 sát đơn 10:00 bị chặn', SQLCODE = -20001);
  END;
  BEGIN
    v_don2 := tao_don(phong('102'), v_t0, v_t0 + phut(180));                      -- cùng giờ nhưng khác phòng
    kiem('khác phòng cùng khung giờ: không trùng', v_don2 IS NOT NULL);
  EXCEPTION WHEN OTHERS THEN
    kiem('khác phòng cùng khung giờ: không trùng (lỗi ' || SQLERRM || ')', FALSE);
  END;

  -- BR-09: CANCELLED nhả phòng
  v_don := tao_don(phong('103'), v_t0, v_t0 + phut(180));
  UPDATE dat_phong SET trang_thai = 'CANCELLED', ly_do_huy = 'kiem thu' WHERE dat_phong_id = v_don;
  BEGIN
    v_don2 := tao_don(phong('103'), v_t0, v_t0 + phut(180));
    kiem('đơn CANCELLED nhả phòng (BR-09)', v_don2 IS NOT NULL);
  EXCEPTION WHEN OTHERS THEN
    kiem('đơn CANCELLED nhả phòng (lỗi ' || SQLERRM || ')', FALSE);
  END;

  -- BR-09, BR-17: HOLD còn hạn chiếm phòng, HOLD quá hạn thì không
  v_don := tao_don(phong('104'), v_t0, v_t0 + phut(180), 'HOLD', SYSTIMESTAMP + phut(15));
  BEGIN
    v_don2 := tao_don(phong('104'), v_t0, v_t0 + phut(180));
    kiem('HOLD còn hạn phải chiếm phòng', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('HOLD còn hạn chiếm phòng', SQLCODE = -20001);
  END;
  v_don := tao_don(phong('105'), v_t0, v_t0 + phut(180), 'HOLD', SYSTIMESTAMP - phut(1));
  BEGIN
    v_don2 := tao_don(phong('105'), v_t0, v_t0 + phut(180));
    kiem('HOLD quá hạn không chiếm phòng', v_don2 IS NOT NULL);
  EXCEPTION WHEN OTHERS THEN
    kiem('HOLD quá hạn không chiếm phòng (lỗi ' || SQLERRM || ')', FALSE);
  END;

  -- BR-19, AC-08: thanh toán về muộn nhưng phòng đã có người đặt thì không được xác nhận lại đơn cũ
  v_don := tao_don(phong('106'), v_t0, v_t0 + phut(180), 'HOLD', SYSTIMESTAMP + phut(15));
  UPDATE dat_phong SET trang_thai = 'EXPIRED' WHERE dat_phong_id = v_don;
  v_don2 := tao_don(phong('106'), v_t0, v_t0 + phut(180));
  BEGIN
    UPDATE dat_phong SET trang_thai = 'CONFIRMED' WHERE dat_phong_id = v_don;
    kiem('EXPIRED về CONFIRMED khi phòng đã có người đặt phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('EXPIRED về CONFIRMED khi phòng đã có người đặt bị chặn (TRG_DAT_PHONG_CHIEM_LAI)', SQLCODE = -20001);
  END;

  DBMS_OUTPUT.PUT_LINE('--- Trạng thái đơn (BR-14, BR-16) ---');
  v_don := tao_don(phong('107'), v_t0, v_t0 + phut(180));
  SELECT ma_tra_cuu INTO v_ma FROM dat_phong WHERE dat_phong_id = v_don;
  kiem('mã tra cứu tự cấp dạng DPnnnnnnn', REGEXP_LIKE(v_ma, '^DP[0-9]{7}$'));
  BEGIN
    v_han := SYSTIMESTAMP + phut(15);
    UPDATE dat_phong SET trang_thai = 'HOLD', han_giu_cho = v_han WHERE dat_phong_id = v_don;
    kiem('CONFIRMED về HOLD phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('CONFIRMED về HOLD bị chặn', SQLCODE = -20003);
  END;
  UPDATE dat_phong SET trang_thai = 'CHECKED_IN', nhan_thuc_te = v_t0 WHERE dat_phong_id = v_don;
  BEGIN
    UPDATE dat_phong SET trang_thai = 'CANCELLED' WHERE dat_phong_id = v_don;
    kiem('AC-10: hủy đơn CHECKED_IN phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('AC-10: hủy đơn CHECKED_IN bị chặn', SQLCODE = -20003);
  END;
  v_han := v_t0 + phut(170);
  UPDATE dat_phong SET trang_thai = 'CHECKED_OUT', tra_thuc_te = v_han WHERE dat_phong_id = v_don;
  BEGIN
    UPDATE dat_phong SET tien_phong = 1, tong_tien = 1 + tien_vat WHERE dat_phong_id = v_don;
    kiem('đơn CHECKED_OUT không sửa tiền', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đơn CHECKED_OUT không sửa tiền (BR-16)', SQLCODE = -20003);
  END;
  BEGIN
    v_don2 := tao_don(phong('108'), v_t0, v_t0 + phut(180), 'CHECKED_IN');
    kiem('tạo đơn mới ở CHECKED_IN phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('tạo đơn mới chỉ được ở HOLD hoặc CONFIRMED', SQLCODE = -20003);
  END;

  DBMS_OUTPUT.PUT_LINE('--- Nhật ký kiểm toán (BR-46 đến BR-48) ---');
  SELECT COUNT(*) INTO v_dem FROM nhat_ky_kiem_toan WHERE bang = 'DAT_PHONG' AND khoa_dong = TO_CHAR(v_don);
  kiem('đơn có nhật ký tạo và đổi trạng thái (' || v_dem || ' dòng)', v_dem >= 3);
  SELECT COUNT(*) INTO v_dem FROM nhat_ky_kiem_toan
   WHERE bang = 'DAT_PHONG' AND khoa_dong = TO_CHAR(v_don) AND hanh_dong = 'DOI_TRANG_THAI'
     AND vai_tro = 'LE_TAN' AND kenh = 'QUAY' AND nguoi_thuc_hien_id = v_nd AND dia_chi_ip = '127.0.0.1';
  kiem('nhật ký ghi người thực hiện, vai trò, kênh, IP (BR-47)', v_dem >= 2);
  BEGIN
    UPDATE nhat_ky_kiem_toan SET ly_do = 'sua' WHERE ROWNUM = 1;
    kiem('sửa nhật ký phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('sửa nhật ký bị chặn (AUDIT_IMMUTABLE)', SQLCODE = -20030);
  END;
  BEGIN
    DELETE FROM nhat_ky_kiem_toan WHERE ROWNUM = 1;
    kiem('xóa nhật ký phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('xóa nhật ký bị chặn (AUDIT_IMMUTABLE)', SQLCODE = -20030);
  END;
  SELECT COUNT(*) INTO v_dem FROM nhat_ky_kiem_toan WHERE bang = 'NGUOI_DUNG' AND gia_tri_moi LIKE '%mat_khau_bam%';
  kiem('nhật ký người dùng không chứa mật khẩu băm', v_dem = 0);

  DBMS_OUTPUT.PUT_LINE('--- Hóa đơn (BR-44) ---');
  v_so1 := pkg_hoa_don.cap_so;  v_so2 := pkg_hoa_don.cap_so;
  kiem('số hóa đơn liên tục', v_so2 = v_so1 + 1);
  INSERT INTO hoa_don (so_hoa_don, dat_phong_id, tong_tien, nguoi_lap_id) VALUES (v_so1, v_don, 259200, v_nd)
    RETURNING hoa_don_id INTO v_hd;
  INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_dong, mo_ta, so_tien) VALUES (v_hd, 'TIEN_PHONG', 'Tiền phòng', 240000);
  BEGIN
    UPDATE hoa_don SET tong_tien = 1 WHERE hoa_don_id = v_hd;
    kiem('sửa hóa đơn phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('sửa hóa đơn bị chặn (INVOICE_IMMUTABLE)', SQLCODE = -20031);
  END;
  BEGIN
    DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id = v_hd;
    kiem('xóa dòng hóa đơn phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('xóa dòng hóa đơn bị chặn (INVOICE_IMMUTABLE)', SQLCODE = -20031);
  END;
  BEGIN   -- hóa đơn điều chỉnh phải trỏ về hóa đơn gốc
    INSERT INTO hoa_don (so_hoa_don, dat_phong_id, la_dieu_chinh, tong_tien, nguoi_lap_id) VALUES (v_so2, v_don, TRUE, -10000, v_nd);
    kiem('hóa đơn điều chỉnh thiếu hóa đơn gốc phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('hóa đơn điều chỉnh thiếu hóa đơn gốc bị chặn (CHECK)', SQLCODE = -2290);
  END;

  DBMS_OUTPUT.PUT_LINE('--- Bảng giá và tham số (BR-02, BR-04, BR-58) ---');
  BEGIN
    INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
      SELECT loai_phong_id, 'GIO', 100000, DATE '2026-01-01' FROM loai_phong WHERE ma_hang = 'SUPERIOR';
    kiem('giá giờ cho Superior phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('giá giờ chỉ cho hạng cho thuê giờ (BR-02)', SQLCODE = -20020);
  END;
  BEGIN
    UPDATE bang_gia SET don_gia = 120000
     WHERE loai_gia = 'GIO' AND loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'STANDARD');
    kiem('5 lần giá giờ vượt giá ngày phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('5 nhân 120.000 vượt giá ngày 550.000 bị chặn (BR-04, FR-28)', SQLCODE = -20022);
  END;
  BEGIN
    UPDATE bang_gia SET don_gia = 110000
     WHERE loai_gia = 'GIO' AND loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'STANDARD');
    kiem('giá giờ 110.000 (5 nhân bằng đúng giá ngày) được lưu', TRUE);
  EXCEPTION WHEN OTHERS THEN
    kiem('giá giờ 110.000 được lưu (lỗi ' || SQLERRM || ')', FALSE);
  END;
  BEGIN
    INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
      SELECT loai_phong_id, 'NGAY', 600000, DATE '2026-06-01' FROM loai_phong WHERE ma_hang = 'STANDARD';
    kiem('giá ngày chồng hiệu lực phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('giá cùng loại không được chồng ngày hiệu lực', SQLCODE = -20021);
  END;
  BEGIN
    INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so) VALUES ('THUE_SUAT_VAT', DATE '2026-06-01', 0.09);
    kiem('tham số chồng hiệu lực phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('tham số không được chồng ngày hiệu lực', SQLCODE = -20023);
  END;
  kiem('VAT ngày 20/10/2026 là 8%',  pkg_cau_hinh.lay_so('THUE_SUAT_VAT', DATE '2026-10-20') = 0.08);
  kiem('VAT ngày 31/12/2026 là 8%',  pkg_cau_hinh.lay_so('THUE_SUAT_VAT', DATE '2026-12-31') = 0.08);
  kiem('VAT ngày 01/01/2027 là 10%', pkg_cau_hinh.lay_so('THUE_SUAT_VAT', DATE '2027-01-01') = 0.10);
  kiem('khoảng đệm là 30 phút',      pkg_cau_hinh.lay_so('KHOANG_DEM_PHUT') = 30);

  DBMS_OUTPUT.PUT_LINE('--- Ràng buộc dữ liệu ---');
  BEGIN
    v_p := phong('101');
    DELETE FROM phong WHERE phong_id = v_p;
    kiem('xóa phòng đã có đơn phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('không xóa phòng đã có đơn (FR-26, ORA-02292)', SQLCODE = -2292);
  END;
  BEGIN
    INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, so_khach,
                           don_gia_ap_dung, don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu)
    VALUES (v_khach, 'NGAY', 'WEB', 'CONFIRMED', v_tuan, v_tuan_t, 1, 550000, 550000, 550000, 0.08, 44000, 594000, 'vi');
    kiem('đơn có giờ trả trước giờ nhận phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đơn có giờ trả trước giờ nhận bị chặn (CHECK)', SQLCODE = -2290);
  END;
  BEGIN
    INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, so_khach,
                           don_gia_ap_dung, don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu)
    VALUES (v_khach, 'NGAY', 'WEB', 'HOLD', v_tuan, v_tuan_s, 1, 550000, 550000, 550000, 0.08, 44000, 594000, 'vi');
    kiem('đơn HOLD không có hạn giữ chỗ phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('đơn HOLD phải có hạn giữ chỗ (CHECK)', SQLCODE = -2290);
  END;
  BEGIN
    INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, so_khach,
                           don_gia_ap_dung, don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu)
    VALUES (v_khach, 'NGAY', 'WEB', 'CONFIRMED', v_tuan, v_tuan_s, 1, 550000, 550000, 550000, 0.08, 44000, 600000, 'vi');
    kiem('tổng tiền lệch tiền phòng cộng VAT phải bị chặn', FALSE);
  EXCEPTION WHEN OTHERS THEN
    kiem('tổng tiền phải bằng tiền phòng cộng VAT (CHECK)', SQLCODE = -2290);
  END;

  DBMS_OUTPUT.PUT_LINE('=== ' || v_dat || ' đạt, ' || v_loi || ' lỗi ===');
  pkg_ngu_canh.xoa;
  ROLLBACK;
  IF v_loi > 0 THEN
    RAISE_APPLICATION_ERROR(-20999, v_loi || ' ca kiểm thử thất bại');
  END IF;
END;
/
