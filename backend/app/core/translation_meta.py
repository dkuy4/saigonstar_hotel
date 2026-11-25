"""
Metadata định nghĩa danh mục nội dung bản dịch chính sách và mẫu email (F16.5, FR-33, BR-55).
"""
from typing import Dict, List, Any

SUPPORTED_LANGUAGES = [
    {"code": "vi", "name": "Tiếng Việt", "is_primary": True},
    {"code": "en", "name": "English", "is_primary": True},
    {"code": "zh-CN", "name": "中文（简体）", "is_primary": False},
    {"code": "ko", "name": "한국어", "is_primary": False},
    {"code": "ja", "name": "日本語", "is_primary": False},
    {"code": "es", "name": "Español", "is_primary": False},
    {"code": "fr", "name": "Français", "is_primary": False},
]

TRANSLATION_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # 1. Chính sách
    "CHINH_SACH_HUY": {
        "loai": "CHINH_SACH",
        "tieu_de": "Chính sách hủy phòng",
        "mo_ta": "Điều kiện hủy phòng và hoàn tiền theo BR-24 (trước 24h hoàn 100%, dưới 24h không hoàn)",
        "bien_bat_buoc": [],
    },
    "CHINH_SACH_NO_SHOW": {
        "loai": "CHINH_SACH",
        "tieu_de": "Chính sách khách không đến (No-show)",
        "mo_ta": "Quy định xử lý phòng khi khách không đến nhận phòng (BR-27, BR-28)",
        "bien_bat_buoc": [],
    },
    "CHINH_SACH_CHUNG": {
        "loai": "CHINH_SACH",
        "tieu_de": "Quy định chung & Nhận trả phòng",
        "mo_ta": "Giờ nhận phòng chuẩn (14:00), trả phòng (12:00), giấy tờ tùy thân và nội quy lưu trú",
        "bien_bat_buoc": [],
    },

    # 2. Mẫu email theo Phụ lục C của BRD
    "EMAIL_XAC_NHAN": {
        "loai": "EMAIL",
        "tieu_de": "Mẫu email xác nhận đặt phòng",
        "mo_ta": "Gửi tự động cho khách khi đơn đặt phòng chuyển sang trạng thái CONFIRMED",
        "bien_bat_buoc": [
            "{ma_don}",
            "{ten_khach}",
            "{ten_hang}",
            "{thoi_gian_nhan}",
            "{thoi_gian_tra}",
            "{tong_tien}",
            "{link_tra_cuu}",
        ],
    },
    "EMAIL_THAY_DOI_DON": {
        "loai": "EMAIL",
        "tieu_de": "Mẫu email thay đổi đơn đặt phòng",
        "mo_ta": "Gửi khi có sự thay đổi về ngày, giờ, phòng hoặc gia hạn lưu trú",
        "bien_bat_buoc": [
            "{ma_don}",
            "{ten_khach}",
            "{thong_tin_cu}",
            "{thong_tin_moi}",
            "{chenh_lech}",
        ],
    },
    "EMAIL_HUY_HOAN_TIEN": {
        "loai": "EMAIL",
        "tieu_de": "Mẫu email hủy đơn và hoàn tiền",
        "mo_ta": "Gửi khi đơn bị hủy và hệ thống tạo lệnh hoàn tiền cho khách theo chính sách",
        "bien_bat_buoc": [
            "{ma_don}",
            "{ten_khach}",
            "{tien_hoan}",
            "{phuong_thuc}",
            "{thoi_gian_du_kien}",
        ],
    },
    "EMAIL_HET_HAN_GIU_CHO": {
        "loai": "EMAIL",
        "tieu_de": "Mẫu email hết hạn giữ chỗ",
        "mo_ta": "Gửi khi đơn HOLD hết thời gian thanh toán và tự động chuyển sang EXPIRED",
        "bien_bat_buoc": [
            "{ma_don}",
            "{ten_khach}",
            "{link_dat_lai}",
        ],
    },
    "EMAIL_THANH_TOAN_VE_MUON": {
        "loai": "EMAIL",
        "tieu_de": "Mẫu email xử lý thanh toán về muộn",
        "mo_ta": "Gửi khi giao dịch thanh toán hoàn tất sau khi đơn đã hết hạn giữ chỗ (BR-19)",
        "bien_bat_buoc": [
            "{ma_don}",
            "{ten_khach}",
            "{noi_dung_xu_ly}",
        ],
    },
}

