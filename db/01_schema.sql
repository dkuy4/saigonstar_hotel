-- =====================================================================
-- Hệ thống đặt phòng khách sạn - Oracle Database 23ai Free
-- 01_schema.sql: tạo bảng, ràng buộc, chỉ mục
-- Căn cứ: SRS v1.0 mục 10, BRD v1.4. File mã hóa UTF-8.
-- Chạy bằng SQLcl hoặc SQL*Plus, kết nối vào schema của ứng dụng (PDB FREEPDB1).
-- Quy ước: bảng và cột giữ tên tiếng Việt không dấu theo SRS (truy vết) ;
--          ràng buộc và chỉ mục đặt tên pk_, fk_, uix_, ck_, idx_ + tên bảng.
--          /*RESTRICT*/ nghĩa là ON DELETE NO ACTION (mặc định Oracle, từ chối xóa cha).
-- Thời điểm: TIMESTAMP(0) WITH TIME ZONE, API gửi kèm +07:00 (BR-07).
-- Tiền: NUMBER(15,2) đơn vị VND. Cờ: BOOLEAN (Oracle 23ai).
-- =====================================================================
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- ---------- Sequence mã tra cứu đơn (DP0000001...) ----------
CREATE SEQUENCE seq_ma_tra_cuu START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;

-- ---------- NGON_NGU ----------
CREATE TABLE ngon_ngu (
  ma_ngon_ngu   VARCHAR2(10)       NOT NULL,
  ten_ngon_ngu  VARCHAR2(50 CHAR)  NOT NULL,
  ngay_tao      TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_ngon_ngu PRIMARY KEY (ma_ngon_ngu)
);

-- ---------- VAI_TRO ----------
CREATE TABLE vai_tro (
  vai_tro_id   NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  ma_vai_tro   VARCHAR2(20)       NOT NULL,
  ten_vai_tro  VARCHAR2(50 CHAR)  NOT NULL,
  ngay_tao     TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_vai_tro PRIMARY KEY (vai_tro_id),
  CONSTRAINT uix_vai_tro_ma_vai_tro UNIQUE (ma_vai_tro),
  CONSTRAINT ck_vai_tro_ma_vai_tro CHECK (ma_vai_tro IN ('LE_TAN','BUONG_PHONG','QUAN_LY'))
);

-- ---------- NGUOI_DUNG (nhân viên; khách không có tài khoản) ----------
CREATE TABLE nguoi_dung (
  nguoi_dung_id  NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  ten_dang_nhap  VARCHAR2(50)        NOT NULL,
  mat_khau_bam   VARCHAR2(255)       NOT NULL,
  ho_ten         VARCHAR2(100 CHAR)  NOT NULL,
  vai_tro_id     NUMBER(19)          NOT NULL,
  trang_thai     VARCHAR2(20) DEFAULT 'HOAT_DONG' NOT NULL,
  so_lan_sai     NUMBER(3)    DEFAULT 0 NOT NULL,
  khoa_den       TIMESTAMP(0) WITH TIME ZONE,
  phai_doi_mat_khau BOOLEAN DEFAULT FALSE NOT NULL,
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_nguoi_dung PRIMARY KEY (nguoi_dung_id),
  CONSTRAINT uix_nguoi_dung_ten_dang_nhap UNIQUE (ten_dang_nhap),
  CONSTRAINT fk_nguoi_dung_vai_tro_id FOREIGN KEY (vai_tro_id) REFERENCES vai_tro (vai_tro_id) /*RESTRICT*/,
  CONSTRAINT ck_nguoi_dung_trang_thai CHECK (trang_thai IN ('HOAT_DONG','KHOA')),
  CONSTRAINT ck_nguoi_dung_so_lan_sai CHECK (so_lan_sai >= 0)
);

