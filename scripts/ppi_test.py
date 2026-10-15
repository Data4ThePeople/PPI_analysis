"""Feasibility test: do PPI final demand item weights x item price changes add up to the headline?

Usage: python3 -I scripts/ppi_test.py <path to ppi-fdallrel.xlsx>
Weights file: https://www.bls.gov/web/ppi/ppi-fdallrel.xlsx (December 2024 column is used).
Compares the sum of leaf contributions, December 2024 to December 2025, with WPUFD4.
Result on 2026-10-15: 3.082% from 710 leaves vs 3.136% published; 98 leaves (1.338% of weight) had no index.
"""
import sys, zipfile, json, urllib.request, xml.etree.ElementTree as ET
sys.path.insert(0, '/Users/ericpachman/.claude/d4tp-process')
from d4tp_env import load_env, get_key
load_env()
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
z = zipfile.ZipFile(sys.argv[1])
ss = [''.join(t.text or '' for t in si.iter(NS+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(NS+'si')]
rows = []
for r in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).iter(NS+'row'):
    vals = []
    for c in r.findall(NS+'c'):
        v = c.find(NS+'v'); x = v.text if v is not None else ''
        if c.get('t') == 's' and x: x = ss[int(x)]
        vals.append(x)
    rows.append(vals)
items = []
for r in rows:
    if len(r) >= 4 and r[0] and r[0] != 'FD4':
        try: w = float(r[2])
        except ValueError: continue
        items.append((r[0], r[1], w))
codes = [c for c, _, _ in items]
leaves = [(c, n, w) for i, (c, n, w) in enumerate(items) if not (i + 1 < len(items) and items[i+1][0].startswith(c) and len(items[i+1][0]) > len(c))]
print('items', len(items), 'leaves', len(leaves), 'leaf weight sum', round(sum(w for *_, w in leaves), 3))
print('sample codes', [c for c, _, _ in leaves[:3]], [c for c, _, _ in leaves[-5:]])
ids = ['WPUFD4'] + ['WPU' + c for c, _, _ in leaves]
data = {}
for i in range(0, len(ids), 50):
    req = urllib.request.Request('https://api.bls.gov/publicAPI/v2/timeseries/data/', json.dumps({'seriesid': ids[i:i+50], 'startyear': '2024', 'endyear': '2025', 'registrationkey': get_key('BLS_API_KEY')}).encode(), {'Content-Type': 'application/json'})
    for s in json.load(urllib.request.urlopen(req))['Results']['series']:
        d = {(x['year'], x['period']): x['value'] for x in s['data']}
        data[s['seriesID']] = d
def chg(sid):
    d = data.get(sid, {})
    try: return float(d[('2025','M12')]) / float(d[('2024','M12')]) - 1
    except (KeyError, ValueError): return None
head = chg('WPUFD4')
tot = 0; miss = []
for c, n, w in leaves:
    g = chg('WPU' + c)
    if g is None: miss.append((c, n, w))
    else: tot += w / 100 * g
print('FD4 Dec24-Dec25 %.3f%%' % (head*100))
print('sum of leaf contributions %.3f%% (from %d leaves)' % (tot*100, len(leaves)-len(miss)))
print('missing', len(miss), 'weight', round(sum(w for *_, w in miss), 3))
for m in sorted(miss, key=lambda x: -x[2])[:12]: print('  ', m)
