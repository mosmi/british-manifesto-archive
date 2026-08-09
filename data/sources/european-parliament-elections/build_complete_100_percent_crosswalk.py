import json
import os
import re

# Load hexjson files
with open('data/hex/elections/1979.hexjson') as f:
    hex_79 = json.load(f)['hexes']
with open('data/hex/elections/1983.hexjson') as f:
    hex_83 = json.load(f)['hexes']
with open('data/hex/elections/1997.hexjson') as f:
    hex_97 = json.load(f)['hexes']

with open('data/sources/european-parliament-elections/ep_pages_wikitext.json') as f:
    pages = json.load(f)

with open('data/sources/european-parliament-elections/constituency-winners-1979-1994.json') as f:
    winners = json.load(f)['elections']

def fix_typos(s):
    s = s.replace('Nottinghsm', 'Nottingham')
    s = s.replace('Wolverhamton', 'Wolverhampton')
    s = s.replace('Westmister', 'Westminster')
    s = s.replace('Ashton-under-Line', 'Ashton-under-Lyne')
    return s

def swap_compass(s):
    m = re.match(r'^(.*?)\s+(N|S|E|W|NE|NW|SE|SW)$', s)
    if m:
        place, compass = m.group(1), m.group(2)
        comp_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West', 'NE': 'North East', 'NW': 'North West', 'SE': 'South East', 'SW': 'South West'}
        return f'{comp_map[compass]} {place}'
    return s

def expand_compass(s):
    s = re.sub(r'\bNE\b', 'North East', s)
    s = re.sub(r'\bNW\b', 'North West', s)
    s = re.sub(r'\bSE\b', 'South East', s)
    s = re.sub(r'\bSW\b', 'South West', s)
    s = re.sub(r'\bN\b', 'North', s)
    s = re.sub(r'\bS\b', 'South', s)
    s = re.sub(r'\bE\b', 'East', s)
    s = re.sub(r'\bW\b', 'West', s)
    s = s.replace('Birmingha ', 'Birmingham ')
    return s

def norm_clean(s):
    s = re.sub(r'\(.*?\)', '', s)
    s = s.replace('&', 'and').replace('-', ' ').replace('.', '')
    s = s.replace('kingston upon hull', 'hull')
    s = s.replace('newcastle upon tyne', 'newcastle')
    s = s.replace('saint ', 'st ')
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

def norm(s):
    s = fix_typos(s)
    return norm_clean(expand_compass(s)), norm_clean(swap_compass(s))

def build_norm_map(hexes):
    nm = {}
    for k in hexes.keys():
        s1, s2 = norm(k)
        nm[s1] = k
        nm[s2] = k
    return nm

map_79 = build_norm_map(hex_79)
map_83 = build_norm_map(hex_83)
map_97 = build_norm_map(hex_97)

# Authoritative manual fallbacks for EP constituencies whose wikitext is unlinked/plain text
manual_compositions = {
    '1979': {
        'Bedfordshire South': ['Luton E', 'Luton W', 'Bedfordshire S', 'Hitchin', 'Hemel Hempstead'],
        'Cornwall & Plymouth': ['Bodmin', 'Falmouth & Camborne', 'St Ives', 'Truro', 'Plymouth Devonport', 'Plymouth Drake', 'Plymouth Sutton', 'Cornwall N'],
        'Cotswolds': ['Cheltenham', 'Cirencester & Tewkesbury', 'Gloucester', 'Stroud', 'Gloucestershire W', 'Gloucestershire S', 'Worcestershire S'],
        'Hereford & Worcester': ['Hereford', 'Worcester', 'Kidderminster', 'Leominster', 'Bromsgrove & Redditch'],
        'Northern Ireland': [k for k, v in hex_79.items() if v.get('region', '') == 'N07000001' or k in ['Armagh', 'Londonderry', 'Down S', 'Antrim N', 'Fermanagh & S Tyrone', 'Belfast S', 'Down N', 'Antrim S', 'Belfast E', 'Ulster Mid', 'Belfast W', 'Belfast N']]
    },
    '1984': {
        'Bedfordshire South': ['Luton South', 'Luton North', 'South West Bedfordshire', 'West Hertfordshire', 'Stevenage'],
        'Cornwall & Plymouth': ['Cornwall South East', 'Falmouth and Camborne', 'St Ives', 'Truro', 'Plymouth Devonport', 'Plymouth Drake', 'Plymouth Sutton', 'North Cornwall'],
        'Cotswolds': ['Cheltenham', 'Cirencester and Tewkesbury', 'Gloucester', 'Stroud', 'West Gloucestershire', 'North Wiltshire'],
        'Hereford & Worcester': ['Hereford', 'Worcester', 'Mid Worcestershire', 'Wyre Forest', 'Leominster', 'South Worcestershire'],
        'Cleveland & Yorkshire North': 'Cleveland and Yorkshire North (European Parliament constituency)',
        'Northern Ireland': [k for k, v in hex_83.items() if v.get('region', '') == 'N07000001' or 'Northern Ireland' in k or k.startswith('Belfast') or k.startswith('Antrim') or k.startswith('Down')]
    },
    '1994': {
        'Cotswolds': ['Cheltenham', 'Cirencester and Tewkesbury', 'Gloucester', 'Stroud', 'Forest of Dean', 'North Wiltshire'],
        'Northern Ireland': [k for k, v in hex_97.items() if v.get('region', '') == 'N07000001' or 'Northern Ireland' in k or k.startswith('Belfast') or k.startswith('Antrim') or k.startswith('Down')]
    }
}