-- ---------- LOAI_PHONG (hạng phòng) ----------
CREATE TABLE loai_phong (
  loai_phong_id  NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  ma_hang        VARCHAR2(20)  NOT NULL,
  suc_chua       NUMBER(2),                       -- chờ khách hàng cung cấp (BRD mục 4.2)
  cho_thue_gio   BOOLEAN DEFAULT FALSE NOT NULL,  -- chỉ Standard bật (BR-02)
  anh_url        VARCHAR2(500),
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_loai_phong PRIMARY KEY (loai_phong_id),
  CONSTRAINT uix_loai_phong_ma_hang UNIQUE (ma_hang),
  CONSTRAINT ck_loai_phong_ma_hang CHECK (ma_hang IN ('STANDARD','SUPERIOR','DELUXE','SUITE')),
  CONSTRAINT ck_loai_phong_suc_chua CHECK (suc_chua IS NULL OR suc_chua > 0)
);

-- ---------- LOAI_PHONG_DICH (nội dung hạng phòng theo ngôn ngữ) ----------
CREATE TABLE loai_phong_dich (
  loai_phong_id  NUMBER(19)          NOT NULL,
  ngon_ngu       VARCHAR2(10)        NOT NULL,
  ten            VARCHAR2(100 CHAR)  NOT NULL,
  mo_ta          VARCHAR2(1000 CHAR),
  tien_nghi      VARCHAR2(1000 CHAR),
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_loai_phong_dich PRIMARY KEY (loai_phong_id, ngon_ngu),
  CONSTRAINT fk_loai_phong_dich_loai_phong_id FOREIGN KEY (loai_phong_id) REFERENCES loai_phong (loai_phong_id) ON DELETE CASCADE,
  CONSTRAINT fk_loai_phong_dich_ngon_ngu FOREIGN KEY (ngon_ngu) REFERENCES ngon_ngu (ma_ngon_ngu) /*RESTRICT*/
);

-- ---------- BANG_GIA ----------
CREATE TABLE bang_gia (
  bang_gia_id    NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  loai_phong_id  NUMBER(19)     NOT NULL,
  loai_gia       VARCHAR2(10)   NOT NULL,
  don_gia        NUMBER(15,2)   NOT NULL,   -- VND, đã gồm phí dịch vụ, chưa gồm VAT (D-26)
  hieu_luc_tu    DATE           NOT NULL,
  hieu_luc_den   DATE,                      -- NULL = không giới hạn
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_bang_gia PRIMARY KEY (bang_gia_id),
  CONSTRAINT fk_bang_gia_loai_phong_id FOREIGN KEY (loai_phong_id) REFERENCES loai_phong (loai_phong_id) /*RESTRICT*/,
  CONSTRAINT ck_bang_gia_loai_gia CHECK (loai_gia IN ('NGAY','GIO')),
  CONSTRAINT ck_bang_gia_don_gia CHECK (don_gia > 0),
  CONSTRAINT ck_bang_gia_hieu_luc CHECK (hieu_luc_den IS NULL OR hieu_luc_den >= hieu_luc_tu)
);

-- ---------- PHONG ----------
CREATE TABLE phong (
  phong_id        NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  ma_phong        VARCHAR2(10)  NOT NULL,
  so_tang         NUMBER(2)     NOT NULL,
  loai_phong_id   NUMBER(19)    NOT NULL,
  trang_thai      VARCHAR2(20) DEFAULT 'TRONG' NOT NULL,
  dang_hoat_dong  BOOLEAN DEFAULT TRUE NOT NULL,
  ghi_chu         VARCHAR2(500 CHAR),
  ngay_tao        TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_phong PRIMARY KEY (phong_id),
  CONSTRAINT uix_phong_ma_phong UNIQUE (ma_phong),
  CONSTRAINT fk_phong_loai_phong_id FOREIGN KEY (loai_phong_id) REFERENCES loai_phong (loai_phong_id) /*RESTRICT*/,
  CONSTRAINT ck_phong_so_tang CHECK (so_tang >= 1),
  CONSTRAINT ck_phong_trang_thai CHECK (trang_thai IN ('TRONG','DANG_O','DANG_DON','BAO_TRI'))
);

