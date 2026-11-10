"""Đọc 01_schema.sql thành mô hình bảng, cột, ràng buộc, chỉ mục (dùng cho ERD, trigger nhật ký, kiểm tra schema)."""
import re

COL_RE = re.compile(r'^(\w+)\s+(NUMBER\(\d+(?:,\d+)?\)|VARCHAR2\(\d+(?: CHAR)?\)|TIMESTAMP\(0\) WITH TIME ZONE|DATE|BOOLEAN|CLOB)(?=\s|$|,)(.*)$')

def parse(path):
    text = open(path, encoding='utf8').read()
    tables, indexes = {}, []
    for m in re.finditer(r'^CREATE TABLE (\w+) \(\n(.*?)\n\);', text, re.S | re.M):
        name, body = m.group(1), m.group(2)
        t = {'name': name, 'cols': [], 'pk': [], 'fks': [], 'uniques': [], 'checks': []}
        for raw in body.split('\n'):
            line = re.sub(r'\s--.*$', '', raw).rstrip()
            s = line.strip()
            if not s or s.startswith('--'):
                continue
            s = s.rstrip(',').strip()
            if s.startswith('CONSTRAINT'):
                cm = re.match(r'CONSTRAINT (\w+) (PRIMARY KEY|UNIQUE|FOREIGN KEY|CHECK)\s*(.*)$', s)
                cname, kind, rest = cm.groups()
                if kind == 'PRIMARY KEY':
                    t['pk'] = [c.strip() for c in re.match(r'\(([^)]*)\)', rest).group(1).split(',')]
                    t['pk_name'] = cname
                elif kind == 'UNIQUE':
                    t['uniques'].append((cname, [c.strip() for c in re.match(r'\(([^)]*)\)', rest).group(1).split(',')]))
                elif kind == 'FOREIGN KEY':
                    fm = re.match(r'\(([^)]*)\) REFERENCES (\w+) \(([^)]*)\)(.*)$', rest)
                    cols, parent, pcols, tail = fm.groups()
                    on_delete = 'CASCADE' if 'ON DELETE CASCADE' in tail else ('SET NULL' if 'ON DELETE SET NULL' in tail else ('RESTRICT' if '/*RESTRICT*/' in tail else None))
                    t['fks'].append({'name': cname, 'cols': [c.strip() for c in cols.split(',')], 'parent': parent,
                                     'pcols': [c.strip() for c in pcols.split(',')], 'on_delete': on_delete})
                else:
                    t['checks'].append((cname, rest))
            else:
                cm = COL_RE.match(s)
                if not cm:
                    raise ValueError(f'{name}: không đọc được cột: {s}')
                cname, ctype, tail = cm.groups()
                t['cols'].append({'name': cname, 'type': ctype, 'not_null': 'NOT NULL' in tail,
                                  'identity': 'GENERATED ALWAYS AS IDENTITY' in tail,
                                  'default': 'DEFAULT' in tail,
                                  'default_text': (re.search(r'DEFAULT (.*?)(?: NOT NULL|$)', tail) or [None, None])[1]})
        tables[name] = t
    for m in re.finditer(r'^CREATE (UNIQUE )?INDEX (\w+)\s+ON (\w+) \((.*)\);', text, re.M):
        indexes.append({'name': m.group(2), 'table': m.group(3), 'unique': bool(m.group(1)),
                        'cols': [c.strip() for c in re.sub(r'\s--.*$', '', m.group(4)).split(',')] if 'CASE' not in m.group(4) else ['<expr>']})
    return tables, indexes
