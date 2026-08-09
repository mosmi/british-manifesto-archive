import json

def oddr_neighbors(q, r):
    if r % 2 == 0:
        return [(q+1, r), (q, r-1), (q-1, r-1), (q-1, r), (q-1, r+1), (q, r+1)]
    else:
        return [(q+1, r), (q+1, r-1), (q, r-1), (q-1, r), (q, r+1), (q+1, r+1)]

def connected_components(occupied):
    seen = set()
    comps = []
    for c in occupied:
        if c in seen: continue
        comp = set()
        stack = [c]
        seen.add(c)
        while stack:
            cur = stack.pop()
            comp.add(cur)
            for nb in oddr_neighbors(*cur):
                if nb in occupied and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps

# 1. 1984 & 1989 Fixes:
# - Durham at (4,13) alongside Cumbria at (3,13) -> 2-hex row 13!
# - London South Inner at (7,1) directly below London Central (7,2), closing gap!
# - Sussex West at (6,0) on South Coast below London!
for yr in ['1984', '1989']:
    file_path = f'data/hex/euro/{yr}.hexjson'
    with open(file_path) as f:
        data = json.load(f)

    hexes = data['hexes']

    # Border & Durham fix
    if 'durham' in hexes and 'cumbria-and-lancashire-north' in hexes:
        hexes['cumbria-and-lancashire-north']['q'], hexes['cumbria-and-lancashire-north']['r'] = 3, 13
        hexes['durham']['q'], hexes['durham']['r'] = 4, 13

    # London South Inner & Sussex West fix
    if 'london-south-inner' in hexes and 'sussex-west' in hexes:
        hexes['london-south-inner']['q'], hexes['london-south-inner']['r'] = 7, 1
        hexes['sussex-west']['q'], hexes['sussex-west']['r'] = 6, 0

    # Verify no duplicate coordinates
    coords = [(h['q'], h['r']) for h in hexes.values()]
    assert len(coords) == len(set(coords)), f'{yr}: duplicate coords found!'

    mainland_keys = [k for k in hexes if not k.startswith('northern-ireland') and k != 'highlands-and-islands']
    mainland_cells = {(hexes[k]['q'], hexes[k]['r']) for k in mainland_keys}
    assert len(connected_components(mainland_cells)) == 1, f'{yr}: mainland not contiguous!'

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f'Updated {file_path}: Durham at (4,13), London South Inner at (7,1) touching London Central, Sussex West at (6,0).')

# 2. 1994 Fixes:
# - Cornwall and West Plymouth at (0,0) (South-West tip of UK!)
# - South Wales 5 seats at q=1..3, r=3..5
# - Cotswolds at (3,3) touching South Wales East (2,3) directly, closing gap!
file_path_94 = 'data/hex/euro/1994.hexjson'
with open(file_path_94) as f:
    data94 = json.load(f)

hexes94 = data94['hexes']

if 'cornwall-and-west-plymouth' in hexes94:
    hexes94['cornwall-and-west-plymouth']['q'], hexes94['cornwall-and-west-plymouth']['r'] = 0, 0
if 'devon' in hexes94:
    hexes94['devon']['q'], hexes94['devon']['r'] = 1, 1

if 'south-wales-west' in hexes94: hexes94['south-wales-west']['q'], hexes94['south-wales-west']['r'] = 1, 3
if 'south-wales-central' in hexes94: hexes94['south-wales-central']['q'], hexes94['south-wales-central']['r'] = 2, 3
if 'south-wales-east' in hexes94: hexes94['south-wales-east']['q'], hexes94['south-wales-east']['r'] = 3, 3
if 'mid-and-west-wales' in hexes94: hexes94['mid-and-west-wales']['q'], hexes94['mid-and-west-wales']['r'] = 2, 4
if 'north-wales' in hexes94: hexes94['north-wales']['q'], hexes94['north-wales']['r'] = 2, 5

if 'cotswolds' in hexes94:
    hexes94['cotswolds']['q'], hexes94['cotswolds']['r'] = 4, 3

coords94 = [(h['q'], h['r']) for h in hexes94.values()]
assert len(coords94) == len(set(coords94)), '1994: duplicate coords found!'

mainland_keys94 = [k for k in hexes94 if not k.startswith('northern-ireland') and k != 'highlands-and-islands']
mainland_cells94 = {(hexes94[k]['q'], hexes94[k]['r']) for k in mainland_keys94}
assert len(connected_components(mainland_cells94)) == 1, '1994: mainland not contiguous!'

with open(file_path_94, 'w') as f:
    json.dump(data94, f, indent=2)

print('Updated 1994.hexjson: Cornwall & Plymouth at (0,0), Wales touching Cotswolds at (4,3), zero gaps.')