-- ---------- KHACH_HANG ----------
CREATE TABLE khach_hang (
  khach_hang_id      NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  ho_ten             VARCHAR2(100 CHAR)  NOT NULL,
  sdt                VARCHAR2(20)        NOT NULL,
  email              VARCHAR2(254)       NOT NULL,   -- lưu chữ thường để tra cứu đơn
  quoc_tich          VARCHAR2(60 CHAR),
  ngon_ngu_uu_tien   VARCHAR2(10) DEFAULT 'vi' NOT NULL,
  ngay_tao           TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_khach_hang PRIMARY KEY (khach_hang_id),
  CONSTRAINT fk_khach_hang_ngon_ngu_uu_tien FOREIGN KEY (ngon_ngu_uu_tien) REFERENCES ngon_ngu (ma_ngon_ngu) /*RESTRICT*/,
  CONSTRAINT ck_khach_hang_email CHECK (email = LOWER(email))
);

-- ---------- GIAY_TO_KHACH (giấy tờ; số giấy tờ do ứng dụng mã hóa trước khi lưu, NFR-13) ----------
CREATE TABLE giay_to_khach (
  giay_to_id     NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  khach_hang_id  NUMBER(19)     NOT NULL,
  loai_giay_to   VARCHAR2(30)   NOT NULL,
  so_giay_to     VARCHAR2(512)  NOT NULL,   -- bản mã hóa (base64)
  anh_url        VARCHAR2(500),
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_giay_to_khach PRIMARY KEY (giay_to_id),
  CONSTRAINT fk_giay_to_khach_khach_hang_id FOREIGN KEY (khach_hang_id) REFERENCES khach_hang (khach_hang_id) ON DELETE CASCADE
);

-- ---------- DAT_PHONG ----------
CREATE TABLE dat_phong (
  dat_phong_id           NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  ma_tra_cuu             VARCHAR2(20)   NOT NULL,   -- trigger tự cấp DP0000001 nếu để trống
  khach_hang_id          NUMBER(19)     NOT NULL,
  loai_dat               VARCHAR2(10)   NOT NULL,
  kenh_dat               VARCHAR2(10)   NOT NULL,
  trang_thai             VARCHAR2(20)   NOT NULL,
  tu_luc                 TIMESTAMP(0) WITH TIME ZONE NOT NULL,
  den_luc                TIMESTAMP(0) WITH TIME ZONE NOT NULL,
  han_giu_cho            TIMESTAMP(0) WITH TIME ZONE,
  so_khach               NUMBER(2)      NOT NULL,   -- bổ sung so với SRS mục 10
  don_gia_ap_dung        NUMBER(15,2)   NOT NULL,   -- đơn giá ngày hoặc giờ đã chốt (BR-42)
  don_gia_ngay_ap_dung   NUMBER(15,2)   NOT NULL,   -- giá ngày đã chốt; đơn giờ cần để tính lại khi vượt 5 giờ (BR-33, BR-34)
  tien_phong             NUMBER(15,2)   NOT NULL,
  thue_suat              NUMBER(5,4)    NOT NULL,   -- thuế suất đã chốt (BR-58)
  tien_vat               NUMBER(15,2)   NOT NULL,
  tong_tien              NUMBER(15,2)   NOT NULL,
  ngon_ngu               VARCHAR2(10)   NOT NULL,
  dong_y_chinh_sach_luc  TIMESTAMP(0) WITH TIME ZONE,  -- bổ sung: bằng chứng đồng ý (FR-05, NFR-15)
  nhan_thuc_te           TIMESTAMP(0) WITH TIME ZONE,
  tra_thuc_te            TIMESTAMP(0) WITH TIME ZONE,
  ly_do_huy              VARCHAR2(500 CHAR),
  nguoi_tao_id           NUMBER(19),                -- rỗng khi khách tự đặt trên web
  ngay_tao               TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_dat_phong PRIMARY KEY (dat_phong_id),
  CONSTRAINT uix_dat_phong_ma_tra_cuu UNIQUE (ma_tra_cuu),
  CONSTRAINT fk_dat_phong_khach_hang_id FOREIGN KEY (khach_hang_id) REFERENCES khach_hang (khach_hang_id) /*RESTRICT*/,
  CONSTRAINT fk_dat_phong_ngon_ngu FOREIGN KEY (ngon_ngu) REFERENCES ngon_ngu (ma_ngon_ngu) /*RESTRICT*/,
  CONSTRAINT fk_dat_phong_nguoi_tao_id FOREIGN KEY (nguoi_tao_id) REFERENCES nguoi_dung (nguoi_dung_id) /*RESTRICT*/,
  CONSTRAINT ck_dat_phong_loai_dat CHECK (loai_dat IN ('NGAY','GIO')),
  CONSTRAINT ck_dat_phong_kenh_dat CHECK (kenh_dat IN ('WEB','QUAY','API')),
  CONSTRAINT ck_dat_phong_trang_thai CHECK (trang_thai IN ('HOLD','CONFIRMED','CHECKED_IN','CHECKED_OUT','CANCELLED','NO_SHOW','EXPIRED')),
  CONSTRAINT ck_dat_phong_thoi_gian CHECK (den_luc > tu_luc),
  CONSTRAINT ck_dat_phong_han_giu_cho CHECK (trang_thai <> 'HOLD' OR han_giu_cho IS NOT NULL),
  CONSTRAINT ck_dat_phong_so_khach CHECK (so_khach > 0),
  CONSTRAINT ck_dat_phong_tien CHECK (don_gia_ap_dung >= 0 AND don_gia_ngay_ap_dung >= 0 AND tien_phong >= 0 AND tien_vat >= 0 AND tong_tien = tien_phong + tien_vat),
  CONSTRAINT ck_dat_phong_thue_suat CHECK (thue_suat >= 0 AND thue_suat <= 1)
);

