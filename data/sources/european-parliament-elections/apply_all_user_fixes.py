import json
import os
import re

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

# Members per election
ni_members = {
    '1979': {'top': ('John Hume', 'sdlp'), 'left': ('Ian Paisley', 'dup'), 'right': ('John Taylor', 'uup')},
    '1984': {'top': ('John Hume', 'sdlp'), 'left': ('Ian Paisley', 'dup'), 'right': ('John Taylor', 'uup')},
    '1989': {'top': ('John Hume', 'sdlp'), 'left': ('Ian Paisley', 'dup'), 'right': ('Jim Nicholson', 'uup')},
    '1994': {'top': ('John Hume', 'sdlp'), 'left': ('Ian Paisley', 'dup'), 'right': ('Jim Nicholson', 'uup')},
}

for yr in ['1979', '1984', '1989', '1994']:
    file_path = f'data/hex/euro/{yr}.hexjson'
    with open(file_path) as f:
        data = json.load(f)

    hexes = data['hexes']

    # 1. Wales shift right to touch England directly (no 1-cell gap)
    wal_keys = [k for k in hexes if 'wales' in k]
    # In 1979 & 1994, check if Wales is at q=1 and shift to q=2
    min_wal_q = min(hexes[k]['q'] for k in wal_keys)
    if min_wal_q == 0 or min_wal_q == 1:
        shift_q = 2 - min_wal_q
        for k in wal_keys:
            hexes[k]['q'] += shift_q

    # 2. Eliminate single-hex rows (South of Scotland & Durham)
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

    # 3. Northern Ireland 3-hex triangle cluster (detached at q=-3, -2, r=12, 13)
    # Shape matching user screenshot:
    # Top (SDLP - green): (-3, 13)
    # Bottom-left (DUP - red/orange): (-3, 12)
    # Bottom-right (UUP - blue): (-2, 12)
    
    # Remove any existing NI keys
    for k in list(hexes.keys()):
        if 'northern-ireland' in k:
            del hexes[k]

    m_info = ni_members[yr]
    hexes['northern-ireland-1'] = {
        'n': f"Northern Ireland — {m_info['top'][0]}",
        'q': -3,
        'r': 13,
        'party': m_info['top'][1],
        'winner': m_info['top'][0]
    }
    hexes['northern-ireland-2'] = {
        'n': f"Northern Ireland — {m_info['left'][0]}",
        'q': -3,
        'r': 12,
        'party': m_info['left'][1],
        'winner': m_info['left'][0]
    }
    hexes['northern-ireland-3'] = {
        'n': f"Northern Ireland — {m_info['right'][0]}",
        'q': -2,
        'r': 12,
        'party': m_info['right'][1],
        'winner': m_info['right'][0]
    }

    # Verify coordinates
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

    # Verify NI detached from GB
    assert not any(nb in mainland_cells for c in ni_cells for nb in oddr_neighbors(*c)), f'{yr}: NI touches GB mainland!'

    data['meta']['ni_seats'] = 3
    data['meta']['layout_method'] = 'compact-fptp-3ni-triangle'
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f'Saved {file_path}: {len(hexes)} hexes. NI 3-hex triangle detached at q=-3..-2, r=12..13. Wales touching England. Border 2-hex wide.')
