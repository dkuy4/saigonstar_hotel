"""Sinh 05_trigger_nhat_ky.sql: trigger ghi nhật ký tự động (FR-45, BR-46, BR-47) từ mô hình bảng trong 01_schema.sql."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ddl_parser import parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tables, _ = parse(os.path.join(ROOT, '01_schema.sql'))

# Bảng cần nhật ký theo BR-46; cột nhạy cảm không đưa vào nhật ký
AUDIT = {
    'dat_phong': [], 'dat_phong_doan': [], 'phong': [], 'giao_dich_thanh_toan': [], 'hoan_tien': [],
    'bang_gia': [], 'loai_phong': [], 'cau_hinh_he_thong': [],
    'nguoi_dung': ['mat_khau_bam'],
}

def json_obj(tbl, prefix, skip):
    parts = [f"'{c['name']}' VALUE :{prefix}.{c['name']}" for c in tables[tbl]['cols'] if c['name'] not in skip]
    return 'JSON_OBJECT(\n        ' + ',\n        '.join(parts) + '\n        RETURNING CLOB)'

def khoa(tbl, prefix):
    pk = tables[tbl]['pk']
    return " || '@' || ".join(f"TO_CHAR(:{prefix}.{c})" if
                              next(x for x in tables[tbl]['cols'] if x['name'] == c)['type'].startswith('NUMBER') else
                              (f"TO_CHAR(:{prefix}.{c}, 'YYYY-MM-DD')" if next(x for x in tables[tbl]['cols'] if x['name'] == c)['type'] == 'DATE' else f":{prefix}.{c}")
                              for c in pk)

out = ['-- =====================================================================',
       '-- 05_trigger_nhat_ky.sql: trigger ghi nhật ký kiểm toán tự động (FR-45, BR-46, BR-47)',
       '-- FILE SINH TỰ ĐỘNG bởi tools/gen_audit.py từ 01_schema.sql. Không sửa tay; đổi schema thì sinh lại.',
       '-- Người thực hiện, vai trò, kênh, IP, lý do lấy từ PKG_NGU_CANH (API gọi PKG_NGU_CANH.DAT đầu mỗi giao dịch).',
       '-- Cột mat_khau_bam của NGUOI_DUNG không đưa vào nhật ký.',
       '-- =====================================================================',
       'WHENEVER SQLERROR EXIT FAILURE ROLLBACK', '']
for tbl, skip in AUDIT.items():
    cols = {c['name'] for c in tables[tbl]['cols']}
    has_tt = 'trang_thai' in cols
    out.append(f'CREATE OR REPLACE TRIGGER trg_ghi_nhat_ky_{tbl}')
    out.append(f'AFTER INSERT OR UPDATE OR DELETE ON {tbl}')
    out.append('FOR EACH ROW')
    out.append('DECLARE')
    out.append('  v_cu   CLOB;')
    out.append('  v_moi  CLOB;')
    out.append('  v_khoa VARCHAR2(100);')
    out.append('  v_act  VARCHAR2(30);')
    out.append('BEGIN')
    out.append('  IF INSERTING THEN')
    out.append(f"    v_act := 'TAO';")
    out.append(f"    v_khoa := {khoa(tbl, 'NEW')};")
    out.append(f"    SELECT {json_obj(tbl, 'NEW', skip)}\n      INTO v_moi FROM dual;")
    out.append('  ELSIF DELETING THEN')
    out.append(f"    v_act := 'XOA';")
    out.append(f"    v_khoa := {khoa(tbl, 'OLD')};")
    out.append(f"    SELECT {json_obj(tbl, 'OLD', skip)}\n      INTO v_cu FROM dual;")
    out.append('  ELSE')
    if has_tt:
        out.append(f"    v_act := CASE WHEN :NEW.trang_thai <> :OLD.trang_thai THEN 'DOI_TRANG_THAI' ELSE 'SUA' END;")
    else:
        out.append("    v_act := 'SUA';")
    out.append(f"    v_khoa := {khoa(tbl, 'NEW')};")
    out.append(f"    SELECT {json_obj(tbl, 'OLD', skip)}\n      INTO v_cu FROM dual;")
    out.append(f"    SELECT {json_obj(tbl, 'NEW', skip)}\n      INTO v_moi FROM dual;")
    out.append('  END IF;')
    out.append(f"  pkg_nhat_ky.ghi('{tbl.upper()}', v_khoa, v_act, v_cu, v_moi);")
    out.append(f'END trg_ghi_nhat_ky_{tbl};')
    out.append('/')
    out.append('')
open(os.path.join(ROOT, '05_trigger_nhat_ky.sql'), 'w', encoding='utf8').write('\n'.join(out))
print('đã sinh', len(AUDIT), 'trigger nhật ký')