-- ---------- DAT_PHONG_DOAN (đoạn lưu trú; kiểm tra trùng chạy trên bảng này) ----------
CREATE TABLE dat_phong_doan (
  doan_id        NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  dat_phong_id   NUMBER(19)  NOT NULL,
  phong_id       NUMBER(19)  NOT NULL,
  tu_luc         TIMESTAMP(0) WITH TIME ZONE NOT NULL,
  den_luc        TIMESTAMP(0) WITH TIME ZONE NOT NULL,
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_dat_phong_doan PRIMARY KEY (doan_id),
  CONSTRAINT fk_dat_phong_doan_dat_phong_id FOREIGN KEY (dat_phong_id) REFERENCES dat_phong (dat_phong_id) /*RESTRICT*/,
  CONSTRAINT fk_dat_phong_doan_phong_id FOREIGN KEY (phong_id) REFERENCES phong (phong_id) /*RESTRICT*/,
  CONSTRAINT ck_dat_phong_doan_thoi_gian CHECK (den_luc > tu_luc)
);

-- ---------- GIAO_DICH_THANH_TOAN ----------
CREATE TABLE giao_dich_thanh_toan (
  giao_dich_id        NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  dat_phong_id        NUMBER(19)     NOT NULL,
  kenh                VARCHAR2(10)   NOT NULL,
  phuong_thuc         VARCHAR2(20)   NOT NULL,
  so_tien             NUMBER(15,2)   NOT NULL,
  trang_thai          VARCHAR2(20) DEFAULT 'CHO_XU_LY' NOT NULL,
  ma_tham_chieu_cong  VARCHAR2(100),   -- mã giao dịch của cổng; UNIQUE để xử lý callback lặp
  ngay_giao_dich      TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  ngay_tao            TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_giao_dich_thanh_toan PRIMARY KEY (giao_dich_id),
  CONSTRAINT uix_giao_dich_thanh_toan_ma_tham_chieu_cong UNIQUE (ma_tham_chieu_cong),
  CONSTRAINT fk_giao_dich_thanh_toan_dat_phong_id FOREIGN KEY (dat_phong_id) REFERENCES dat_phong (dat_phong_id) /*RESTRICT*/,
  CONSTRAINT ck_giao_dich_thanh_toan_kenh CHECK (kenh IN ('QUAY','CONG')),
  CONSTRAINT ck_giao_dich_thanh_toan_phuong_thuc CHECK (phuong_thuc IN ('TIEN_MAT','CHUYEN_KHOAN','THE','ONLINE')),
  CONSTRAINT ck_giao_dich_thanh_toan_so_tien CHECK (so_tien > 0),
  CONSTRAINT ck_giao_dich_thanh_toan_trang_thai CHECK (trang_thai IN ('CHO_XU_LY','THANH_CONG','THAT_BAI'))
);

