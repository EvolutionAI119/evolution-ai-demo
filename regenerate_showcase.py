#!/usr/bin/env python3
"""Regenerate v3_showcase.html with updated car_body_builder data."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from car_body_builder import CarParamsV3, apply_preset, build_full_car_v3, SIX_CAR_PRESETS

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

# Generate data for all 6 car types
CAR_DATA = {}
for car_type in SIX_CAR_PRESETS:
    p = apply_preset(car_type)
    parts = build_full_car_v3(p)
    total_verts = sum(len(d['vertices']) for d in parts.values())
    total_faces = sum(len(d['faces']) for d in parts.values())
    CAR_DATA[car_type] = {
        'total_parts': len(parts),
        'total_verts': total_verts,
        'total_faces': total_faces,
        'parts': {}
    }
    for name, data in parts.items():
        entry = {
            'vertices': data['vertices'].tolist(),
            'faces': data['faces'].tolist(),
            'color': data.get('color', '#c0c0c0'),
        }
        if 'opacity' in data:
            entry['opacity'] = data['opacity']
        else:
            entry['opacity'] = 1.0
        CAR_DATA[car_type]['parts'][name] = entry

    print(f"{car_type}: {len(parts)} parts, {total_verts} verts, {total_faces} faces")

# Read existing HTML template
HTML_PATH = os.path.join(os.path.dirname(__file__), 'docs', 'v3_showcase.html')
with open(HTML_PATH, 'r') as f:
    html = f.read()

# Find and replace CAR_DATA
old_start = html.index('const CAR_DATA = ')
old_end_marker = '};\n\nlet scene'
old_end = html.index(old_end_marker, old_start) + len('};')

new_car_data_json = json.dumps(CAR_DATA, cls=NpEncoder, separators=(',', ':'))
new_html = html[:old_start] + f'const CAR_DATA = {new_car_data_json}' + html[old_end:]

with open(HTML_PATH, 'w') as f:
    f.write(new_html)

print(f"\nHTML updated: {len(new_html):,} bytes")
print("Done!")
