#!/usr/bin/env python3
"""يبني index.html من data/site.json و data/numbers.json (يستبدل ما بين علامات B:)."""
import json, re, html, datetime, pathlib
ROOT = pathlib.Path(__file__).parent
site = json.loads((ROOT/'data/site.json').read_text(encoding='utf-8'))
nums = json.loads((ROOT/'data/numbers.json').read_text(encoding='utf-8'))
page = (ROOT/'index.html').read_text(encoding='utf-8')

CAT = {'eco':('اقتصاد','c-lime'),'sport':('رياضة','c-coral'),'sci':('علوم','c-cyan'),'game':('ألعاب','c-yellow'),
       'lux':('فخامة','c-white'),'gulf':('خليجي','c-soft'),'world':('عالمي','c-white')}
STORY_BG = {'eco':'#BFFB03','sport':'#FF6279','gulf':'#FDFF04','lux':'#FDFF04','game':'#FFFFFF','sci':'#FFFFFF','world':'#FFFFFF'}
ICONS = set(re.findall(r'<symbol id="(i-[\w-]+)"', page))
e = lambda t: html.escape(str(t), quote=True)

def put(tag, content, js=False):
    global page
    a, b = (f'/*B:{tag}*/', f'/*/B:{tag}*/') if js else (f'<!--B:{tag}-->', f'<!--/B:{tag}-->')
    i, j = page.index(a) + len(a), page.index(b)
    page = page[:i] + content + page[j:]

def split_num(s):
    m = re.match(r'^(\D*?)([\d][\d,\.]*)(.*)$', s)
    if not m: return None
    pre, n, suf = m.groups()
    return pre, n.replace(',', ''), suf

def check(item, where):
    ic = item.get('icon') or item.get('ico')
    if ic not in ICONS: raise SystemExit(f'{where}: أيقونة غير معروفة {ic}. المتاح: {sorted(ICONS)}')
    img = item.get('image') or (f"img/{item['img']}.webp" if item.get('img') else None)
    if img and not (ROOT/img).exists(): raise SystemExit(f'{where}: الصورة غير موجودة {img}')

# week cards
cards = site['week']['cards']
out = []
for k, c in enumerate(cards):
    check(c, f'week[{k}]')
    name, cls = CAT[c['cat']]
    sp = split_num(c['number'])
    attrs = ''
    if sp:
        pre, n, suf = sp
        if '.' not in n:  # عدّاد للأعداد الصحيحة فقط
            attrs = f' data-count="{n}"' + (f' data-prefix="{e(pre)}"' if pre else '') + (f' data-suffix="{e(suf)}"' if suf else '')
    out.append(f'''      <article class="bigcard {cls}">
        <div class="bc-photo"><img src="{e(c['image'])}" alt="{e(c['tag'])}" loading="lazy"><span class="cat">{name}</span><span class="bc-ico"><svg aria-hidden="true"><use href="#{c['icon']}"/></svg></span><span class="corner tl" aria-hidden="true"></span><span class="corner br" aria-hidden="true"></span></div>
        <div class="bc-body"><div class="big num fit"{attrs}>{e(c['number'])}</div><div class="unit"><span>{e(c['unit'])}</span></div><p>{e(c['text'])}</p></div>
      </article>''')
put('week', '\n' + '\n'.join(out) + '\n')
put('wktotal', f'/ {len(cards):02d}')
giant = ' · '.join(c['number'] for c in cards)
put('giant', e(giant + ' · ' + giant + ' ·'))

# hero stories
st = []
for k, s in enumerate(site['stories']):
    check(s, f'stories[{k}]')
    st.append({'n': s['n'], 'cat': CAT[s['cat']][0], 'bg': STORY_BG.get(s['cat'], '#FFFFFF'), 'unit': s['unit'], 'label': s['label'], 'ico': s['ico'], 'img': s['img']})
put('stories', 'const STORIES=' + json.dumps(st, ensure_ascii=False) + ';', js=True)

# ticker
put('ticker', 'const T=' + json.dumps(site['ticker'], ensure_ascii=False) + ';', js=True)

# archive fallback (same list the page fetches)
for k, it in enumerate(nums['items']): check(it, f'archive[{k}]')
put('archive', 'const ARCHIVE_FALLBACK=' + json.dumps(nums['items'], ensure_ascii=False) + ';', js=True)

# audience bars + ads stats
ig = site['instagram']
colors = ['var(--cyan)', '', '', '']
bars = []
for k, (name, pct) in enumerate(ig['countries']):
    style = f'width:{pct}%' + (f';background:{colors[k]}' if k < len(colors) and colors[k] else '')
    bars.append(f'          <div class="bar"><span>{e(name)}</span><div class="track" style="background:#EEF2F3"><div class="fill" style="{style}"></div></div><span class="v num">{pct}%</span></div>')
put('bars', '\n' + '\n'.join(bars) + '\n')
def short(n): return f'{n/1000:.1f}K'.replace('.0K', 'K') if n >= 1000 else str(n)
tiles = [(short(ig['reach']), ig['reach'], 'حساب وصلنا له خلال آخر 28 يوم'),
         (short(ig['views']), ig['views'], 'مشاهدة لمحتوى «رقم» خلال آخر 28 يوم'),
         (f"{ig['core_age_share']}%", None, f"من جمهورنا بين {ig['core_age']} سنة")]
put('adsstats', ''.join(f'<div class="stat"><div class="n num">{e(t)}</div><div class="l">{e(l)}</div></div>' for t, _, l in tiles))
d = datetime.date.fromisoformat(ig['as_of'])
put('asof', e(f'أرقام إنستقرام @raqam.ar، محدّثة في {d.day}/{d.month}/{d.year}.'))

(ROOT/'index.html').write_text(page, encoding='utf-8')
# sitemap lastmod
sm = ROOT/'sitemap.xml'
sm.write_text(re.sub(r'(<loc>https://raqam.site/</loc><lastmod>)[^<]+', r'\g<1>' + site['updated'], sm.read_text(encoding='utf-8')), encoding='utf-8')
print(f'built: {len(cards)} week cards, {len(st)} stories, {len(nums["items"])} archive items, as of {ig["as_of"]}')