-- ---------- HOAN_TIEN ----------
CREATE TABLE hoan_tien (
  hoan_tien_id      NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  giao_dich_id      NUMBER(19)         NOT NULL,
  so_tien           NUMBER(15,2)       NOT NULL,
  ly_do             VARCHAR2(500 CHAR) NOT NULL,
  trang_thai        VARCHAR2(20) DEFAULT 'CHO_DUYET' NOT NULL,
  nguoi_de_nghi_id  NUMBER(19),          -- rỗng khi hệ thống tự hoàn (BR-24, BR-19)
  nguoi_duyet_id    NUMBER(19),
  ngay_tao          TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_hoan_tien PRIMARY KEY (hoan_tien_id),
  CONSTRAINT fk_hoan_tien_giao_dich_id FOREIGN KEY (giao_dich_id) REFERENCES giao_dich_thanh_toan (giao_dich_id) /*RESTRICT*/,
  CONSTRAINT fk_hoan_tien_nguoi_de_nghi_id FOREIGN KEY (nguoi_de_nghi_id) REFERENCES nguoi_dung (nguoi_dung_id) /*RESTRICT*/,
  CONSTRAINT fk_hoan_tien_nguoi_duyet_id FOREIGN KEY (nguoi_duyet_id) REFERENCES nguoi_dung (nguoi_dung_id) /*RESTRICT*/,
  CONSTRAINT ck_hoan_tien_so_tien CHECK (so_tien > 0),
  CONSTRAINT ck_hoan_tien_trang_thai CHECK (trang_thai IN ('CHO_DUYET','DA_DUYET','DA_HOAN','TU_CHOI'))
);

-- ---------- HOA_DON (nội bộ, số liên tục, không sửa sau khi lập: BR-44) ----------
CREATE TABLE hoa_don (
  hoa_don_id      NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  so_hoa_don      NUMBER(12)    NOT NULL,
  dat_phong_id    NUMBER(19)    NOT NULL,
  la_dieu_chinh   BOOLEAN DEFAULT FALSE NOT NULL,
  hoa_don_goc_id  NUMBER(19),
  tong_tien       NUMBER(15,2)  NOT NULL,   -- hóa đơn điều chỉnh có thể âm
  ngay_lap        TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  nguoi_lap_id    NUMBER(19)    NOT NULL,
  ngay_tao        TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_hoa_don PRIMARY KEY (hoa_don_id),
  CONSTRAINT uix_hoa_don_so_hoa_don UNIQUE (so_hoa_don),
  CONSTRAINT fk_hoa_don_dat_phong_id FOREIGN KEY (dat_phong_id) REFERENCES dat_phong (dat_phong_id) /*RESTRICT*/,
  CONSTRAINT fk_hoa_don_hoa_don_goc_id FOREIGN KEY (hoa_don_goc_id) REFERENCES hoa_don (hoa_don_id) /*RESTRICT*/,
  CONSTRAINT fk_hoa_don_nguoi_lap_id FOREIGN KEY (nguoi_lap_id) REFERENCES nguoi_dung (nguoi_dung_id) /*RESTRICT*/,
  CONSTRAINT ck_hoa_don_dieu_chinh CHECK ((la_dieu_chinh = TRUE AND hoa_don_goc_id IS NOT NULL) OR (la_dieu_chinh = FALSE AND hoa_don_goc_id IS NULL))
);

-- ---------- BO_DEM_HOA_DON (cấp số liên tục, không hở số; bổ sung theo SRS mục 10) ----------
CREATE TABLE bo_dem_hoa_don (
  loai           VARCHAR2(20) NOT NULL,
  gia_tri_cuoi   NUMBER(12) DEFAULT 0 NOT NULL,
  CONSTRAINT pk_bo_dem_hoa_don PRIMARY KEY (loai),
  CONSTRAINT ck_bo_dem_hoa_don_gia_tri_cuoi CHECK (gia_tri_cuoi >= 0)
);

