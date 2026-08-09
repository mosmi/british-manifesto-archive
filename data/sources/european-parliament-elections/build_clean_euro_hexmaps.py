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

# Load 1979 hexjson as gold reference (1979 remains 100% untouched)
with open('data/hex/euro/1979.hexjson') as f:
    d79 = json.load(f)['hexes']

# 1984/1989 mapping from 1979 base
map_84 = {
    "cumbria-and-lancashire-north": d79["cumbria"],
    "durham": d79["durham"],
    "scotland-south": d79["south-of-scotland"],
    "strathclyde-west": d79["strathclyde-west"],
    "glasgow": d79["glasgow"],
    "strathclyde-east": d79["strathclyde-east"],
    "lothians": d79["lothians"],
    "scotland-mid-and-fife": d79["mid-scotland-and-fife"],
    "scotland-north-east": d79["north-east-scotland"],
    "highlands-and-islands": d79["highlands-and-islands"],
    "wales-north": d79["wales-north"],
    "wales-mid-and-west": d79["wales-mid-and-west"],
    "wales-south": d79["wales-south"],
    "wales-south-east": d79["wales-south-east"],
}

# Fix Sussex West vs London South Inner in 1984 & 1989
# In 1979:
# London South Inner is at (7, 1) or (6, 2)
# Sussex West is at (5, 1)
# We swap r of Sussex West and London South Inner if Sussex West is above London South Inner!

for yr in ['1984', '1989']:
    file_path = f'data/hex/euro/{yr}.hexjson'
    with open(file_path) as f:
        data = json.load(f)

    hexes = data['hexes']

    # 1. NI 3-hex triangle at r=12..13, q=-1..0
    hexes['northern-ireland-1']['q'], hexes['northern-ireland-1']['r'] = -1, 13
    hexes['northern-ireland-2']['q'], hexes['northern-ireland-2']['r'] = -1, 12
    hexes['northern-ireland-3']['q'], hexes['northern-ireland-3']['r'] = 0, 12

    # 2. Wales touching England (q=2)
    hexes['wales-south-east']['q'], hexes['wales-south-east']['r'] = 1, 3
    hexes['wales-south']['q'], hexes['wales-south']['r'] = 2, 3
    hexes['wales-mid-and-west']['q'], hexes['wales-mid-and-west']['r'] = 2, 4
    hexes['wales-north']['q'], hexes['wales-north']['r'] = 2, 5

    # 3. Scotland / Border
    hexes['cumbria-and-lancashire-north']['q'], hexes['cumbria-and-lancashire-north']['r'] = 3, 13
    hexes['durham']['q'], hexes['durham']['r'] = 4, 13
    hexes['strathclyde-west']['q'], hexes['strathclyde-west']['r'] = 3, 14
    hexes['scotland-south']['q'], hexes['scotland-south']['r'] = 4, 14
    hexes['glasgow']['q'], hexes['glasgow']['r'] = 3, 15
    hexes['strathclyde-east']['q'], hexes['strathclyde-east']['r'] = 4, 15
    hexes['lothians']['q'], hexes['lothians']['r'] = 5, 15
    hexes['scotland-mid-and-fife']['q'], hexes['scotland-mid-and-fife']['r'] = 3, 16
    hexes['scotland-north-east']['q'], hexes['scotland-north-east']['r'] = 4, 16
    hexes['highlands-and-islands']['q'], hexes['highlands-and-islands']['r'] = 4, 18

    # 4. Fix relative oddity: Sussex West (South Coast) vs London South Inner
    # London South Inner -> (7, 2), Sussex West -> (5, 1)
    if 'london-south-inner' in hexes and 'sussex-west' in hexes:
        hexes['london-south-inner']['q'], hexes['london-south-inner']['r'] = 7, 2
        hexes['sussex-west']['q'], hexes['sussex-west']['r'] = 5, 1

    # Verify no clashes
    coords = [(h['q'], h['r']) for h in hexes.values()]
    assert len(coords) == len(set(coords)), f'{yr}: duplicate coords found!'

    mainland_keys = [k for k in hexes if not k.startswith('northern-ireland') and k != 'highlands-and-islands']
    mainland_cells = {(hexes[k]['q'], hexes[k]['r']) for k in mainland_keys}
    assert len(connected_components(mainland_cells)) == 1, f'{yr}: mainland not contiguous!'

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f'Updated {file_path}: 100% clean, zero clashes, Sussex West on South Coast below London South Inner.')

# 1994 Alignment
file_path_94 = 'data/hex/euro/1994.hexjson'
with open(file_path_94) as f:
    data94 = json.load(f)

hexes94 = data94['hexes']

hexes94['northern-ireland-1']['q'], hexes94['northern-ireland-1']['r'] = -1, 13
hexes94['northern-ireland-2']['q'], hexes94['northern-ireland-2']['r'] = -1, 12
hexes94['northern-ireland-3']['q'], hexes94['northern-ireland-3']['r'] = 0, 12

hexes94['south-wales-west']['q'], hexes94['south-wales-west']['r'] = 0, 3
hexes94['south-wales-central']['q'], hexes94['south-wales-central']['r'] = 1, 3
hexes94['south-wales-east']['q'], hexes94['south-wales-east']['r'] = 2, 3
hexes94['mid-and-west-wales']['q'], hexes94['mid-and-west-wales']['r'] = 1, 4
hexes94['north-wales']['q'], hexes94['north-wales']['r'] = 1, 5

hexes94['cumbria-and-lancashire-north']['q'], hexes94['cumbria-and-lancashire-north']['r'] = 3, 13
hexes94['durham']['q'], hexes94['durham']['r'] = 4, 13
hexes94['strathclyde-west']['q'], hexes94['strathclyde-west']['r'] = 3, 14
hexes94['south-of-scotland']['q'], hexes94['south-of-scotland']['r'] = 4, 14
hexes94['glasgow']['q'], hexes94['glasgow']['r'] = 3, 15
hexes94['strathclyde-east']['q'], hexes94['strathclyde-east']['r'] = 4, 15
hexes94['lothians']['q'], hexes94['lothians']['r'] = 5, 15
hexes94['mid-scotland-and-fife']['q'], hexes94['mid-scotland-and-fife']['r'] = 3, 16
hexes94['north-east-scotland']['q'], hexes94['north-east-scotland']['r'] = 4, 16
hexes94['highlands-and-islands']['q'], hexes94['highlands-and-islands']['r'] = 4, 18

coords94 = [(h['q'], h['r']) for h in hexes94.values()]
assert len(coords94) == len(set(coords94)), '1994: duplicate coords found!'

mainland_keys94 = [k for k in hexes94 if not k.startswith('northern-ireland') and k != 'highlands-and-islands']
mainland_cells94 = {(hexes94[k]['q'], hexes94[k]['r']) for k in mainland_keys94}
assert len(connected_components(mainland_cells94)) == 1, '1994: mainland not contiguous!'

with open(file_path_94, 'w') as f:
    json.dump(data94, f, indent=2)

print('Updated 1994.hexjson: 100% clean, zero clashes.')
