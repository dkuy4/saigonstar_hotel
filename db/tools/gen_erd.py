"""Vẽ ERD từ 01_schema.sql bằng Graphviz; sinh thêm bản Mermaid (ERD.md)."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from ddl_parser import parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tables, _ = parse(os.path.join(ROOT, '01_schema.sql'))

GROUPS = {   # nhóm màu theo module của SRS mục 3.1
    'Danh mục và cấu hình': (['ngon_ngu', 'cau_hinh_he_thong', 'noi_dung_dich', 'ty_gia'], '#EDEDED'),
    'Tài khoản': (['vai_tro', 'nguoi_dung'], '#E3F1E3'),
    'Phòng và giá': (['loai_phong', 'loai_phong_dich', 'bang_gia', 'phong'], '#EAF0F8'),
    'Đặt phòng': (['khach_hang', 'giay_to_khach', 'dat_phong', 'dat_phong_doan', 'hang_doi_email'], '#FFF6D6'),
    'Thanh toán và hóa đơn': (['giao_dich_thanh_toan', 'hoan_tien', 'hoa_don', 'chi_tiet_hoa_don', 'bo_dem_hoa_don'], '#F6EBDD'),
    'Kiểm toán': (['nhat_ky_kiem_toan'], '#F8E1E1'),
}
color = {t: c for _, (ts, c) in GROUPS.items() for t in ts}
SHORT = lambda c: c['type'].replace('TIMESTAMP(0) WITH TIME ZONE', 'TSTZ').replace(' CHAR', '').replace('VARCHAR2', 'VC2')

def label(t):
    d = tables[t]; fkc = {c for f in d['fks'] for c in f['cols']}
    rows = [f'<TR><TD COLSPAN="3" BGCOLOR="#33415C"><FONT COLOR="white"><B>{t.upper()}</B></FONT></TD></TR>']
    for c in d['cols']:
        key = 'PK' if c['name'] in d['pk'] else ('FK' if c['name'] in fkc else '')
        if c['name'] in d['pk'] and c['name'] in fkc: key = 'PK,FK'
        nm = f'<B>{c["name"]}</B>' if c['name'] in d['pk'] else c['name']
        nn = '' if c['not_null'] or c['identity'] else '?'
        rows.append(f'<TR><TD ALIGN="LEFT">{nm}{nn}</TD><TD ALIGN="LEFT"><FONT COLOR="#555555">{SHORT(c)}</FONT></TD><TD>{key}</TD></TR>')
    return f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2" BGCOLOR="{color[t]}">' + ''.join(rows) + '</TABLE>>'

dot = ['digraph ERD {', '  rankdir=LR; splines=ortho; nodesep=0.35; ranksep=0.9; fontname="DejaVu Sans";',
       '  node [shape=plain, fontname="DejaVu Sans", fontsize=9]; edge [fontname="DejaVu Sans", fontsize=8, color="#33415C", arrowsize=0.7];']
for t in tables: dot.append(f'  {t} [label={label(t)}];')
for t, d in tables.items():
    for f in d['fks']:
        style = 'solid' if f['on_delete'] == 'CASCADE' else 'solid'
        dot.append(f'  {f["parent"]} -> {t} [arrowhead=crow, arrowtail=tee, dir=both, taillabel="1", headlabel="N", style={style}];')
dot.append('  labelloc=b; fontsize=10; label="ERD hệ thống đặt phòng khách sạn (21 bảng). ? = cho phép NULL; PK khóa chính; FK khóa ngoại; mũi tên từ bảng cha (1) tới bảng con (N).";')
dot.append('}')
open(os.path.join(ROOT, 'tools', 'erd.dot'), 'w', encoding='utf8').write('\n'.join(dot))
subprocess.run(['dot', '-Tpng', '-Gdpi=130', os.path.join(ROOT, 'tools', 'erd.dot'), '-o', os.path.join(ROOT, 'ERD.png')], check=True)
subprocess.run(['dot', '-Tsvg', os.path.join(ROOT, 'tools', 'erd.dot'), '-o', os.path.join(ROOT, 'ERD.svg')], check=True)

# Mermaid
mm = ['```mermaid', 'erDiagram']
for t, d in tables.items():
    for f in d['fks']:
        opt = 'o{' if any(not next(c for c in d['cols'] if c['name'] == x)['not_null'] for x in f['cols']) else '|{'
        mm.append(f'  {f["parent"].upper()} ||--{opt} {t.upper()} : "{f["cols"][0]}"')
for t, d in tables.items():
    fkc = {c for f in d['fks'] for c in f['cols']}
    mm.append(f'  {t.upper()} {{')
    for c in d['cols']:
        ty = c['type'].replace('TIMESTAMP(0) WITH TIME ZONE', 'TSTZ').replace(' CHAR', '').replace('(', '_').replace(')', '').replace(',', '_')
        k = 'PK' if c['name'] in d['pk'] else ('FK' if c['name'] in fkc else '')
        mm.append(f'    {ty} {c["name"]} {k}'.rstrip())
    mm.append('  }')
mm.append('```')
open(os.path.join(ROOT, 'tools', 'erd_mermaid.txt'), 'w', encoding='utf8').write('\n'.join(mm))
print('ERD xong', len(tables), 'bảng')