-- ---------- CHI_TIET_HOA_DON ----------
CREATE TABLE chi_tiet_hoa_don (
  chi_tiet_id  NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  hoa_don_id   NUMBER(19)          NOT NULL,
  loai_dong    VARCHAR2(20)        NOT NULL,
  mo_ta        VARCHAR2(500 CHAR)  NOT NULL,
  so_tien      NUMBER(15,2)        NOT NULL,
  thue_suat    NUMBER(5,4),
  ngay_tao     TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_chi_tiet_hoa_don PRIMARY KEY (chi_tiet_id),
  CONSTRAINT fk_chi_tiet_hoa_don_hoa_don_id FOREIGN KEY (hoa_don_id) REFERENCES hoa_don (hoa_don_id) /*RESTRICT*/,
  CONSTRAINT ck_chi_tiet_hoa_don_loai_dong CHECK (loai_dong IN ('TIEN_PHONG','VAT','PHU_THU','GIAM_GIA','QUA_GIO')),
  CONSTRAINT ck_chi_tiet_hoa_don_thue_suat CHECK (thue_suat IS NULL OR (thue_suat >= 0 AND thue_suat <= 1))
);

-- ---------- NHAT_KY_KIEM_TOAN (chỉ thêm: BR-48, NFR-04) ----------
CREATE TABLE nhat_ky_kiem_toan (
  nhat_ky_id          NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  bang                VARCHAR2(50)   NOT NULL,
  khoa_dong           VARCHAR2(100)  NOT NULL,
  hanh_dong           VARCHAR2(30)   NOT NULL,
  gia_tri_cu          CLOB,
  gia_tri_moi         CLOB,
  ly_do               VARCHAR2(500 CHAR),
  nguoi_thuc_hien_id  NUMBER(19),          -- rỗng khi khách hoặc hệ thống thao tác
  vai_tro             VARCHAR2(20)   NOT NULL,
  kenh                VARCHAR2(20)   NOT NULL,
  dia_chi_ip          VARCHAR2(45),
  thoi_diem           TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_nhat_ky_kiem_toan PRIMARY KEY (nhat_ky_id),
  CONSTRAINT fk_nhat_ky_kiem_toan_nguoi_thuc_hien_id FOREIGN KEY (nguoi_thuc_hien_id) REFERENCES nguoi_dung (nguoi_dung_id) /*RESTRICT*/,
  CONSTRAINT ck_nhat_ky_kiem_toan_vai_tro CHECK (vai_tro IN ('KHACH','LE_TAN','BUONG_PHONG','QUAN_LY','HE_THONG')),
  CONSTRAINT ck_nhat_ky_kiem_toan_kenh CHECK (kenh IN ('WEB','QUAY','API','HE_THONG')),
  CONSTRAINT ck_nhat_ky_kiem_toan_cu CHECK (gia_tri_cu IS JSON),
  CONSTRAINT ck_nhat_ky_kiem_toan_moi CHECK (gia_tri_moi IS JSON)
);

-- ---------- TY_GIA ----------
CREATE TABLE ty_gia (
  ngoai_te         VARCHAR2(3)   NOT NULL,
  ngay_cap_nhat    DATE          NOT NULL,
  ty_gia_vnd       NUMBER(15,4)  NOT NULL,
  CONSTRAINT pk_ty_gia PRIMARY KEY (ngoai_te, ngay_cap_nhat),
  CONSTRAINT ck_ty_gia_ngoai_te CHECK (ngoai_te IN ('USD','EUR','CNY','KRW','JPY')),
  CONSTRAINT ck_ty_gia_ty_gia_vnd CHECK (ty_gia_vnd > 0)
);

-- ---------- CAU_HINH_HE_THONG (khóa ghép: tham số có nhiều phiên bản theo ngày hiệu lực) ----------
CREATE TABLE cau_hinh_he_thong (
  ma_tham_so    VARCHAR2(50)        NOT NULL,
  hieu_luc_tu   DATE                NOT NULL,
  hieu_luc_den  DATE,
  gia_tri_so    NUMBER(15,4),
  gia_tri_chu   VARCHAR2(200 CHAR),
  mo_ta         VARCHAR2(500 CHAR),
  ngay_tao      TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_cau_hinh_he_thong PRIMARY KEY (ma_tham_so, hieu_luc_tu),
  CONSTRAINT ck_cau_hinh_he_thong_hieu_luc CHECK (hieu_luc_den IS NULL OR hieu_luc_den >= hieu_luc_tu),
  CONSTRAINT ck_cau_hinh_he_thong_gia_tri CHECK ((gia_tri_so IS NOT NULL AND gia_tri_chu IS NULL) OR (gia_tri_so IS NULL AND gia_tri_chu IS NOT NULL))
);

