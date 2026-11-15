import re, json, os, sys, copy
from bs4 import BeautifulSoup
S = '/tmp/claude-0/-home-claude/f2b6ad73-d825-5f47-917e-b8750b100caa/scratchpad/'
html_src = open(S + 'v2010/c2010.html', encoding='utf-8').read()
# split <br> inside paragraphs/headings into separate paragraphs, keeping inline formatting
def split_br(m):
    tag, attrs, inner = m.group(1), m.group(2), m.group(3)
    if '<br' not in inner: return m.group(0)
    parts = re.split(r'<br\s*/?>', inner)
    out = []
    opened = []
    for p in parts:
        # carry open em/strong tags across pieces
        prefix = ''.join('<%s>' % t for t in opened)
        seg = prefix + p
        stack = []
        for t in re.finditer(r'<(/?)(em|strong)>', seg):
            if t.group(1):
                if stack: stack.pop()
            else: stack.append(t.group(2))
        opened = stack[:]
        seg += ''.join('</%s>' % t for t in reversed(stack))
        out.append('<p>%s</p>' % seg)
    if tag == 'p': return '\n'.join(out)
    segs = [o[3:-4] for o in out if re.sub(r'<[^>]+>|\s', '', o)]
    return '\n'.join('<%s>%s</%s>' % (tag, s_, tag) for s_ in segs)
html_src = re.sub(r'<(p|h1|h2)([^>]*)>((?:(?!</\1>).)*)</\1>', split_br, html_src, flags=re.S)
soup = BeautifulSoup(html_src, 'html.parser')
raw = [l.rstrip('\n') for l in open(S + 'v2010/clean.txt', encoding='utf-8')]
def norm(s): return re.sub(r'[^a-z0-9½¼¾⅓⅔⅛]+', '', s.lower())
rawmap = {}
for l in raw: rawmap.setdefault(norm(l), l)
def T(el): return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()
def frac_all(el, tag):
    t = norm(T(el))
    if not t: return False
    return len(norm(''.join(T(x) for x in el.find_all(tag)))) >= 0.9 * len(t)
def split_cells(text):
    r = rawmap.get(norm(text))
    if r is None: return [text]
    cells = [c.strip() for c in re.split(r'\t+| {3,}', r.strip()) if c.strip()]
    return cells or [text]
SMALL = {'image%d.png' % i for i in (1, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 19, 21, 29, 38, 40, 41, 42, 45, 50, 51)}
flat = []
def emit(el):
    imgs = [os.path.basename(i['src']) for i in el.find_all('img')]
    t = T(el)
    photos = [i for i in imgs if i not in SMALL]
    john = any(i in SMALL for i in imgs)
    if photos: flat.append({'k': 'img', 'files': photos})
    if not t or t == '.': return
    em, st = frac_all(el, 'em'), frac_all(el, 'strong')
    k = el.name if el.name in ('h1', 'h2') else ('X' if em and st else 'E' if em else 'S' if st else 'P')
    lead = None
    s0 = el.find('strong')
    if k == 'P' and s0 and T(s0) and t.startswith(T(s0)) and len(T(s0)) < 45: lead = T(s0).rstrip(':').strip()
    flat.append({'k': k, 't': t, 'john': john, 'lead': lead})
