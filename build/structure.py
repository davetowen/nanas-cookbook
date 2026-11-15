import re, json, sys, os, unicodedata
S = '/tmp/claude-0/-home-claude/f2b6ad73-d825-5f47-917e-b8750b100caa/scratchpad/'
D = json.load(open(S + 'build/raw2.json', encoding='utf-8'))
try:
    from overrides import GROUPS, NOTES_TAIL, STORY_FIX, TITLES, DROP
except Exception as e:
    print('no overrides', e); GROUPS, NOTES_TAIL, STORY_FIX, TITLES, DROP = {}, {}, {}, {}, set()
from edits import QUIET, EDITS, ASKS

LABEL_RE = re.compile(r'^(pastry|filling|crust|topping|stuffing|sauce|meat sauce|dressing|vinaigrette|shortbread|roulade|salad|meringue|cake|butter ?cream|buttercream|mousse|icing|cookies|condiments|shrimp|lime curd|cranberry topping|white chocolate cream|candied cranberries|herb filling|simple syrup|bottom layer|second layer|third layer|fourth layer|streusel|root vegetables|gremolata topping|meringue layers|peppermint syrup|herb & lemon sauce|béchamel sauce|italian béchamel sauce-besciamella|caramel sauce|bourbon whipped cream|bourbon pan gravy|caramel/pecan glaze|mix together|sift together|cocktail)\s*:?$', re.I)
def is_label(s):
    s = s.strip()
    if re.search(r'\d|[½¼¾⅓⅔⅛]', s): return False
    return bool(LABEL_RE.match(s)) or (s.endswith(':') and len(s) < 42)