-- ---------- NOI_DUNG_DICH (chính sách, mẫu email, mã lỗi theo ngôn ngữ) ----------
CREATE TABLE noi_dung_dich (
  ma_noi_dung  VARCHAR2(100) NOT NULL,
  ngon_ngu     VARCHAR2(10)  NOT NULL,
  noi_dung     CLOB          NOT NULL,
  ngay_tao     TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_noi_dung_dich PRIMARY KEY (ma_noi_dung, ngon_ngu),
  CONSTRAINT fk_noi_dung_dich_ngon_ngu FOREIGN KEY (ngon_ngu) REFERENCES ngon_ngu (ma_ngon_ngu) /*RESTRICT*/
);

-- ---------- HANG_DOI_EMAIL ----------
CREATE TABLE hang_doi_email (
  email_id       NUMBER(19) GENERATED ALWAYS AS IDENTITY,
  dat_phong_id   NUMBER(19)    NOT NULL,
  loai_email     VARCHAR2(30)  NOT NULL,
  ngon_ngu       VARCHAR2(10)  NOT NULL,
  trang_thai     VARCHAR2(20) DEFAULT 'CHO_GUI' NOT NULL,
  so_lan_thu     NUMBER(3)    DEFAULT 0 NOT NULL,
  lan_gui_cuoi   TIMESTAMP(0) WITH TIME ZONE,
  loi            VARCHAR2(1000 CHAR),
  ngay_tao       TIMESTAMP(0) WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_hang_doi_email PRIMARY KEY (email_id),
  CONSTRAINT fk_hang_doi_email_dat_phong_id FOREIGN KEY (dat_phong_id) REFERENCES dat_phong (dat_phong_id) /*RESTRICT*/,
  CONSTRAINT fk_hang_doi_email_ngon_ngu FOREIGN KEY (ngon_ngu) REFERENCES ngon_ngu (ma_ngon_ngu) /*RESTRICT*/,
  CONSTRAINT ck_hang_doi_email_trang_thai CHECK (trang_thai IN ('CHO_GUI','DA_GUI','LOI')),
  CONSTRAINT ck_hang_doi_email_so_lan_thu CHECK (so_lan_thu >= 0)
);

