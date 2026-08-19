import re

data = open('../font_fvf_fernando.h', encoding='utf-8').read()   # script nam trong tools/

rowdata_m = re.search(r'FVF_ROWDATA\[\d+\] = \{(.+?)\};', data, re.S)
rowdata = [int(x, 16) for x in re.findall(r'0x[0-9A-F]{4}', rowdata_m.group(1))]

entry_pattern = re.compile(
    r'/\* (.+?) U\+([0-9A-F]{4}) \*/ \{ 0x[0-9A-F]+, (\d+), (\d+), (\d+), (\d+) \}'
)

entries = []
for m in entry_pattern.finditer(data):
    label, code, width, yoff, height, idx = m.groups()
    entries.append({
        'cp': int(code, 16),
        'label': label,
        'width': int(width),
        'yoff': int(yoff),
        'height': int(height),
        'idx': int(idx),
    })

print('Tong so ky tu:', len(entries))

# --- 1) Ky tu co ve dang bi loi trich xuat (qua nho / height=0 nhung khong
#     phai space) ---
print('\n--- Nghi ngo bi mat net (height <= 1, tru dau . , : \' ` da biet) ---')
suspicious_small = [e for e in entries if e['height'] <= 1 and e['cp'] != 0x20]
for e in suspicious_small:
    print(' ', e['label'], hex(e['cp']), 'height=', e['height'])
if not suspicious_small:
    print('  (khong co)')

# --- 2) Trung lap bitmap: 2 ky tu KHAC NHAU nhung render y het nhau ---
print('\n--- Trung lap bitmap (2 ky tu khac nhau nhung hinh giong het) ---')
seen = {}
dupes = []
for e in entries:
    rows = tuple(rowdata[e['idx']:e['idx'] + e['height']])
    key = (e['width'], rows)
    if key in seen:
        dupes.append((seen[key], e))
    else:
        seen[key] = e
for a, b in dupes:
    print(' ', a['label'], hex(a['cp']), '  <->  ', b['label'], hex(b['cp']))
if not dupes:
    print('  (khong co)')

# --- 3) Ky tu co width bat thuong (=1, thuong la loi doi voi chu khong
#     phai i/l/dau cau) ---
print('\n--- Width=1 (binh thuong chi co i,l,!,\', |, ; nen co, con lai la dang ngo) ---')
expected_narrow = set("il!'|.,:;")
narrow_odd = [e for e in entries if e['width'] == 1 and chr(e['cp']) not in expected_narrow]
for e in narrow_odd:
    print(' ', e['label'], hex(e['cp']), 'width=1')
if not narrow_odd:
    print('  (khong co)')

print('\nXong audit.')
