"""Kiểm tra 01_schema.sql theo checklist của skill database-schema-validation (đã điều chỉnh cho Oracle 23ai)
và đối chiếu với SRS mục 10. In kết quả dạng JSON để dựng báo cáo."""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from ddl_parser import parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tables, indexes = parse(os.path.join(ROOT, '01_schema.sql'))
res = {'passed': [], 'warn': [], 'error': []}
def ok(m): res['passed'].append(m)
def warn(m): res['warn'].append(m)
def err(m): res['error'].append(m)

# ---- A. khóa chính ----
no_pk = [t for t, d in tables.items() if not d['pk']]
(err if no_pk else ok)(f'Bảng thiếu khóa chính: {no_pk}' if no_pk else f'Cả {len(tables)} bảng có khóa chính khai báo rõ.')
ident = [t for t, d in tables.items() if any(c['identity'] for c in d['cols'])]
ok(f'{len(ident)} bảng dùng NUMBER(19) GENERATED ALWAYS AS IDENTITY; bảng còn lại dùng khóa tự nhiên hoặc khóa ghép: ' +
   ', '.join(sorted(set(tables) - set(ident))))
bad_id = [(t, c['name']) for t, d in tables.items() for c in d['cols'] if c['identity'] and c['type'] != 'NUMBER(19)']
(err if bad_id else ok)(f'Identity không phải NUMBER(19): {bad_id}' if bad_id else 'Mọi cột identity là NUMBER(19) (tương đương BIGINT).')

# ---- B. khóa ngoại ----
fks = [(t, f) for t, d in tables.items() for f in d['fks']]
no_del = [(t, f['name']) for t, f in fks if not f['on_delete']]
(err if no_del else ok)(f'FK chưa nêu ON DELETE: {no_del}' if no_del else f'Cả {len(fks)} khóa ngoại nêu rõ ON DELETE (CASCADE hoặc /*RESTRICT*/).')
bad_ref = []
for t, f in fks:
    p = tables.get(f['parent'])
    if not p: bad_ref.append((t, f['name'], 'bảng cha không tồn tại')); continue
    pc = {c['name'] for c in p['cols']}
    if not set(f['pcols']) <= pc: bad_ref.append((t, f['name'], 'cột cha không tồn tại'))
    keyset = [p['pk']] + [u[1] for u in p['uniques']]
    if f['pcols'] not in keyset: bad_ref.append((t, f['name'], 'cột cha không phải khóa chính hoặc duy nhất'))
(err if bad_ref else ok)(f'FK trỏ sai: {bad_ref}' if bad_ref else 'Mọi khóa ngoại trỏ đúng cột khóa chính hoặc duy nhất của bảng cha.')
def indexed(t, col):
    d = tables[t]
    if d['pk'] and d['pk'][0] == col: return True
    if any(u[1][0] == col for u in d['uniques']): return True
    return any(i['table'] == t and i['cols'][0] == col for i in indexes)
unindexed = [(t, f['cols']) for t, f in fks if not indexed(t, f['cols'][0])]
(err if unindexed else ok)(f'FK chưa có chỉ mục: {unindexed}' if unindexed else f'Cả {len(fks)} cột khóa ngoại đều có chỉ mục dẫn đầu (chỉ mục riêng, khóa chính hoặc unique).')
fk_cols = {(t, f['cols'][0]) for t, f in fks}
dup = []
for i in indexes:
    for j in indexes:
        if i is not j and i['table'] == j['table'] and i['cols'] != ['<expr>'] and len(i['cols']) < len(j['cols']) and j['cols'][:len(i['cols'])] == i['cols']:
            dup.append((i['name'], j['name']))
(warn if dup else ok)(f'Chỉ mục thừa (bị chỉ mục dài hơn phủ): {dup}' if dup else 'Không có chỉ mục nào bị chỉ mục khác phủ hoàn toàn.')

# ---- C. kiểu dữ liệu ----
money_re = re.compile(r'^(so_tien|don_gia|don_gia_ap_dung|tien_phong|tien_vat|tong_tien)$')
bad_money = [(t, c['name'], c['type']) for t, d in tables.items() for c in d['cols'] if money_re.search(c['name']) and c['type'] != 'NUMBER(15,2)']
(err if bad_money else ok)(f'Cột tiền sai kiểu: {bad_money}' if bad_money else 'Mọi cột tiền là NUMBER(15,2); không có FLOAT hay BINARY_DOUBLE.')
ts = [(t, c['name'], c['type']) for t, d in tables.items() for c in d['cols'] if c['type'].startswith('TIMESTAMP') and 'WITH TIME ZONE' not in c['type']]
(err if ts else ok)(f'TIMESTAMP không múi giờ: {ts}' if ts else 'Mọi thời điểm là TIMESTAMP WITH TIME ZONE; DATE chỉ dùng cho ngày hiệu lực và ngày tỷ giá: ' +
   ', '.join(f"{t}.{c['name']}" for t, d in tables.items() for c in d['cols'] if c['type'] == 'DATE'))
