import oracledb

def fix_translations():
    conn = oracledb.connect(
        user="hotel_app",
        password="HotelApp123#",
        dsn="localhost:1521/FREEPDB1"
    )
    with conn.cursor() as cur:
        cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
        
        # Standard
        cur.execute("""
            UPDATE loai_phong_dich SET
              ten = :ten,
              mo_ta = :mo_ta,
              tien_nghi = :tien_nghi
            WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'STANDARD') AND ngon_ngu = 'vi'
        """, {
            "ten": "Phòng Tiêu Chuẩn (Standard)",
            "mo_ta": "Phòng tiêu chuẩn ấm cúng, đầy đủ tiện nghi thiết yếu, thích hợp cho khách công tác hoặc lưu trú ngắn hạn và thuê theo giờ.",
            "tien_nghi": "Wifi tốc độ cao, Smart TV 43 inch, Điều hòa 2 chiều, Bàn làm việc, Bình nóng lạnh, Máy sấy tóc"
        })
        
        # Superior
        cur.execute("""
            UPDATE loai_phong_dich SET
              ten = :ten,
              mo_ta = :mo_ta,
              tien_nghi = :tien_nghi
            WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'SUPERIOR') AND ngon_ngu = 'vi'
        """, {
            "ten": "Phòng Cao Cấp (Superior)",
            "mo_ta": "Phòng cao cấp không gian thoáng đãng với ban công nhìn ra cảnh quan thành phố, trang bị nội thất gỗ sang trọng.",
            "tien_nghi": "Wifi tốc độ cao, Smart TV 50 inch, Minibar, Ban công ngắm cảnh, Bồn tắm nằm, Két an toàn"
        })
        
        # Deluxe
        cur.execute("""
            UPDATE loai_phong_dich SET
              ten = :ten,
              mo_ta = :mo_ta,
              tien_nghi = :tien_nghi
            WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'DELUXE') AND ngon_ngu = 'vi'
        """, {
            "ten": "Phòng Sang Trọng (Deluxe)",
            "mo_ta": "Phòng Deluxe rộng rãi ở tầng cao với tầm nhìn toàn cảnh, thiết kế tinh tế mang lại trải nghiệm nghỉ dưỡng hoàn hảo.",
            "tien_nghi": "Giường King-size đệm lò xo túi, Sofa thư giãn, View toàn cảnh thành phố, Máy pha cà phê espresso, Bồn tắm kính"
        })
        
        # Suite
        cur.execute("""
            UPDATE loai_phong_dich SET
              ten = :ten,
              mo_ta = :mo_ta,
              tien_nghi = :tien_nghi
            WHERE loai_phong_id = (SELECT loai_phong_id FROM loai_phong WHERE ma_hang = 'SUITE') AND ngon_ngu = 'vi'
        """, {
            "ten": "Phòng Thượng Hạng (Suite)",
            "mo_ta": "Phòng Suite thượng hạng với phòng khách và phòng ngủ riêng biệt, bồn sục Jacuzzi đẳng cấp và dịch vụ đặc quyền.",
            "tien_nghi": "Căn hộ cao cấp 55m², Phòng khách riêng biệt, Bồn sục Jacuzzi, Bếp ăn mini, Dịch vụ phòng 24/7"
        })
        
        conn.commit()
        print("Updated Vietnamese room translations successfully!")

if __name__ == "__main__":
    fix_translations()