aliases = {
    'Wales North': 'North Wales (European Parliament constituency)',
    'Wales Mid & West': 'Mid and West Wales (European Parliament constituency)',
    'Wales South': 'South Wales (European Parliament constituency)',
    'Wales South East': 'South Wales East (European Parliament constituency)',
    'Wales Mid and West': 'Mid and West Wales (European Parliament constituency)',
    'Tyne South and Wear': 'Tyne South and Wear (European Parliament constituency)',
    'Tyne and Wear': 'Tyne and Wear (European Parliament constituency)',
    'Scotland Mid & Fife': 'Mid Scotland and Fife (European Parliament constituency)',
    'Scotland Mid and Fife': 'Mid Scotland and Fife (European Parliament constituency)',
    'Scotland South': 'South of Scotland (European Parliament constituency)',
    'Scotland North East': 'North East Scotland (European Parliament constituency)',
    'Cambridgeshire & Bedfordshire North': 'Cambridge and Bedfordshire North (European Parliament constituency)',
    'Cambridgeshire and Bedfordshire North': 'Cambridge and Bedfordshire North (European Parliament constituency)',
    'Cleveland & Yorkshire North': 'Cleveland and Yorkshire North (European Parliament constituency)',
}

def find_wiki_page(ep_name):
    if ep_name in aliases and aliases[ep_name] in pages:
        return aliases[ep_name]
    target1 = f'{ep_name} (European Parliament constituency)'
    if target1 in pages:
        return target1
    if ep_name in pages:
        return ep_name
    n1, n2 = norm(ep_name)
    for wt in pages.keys():
        w1, w2 = norm(re.sub(r'\s*\(European Parliament constituency\)', '', wt))
        if n1 in (w1, w2) or n2 in (w1, w2):
            return wt
    return None

def extract_seats_links_and_text(wt, hex_norm_map):
    extracted_w_names = []
    links = re.findall(r'\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]', wt)
    for target, display in links:
        if any(x in target for x in ['Category:', 'File:', 'European Parliament', 'Wikipedia:', 'Template:', 'List of', 'proportional representation']):
            continue
        item = display if display else target
        item = re.sub(r'\s*\(UK Parliament constituency\)', '', target if not display else display).strip()
        n1, n2 = norm(item)
        w_name = hex_norm_map.get(n1) or hex_norm_map.get(n2)
        if w_name and w_name not in extracted_w_names:
            extracted_w_names.append(w_name)

    clean_wt = re.sub(r'<.*?>', ' ', wt)
    clean_wt = re.sub(r'\[\[.*?\]\]', ' ', clean_wt)
    tokens = [t.strip() for t in re.split(r'[;,\.\n]', clean_wt) if t.strip()]
    for tok in tokens:
        n1, n2 = norm(tok)
        w_name = hex_norm_map.get(n1) or hex_norm_map.get(n2)
        if w_name and w_name not in extracted_w_names:
            extracted_w_names.append(w_name)
    return extracted_w_names

for yr, hex_data, hex_norm_map in [('1979', hex_79, map_79), ('1984', hex_83, map_83), ('1994', hex_97, map_97)]:
    eps = [c['constituency'] for c in winners[yr]['constituencies']]
    crosswalk = {}
    hex_to_ep = {}
    centroids = {}
    
    for ep in eps:
        matched_westminster = []
        if yr in manual_compositions and ep in manual_compositions[yr]:
            matched_westminster = manual_compositions[yr][ep]
        else:
            page_title = find_wiki_page(ep)
            wt = pages.get(page_title, '') if page_title else ''
            matched_westminster = extract_seats_links_and_text(wt, hex_norm_map)
            
        crosswalk[ep] = matched_westminster
        for w in matched_westminster:
            hex_to_ep[w] = ep
            
        # Calculate q, r centroid for EP constituency
        q_sum, r_sum, count = 0, 0, 0
        for w in matched_westminster:
            if w in hex_data:
                q_sum += hex_data[w]['q']
                r_sum += hex_data[w]['r']
                count += 1
        if count > 0:
            centroids[ep] = {
                'q': round(q_sum / count),
                'r': round(r_sum / count),
                'count': count
            }

    empty_eps = [ep for ep, seats in crosswalk.items() if len(seats) == 0]
    total_hexes = list(hex_data.keys())
    unmapped_hexes = [k for k in total_hexes if k not in hex_to_ep]

    print(f'Year {yr}: {len(crosswalk)} EP constituencies. Empty EP lists: {len(empty_eps)}. Mapped {len(hex_to_ep)} / {len(total_hexes)} total Westminster hexes. Centroids calculated: {len(centroids)}')

    out_path = f'data/sources/european-parliament-elections/westminster-to-ep/{yr}.json'
    out_data = {
        'metadata': {
            'year': yr,
            'title': f'Westminster to EP Constituency Crosswalk ({yr})',
            'description': f'Mapping of UK European Parliament constituencies to Westminster Parliamentary constituencies and calculated (q,r) centroids for the {yr} FPTP era.',
            'ep_constituencies_count': len(crosswalk),
            'westminster_constituencies_mapped': len(hex_to_ep)
        },
        'centroids': centroids,
        'ep_to_westminster': crosswalk,
        'westminster_to_ep': hex_to_ep
    }
    with open(out_path, 'w') as f:
        json.dump(out_data, f, indent=2)
    print(f'Saved {out_path}')
