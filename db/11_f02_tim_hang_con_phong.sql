-- =====================================================================
-- F02: Bổ sung kiểu dữ liệu và hàm TIM_HANG_CON_PHONG vào PKG_DAT_PHONG
-- =====================================================================
ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER;

-- 1. Tạo các kiểu đối tượng
CREATE OR REPLACE TYPE t_hang_con_phong AS OBJECT (
  loai_phong_id NUMBER(19),
  ma_hang       VARCHAR2(20),
  so_phong_con  NUMBER,
  don_gia       NUMBER(15,2),
  don_gia_ngay  NUMBER(15,2),
  tien_phong    NUMBER(15,2),
  thue_suat     NUMBER(5,4),
  tien_vat      NUMBER(15,2),
  tong_tien     NUMBER(15,2),
  suc_chua      NUMBER(2),
  cho_thue_gio  VARCHAR2(5),
  anh_url       VARCHAR2(500)
);
/

CREATE OR REPLACE TYPE t_hang_con_phong_tab AS TABLE OF t_hang_con_phong;
/

GRANT EXECUTE ON t_hang_con_phong TO hotel_app;
GRANT EXECUTE ON t_hang_con_phong_tab TO hotel_app;
GRANT SELECT ON ty_gia TO hotel_app;
GRANT SELECT ON loai_phong TO hotel_app;
GRANT SELECT ON loai_phong_dich TO hotel_app;
GRANT SELECT ON bang_gia TO hotel_app;

-- 2. Thêm seed tỷ giá
MERGE INTO ty_gia t
USING (
  SELECT 'USD' AS ngoai_te, TRUNC(SYSDATE) AS ngay_cap_nhat, 25450.0000 AS ty_gia_vnd FROM dual UNION ALL
  SELECT 'EUR', TRUNC(SYSDATE), 27200.0000 FROM dual UNION ALL
  SELECT 'CNY', TRUNC(SYSDATE),  3520.0000 FROM dual UNION ALL
  SELECT 'KRW', TRUNC(SYSDATE),    18.5000 FROM dual UNION ALL
  SELECT 'JPY', TRUNC(SYSDATE),   168.0000 FROM dual
) s ON (t.ngoai_te = s.ngoai_te AND t.ngay_cap_nhat = s.ngay_cap_nhat)
WHEN NOT MATCHED THEN
  INSERT (ngoai_te, ngay_cap_nhat, ty_gia_vnd)
  VALUES (s.ngoai_te, s.ngay_cap_nhat, s.ty_gia_vnd)
WHEN MATCHED THEN
  UPDATE SET ty_gia_vnd = s.ty_gia_vnd;

-- 3. Cập nhật thông tin hạng phòng và bản dịch
UPDATE loai_phong SET suc_chua = 2, anh_url = '/images/rooms/standard.jpg' WHERE ma_hang = 'STANDARD';
UPDATE loai_phong SET suc_chua = 3, anh_url = '/images/rooms/superior.jpg' WHERE ma_hang = 'SUPERIOR';
UPDATE loai_phong SET suc_chua = 4, anh_url = '/images/rooms/deluxe.jpg' WHERE ma_hang = 'DELUXE';
UPDATE loai_phong SET suc_chua = 4, anh_url = '/images/rooms/suite.jpg' WHERE ma_hang = 'SUITE';

-- Cập nhật bản dịch tiếng Việt
UPDATE loai_phong_dich SET
  ten = 'Phòng Tiêu Chuẩn (Standard)',
  mo_ta = 'Phòng tiêu chuẩn ấm cúng, đầy đủ tiện nghi thiết yếu, thích hợp cho khách công tác hoặc lưu trú ngắn hạn và thuê theo giờ.',
  tien_nghi = 'Wifi tốc độ cao, Smart TV 43 inch, Điều hòa 2 chiều, Bàn làm việc, Bình nóng lạnh, Máy sấy tóc'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'STANDARD') AND ngon_ngu = 'vi';

UPDATE loai_phong_dich SET
  ten = 'Phòng Cao Cấp (Superior)',
  mo_ta = 'Phòng cao cấp không gian thoáng đãng với ban công nhìn ra cảnh quan thành phố, trang bị nội thất gỗ sang trọng.',
  tien_nghi = 'Wifi tốc độ cao, Smart TV 50 inch, Minibar, Ban công ngắm cảnh, Bồn tắm nằm, Két an toàn'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'SUPERIOR') AND ngon_ngu = 'vi';

UPDATE loai_phong_dich SET
  ten = 'Phòng Sang Trọng (Deluxe)',
  mo_ta = 'Phòng Deluxe rộng rãi ở tầng cao với tầm nhìn toàn cảnh, thiết kế tinh tế mang lại trải nghiệm nghỉ dưỡng hoàn hảo.',
  tien_nghi = 'Giường King-size đệm lò xo túi, Sofa thư giãn, View toàn cảnh thành phố, Máy pha cà phê espresso, Bồn tắm kính'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'DELUXE') AND ngon_ngu = 'vi';

UPDATE loai_phong_dich SET
  ten = 'Phòng Thượng Hạng (Suite)',
  mo_ta = 'Phòng Suite thượng hạng với phòng khách và phòng ngủ riêng biệt, bồn sục Jacuzzi đẳng cấp và dịch vụ đặc quyền.',
  tien_nghi = 'Căn hộ cao cấp 55m², Phòng khách riêng biệt, Bồn sục Jacuzzi, Bếp ăn mini, Dịch vụ phòng 24/7'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'SUITE') AND ngon_ngu = 'vi';

-- Cập nhật bản dịch tiếng Anh
UPDATE loai_phong_dich SET
  ten = 'Standard Room',
  mo_ta = 'Cozy standard room with essential modern amenities, perfect for business travelers or short stays and hourly rental.',
  tien_nghi = 'High-speed Wi-Fi, 43-inch Smart TV, Air conditioning, Work desk, Hot water shower, Hairdryer'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'STANDARD') AND ngon_ngu = 'en';

UPDATE loai_phong_dich SET
  ten = 'Superior Room',
  mo_ta = 'Spacious superior room featuring private city-view balcony and elegant wooden furnishings.',
  tien_nghi = 'High-speed Wi-Fi, 50-inch Smart TV, Minibar, Scenic balcony, Bathtub, Safe box'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'SUPERIOR') AND ngon_ngu = 'en';

UPDATE loai_phong_dich SET
  ten = 'Deluxe Room',
  mo_ta = 'Luxurious Deluxe room located on high floors offering panoramic city skyline views and ultimate comfort.',
  tien_nghi = 'King-size premium bed, Lounge sofa, Panoramic skyline view, Espresso machine, Glass-enclosed bathtub'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'DELUXE') AND ngon_ngu = 'en';

UPDATE loai_phong_dich SET
  ten = 'Executive Suite',
  mo_ta = 'Executive suite with private living room and bedroom, Jacuzzi bathtub, and VIP hospitality services.',
  tien_nghi = '55sqm luxury layout, Separate living room, Private Jacuzzi, Kitchenette, 24/7 Butler concierge'
WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'SUITE') AND ngon_ngu = 'en';

COMMIT;
