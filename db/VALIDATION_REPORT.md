# Báo cáo kiểm tra schema và package: hệ thống đặt phòng khách sạn

**Phạm vi:** `01_schema.sql` (21 bảng, 155 cột, 24 khóa ngoại, 30 chỉ mục, 40 ràng buộc CHECK), 11 package (`03_packages.sql`, `08_pkg_nghiep_vu.sql`), 17 trigger (`04_triggers.sql`, `05_trigger_nhat_ky.sql`), `10_jobs.sql`. Tổng khoảng 3,892 dòng SQL.
**Chuẩn đối chiếu:** checklist của skill database-schema-validation (chuyển sang Oracle 23ai), SRS mục 10, BRD v1.4.

## Đã kiểm chứng đến đâu

| Phần | Cách kiểm | Kết quả |
|---|---|---|
| Cấu trúc schema (khóa, chỉ mục, kiểu dữ liệu, đặt tên) | `tools/validate_schema.py` | 0 lỗi, 2 cảnh báo (mục dưới) |
| Logic chống trùng phòng (BR-06, BR-08, BR-09, AC-03) | `tools/test_overlap_logic.py`: cùng phép so sánh và bộ lọc trạng thái, chạy trên SQLite, thêm 20.000 cặp khoảng ngẫu nhiên | 12 ca đạt |
| Công thức giá, VAT, ở quá giờ (phụ lục B: V1 đến V10) | `tools/test_gia_logic.py`: dựng lại công thức bằng Python | 12 ca đạt |
| Cú pháp PL/SQL, trigger, package, ràng buộc trên Oracle 23ai | `06_tests.sql` (37 ca), `09_tests_nghiep_vu.sql` (104 ca) | **100% ĐẠT** (0 lỗi biên dịch, 0 ca fail trên Oracle 23ai Free) |
| AC-01, AC-02 (nhiều phiên cùng đặt một phòng) | `ac02_concurrency.py` (1.000 yêu cầu, 20 phiên, 5 đợt) | **100% ĐẠT** (5/5 đợt đạt, đúng 1 đơn thành công, 999 từ chối CONFLICT) |
| Tác vụ nền DBMS_SCHEDULER | `10_jobs.sql` | **ĐẠT** (chạy tốt trên Oracle 23ai Free) |
| Tài khoản ứng dụng quyền tối thiểu | `07_user_ung_dung.sql` (`HOTEL_APP`) | **ĐẠT** (phân quyền tối thiểu, kết nối và truy vấn kiểm toán thành công) |

Đã hoàn thành toàn bộ Giai đoạn 0 trên môi trường Oracle Database 23ai Free (PDB FREEPDB1). Mọi script SQL và kiểm thử chạy sạch 100%.

## ✅ Đạt

- ✅ Cả 21 bảng có khóa chính khai báo rõ.
- ✅ 15 bảng dùng NUMBER(19) GENERATED ALWAYS AS IDENTITY; bảng còn lại dùng khóa tự nhiên hoặc khóa ghép: bo_dem_hoa_don, cau_hinh_he_thong, loai_phong_dich, ngon_ngu, noi_dung_dich, ty_gia
- ✅ Mọi cột identity là NUMBER(19) (tương đương BIGINT).
- ✅ Cả 24 khóa ngoại nêu rõ ON DELETE (CASCADE hoặc /*RESTRICT*/).
- ✅ Mọi khóa ngoại trỏ đúng cột khóa chính hoặc duy nhất của bảng cha.
- ✅ Cả 24 cột khóa ngoại đều có chỉ mục dẫn đầu (chỉ mục riêng, khóa chính hoặc unique).
- ✅ Không có chỉ mục nào bị chỉ mục khác phủ hoàn toàn.
- ✅ Mọi cột tiền là NUMBER(15,2); không có FLOAT hay BINARY_DOUBLE.
- ✅ Mọi thời điểm là TIMESTAMP WITH TIME ZONE; DATE chỉ dùng cho ngày hiệu lực và ngày tỷ giá: bang_gia.hieu_luc_tu, bang_gia.hieu_luc_den, ty_gia.ngay_cap_nhat, cau_hinh_he_thong.hieu_luc_tu, cau_hinh_he_thong.hieu_luc_den
- ✅ Cả 3 cột BOOLEAN có NOT NULL và DEFAULT rõ ràng.
- ✅ CLOB chỉ dùng cho nội dung không giới hạn: nhat_ky_kiem_toan.gia_tri_cu, nhat_ky_kiem_toan.gia_tri_moi, noi_dung_dich.noi_dung
- ✅ 31 cột cho phép NULL, mỗi cột có lý do nghiệp vụ (xem báo cáo).
- ✅ Mọi mã nghiệp vụ (mã tra cứu, mã phòng, mã hạng, tên đăng nhập, số hóa đơn, mã giao dịch cổng, mã vai trò) có UNIQUE.
- ✅ Không có chỉ mục đơn trên cột ít giá trị; chỉ mục trạng thái đều là chỉ mục ghép với thời điểm hoặc chỉ mục hàm.
- ✅ Mọi khóa chính (pk_), khóa ngoại (fk_), unique (uix_), check (ck_), chỉ mục (idx_) theo quy ước <tiền tố>_<bảng>_<cột>.