# Dữ liệu mặc định mẫu phục vụ khởi tạo khi bảng rỗng
DEFAULT_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "CHINH_SACH_HUY": {
        "vi": "CHÍNH SÁCH HỦY PHÒNG (BR-24):\n1. Hủy phòng trước giờ nhận phòng từ 24 giờ trở lên: Quý khách được hoàn 100% số tiền đã thanh toán (bao gồm thuế VAT).\n2. Hủy phòng khi còn dưới 24 giờ tính đến giờ nhận phòng: Không áp dụng hoàn tiền.\n3. Tiền hoàn sẽ được chuyển về đúng phương thức thanh toán ban đầu của quý khách.",
        "en": "CANCELLATION POLICY (BR-24):\n1. Cancellation 24 hours or more prior to standard check-in time: 100% refund of the total amount paid (including VAT).\n2. Cancellation less than 24 hours prior to standard check-in time: Non-refundable.\n3. Refunds will be processed back to the original payment method.",
        "zh-CN": "取消政策 (BR-24)：\n1. 入住前24小时或更早取消：退还已付金额的100%（含增值税）。\n2. 入住前24小时内取消：不予退款。\n3. 退款将退回原付款方式。",
        "ko": "취소 정책 (BR-24):\n1. 체크인 시간 24시간 이전 취소: 결제 금액 100% 전액 환불(VAT 포함).\n2. 체크인 시간 24시간 미만 취소: 환불 불가.\n3. 환불은 원래 결제하신 수단으로 진행됩니다.",
        "ja": "キャンセルポリシー (BR-24):\n1. チェックインの24時間前までのキャンセル: お支払い金額の100%を返金いたします(VAT含む)。\n2. チェックインまで24時間未満のキャンセル: 返金不可となります。\n3. 返金は元のお支払い方法へ行われます。",
        "es": "POLÍTICA DE CANCELACIÓN (BR-24):\n1. Cancelación con 24 horas o más de anticipación al check-in: Reembolso del 100% del monto pagado (incluido IVA).\n2. Cancelación con menos de 24 horas de anticipación: No reembolsable.\n3. Los reembolsos se procesarán al método de pago original.",
        "fr": "POLITIQUE D'ANNULATION (BR-24):\n1. Annulation effectuée 24 heures ou plus avant l'arrivée: Remboursement à 100% du montant payé (TVA incluse).\n2. Annulation effectuée moins de 24 heures avant l'arrivée: Non remboursable.\n3. Les remboursements seront effectués sur le moyen de paiement d'origine.",
    },
    "CHINH_SACH_NO_SHOW": {
        "vi": "CHÍNH SÁCH KHÁCH KHÔNG ĐẾN (NO-SHOW):\n1. Đơn chưa thanh toán trước: Tự động chuyển trạng thái NO_SHOW và nhả phòng sau 2 giờ kể từ giờ nhận chuẩn (đối với đơn ngày) hoặc sau 30 phút (đối với đơn theo giờ).\n2. Đơn đã thanh toán trước: Khách sạn giữ phòng cho quý khách đến 12:00 trưa ngày kế tiếp (đơn ngày) hoặc hết khung giờ thuê (đơn giờ). Sau thời gian này, phòng sẽ được giải phóng và không hoàn tiền.",
        "en": "NO-SHOW POLICY:\n1. Unpaid bookings: Automatically marked as NO_SHOW and room released after 2 hours past standard check-in (daily stay) or 30 minutes (hourly stay).\n2. Prepaid bookings: Room is held until 12:00 PM next day (daily stay) or until reserved slot ends (hourly stay). Non-refundable thereafter.",
        "zh-CN": "未入住政策 (NO-SHOW)：\n1. 未付款预订：超过标准入住时间2小时（日租）或30分钟（时租）后自动标记为未入住并释放客房。\n2. 已付款预订：客房将保留至次日中午12:00（日租）或预订时段结束。逾期不予退款。",
        "ko": "노쇼(No-Show) 정책:\n1. 미결제 예약: 표준 체크인 시간으로부터 2시간(일박) 또는 30분(대실) 경과 시 자동 노쇼 처리 및 객실 배정이 취소됩니다.\n2. 사전 결제 예약: 익일 낮 12:00(일박) 또는 예약 종료 시간(대실)까지 객실이 유지되며, 이후 취소 시 환불되지 않습니다.",
        "ja": "ノーショーポリシー (不泊):\n1. 未払い予約: チェックイン時刻から2時間(日泊)または30分(時間泊)経過後に自動的にノーショー処理され、客室は解放されます。\n2. 事前決済予約: 翌日正午12:00(日泊)または予約枠終了まで客室を確保いたします。以降の返金はございません。",
        "es": "POLÍTICA DE NO PRESENTACIÓN (NO-SHOW):\n1. Reservas no pagadas: Se marcarán como NO_SHOW y se liberará la habitación tras 2 horas de retraso (estancia diaria) o 30 minutos (por horas).\n2. Reservas prepagadas: Se retiene la habitación hasta las 12:00 del día siguiente. No reembolsable posteriormente.",
        "fr": "POLITIQUE DE NON-PRÉSENTATION (NO-SHOW):\n1. Réservations non payées: Marqué comme NO_SHOW et chambre libérée après 2 heures (séjour à la journée) ou 30 minutes (séjour à l'heure).\n2. Réservations prépayées: Chambre conservée jusqu'à 12h00 le lendemain. Non remboursable par la suite.",
    },
    "CHINH_SACH_CHUNG": {
        "vi": "QUY ĐỊNH CHUNG & LƯU TRÚ:\n1. Giờ nhận phòng chuẩn: 14:00. Giờ trả phòng chuẩn: 12:00.\n2. Quý khách vui lòng xuất trình Căn cước công dân hoặc Hộ chiếu hợp lệ khi làm thủ tục nhận phòng.\n3. Khách sạn nghiêm cấm hút thuốc trong phòng và mang chất cấm, vũ khí, thú cưng vào khuôn viên khách sạn.",
        "en": "GENERAL TERMS & STAY CONDITIONS:\n1. Standard check-in: 14:00. Standard check-out: 12:00.\n2. Please present a valid National ID or Passport upon check-in.\n3. Smoking in guest rooms, possession of illegal substances, weapons, and pets are strictly prohibited on hotel premises.",
        "zh-CN": "通用条款与住宿须知：\n1. 标准入住时间：14:00。标准退房时间：12:00。\n2. 办理入住时请出示有效身份证件或护照。\n3. 酒店客房内严禁吸烟，严禁携带违禁品、武器或宠物入内。",
        "ko": "일반 이용 규정 및 안내:\n1. 표준 체크인: 14:00. 표준 체크아웃: 12:00.\n2. 체크인 시 유효한 신분증 또는 여권을 제시해 주시기 바랍니다.\n3. 객실 내 흡연, 유해 물질 및 무기류 반입, 반려동물 동반은 엄격히 금지됩니다.",
        "ja": "ご利用規約・宿泊案内:\n1. 標準チェックイン時刻: 14:00。標準チェックアウト時刻: 12:00。\n2. チェックイン時に身分証明書またはパスポートをご提示ください。\n3. 客室内での喫煙、危険物やペットの持ち込みは固くお断りいたします。",
        "es": "TÉRMINOS GENERALES Y ESTANCIA:\n1. Check-in estándar: 14:00. Check-out estándar: 12:00.\n2. Por favor presente documento de identidad o pasaporte válido al registrarse.\n3. Se prohíbe fumar en las habitaciones, así como ingresar sustancias ilícitas, armas o mascotas.",
        "fr": "CONDITIONS GÉNÉRALES DU SÉJOUR:\n1. Arrivée standard: 14h00. Départ standard: 12h00.\n2. Veuillez présenter une pièce d'identité ou un passeport valide lors de l'enregistrement.\n3. Il est strictement interdit de fumer dans les chambres ou d'introduire des substances illicites, armes ou animaux.",
    },
    "EMAIL_XAC_NHAN": {
        "vi": "Kính gửi quý khách {ten_khach},\n\nKhách sạn Sài Gòn Star xin chân thành cảm ơn quý khách đã tin tưởng lựa chọn dịch vụ của chúng tôi. Đơn đặt phòng của quý khách đã được XÁC NHẬN thành công với thông tin chi tiết như sau:\n\n- Mã đặt phòng: {ma_don}\n- Hạng phòng: {ten_hang}\n- Thời gian nhận phòng: {thoi_gian_nhan}\n- Thời gian trả phòng: {thoi_gian_tra}\n- Tổng thanh toán: {tong_tien}\n\nQuý khách có thể quản lý và tra cứu đơn bất cứ lúc nào tại liên kết sau:\n{link_tra_cuu}\n\nTrân trọng cảm ơn và hân hạnh được đón tiếp quý khách!",
        "en": "Dear {ten_khach},\n\nThank you for choosing Saigon Star Hotel. Your reservation has been CONFIRMED with the following details:\n\n- Booking Code: {ma_don}\n- Room Type: {ten_hang}\n- Check-in Time: {thoi_gian_nhan}\n- Check-out Time: {thoi_gian_tra}\n- Total Paid: {tong_tien}\n\nYou can review and manage your reservation at:\n{link_tra_cuu}\n\nWe look forward to welcoming you soon!",
        "zh-CN": "尊敬的 {ten_khach}，\n\n感谢您选择西贡之星酒店。您的预订已确认成功，预订详情如下：\n\n- 预订编号：{ma_don}\n- 房型：{ten_hang}\n- 入住时间：{thoi_gian_nhan}\n- 退房时间：{thoi_gian_tra}\n- 总计金额：{tong_tien}\n\n您可以随时点击下方链接查看和管理您的订单：\n{link_tra_cuu}\n\n西贡之星酒店热忱期待您的光临！",
        "ko": "{ten_khach} 고객님께,\n\n사이공 스타 호텔을 이용해 주셔서 진심으로 감사드립니다. 예약이 성공적으로 확정되었습니다.\n\n- 예약 번호: {ma_don}\n- 객실 유형: {ten_hang}\n- 체크인 시간: {thoi_gian_nhan}\n- 체크아웃 시간: {thoi_gian_tra}\n- 총 결제 금액: {tong_tien}\n\n아래 링크에서 언제든지 예약 세부 사항을 확인하실 수 있습니다:\n{link_tra_cuu}\n\n고객님을 모시게 되어 영광입니다.",
        "ja": "{ten_khach} 様\n\nサイゴンスターホテルをご利用いただき、誠にありがとうございます。以下の通りご予約が確定いたしました。\n\n- 予約番号: {ma_don}\n- お部屋タイプ: {ten_hang}\n- チェックイン日時: {thoi_gian_nhan}\n- チェックアウト日時: {thoi_gian_tra}\n- 合計金額: {tong_tien}\n\n以下のリンクよりいつでも予約内容をご確認・管理いただけます:\n{link_tra_cuu}\n\n皆様のお越しを心よりお待ち申し上げております。",
        "es": "Estimado/a {ten_khach},\n\nGracias por elegir Saigon Star Hotel. Su reserva ha sido CONFIRMADA con los siguientes detalles:\n\n- Código de reserva: {ma_don}\n- Tipo de habitación: {ten_hang}\n- Fecha/Hora de entrada: {thoi_gian_nhan}\n- Fecha/Hora de salida: {thoi_gian_tra}\n- Total pagado: {tong_tien}\n\nPuede gestionar su reserva en cualquier momento en:\n{link_tra_cuu}\n\n¡Esperamos darle la bienvenida pronto!",
        "fr": "Cher/Chère {ten_khach},\n\nMerci d'avoir choisi le Saigon Star Hotel. Votre réservation est CONFIRMÉE avec les informations suivantes:\n\n- Numéro de réservation: {ma_don}\n- Type d'hébergement: {ten_hang}\n- Arrivée: {thoi_gian_nhan}\n- Départ: {thoi_gian_tra}\n- Total payé: {tong_tien}\n\nConsultez et gérez votre réservation à tout moment via ce lien:\n{link_tra_cuu}\n\nNous nous réjouissons de vous accueillir!",
    },
    "EMAIL_THAY_DOI_DON": {
        "vi": "Kính gửi quý khách {ten_khach},\n\nKhách sạn Sài Gòn Star xin thông báo đơn đặt phòng mã {ma_don} của quý khách đã được điều chỉnh thành công:\n\n- Thông tin trước thay đổi: {thong_tin_cu}\n- Thông tin mới cập nhật: {thong_tin_moi}\n- Chênh lệch thanh toán phát sinh: {chenh_lech}\n\nNếu cần thêm hỗ trợ, quý khách vui lòng liên hệ bộ phận Lễ tân khách sạn.",
        "en": "Dear {ten_khach},\n\nPlease be advised that your reservation {ma_don} at Saigon Star Hotel has been modified:\n\n- Previous details: {thong_tin_cu}\n- Updated details: {thong_tin_moi}\n- Price adjustment: {chenh_lech}\n\nPlease contact our reception desk should you require any further assistance.",
        "zh-CN": "尊敬的 {ten_khach}，\n\n您在西贡之星酒店的预订 {ma_don} 已成功修改：\n\n- 原预订信息：{thong_tin_cu}\n- 更新后信息：{thong_tin_moi}\n- 费用变动：{chenh_lech}\n\n如需任何进一步帮助，请随时联系酒店前台。",
        "ko": "{ten_khach} 고객님께,\n\n예약 번호 {ma_don}의 예약 내역이 다음과 같이 성공적으로 변경되었습니다:\n\n- 이전 정보: {thong_tin_cu}\n- 변경된 정보: {thong_tin_moi}\n- 차액 정산: {chenh_lech}\n\n추가 문의 사항은 호텔 프런트 데스크로 연락해 주시기 바랍니다.",
        "ja": "{ten_khach} 様\n\nサイゴンスターホテルでのご予約 (予約番号: {ma_don}) の変更が完了いたしました:\n\n- 変更前の内容: {thong_tin_cu}\n- 変更後の内容: {thong_tin_moi}\n- 差額のご案内: {chenh_lech}\n\nご不明な点がございましたら、フロントデスクまでお気軽にお問い合わせください。",
        "es": "Estimado/a {ten_khach},\n\nLe informamos que su reserva {ma_don} en Saigon Star Hotel ha sido modificada:\n\n- Detalles anteriores: {thong_tin_cu}\n- Nuevos detalles: {thong_tin_moi}\n- Ajuste de tarifa: {chenh_lech}\n\nContáctenos si necesita asistencia adicional.",
        "fr": "Cher/Chère {ten_khach},\n\nVotre réservation {ma_don} au Saigon Star Hotel a bien été modifiée:\n\n- Détails précédents: {thong_tin_cu}\n- Nouveaux détails: {thong_tin_moi}\n- Différence tarifaire: {chenh_lech}\n\nContactez notre réception pour toute assistance complémentaire.",
    },
    "EMAIL_HUY_HOAN_TIEN": {
        "vi": "Kính gửi quý khách {ten_khach},\n\nKhách sạn Sài Gòn Star xin thông báo đơn đặt phòng mã {ma_don} đã được HỦY theo yêu cầu của quý khách:\n\n- Số tiền hoàn lại: {tien_hoan}\n- Phương thức hoàn tiền: {phuong_thuc}\n- Thời gian dự kiến nhận tiền: {thoi_gian_du_kien}\n\nKhách sạn rất tiếc chưa thể phục vụ quý khách trong đợt lưu trú này và hy vọng có cơ hội chào đón quý khách trong tương lai gần.",
        "en": "Dear {ten_khach},\n\nYour booking {ma_don} at Saigon Star Hotel has been CANCELLED as requested:\n\n- Refund Amount: {tien_hoan}\n- Refund Method: {phuong_thuc}\n- Expected Processing Time: {thoi_gian_du_kien}\n\nWe regret that we could not host you this time and look forward to welcoming you in the future.",
        "zh-CN": "尊敬的 {ten_khach}，\n\n您在西贡之星酒店的预订 {ma_don} 已按要求取消：\n\n- 退款金额：{tien_hoan}\n- 退款方式：{phuong_thuc}\n- 预计到账时间：{thoi_gian_du_kien}\n\n我们遗憾未能在此次为您服务，期待未来能有机会为您效劳。",
        "ko": "{ten_khach} 고객님께,\n\n요청하신 예약 번호 {ma_don}의 취소 및 환불 처리가 완료되었습니다:\n\n- 환불 금액: {tien_hoan}\n- 환불 수단: {phuong_thuc}\n- 예상 환불 소요 시간: {thoi_gian_du_kien}\n\n이번 방문에 모시지 못해 아쉬운 마음이며, 다음 기회에 더욱 정성껏 모시겠습니다.",
        "ja": "{ten_khach} 様\n\nご予約 (予約番号: {ma_don}) のキャンセル及びご返金手続きを受け付けました:\n\n- 返金金額: {tien_hoan}\n- 返金方法: {phuong_thuc}\n- 処理予定期間: {thoi_gian_du_kien}\n\nこの度はご宿泊いただけず誠に残念ですが、またのご来館を心よりお待ちしております。",
        "es": "Estimado/a {ten_khach},\n\nSu reserva {ma_don} ha sido CANCELADA según lo solicitado:\n\n- Importe reembolsado: {tien_hoan}\n- Método de reembolso: {phuong_thuc}\n- Plazo estimado: {thoi_gian_du_kien}\n\nLamentamos no poder recibirle en esta ocasión y esperamos darle la bienvenida próximamente.",
        "fr": "Cher/Chère {ten_khach},\n\nVotre réservation {ma_don} a bien été ANNULÉE à votre demande:\n\n- Montant remboursé: {tien_hoan}\n- Moyen de remboursement: {phuong_thuc}\n- Délai estimé: {thoi_gian_du_kien}\n\nNous regrettons de ne pouvoir vous recevoir cette fois-ci et espérons vous revoir très bientôt.",
    },
    "EMAIL_HET_HAN_GIU_CHO": {
        "vi": "Kính gửi quý khách {ten_khach},\n\nĐơn đặt phòng mã {ma_don} tại Khách sạn Sài Gòn Star đã HẾT HẠN THỜI GIAN GIỮ CHỖ thanh toán. Phòng tạm giữ đã được tự động giải phóng để phục vụ khách hàng khác.\n\nNếu quý khách vẫn có nhu cầu lưu trú, vui lòng truy cập liên kết sau để tạo đơn mới:\n{link_dat_lai}\n\nXin cảm ơn quý khách!",
        "en": "Dear {ten_khach},\n\nYour hold window for reservation {ma_don} at Saigon Star Hotel has EXPIRED. The held room has been released for other guests.\n\nIf you still wish to stay with us, please make a new booking at:\n{link_dat_lai}\n\nThank you for choosing Saigon Star Hotel!",
        "zh-CN": "尊敬的 {ten_khach}，\n\n您在西贡之星酒店的预订 {ma_don} 保留时间已过期，客房已重新释放供其他客人预订。\n\n如您仍需订房，请点击以下链接重新预订：\n{link_dat_lai}\n\n感谢您的理解！",
        "ko": "{ten_khach} 고객님께,\n\n예약 번호 {ma_don}의 결제 유예 시간이 만료되었습니다. 배정 대기 중이던 객실은 다른 고객을 위해 해제되었습니다.\n\n예약을 계속 진행하시려면 아래 링크에서 다시 예약해 주시기 바랍니다:\n{link_dat_lai}\n\n감사합니다.",
        "ja": "{ten_khach} 様\n\nサイゴンスターホテルのご予約 (予約番号: {ma_don}) の仮押さえ有効期限が切れました。客室は他のご予約のために解放されました。\n\n引き続きご宿泊をご希望の場合は、以下のリンクより再度ご予約をお願いいたします:\n{link_dat_lai}\n\n何卒ご理解のほどお願い申し上げます。",
        "es": "Estimado/a {ten_khach},\n\nEl plazo de reserva temporal para su código {ma_don} ha EXPIRADO. La habitación ha sido liberada.\n\nSi desea continuar con su estancia, por favor realice una nueva reserva en:\n{link_dat_lai}\n\n¡Gracias por su interés!",
        "fr": "Cher/Chère {ten_khach},\n\nLe délai de maintien de réservation pour le code {ma_don} a EXPIRÉ. La chambre a été libérée.\n\nPour réserver à nouveau, veuillez cliquer sur ce lien:\n{link_dat_lai}\n\nMerci de votre compréhension!",
    },
    "EMAIL_THANH_TOAN_VE_MUON": {
        "vi": "Kính gửi quý khách {ten_khach},\n\nKhách sạn Sài Gòn Star đã nhận được giao dịch thanh toán cho đơn {ma_don}. Tuy nhiên giao dịch được ghi nhận sau khi đơn đã hết hạn giữ chỗ. Kết quả xử lý nghiệp vụ cụ thể như sau:\n\n{noi_dung_xu_ly}\n\nQuý khách vui lòng liên hệ bộ phận Chăm sóc khách hàng hoặc Lễ tân nếu cần hỗ trợ thêm thông tin.",
        "en": "Dear {ten_khach},\n\nSaigon Star Hotel has received payment for reservation {ma_don}. However, this payment arrived after your hold window had expired. The system resolution is as follows:\n\n{noi_dung_xu_ly}\n\nPlease contact our Front Desk team if you have any questions.",
        "zh-CN": "尊敬的 {ten_khach}，\n\n西贡之星酒店已收到您的预订 {ma_don} 支付款项。但款项在保留期结束后才被系统接收。处理结果如下：\n\n{noi_dung_xu_ly}\n\n如需进一步协助，请随时联系前台客服。",
        "ko": "{ten_khach} 고객님께,\n\n예약 번호 {ma_don}의 결제 내역이 확인되었습니다. 다만 결제가 예약 유예 시간 만료 후 승인되어 다음과 같이 처리되었습니다:\n\n{noi_dung_xu_ly}\n\n추가 안내가 필요하시면 프런트 데스크로 문의해 주시기 바랍니다.",
        "ja": "{ten_khach} 様\n\nご予約 (予約番号: {ma_don}) のお支払いを確認いたしました。しかしながら、仮押さえ期限終了後のお手続きとなったため、以下の通り処理させていただきました:\n\n{noi_dung_xu_ly}\n\nご不明な点がございましたら、お気軽にフロントまでご連絡ください。",
        "es": "Estimado/a {ten_khach},\n\nHemos recibido el pago de su reserva {ma_don}. No obstante, el pago se procesó tras expirar el tiempo de espera. La resolución es la siguiente:\n\n{noi_dung_xu_ly}\n\nContáctenos para cualquier aclaración.",
        "fr": "Cher/Chère {ten_khach},\n\nLe paiement de votre réservation {ma_don} a été reçu après l'expiration du délai de maintien. Voici le traitement appliqué:\n\n{noi_dung_xu_ly}\n\nN'hésitez pas à contacter notre réception pour toute question.",
    },
}