for el in soup.find_all(['h1', 'h2', 'p', 'table']):
    if el.find_parent('table'): continue
    if el.name == 'table':
        if el.find(['h1', 'h2']):
            for tr in el.find_all('tr'):
                for c in tr.find_all(['td', 'th'], recursive=False):
                    kids = c.find_all(['h1', 'h2', 'p'])
                    if kids:
                        for kd in kids: emit(kd)
                    elif T(c): emit(c)
            continue
        for i in el.find_all('img'):
            f = os.path.basename(i['src'])
            if f not in SMALL: flat.append({'k': 'img', 'files': [f]})
        def lines(c): return [re.sub(r'\s+', ' ', x).strip() for x in c.get_text('\n').split('\n') if x.strip()]
        rows = [[lines(c) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in el.find_all('tr') if tr.find_parent('table') is el]
        if not rows: continue
        ncol = max(len(r) for r in rows)
        cols = [[x for r in rows if ci < len(r) for x in r[ci]] for ci in range(ncol)]
        flat.append({'k': 'table', 'cols': cols}); continue
    emit(el)
start = next(i for i, b in enumerate(flat) if b.get('t') == 'Handy Kitchen Measurements' and b['k'] == 'h1')
front, main = flat[:start], flat[start:]

CHAPTERS = ['Handy Kitchen Measurements', 'Breakfast & Brunch', 'Soups & Appetizers', 'Drinks & Cocktails', 'Salads, Vegetables & Sauces',
            'The Main Course - Meat', 'Fish and Fowl', 'Potatoes, Pasta & Bread', 'Desserts: Pies – Cakes - Cookies', 'Easter – Celebrate Spring!',
            'OctoberFest', 'Hooray for Thanksgiving!', 'Here Comes Santa Claus -']
EXTRA_TITLES = ['Appletini', 'Schaum Torte', 'Gingerbread Men', 'Peppermint Meringue Cake with Chocolate Buttercream', 'Citrus Vodka', 'Buttered New Potatoes']
SECTIONS = ['Salads', 'Desserts', 'Dessert', 'A Perfectly Stuffed Turkey', 'Early Courses', 'Vegetables', 'Christmas Eve', 'Christmas Morning', 'Christmas Potatoes',
            'The Meat!', 'Sauces for the roast!', 'Christmas Cookies', 'Christmas Desserts', 'Christmas Gift Baskets', 'A Bonnie Christmas Story',
            'Our Thanksgiving Tradition', 'The Thanksgiving Meal', 'Cranberry Sauce']
SKIP = ['Curried Shrimp (Contd)', 'Continued on next page.', 'Christmas!!']
chapters = []; cur = None; rec = None; closing = []
in_closing = False
for b in main:
    t = b.get('t', '')
    if in_closing: closing.append(b); continue
    if t.startswith('My hope is that there will never be an end'): in_closing = True; closing.append(b); continue
    if t in SKIP: continue
    if t in CHAPTERS and (b['k'] in ('h1', 'h2', 'X', 'S', 'P', 'E')) and not (cur and cur['title'] == t):
        cur = {'title': t, 'items': []}; chapters.append(cur); rec = None; continue
    if t in SECTIONS and b['k'] in ('h1', 'h2', 'X', 'S') and cur and cur['title'] not in ('Handy Kitchen Measurements',):
        rec = None; cur['items'].append({'type': 'section', 'title': t, 'blocks': []}); rec = cur['items'][-1]; continue
    if b['k'] == 'h2' or (t in EXTRA_TITLES and b['k'] in ('X', 'S', 'P', 'E')):
        rec = {'type': 'recipe', 'title': t, 'john': b.get('john', False), 'blocks': []}; cur['items'].append(rec); continue
    if rec is None:
        rec = {'type': 'section', 'title': '', 'blocks': []}; cur['items'].append(rec)
    if b['k'] == 'S': b = dict(b, cells=split_cells(b['t']))
    rec['blocks'].append(b)
# merge two-line titles (recipe with no blocks followed by a recipe)
for c in chapters:
    out = []
    for it in c['items']:
        if out and out[-1]['type'] == 'recipe' and not out[-1]['blocks'] and it['type'] == 'recipe':
            it['title'] = out[-1]['title'] + ' ' + it['title']; it['john'] = it['john'] or out[-1]['john']; out[-1] = it
        else: out.append(it)
    c['items'] = out
json.dump({'front': front, 'chapters': chapters, 'closing': closing}, open(S + 'build/raw2.json', 'w'), ensure_ascii=False, indent=1)
n = 0
for c in chapters:
    print('\n#', c['title'])
    for it in c['items']:
        ks = ''.join({'table': 'T', 'img': 'I'}.get(b['k'], b['k']) for b in it['blocks'])
        if it['type'] == 'recipe': n += 1
        print(f"  {'R' if it['type']=='recipe' else '§'}{'J' if it.get('john') else ' '} {it['title'][:56]:56} {ks[:60]}")
print(n, 'recipes; closing', len(closing), 'front', len(front))