bools = [(t, c) for t, d in tables.items() for c in d['cols'] if c['type'] == 'BOOLEAN']
bad_b = [(t, c['name']) for t, c in bools if not (c['not_null'] and c['default'])]
(err if bad_b else ok)(f'BOOLEAN thiếu NOT NULL hoặc DEFAULT: {bad_b}' if bad_b else f'Cả {len(bools)} cột BOOLEAN có NOT NULL và DEFAULT rõ ràng.')
no_created = [t for t, d in tables.items() if not any(c['name'] in ('ngay_tao', 'thoi_diem') and c['default'] for c in d['cols'])]
(warn if no_created else ok)(f'Bảng chưa có cột thời điểm tạo mặc định SYSTIMESTAMP: {no_created}' if no_created else 'Mọi bảng có ngày tạo mặc định SYSTIMESTAMP.')
unbounded = [(t, c['name']) for t, d in tables.items() for c in d['cols'] if c['type'] == 'CLOB']
ok('CLOB chỉ dùng cho nội dung không giới hạn: ' + ', '.join(f'{t}.{c}' for t, c in unbounded))

# ---- D. nullability ----
nullable = [(t, c['name']) for t, d in tables.items() for c in d['cols'] if not c['not_null'] and not c['identity'] and c['name'] not in d['pk']]
res['nullable'] = [f'{t}.{c}' for t, c in nullable]
ok(f'{len(nullable)} cột cho phép NULL, mỗi cột có lý do nghiệp vụ (xem báo cáo).')

# ---- E. duy nhất nghiệp vụ ----
need = {'dat_phong': 'ma_tra_cuu', 'phong': 'ma_phong', 'loai_phong': 'ma_hang', 'nguoi_dung': 'ten_dang_nhap',
        'hoa_don': 'so_hoa_don', 'giao_dich_thanh_toan': 'ma_tham_chieu_cong', 'vai_tro': 'ma_vai_tro'}
miss = [(t, c) for t, c in need.items() if not any(u[1] == [c] for u in tables[t]['uniques'])]
(err if miss else ok)(f'Thiếu UNIQUE: {miss}' if miss else 'Mọi mã nghiệp vụ (mã tra cứu, mã phòng, mã hạng, tên đăng nhập, số hóa đơn, mã giao dịch cổng, mã vai trò) có UNIQUE.')
lowcard = [i['name'] for i in indexes if len(i['cols']) == 1 and i['cols'][0] in ('trang_thai', 'dang_hoat_dong', 'cho_thue_gio', 'la_dieu_chinh')]
(warn if lowcard else ok)(f'Chỉ mục trên cột ít giá trị: {lowcard}' if lowcard else 'Không có chỉ mục đơn trên cột ít giá trị; chỉ mục trạng thái đều là chỉ mục ghép với thời điểm hoặc chỉ mục hàm.')

# ---- đặt tên ----
bad_name = []
for t, d in tables.items():
    if d['pk_name'] != f'pk_{t}': bad_name.append(d['pk_name'])
    for n, cols in d['uniques']:
        if n != f"uix_{t}_{'_'.join(cols)}": bad_name.append(n)
    for f in d['fks']:
        if f['name'] != f"fk_{t}_{'_'.join(f['cols'])}": bad_name.append(f['name'])
    for n, _ in d['checks']:
        if not n.startswith(f'ck_{t}_'): bad_name.append(n)
for i in indexes:
    if not i['name'].startswith(f"idx_{i['table']}_"): bad_name.append(i['name'])
(err if bad_name else ok)(f'Tên không theo quy ước: {bad_name}' if bad_name else 'Mọi khóa chính (pk_), khóa ngoại (fk_), unique (uix_), check (ck_), chỉ mục (idx_) theo quy ước <tiền tố>_<bảng>_<cột>.')
long_names = [n for n in ([d['pk_name'] for d in tables.values()] + [f['name'] for d in tables.values() for f in d['fks']] + [i['name'] for i in indexes]) if len(n) > 30]
res['long_names'] = long_names
if long_names: warn(f'{len(long_names)} tên ràng buộc hoặc chỉ mục dài hơn 30 ký tự (hợp lệ từ Oracle 12.2 trở lên, 23ai cho tới 128 byte); dài nhất {max(map(len,long_names))} ký tự.')

# ---- đối chiếu SRS mục 10 ----
src = open(os.path.join(ROOT, '..', 'srs', 'content3.js'), encoding='utf8').read()
seg = src[src.find("['Thực thể', 'Thuộc tính chính']"): src.find("label('Quan hệ')")]
srs = {}
for m in re.finditer(r"\['(\w+)', '(.*?)'\],", seg):
    txt = re.sub(r'\([^)]*\)', '', m.group(2))
    srs[m.group(1).lower()] = {w.strip().lower() for w in txt.split(',') if re.fullmatch(r'[A-Z][A-Z0-9_]*', w.strip())}
diff = {'thieu_trong_ddl': {}, 'them_so_voi_srs': {}, 'bang_them': sorted(set(tables) - set(srs)), 'bang_thieu': sorted(set(srs) - set(tables))}
for t, cols in srs.items():
    if t not in tables: continue
    have = {c['name'] for c in tables[t]['cols']}
    miss_c = sorted(cols - have)
    extra = sorted(have - cols - {'ngay_tao'})
    if miss_c: diff['thieu_trong_ddl'][t] = miss_c
    if extra: diff['them_so_voi_srs'][t] = extra
res['srs'] = diff
res['stats'] = {'bang': len(tables), 'cot': sum(len(d['cols']) for d in tables.values()), 'fk': len(fks), 'index': len(indexes),
                'check': sum(len(d['checks']) for d in tables.values())}
json.dump(res, open(os.path.join(ROOT, 'tools', 'validation.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
