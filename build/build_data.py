import json, re, os, unicodedata
S = '/tmp/claude-0/-home-claude/f2b6ad73-d825-5f47-917e-b8750b100caa/scratchpad/'
D = json.load(open(S + 'build/data.json', encoding='utf-8'))
M = json.load(open(S + 'build/media.json', encoding='utf-8'))
for e in M['album']:
    if e['id'] in ('z45', 'z51'): e['recon'] = True
    if e['id'] == 'z17': e['preferOriginal'] = True
def slug(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')
def bphoto(p):
    k = os.path.splitext(p['file'])[0]
    b = M['book'].get(k)
    if not b: return None
    cap = [c for c in p['cap'] if c]
    return dict(b, id='b_' + k, cap=' · '.join(cap))
CH = {'Handy Kitchen Measurements': ('Handy Kitchen Measurements', 'measure'), 'Breakfast & Brunch': ('Breakfast & Brunch', 'food'),
      'Soups & Appetizers': ('Soups & Appetizers', 'food'), 'Drinks & Cocktails': ('Drinks & Cocktails', 'food'),
      'Salads, Vegetables & Sauces': ('Salads, Vegetables & Sauces', 'food'), 'The Main Course - Meat': ('The Main Course: Meat', 'food'),
      'Fish and Fowl': ('Fish and Fowl', 'food'), 'Potatoes, Pasta & Bread': ('Potatoes, Pasta & Bread', 'food'),
      'Desserts: Pies – Cakes - Cookies': ('Desserts: Pies, Cakes, Cookies', 'food'), 'Easter – Celebrate Spring!': ('Easter: Celebrate Spring!', 'easter'),
      'OctoberFest': ('OctoberFest', 'oktober'), 'Hooray for Thanksgiving!': ('Hooray for Thanksgiving!', 'thanks'), 'Here Comes Santa Claus -': ('Here Comes Santa Claus: Christmas!!', 'xmas')}
HAZEL = ['Spritz Cookies', 'Russian Tea Cakes', 'Bourbon Balls', 'Rum Butter Cookies', 'Pecan Bars', 'Fresh Strawberry Pie', 'Baked Apples', 'Beer Bratwurst',
         'Ice Berg Wedge Salad', 'The Dreaded Xmas Fruit Cake', 'Jen’s Twice Baked Potatoes', 'Pecan Pie', 'Schaum Torte', 'Wisconsin Malted Milk', 'Goulash from Cobb', 'Sunday’s Traditional Pot Roast']
DODIE = ['Turkey Tetrazzini', 'El Dorado Beef/Cheese Casserole', 'California Fresh Lemonade', 'Rich and Fattening - Easy Cookies']
def tags(r):
    txt = ' '.join([r['title']] + r['story'] + r['notes'] + r['orig'])
    t = []
    if re.search(r'Hazel|Grammy’s|Mom’s', r['title']) or r['title'] in HAZEL: t.append('Grammy Hazel')
    if 'Dodie' in r['title'] or r['title'] in DODIE or 'Dorothy Owen' in txt: t.append('Dodie')
    if 'Nellie' in r['title']: t.append('Great-Grandmother Nellie')
    if 'Duane' in r['title'] or r['title'] == 'Old Fashions': t.append('Grampy Duane')
    for name, pat in [('Beth Huffman', r'Beth Huffman|Beth’s|Huffman'), ('Auntie Brenda', r'Auntie Brenda'), ('Anne Shepherd', r'Ann(e)? Shepherd'),
                      ('Mary Johnson', r'Mary Johnson'), ('Karen Hill', r'Karen Hill'), ('Jane Nelson', r'Jane Nelson'), ('Bev Schmitt', r'Bev Schmitt')]:
        if re.search(pat, txt): t.append(name)
    src = []
    for name, pat in [('The Silver Palate Cookbook', r'Silver Palate'), ('John Clancy’s Christmas Cookbook', r'John Clanc'), ('Bon Appétit', r'Bon App'),
                      ('Ina Garten', r'Ina Garten|food channel'), ('Gourmet', r'Gourmet Magazine'), ('Better Homes and Gardens', r'Better Homes'),
                      ('Crème de Colorado', r'Crème de Colorado'), ('Food Network', r'Food Network')]:
        if re.search(pat, txt): src.append(name)
    return t, src
recipes = []
EXTRA = {'hazels-scrumptious-beer-cheese-dip': ['z22', 'z40'], 'duanes-super-famous-tom-and-jerrys': ['z11'], 'davids-chicken-and-dumplings': ['z14'],
         'old-fashions': ['z36'], 'beer-bratwurst': ['z15'], 'hazels-stuffed-turkey': ['z47'], 'nellies-lemon-meringue-pie': ['z42'], 'pecan-pie': ['z24'],
         'moms-famous-apple-pie': ['z39'], 'grammys-brown-cows': ['z35'], 'the-dreaded-xmas-fruit-cake': ['z43'], 'spritz-cookies': ['z10']}
for r in D['recipes']:
    kitchen, source = tags(r)
    ph = [x for x in (bphoto(p) for p in r['photos']) if x]
    recipes.append({'id': r['id'], 'title': r['title'], 'ch': slug(CH[r['chapter']][0]), 'john': r['john'], 'sub': r['sub'], 'story': r['story'], 'parts': r['parts'],
                    'notes': r['notes'], 'asks': [a['q'] for a in r['asks']], 'orig': r['orig'], 'kitchen': kitchen, 'source': source, 'photos': ph, 'album': EXTRA.get(r['id'], [])})
chapters = []
for c in D['chapters']:
    title, kind = CH[c['title']]
    ch = {'id': slug(title), 'title': title, 'kind': kind, 'items': []}
    for it in c['items']:
        if 'r' in it: ch['items'].append({'r': it['r']})
        else:
            s = it['s']
            if kind == 'measure': s['lines'] = [l.replace('3/4 Cup = 6 Fl Oz = 16 Tbsp = 48 Tsp', '3/4 Cup = 6 Fl Oz = \u27e6m1\u27e7') for l in s['lines']]
            ch['items'].append({'s': {'title': s['title'], 'text': s['text'], 'lines': s['lines'], 'photos': [x for x in (bphoto(p) for p in s['photos']) if x]}})
    chapters.append(ch)
# front matter
front = {'ded': [], 'intro': [], 'sign': []}
for b in D['front']:
    t = b.get('t', '')
    if b['k'] == 'X' and len(front['intro']) == 0 and not re.match(r'^(Hazel|June)', t): front['ded'].append(t)
    elif b['k'] == 'E' and len(t) > 60: front['intro'].append(t)
    elif t.startswith('Ginny Bonnie Owen') or t.startswith('Christmas 2009'): front['sign'].append(t)
    if t.startswith('Table of Contents'): break
closing = [b['t'] for b in D['closing'] if b.get('t') and b['k'] != 'img' and not re.match(r'^(Duane & Hazel Bonnie|1963)$', b['t'])]
out = {'chapters': chapters, 'recipes': recipes, 'edits': D['edits'], 'album': M['album'], 'front': front, 'closing': closing,
       'cover': {'hazel': M['book'].get('image54'), 'ginny': M['book'].get('image48'), 'last': M['book'].get('image46')}}
out['asks'] = [
 {'t': 'Hazel\u2019s portrait on the opening page', 'q': 'The book captions this portrait "Hazel Eastman, 1929," but the same photo in the family scans is labeled "Hazel Eastman, 1938." Which year is right?'},
 {'t': 'Your dad\u2019s Army photo', 'q': 'The book captions the glider school photo "Corporal Duane Bonnie, 1942," and the scan is labeled 1943. Which year is right?'},
 {'t': 'Your uncle\u2019s name', 'q': 'The OctoberFest story spells it "Uncle Allen," and the photo captions spell it "Allyn." Which spelling is right?'},
]
js = 'window.BOOK=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
open(S + 'site2/data.js', 'w', encoding='utf-8').write(js)
page = open(S + 'build/page.html', encoding='utf-8').read()
open(S + 'site2/index.html', 'w', encoding='utf-8').write('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="robots" content="noindex">\n' + page.split('<div class="top">')[0] + '</head>\n<body>\n<div class="top">' + page.split('<div class="top">', 1)[1] + '\n</body>\n</html>\n')
open(S + 'site2/preview.html', 'w', encoding='utf-8').write(page)
print(len(js) // 1024, 'KB', len(recipes), 'recipes', [(c['id'], sum(1 for i in c['items'] if 'r' in i)) for c in chapters])
print('front', len(front['ded']), len(front['intro']), front['sign'], 'closing', len(closing))
from collections import Counter
print(Counter(k for r in recipes for k in r['kitchen']).most_common(), Counter(k for r in recipes for k in r['source']).most_common())
print('john', sum(r['john'] for r in recipes), 'asks', sum(len(r['asks']) for r in recipes))