def slug(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')
ABBR = r'(?:tsp|tbl|tbsp|oz|lb|lbs|pkg|qt|qts|min|med|lg|approx|etc|vs|St|Mr|Mrs|Dr|in|hr|N\.C|c|C|pt)'
def sentences(p):
    p = p.strip()
    out, buf, depth = [], '', 0
    toks = re.split(r'(\s+)', p)
    for i, tok in enumerate(toks):
        buf += tok
        depth += tok.count('(') - tok.count(')')
        if depth > 0 or not tok.strip(): continue
        if re.search(r'[.!?…][)”"\']?$', tok):
            nxt = next((t for t in toks[i + 1:] if t.strip()), '')
            if not nxt: continue
            if re.search(r'(?:^|[\s(])' + ABBR + r'\.$', tok) and not re.match(r'[A-Z]', nxt): continue
            if re.search(r'(?:^|[\s(])' + ABBR + r'\.$', tok) and len(tok) <= 5 and re.match(r'[A-Z][a-z]', nxt) and not re.search(r'(min|hr|oz|lb|lbs|in)\.$', tok): continue
            if re.match(r'[A-Z(“"0-9]', nxt):
                out.append(buf.strip()); buf = ''
    if buf.strip(): out.append(buf.strip())
    # merge very short fragments into previous
    merged = []
    for s in out:
        if merged and (len(s) < 28 or len(merged[-1]) < 28): merged[-1] += ' ' + s
        else: merged.append(s)
    return merged
FR = {'½': .5, '¼': .25, '¾': .75, '⅓': 1 / 3, '⅔': 2 / 3, '⅛': .125}
NUM = r'(?:\d+\s+\d/\d|\d+\s*[½¼¾⅓⅔⅛]|[½¼¾⅓⅔⅛]|\d+/\d+|\d+(?:\.\d+)?)'
def val(s):
    s = s.strip()
    m = re.match(r'^(\d+)\s+(\d)/(\d)$', s)
    if m: return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    m = re.match(r'^(\d+)\s*([½¼¾⅓⅔⅛])$', s)
    if m: return int(m.group(1)) + FR[m.group(2)]
    if s in FR: return FR[s]
    m = re.match(r'^(\d+)/(\d+)$', s)
    if m: return int(m.group(1)) / int(m.group(2))
    return float(s)
SIZE = r'(?:oz|ounce|ounces|inch|in\b|lb\b|”|"|X|x|\d)'
def qty(line):
    """return [lo, hi, rest] when the leading amount is safely scalable, else None"""
    l = line.strip()
    m = re.match(r'^(about\s+)?(' + NUM + r')(\s*[-–]\s*(' + NUM + r'))?(.*)$', l, re.I)
    if not m: return None
    lo, hi, rest = m.group(2), m.group(4), m.group(5)
    if hi:
        # "1-8 oz cream cheese", "2-9 inch pie shells": count x size, scale only the count
        if re.match(r'\s*(?:oz|ounce|inch|in\b|lb\b|”|")', rest, re.I) and val(lo) <= 12 and not re.search(r'[½¼¾⅓⅔⅛/]', lo):
            return [val(lo), None, m.group(3) + rest, 'x']
        if val(hi) <= val(lo): return None
        return [val(lo), val(hi), rest]
    if re.match(r'\s*(?:' + NUM + r')', rest): return None   # "3 14 oz cans", "1 4oz."
    if re.match(r'\s*[xX]\s', rest) or re.match(r'\s*[”"]', rest): return None
    return [val(lo), None, rest]
def clean(t):
    for a, b in QUIET:
        t = re.sub(a, b, t)
    return t
VERB = r'^(Preheat|Position|Combine|Mix|In a |Place|Melt|Cook|Bring|Using|Take|Into|Cut|Wash|Beat|Saut|Heat|Whisk|Stir|For |Make|Soak|Add|Roll|Brush|Split|Core|Boil|Prepare|Trim|Bake|Finely|Coarsely|Cream|Butter |Grease|Line|Blend|Sift|Peel|Transfer|Remove|Spread|Pour)'
CONT = r'^(Days|Bread to|Before draining|Drained \(|Full bodied|Beans, drained|And peeled|Grated nutmeg|\(Canadian|Cheese cloth|Giblets$|Into ½|Room temperature|Cored, peeled|Chopped$|removed from|and seeded|Or pulverized|Or if you|milder in|sage you|cored and cut)'
raw_lines = [l.rstrip('\n') for l in open(S + 'v2010/clean.txt', encoding='utf-8')]
def norm(s): return re.sub(r'[^a-z0-9½¼¾⅓⅔⅛]+', '', s.lower())
rawmap = {}
for l in raw_lines: rawmap.setdefault(norm(l), l)
recipes, chapters_out, sections = [], [], []
seen_slugs = {}
diag = []
def build(it, chapter):
    title = TITLES.get(it['title'], it['title'])
    sl = slug(title)
    if sl in seen_slugs: sl = sl + '-' + slug(chapter.split()[0]);
    seen_slugs[sl] = 1
    r = {'id': sl, 'title': title, 'chapter': chapter, 'john': it.get('john', False), 'story': [], 'sub': [], 'parts': [], 'notes': [], 'photos': []}
    blocks = it['blocks']
    r['orig'] = []
    for b in blocks:
        if b['k'] == 'table': r['orig'] += [x for col in b['cols'] for x in col]
        elif b['k'] != 'img' and not b.get('t', '').startswith('Image may contain'): r['orig'].append('   '.join(b.get('cells') or [b.get('t', '')]))
    has_ing = any(b['k'] in ('S', 'table') for b in blocks)
    part = {'label': None, 'groups': [], 'steps': []}
    def newpart(label=None):
        nonlocal part
        if part['groups'] or part['steps']: r['parts'].append(part)
        part = {'label': label, 'groups': [], 'steps': []}
    def add_lines(lines):
        nonlocal part
        if part['steps']: newpart(pend.pop() if pend else None)
        elif pend and not part['groups'] and not part['label']: part['label'] = pend.pop()
        for ln in lines:
            ln = ln.strip()
            if not ln: continue
            if is_label(ln):
                part['groups'].append({'label': ln.rstrip(':').strip(), 'items': []}); continue
            if not part['groups']: part['groups'].append({'label': None, 'items': []})
            items = part['groups'][-1]['items']
            if items and (re.match(r'^[a-z(]', ln) and not re.match(r'^(about|or)\b', ln) and (items[-1].count('(') > items[-1].count(')') or re.match(r'^[a-z]', ln)) or items[-1].count('(') > items[-1].count(')') or ln in ('Or', 'Chopped')):
                items[-1] += ' ' + ln
            elif items and not re.search(r'[.)]$', items[-1]) and re.match(CONT, ln):
                items[-1] += ' ' + ln
            else: items.append(ln)
    pend = []; seen_ing = seen_step = False; cap_for = None; cap_left = 0
    for i, b in enumerate(blocks):
        k = b['k']
        if k == 'img':
            for f in b['files']: r['photos'].append({'file': f, 'cap': []})
            cap_for = r['photos'][-1]; cap_left = 3; continue
        t = b.get('t', '')
        if cap_left and k in ('S', 'X', 'P') and len(t) < 110 and not re.match(r'^\s*' + NUM + r'\s', t + ' ') or (cap_left and re.match(r'^(19|20)[\d?]{2}$', t)):
            if not t.startswith('Image may contain'): cap_for['cap'].append(t)
            cap_left -= 1; continue
        cap_left = 0
        if t.startswith('Image may contain'): continue
        if k == 'E' or (k == 'X' and len(t) > 110):
            if seen_ing and re.match(VERB, t) and len(t) > 80:
                part['steps'].append({'h': None, 'text': t}); seen_step = True; continue
            (r['story'] if not seen_step else r['notes']).append(t); continue
        if k == 'X':
            if not (seen_ing or seen_step) and not is_label(t) and not re.search(r'\d', t): r['sub'].append(t)
            elif re.search(r'\d|[½¼¾]', t) and not is_label(t): add_lines(b.get('cells') or re.split(r' {3,}', t)); seen_ing = True
            else: pend.append(t.rstrip(':'))
            continue
        if k == 'table':
            add_lines([x for col in b['cols'] for x in col]); seen_ing = True; continue
        if k == 'S':
            cells = b.get('cells') or [t]
            # a bold line that is really prose (credit or note)
            if len(cells) == 1 and len(t) > 150 and seen_step and not re.match(r'^\s*' + NUM, t):
                part['steps'].append({'h': None, 'text': t}); seen_step = True; continue
            later_p = any(x['k'] in ('P', 'S', 'table') for x in blocks[i + 1:])
            if len(cells) == 1 and seen_step and not later_p and not re.match(r'^\s*' + NUM, t) and not is_label(t):
                r['notes'].append(t); continue
            add_lines(cells); seen_ing = True; continue
        if k == 'P':
            if has_ing and not seen_ing and not seen_step and len(t) > 0 and not re.match(r'^(Preheat|Combine|Mix|Melt|Place|In a|Using|Bring)', t):
                (r['sub'] if len(t) < 40 else r['story']).append(t); continue
            pc = [c.strip() for c in re.split(r'\t+| {3,}', (rawmap.get(norm(t)) or t).strip()) if c.strip()]
            if len(t) < 120 and not t.rstrip().endswith('.') and not re.match(r'^\d+\.\s', t) and (re.match(r'^\s*(about\s+)?' + NUM + r'\s', t + ' ') or (len(pc) > 1 and all(len(c) < 70 for c in pc))):
                add_lines(pc); seen_ing = True; continue
            lead = b.get('lead')
            m = re.match(r'^([A-Z][A-Za-z’\' /&-]{2,38}):\s+(.*)$', t)
            if lead and t.startswith(lead): body = t[len(lead):].lstrip(' :'); h = lead
            elif m and not re.match(r'^(Note|Serve|Makes)', m.group(1)): h, body = m.group(1), m.group(2)
            else: h, body = None, t
            part['steps'].append({'h': h, 'text': body}); seen_step = True
    newpart()
    # overrides
    if title in GROUPS:
        g = GROUPS[title]
        r['parts'][0]['groups'] = [{'label': lab, 'items': items} for lab, items in g]
        for p_ in r['parts'][1:]:
            if p_.get('_keep'): continue
        if title in DROP:
            for p_ in r['parts'][1:]: p_['groups'] = []
    if title in NOTES_TAIL:
        n = NOTES_TAIL[title]; last = r['parts'][-1]
        moved = last['steps'][-n:]; last['steps'] = last['steps'][:-n]
        r['notes'] = [m['text'] if not m['h'] else m['h'] + ': ' + m['text'] for m in moved] + r['notes']
    if title in STORY_FIX:
        n = STORY_FIX[title]; first = r['parts'][0]
        moved = first['steps'][:n]; first['steps'] = first['steps'][n:]
        r['story'] += [m['text'] for m in moved]
    # tidy: duplicate combined cells, empty groups become step headings
    for p_ in r['parts']:
        for g in p_['groups']:
            ns_ = [norm(x) for x in g['items']]
            g['items'] = [x for x, n_ in zip(g['items'], ns_) if sum(1 for m_ in ns_ if m_ != n_ and len(m_) > 6 and m_ in n_) < 2]
        empties = [g for g in p_['groups'] if not g['items'] and g['label']]
        p_['groups'] = [g for g in p_['groups'] if g['items']]
        if empties and p_['steps'] and not p_['steps'][0]['h'] and not p_['groups']: p_['steps'][0]['h'] = empties[0]['label']
    # steps -> sentences, cleaning, scaling
    edits_here = [e for e in EDITS if e['recipe'] == title or e['recipe'] == sl]
    def apply(t, where):
        t = clean(t)
        for e in edits_here:
            if e.get('where', where) == where and e['find'] in t:
                t = t.replace(e['find'], '⟦%s⟧' % e['id'], 1); e['hit'] = e.get('hit', 0) + 1
        return t
    ni = ns = 0
    for p_ in r['parts']:
        for g in p_['groups']:
            its = []
            for x in g['items']:
                x2 = apply(x, 'ing'); q = qty(x2) if '⟦' not in x2[:3] else None
                its.append({'t': x2, 'q': q}); ni += 1
            g['items'] = its
        st = []
        for s_ in p_['steps']:
            first = True
            for sent in sentences(apply(s_['text'], 'step')):
                st.append({'h': s_['h'] if first else None, 't': sent}); first = False; ns += 1
        p_['steps'] = st
    r['notes'] = [apply(n_, 'note') for n_ in r['notes']]
    r['asks'] = [a for a in ASKS if a['recipe'] == title]
    diag.append((chapter[:10], title, len(r['story']), len(r['parts']), ni, ns, len(r['notes']), len(r['photos'])))
    return r
for c in D['chapters']:
    ch = {'title': c['title'], 'items': []}
    for it in c['items']:
        if it['type'] == 'recipe':
            r = build(it, c['title']); recipes.append(r); ch['items'].append({'r': r['id']})
        else:
            sec = {'title': it['title'], 'text': [], 'photos': [], 'lines': []}
            cap_for = None; cap_left = 0
            for b in it['blocks']:
                if b['k'] == 'img':
                    for f in b['files']: sec['photos'].append({'file': f, 'cap': []})
                    cap_for = sec['photos'][-1]; cap_left = 3; continue
                t = b.get('t', '')
                if t.startswith('Image may contain'): continue
                if cap_left and len(t) < 260 and b['k'] in ('S', 'P', 'X') :
                    cap_for['cap'].append(t); cap_left -= 1; continue
                cap_left = 0
                if b['k'] in ('E', 'X', 'P') : sec['text'].append(t)
                else: sec['lines'].append(t)
            ch['items'].append({'s': sec})
    chapters_out.append(ch)
out = {'chapters': chapters_out, 'recipes': recipes, 'edits': {e['id']: {k: e[k] for k in ('recipe', 'find', 'fix', 'why')} for e in EDITS},
       'front': D['front'], 'closing': D['closing']}
json.dump(out, open(S + 'build/data.json', 'w'), ensure_ascii=False, indent=1)
if '-v' in sys.argv:
    for d in diag: print('%-10s %-52s story=%d parts=%d ing=%2d steps=%2d notes=%d ph=%d' % (d[0], d[1][:52], *d[2:]))
print(len(recipes), 'recipes;', 'unhit edits:', [e['id'] for e in EDITS if not e.get('hit')])
bad = [d for d in diag if d[4] == 0 or d[5] == 0]
print('no ingredients or no steps:', [(d[1], d[4], d[5]) for d in bad])