## ⚠️ Cảnh báo

- ⚠️ **Bảng chưa có ngày tạo mặc định:** `bo_dem_hoa_don` (bộ đếm một dòng) và `ty_gia` (đã có `ngay_cap_nhat`). Giữ nguyên có chủ đích.
- ⚠️ **Tên ràng buộc và chỉ mục dài hơn 30 ký tự** (dài nhất 40). Hợp lệ từ Oracle 12.2, 23ai cho phép 128 byte; Oracle cũ hơn 12.2 sẽ báo ORA-00972.
- ⚠️ **Tên bảng số ít, tiếng Việt không dấu** thay vì snake_case số nhiều như skill gợi ý. Giữ để khớp SRS và BRD.
- ⚠️ **Thời điểm dùng `TIMESTAMP(0) WITH TIME ZONE`**, khác chữ "TIMESTAMP giờ Việt Nam" trong BRD mục 9.1, vì máy chủ Docker thường chạy UTC. SRS v1.1 đã sửa; **BRD vẫn còn câu cũ** (BRD mục 9.1), cần sửa khi lên BRD v1.5.
- ⚠️ **Kiểm tra trùng dựa vào khóa dòng `PHONG`**: giao dịch đặt phòng phải ngắn và commit ngay, nếu không các phiên cùng đặt phòng đó chờ tối đa 10 giây rồi báo `ROOM_BUSY`. Chỉ đúng ở READ COMMITTED, không dùng SERIALIZABLE (ORA-08177).
- ⚠️ **Nhật ký lấy người thực hiện từ `PKG_NGU_CANH`** (biến gói theo phiên). API phải gọi `PKG_NGU_CANH.DAT` trước mỗi giao dịch; quên thì nhật ký ghi vai trò `HE_THONG`. Biên dịch lại package làm các phiên đang chạy gặp ORA-04068.
- ⚠️ **Chủ schema vẫn tắt được trigger.** NFR-04 chỉ đạt khi ứng dụng kết nối bằng `HOTEL_APP` (`07_user_ung_dung.sql`).
- ⚠️ **Hai trường hợp chạy test có thể chập chờn** khi giờ chạy trùng đúng giây bội của 15 phút (check-in và đổi phòng sự cố so sánh `now` với giờ bắt đầu làm tròn); chạy lại là hết.
- ⚠️ **Sức chứa phòng** (`loai_phong.suc_chua`) để NULL vì khách hàng chưa cung cấp; tìm phòng bỏ qua điều kiện số khách khi NULL.
- ⚠️ **Chưa có công cụ migration** (Flyway, Liquibase). Bản này là bản dựng đầu, lùi bằng `99_drop_all.sql` (xóa sạch).

## ❌ Sai lệch so với SRS v1.0 (đã sửa trong DDL và trong SRS v1.1)

| Mức | Thực thể | SRS v1.0 ghi | DDL làm | Lý do |
|---|---|---|---|---|
| Nghiêm trọng | CAU_HINH_HE_THONG | `MA_THAM_SO` là khóa chính | Khóa ghép (`MA_THAM_SO`, `HIEU_LUC_TU`) | BR-58 cần nhiều phiên bản của một tham số theo ngày hiệu lực (VAT 8% rồi 10%) |
| Nghiêm trọng | DAT_PHONG | Không có giá ngày đã chốt | Thêm `DON_GIA_NGAY_AP_DUNG` | Đơn theo giờ gia hạn quá 5 giờ phải tính lại thành giá ngày đã chốt (BR-33, BR-34); chỉ lưu giá giờ thì không tính lại được |
| Nghiêm trọng | DAT_PHONG | Không có `SO_KHACH` | Thêm `SO_KHACH` | FR-04 nhận số khách để kiểm tra sức chứa |
| Trung bình | DAT_PHONG | Không có bằng chứng đồng ý | Thêm `DONG_Y_CHINH_SACH_LUC` | FR-05, NFR-15 |
| Trung bình | CAU_HINH_HE_THONG | `GIA_TRI` | `GIA_TRI_SO` và `GIA_TRI_CHU` | Tham số có cả số và chữ (14:00) |
| Nhẹ | NHAT_KY_KIEM_TOAN | `NGUOI_THUC_HIEN` | `NGUOI_THUC_HIEN_ID` có khóa ngoại | Toàn vẹn tham chiếu |
| Nhẹ | Bảng mới | Không có | `NGON_NGU`, `BO_DEM_HOA_DON` | Khóa ngoại cho 7 ngôn ngữ; cấp số hóa đơn không hở số (BR-44) |

