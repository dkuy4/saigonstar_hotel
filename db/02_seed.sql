-- =====================================================================
-- 02_seed.sql: dữ liệu khởi tạo theo BRD v1.4
-- Không tạo tài khoản nhân viên: mật khẩu băm do ứng dụng sinh, không để mật khẩu mẫu trong script.
-- Chạy sau 01_schema.sql và trước 03_packages.sql, 04_triggers.sql, 05_trigger_nhat_ky.sql:
-- dữ liệu khởi tạo không đi qua trigger kiểm tra giá và không sinh nhật ký. Thứ tự chuẩn xem 00_run_all.sql.
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- 7 ngôn ngữ giao diện cho khách (D-24); lễ tân, buồng phòng, quản lý dùng vi và en (D-48)
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('vi',    'Tiếng Việt');
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('en',    'English');
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('zh-CN', '中文（简体）');
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('ko',    '한국어');
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('ja',    '日本語');
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('es',    'Español');
INSERT INTO ngon_ngu (ma_ngon_ngu, ten_ngon_ngu) VALUES ('fr',    'Français');

INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('LE_TAN',      'Lễ tân');
INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('BUONG_PHONG', 'Buồng phòng');
INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('QUAN_LY',     'Quản lý');

-- 4 hạng phòng; chỉ Standard cho thuê theo giờ (BR-02). Sức chứa chờ khách hàng cung cấp.
INSERT INTO loai_phong (ma_hang, cho_thue_gio) VALUES ('STANDARD', TRUE);
INSERT INTO loai_phong (ma_hang, cho_thue_gio) VALUES ('SUPERIOR', FALSE);
INSERT INTO loai_phong (ma_hang, cho_thue_gio) VALUES ('DELUXE',   FALSE);
INSERT INTO loai_phong (ma_hang, cho_thue_gio) VALUES ('SUITE',    FALSE);

-- Tên hạng bằng vi và en. Mô tả, tiện nghi và 5 ngôn ngữ còn lại do khách hàng cung cấp (BRD mục 4.2).
INSERT INTO loai_phong_dich (loai_phong_id, ngon_ngu, ten)
  SELECT loai_phong_id, 'vi', INITCAP(ma_hang) FROM loai_phong;
INSERT INTO loai_phong_dich (loai_phong_id, ngon_ngu, ten)
  SELECT loai_phong_id, 'en', INITCAP(ma_hang) FROM loai_phong;

-- Bảng giá (D-26): VND, đã gồm phí dịch vụ, chưa gồm VAT. Thêm giá ngày trước giá giờ.
INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
  SELECT loai_phong_id, 'NGAY',  550000, DATE '2026-01-01' FROM loai_phong WHERE ma_hang = 'STANDARD';
INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
  SELECT loai_phong_id, 'NGAY',  950000, DATE '2026-01-01' FROM loai_phong WHERE ma_hang = 'SUPERIOR';
INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
  SELECT loai_phong_id, 'NGAY', 1450000, DATE '2026-01-01' FROM loai_phong WHERE ma_hang = 'DELUXE';
INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
  SELECT loai_phong_id, 'NGAY', 1950000, DATE '2026-01-01' FROM loai_phong WHERE ma_hang = 'SUITE';
INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu)
  SELECT loai_phong_id, 'GIO',    80000, DATE '2026-01-01' FROM loai_phong WHERE ma_hang = 'STANDARD';

-- 50 phòng, 5 lầu (D-09). Mã phòng là đề xuất theo BRD mục 4.1, khách hàng đối chiếu với mã đang dùng.
DECLARE
  PROCEDURE tao (p_ma VARCHAR2, p_tang NUMBER, p_hang VARCHAR2) IS
  BEGIN
    INSERT INTO phong (ma_phong, so_tang, loai_phong_id)
    VALUES (p_ma, p_tang, (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = p_hang));
  END tao;