-- =====================================================================
-- Chỉ mục trên khóa ngoại (khóa ngoại nằm ở cột đầu của khóa chính thì đã có chỉ mục sẵn)
-- =====================================================================
CREATE INDEX idx_nguoi_dung_vai_tro_id          ON nguoi_dung (vai_tro_id);
CREATE INDEX idx_loai_phong_dich_ngon_ngu       ON loai_phong_dich (ngon_ngu);
CREATE INDEX idx_bang_gia_loai_phong_id         ON bang_gia (loai_phong_id, loai_gia, hieu_luc_tu);
CREATE INDEX idx_phong_loai_phong_id            ON phong (loai_phong_id);
CREATE INDEX idx_khach_hang_ngon_ngu_uu_tien    ON khach_hang (ngon_ngu_uu_tien);
CREATE INDEX idx_giay_to_khach_khach_hang_id    ON giay_to_khach (khach_hang_id);
CREATE INDEX idx_dat_phong_khach_hang_id        ON dat_phong (khach_hang_id);
CREATE INDEX idx_dat_phong_ngon_ngu             ON dat_phong (ngon_ngu);
CREATE INDEX idx_dat_phong_nguoi_tao_id         ON dat_phong (nguoi_tao_id);
CREATE INDEX idx_dat_phong_doan_dat_phong_id    ON dat_phong_doan (dat_phong_id);
-- Chỉ mục tìm phòng trống và kiểm tra trùng (BRD mục 9.2): phong_id đứng đầu nên cũng phủ khóa ngoại phong_id
CREATE INDEX idx_dat_phong_doan_phong_id        ON dat_phong_doan (phong_id, tu_luc, den_luc);
CREATE INDEX idx_giao_dich_thanh_toan_dat_phong_id ON giao_dich_thanh_toan (dat_phong_id);
CREATE INDEX idx_hoan_tien_giao_dich_id         ON hoan_tien (giao_dich_id);
CREATE INDEX idx_hoan_tien_nguoi_de_nghi_id     ON hoan_tien (nguoi_de_nghi_id);
CREATE INDEX idx_hoan_tien_nguoi_duyet_id       ON hoan_tien (nguoi_duyet_id);
CREATE INDEX idx_hoa_don_dat_phong_id           ON hoa_don (dat_phong_id);
CREATE INDEX idx_hoa_don_hoa_don_goc_id         ON hoa_don (hoa_don_goc_id);
CREATE INDEX idx_hoa_don_nguoi_lap_id           ON hoa_don (nguoi_lap_id);
CREATE INDEX idx_chi_tiet_hoa_don_hoa_don_id    ON chi_tiet_hoa_don (hoa_don_id);
CREATE INDEX idx_nhat_ky_kiem_toan_nguoi_thuc_hien_id ON nhat_ky_kiem_toan (nguoi_thuc_hien_id);
CREATE INDEX idx_noi_dung_dich_ngon_ngu         ON noi_dung_dich (ngon_ngu);
CREATE INDEX idx_hang_doi_email_dat_phong_id    ON hang_doi_email (dat_phong_id);
CREATE INDEX idx_hang_doi_email_ngon_ngu        ON hang_doi_email (ngon_ngu);

-- ---------- Chỉ mục theo truy vấn nghiệp vụ ----------
-- tra cứu đơn, đếm đơn chưa thanh toán (BR-21)
CREATE INDEX idx_khach_hang_email               ON khach_hang (email);
CREATE INDEX idx_khach_hang_sdt                 ON khach_hang (sdt);
-- tác vụ no-show, danh sách đơn theo ngày
CREATE INDEX idx_dat_phong_trang_thai_tu_luc    ON dat_phong (trang_thai, tu_luc);
-- Oracle không có chỉ mục một phần: dùng chỉ mục hàm để tác vụ hết hạn HOLD chỉ quét các đơn HOLD
CREATE INDEX idx_dat_phong_han_giu_cho          ON dat_phong (CASE WHEN trang_thai = 'HOLD' THEN han_giu_cho END);
-- trạng thái tại thời điểm (FR-47)
CREATE INDEX idx_nhat_ky_kiem_toan_bang_khoa_dong ON nhat_ky_kiem_toan (bang, khoa_dong, thoi_diem);
CREATE INDEX idx_nhat_ky_kiem_toan_thoi_diem    ON nhat_ky_kiem_toan (thoi_diem);
-- tiến trình gửi email
CREATE INDEX idx_hang_doi_email_trang_thai_ngay_tao ON hang_doi_email (trang_thai, ngay_tao);

-- ---------- Ghi chú cho bảng quan trọng ----------
COMMENT ON TABLE dat_phong_doan IS 'Đoạn lưu trú: kiểm tra trùng phòng (BR-08) chạy trên bảng này qua TRG_DAT_PHONG_DOAN_TRUNG';
COMMENT ON TABLE nhat_ky_kiem_toan IS 'Chỉ thêm. TRG_NHAT_KY_CHAN_SUA_XOA chặn UPDATE và DELETE (BR-48, NFR-04)';
COMMENT ON TABLE cau_hinh_he_thong IS 'Tham số có ngày hiệu lực; lấy giá trị qua PKG_CAU_HINH';
COMMENT ON COLUMN giay_to_khach.so_giay_to IS 'Bản mã hóa do ứng dụng tạo, không lưu rõ (NFR-13)';
COMMENT ON COLUMN loai_phong.suc_chua IS 'NULL cho đến khi khách hàng cung cấp sức chứa (BRD mục 4.2)';