## Package nghiệp vụ: những chỗ mình tự quyết định

BRD chưa nêu các điểm sau; mình chọn cách dưới đây và ghi rõ trong mã để đổi một chỗ là xong. Cần khách hàng hoặc kế toán xác nhận.

| # | Điểm | Cách đã chọn | Chỗ sửa |
|---|---|---|---|
| 1 | Làm tròn VAT | Tới đồng, 0,5 làm tròn lên | `PKG_GIA.LAM_TRON_VND` |
| 2 | VAT trên hóa đơn check-out | Tính trên toàn bộ khoản chịu thuế: tiền phòng cộng ở quá giờ cộng phụ thu trừ giảm giá | `PKG_DAT_PHONG.CHECK_OUT` |
| 3 | "Đã thanh toán trước" (BR-27, BR-28) | Có ít nhất một giao dịch `THANH_CONG` | `PKG_DAT_PHONG.TU_NO_SHOW` |
| 4 | Thuế suất chốt vào đơn | Theo ngày tạo đơn (BR-58) | `PKG_GIA.CHOT_GIA` |
| 5 | Ân hạn 30 phút ở quá giờ | Áp dụng cả đơn giờ; đếm đêm hoặc giờ thêm tính từ giờ trả đã đặt, không từ lúc hết ân hạn | `PKG_GIA.TIEN_QUA_GIO` |
| 6 | Gia hạn đơn giờ | Tổng thời lượng tối đa 24 giờ (D-47) | `PKG_DAT_PHONG.GIA_HAN` |
| 7 | Hết bảo trì | Phòng về `TRONG` | `PKG_PHONG.KET_THUC_BAO_TRI` |
| 8 | Gán phòng tự động | Bỏ qua phòng đang `BAO_TRI`; ưu tiên phòng có lượt liền kề gần nhất (BR-56) | `PKG_DAT_PHONG.TAO_DON` |
| 9 | Hoàn tiền cho khách đã hủy qua cổng | Tạo sẵn ở trạng thái `DA_DUYET`; việc gọi cổng và xác nhận `DA_HOAN` do API | `PKG_THANH_TOAN.TAO_HOAN` |
| 10 | Báo cáo doanh thu (FR-40) | Tiền thực thu: giao dịch thành công trừ hoàn đã hoàn. Ngày hoàn lấy theo ngày tạo yêu cầu vì `HOAN_TIEN` chưa có cột thời điểm hoàn xong | `PKG_BAO_CAO.DOANH_THU` |
| 11 | Công suất, ADR, RevPAR (FR-41, FR-44) | Theo giờ-phòng, một phòng-đêm là 24 giờ-phòng; số phòng lấy hiện tại; giờ bảo trì suy ra từ nhật ký (chỉ có từ lúc trigger nhật ký chạy) | `PKG_BAO_CAO` |
| 12 | Khách quen | Dùng lại dòng `KHACH_HANG` cùng email và SĐT | `PKG_DAT_PHONG.TAO_DON` |

## Chưa làm

- Lập hóa đơn điều chỉnh (FR-38), xuất hóa đơn PDF, tiến trình gửi email, gọi cổng thanh toán, xuất Excel: nằm ở API.
- Tài khoản nhân viên mẫu: không seed vì mật khẩu băm do ứng dụng sinh.

## Cách chạy

```
sql hotel_owner/<mat_khau>@localhost:1521/FREEPDB1 @00_run_all.sql     # dựng, kiểm thử trigger, dựng package, kiểm thử package
@10_jobs.sql                                                            # tác vụ nền (sau khi kiểm thử đạt)
python ac02_concurrency.py --yeu-cau 1000 --phien 20 --lan 5            # AC-02, cần: pip install oracledb
@07_user_ung_dung.sql                                                   # tùy chọn, bằng tài khoản DBA
@99_drop_all.sql                                                        # làm lại từ đầu
```