BEGIN
  FOR i IN 1 .. 10 LOOP
    tao('1' || LPAD(i, 2, '0'), 1, 'STANDARD');   -- 101-110
    tao('2' || LPAD(i, 2, '0'), 2, 'STANDARD');   -- 201-210
    tao('3' || LPAD(i, 2, '0'), 3, 'SUPERIOR');   -- 301-310
  END LOOP;
  FOR i IN 1 .. 5 LOOP
    tao('4' || LPAD(i, 2, '0'), 4, 'SUPERIOR');   -- 401-405
    tao('5' || LPAD(i, 2, '0'), 5, 'DELUXE');     -- 501-505
  END LOOP;
  FOR i IN 6 .. 10 LOOP
    tao('4' || LPAD(i, 2, '0'), 4, 'DELUXE');     -- 406-410
    tao('5' || LPAD(i, 2, '0'), 5, 'SUITE');      -- 506-510
  END LOOP;
END;
/

-- Tham số cấu hình (NFR-20): mọi con số nghiệp vụ nằm ở đây, không nằm cứng trong mã.
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('KHOANG_DEM_PHUT',          DATE '2025-01-01', 30, 'Khoảng đệm dọn phòng sau mỗi lượt (BR-06, D-27)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('PHUT_GIU_CHO',             DATE '2025-01-01', 15, 'Thời gian giữ chỗ HOLD khi thanh toán trực tuyến (BR-17)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('NGUONG_GIO_TINH_NGAY',    DATE '2025-01-01',  5, 'Đơn theo giờ từ 1 đến ngưỡng này tính theo giờ, vượt thì tính một giá ngày (BR-04)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('BUOC_PHUT_DON_GIO',        DATE '2025-01-01', 15, 'Bước chọn giờ bắt đầu đơn theo giờ (D-47)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('SO_GIO_TOI_DA_DON_GIO',    DATE '2025-01-01', 24, 'Số giờ tối đa của đơn theo giờ (D-47)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('GIO_HUY_MIEN_PHI',        DATE '2025-01-01', 24, 'Hủy trước giờ nhận ít nhất số giờ này thì hoàn 100% (BR-24)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('GIO_CHO_NO_SHOW',         DATE '2025-01-01',  2, 'Đơn theo ngày chưa thanh toán: chờ bao nhiêu giờ sau giờ nhận thì NO_SHOW (BR-27)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('PHUT_CHO_NO_SHOW_DON_GIO', DATE '2025-01-01', 30, 'Đơn theo giờ: chờ bao nhiêu phút (D-28)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('PHUT_AN_HAN_QUA_GIO',     DATE '2025-01-01', 30, 'Ân hạn khi ở quá giờ trả (D-43)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('SO_DON_CHUA_TT_TOI_DA',    DATE '2025-01-01',  3, 'Số đơn CONFIRMED chưa thanh toán tối đa trên một email hoặc SĐT (BR-21)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('SO_LAN_DANG_NHAP_SAI_TOI_DA', DATE '2025-01-01', 5, 'Số lần đăng nhập sai tối đa trước khi khóa tạm (FR-48)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta) VALUES ('PHUT_KHOA_TAM',              DATE '2025-01-01', 15, 'Số phút khóa tạm tài khoản khi đăng nhập sai quá số lần (FR-48)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_chu, mo_ta) VALUES ('GIO_NHAN_PHONG',         DATE '2025-01-01', '14:00', 'Giờ nhận phòng của đơn theo ngày (BR-01)');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_chu, mo_ta) VALUES ('GIO_TRA_PHONG',          DATE '2025-01-01', '12:00', 'Giờ trả phòng của đơn theo ngày (BR-01)');

-- Thuế suất VAT (BR-58). Mốc 31/12/2026 và mức 10% từ 2027 là kết quả BA tra cứu, kế toán của khách hàng xác nhận
-- trước khi triển khai thật. Nếu có văn bản gia hạn thì sửa dòng bằng cách đóng dòng cũ và thêm dòng mới, không sửa đè.
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, hieu_luc_den, gia_tri_so, mo_ta)
  VALUES ('THUE_SUAT_VAT', DATE '2025-07-01', DATE '2026-12-31', 0.08, 'VAT dịch vụ lưu trú: mức giảm theo Nghị quyết 204/2025/QH15');
INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, gia_tri_so, mo_ta)
  VALUES ('THUE_SUAT_VAT', DATE '2027-01-01', 0.10, 'VAT dịch vụ lưu trú từ 01/01/2027 nếu không có văn bản gia hạn');

-- Bộ đếm số hóa đơn (BR-44)
INSERT INTO bo_dem_hoa_don (loai, gia_tri_cuoi) VALUES ('HOA_DON', 0);

COMMIT;
