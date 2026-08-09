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

for yr in ['1979', '1984', '1989', '1994']:
    file_path = f'data/hex/euro/{yr}.hexjson'
    with open(file_path) as f:
        data = json.load(f)

    hexes = data['hexes']

    # 1. Northern Ireland 3-hex triangle (r=12..13, q=-1..0) across ALL 4 YEARS
    hexes['northern-ireland-1']['q'], hexes['northern-ireland-1']['r'] = -1, 13
    hexes['northern-ireland-2']['q'], hexes['northern-ireland-2']['r'] = -1, 12
    hexes['northern-ireland-3']['q'], hexes['northern-ireland-3']['r'] = 0, 12

    # 2. Wales (touching England directly, no gap)
    if yr in ['1979', '1984', '1989']:
        if 'wales-south-east' in hexes: hexes['wales-south-east']['q'], hexes['wales-south-east']['r'] = 1, 3
        if 'wales-south' in hexes: hexes['wales-south']['q'], hexes['wales-south']['r'] = 2, 3
        if 'wales-mid-and-west' in hexes: hexes['wales-mid-and-west']['q'], hexes['wales-mid-and-west']['r'] = 2, 4
        if 'wales-north' in hexes: hexes['wales-north']['q'], hexes['wales-north']['r'] = 2, 5

    if yr == '1994':
        if 'south-wales-west' in hexes: hexes['south-wales-west']['q'], hexes['south-wales-west']['r'] = 1, 3
        if 'south-wales-central' in hexes: hexes['south-wales-central']['q'], hexes['south-wales-central']['r'] = 2, 3
        if 'south-wales-east' in hexes: hexes['south-wales-east']['q'], hexes['south-wales-east']['r'] = 3, 3
        if 'mid-and-west-wales' in hexes: hexes['mid-and-west-wales']['q'], hexes['mid-and-west-wales']['r'] = 2, 4
        if 'north-wales' in hexes: hexes['north-wales']['q'], hexes['north-wales']['r'] = 2, 5

    # 3. Anglo-Scottish Border (Cumbria + Durham 2 hexes wide, Strathclyde West + South of Scotland 2 hexes wide)
    if yr == '1979':
        if 'cumbria' in hexes and 'durham' in hexes:
            hexes['cumbria']['q'], hexes['cumbria']['r'] = 3, 13
            hexes['durham']['q'], hexes['durham']['r'] = 4, 13
        if 'strathclyde-west' in hexes and 'south-of-scotland' in hexes:
            hexes['strathclyde-west']['q'], hexes['strathclyde-west']['r'] = 3, 14
            hexes['south-of-scotland']['q'], hexes['south-of-scotland']['r'] = 4, 14
        if 'glasgow' in hexes and 'strathclyde-east' in hexes and 'lothians' in hexes:
            hexes['glasgow']['q'], hexes['glasgow']['r'] = 3, 15
            hexes['strathclyde-east']['q'], hexes['strathclyde-east']['r'] = 4, 15
            hexes['lothians']['q'], hexes['lothians']['r'] = 5, 15
        if 'mid-scotland-and-fife' in hexes and 'north-east-scotland' in hexes:
            hexes['mid-scotland-and-fife']['q'], hexes['mid-scotland-and-fife']['r'] = 3, 16
            hexes['north-east-scotland']['q'], hexes['north-east-scotland']['r'] = 4, 16
        if 'highlands-and-islands' in hexes:
            hexes['highlands-and-islands']['q'], hexes['highlands-and-islands']['r'] = 4, 18

    if yr in ['1984', '1989']:
        if 'cumbria-and-lancashire-north' in hexes and 'durham' in hexes:
            hexes['cumbria-and-lancashire-north']['q'], hexes['cumbria-and-lancashire-north']['r'] = 3, 13
            hexes['durham']['q'], hexes['durham']['r'] = 4, 13
        if 'strathclyde-west' in hexes and 'scotland-south' in hexes:
            hexes['strathclyde-west']['q'], hexes['strathclyde-west']['r'] = 3, 14
            hexes['scotland-south']['q'], hexes['scotland-south']['r'] = 4, 14
        if 'glasgow' in hexes and 'strathclyde-east' in hexes and 'lothians' in hexes:
            hexes['glasgow']['q'], hexes['glasgow']['r'] = 3, 15
            hexes['strathclyde-east']['q'], hexes['strathclyde-east']['r'] = 4, 15
            hexes['lothians']['q'], hexes['lothians']['r'] = 5, 15
        if 'scotland-mid-and-fife' in hexes and 'scotland-north-east' in hexes:
            hexes['scotland-mid-and-fife']['q'], hexes['scotland-mid-and-fife']['r'] = 3, 16
            hexes['scotland-north-east']['q'], hexes['scotland-north-east']['r'] = 4, 16
        if 'highlands-and-islands' in hexes:
            hexes['highlands-and-islands']['q'], hexes['highlands-and-islands']['r'] = 4, 18

    if yr == '1994':
        if 'cumbria-and-lancashire-north' in hexes and 'durham' in hexes:
            hexes['cumbria-and-lancashire-north']['q'], hexes['cumbria-and-lancashire-north']['r'] = 3, 13
            hexes['durham']['q'], hexes['durham']['r'] = 4, 13
        if 'strathclyde-west' in hexes and 'south-of-scotland' in hexes:
            hexes['strathclyde-west']['q'], hexes['strathclyde-west']['r'] = 3, 14
            hexes['south-of-scotland']['q'], hexes['south-of-scotland']['r'] = 4, 14
        if 'glasgow' in hexes and 'strathclyde-east' in hexes and 'lothians' in hexes:
            hexes['glasgow']['q'], hexes['glasgow']['r'] = 3, 15
            hexes['strathclyde-east']['q'], hexes['strathclyde-east']['r'] = 4, 15
            hexes['lothians']['q'], hexes['lothians']['r'] = 5, 15
        if 'mid-scotland-and-fife' in hexes and 'north-east-scotland' in hexes:
            hexes['mid-scotland-and-fife']['q'], hexes['mid-scotland-and-fife']['r'] = 3, 16
            hexes['north-east-scotland']['q'], hexes['north-east-scotland']['r'] = 4, 16
        if 'highlands-and-islands' in hexes:
            hexes['highlands-and-islands']['q'], hexes['highlands-and-islands']['r'] = 4, 18

    # Verify no duplicate coordinates
    coords = [(h['q'], h['r']) for h in hexes.values()]
    assert len(coords) == len(set(coords)), f'{yr}: duplicate coords found!'

    # Verify mainland contiguity
    mainland_keys = [k for k in hexes if not k.startswith('northern-ireland') and k != 'highlands-and-islands']
    mainland_cells = {(hexes[k]['q'], hexes[k]['r']) for k in mainland_keys}
    m_comps = connected_components(mainland_cells)
    assert len(m_comps) == 1, f'{yr}: mainland not contiguous!'

    # Verify NI cluster contiguity
    ni_cells = {(hexes[f'northern-ireland-{i}']['q'], hexes[f'northern-ireland-{i}']['r']) for i in range(1, 4)}
    ni_comps = connected_components(ni_cells)
    assert len(ni_comps) == 1, f'{yr}: NI cluster not contiguous!'

    # Verify NI is detached from GB mainland
    assert not any(nb in mainland_cells for c in ni_cells for nb in oddr_neighbors(*c)), f'{yr}: NI touches GB mainland!'

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f'Updated {file_path}: NI at (-1,13), (-1,12), (0,12), Wales touching England, border 2-hex wide, Glasgow Central Belt.')
