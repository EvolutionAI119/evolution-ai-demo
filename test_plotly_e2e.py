#!/usr/bin/env python3
"""
End-to-end Plotly rendering test.
Generates a real Plotly HTML file to verify mesh data is correct.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import plotly.graph_objects as go
import plotly

print(f"Plotly version: {plotly.__version__}")

# Mock Streamlit for app.py imports
class MockSessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)

class MockStreamlit:
    class session_state:
        _state = {"car_type": "sedan", "lang": "zh"}
        @classmethod
        def get(cls, key, default=None):
            return cls._state.get(key, default)
        @classmethod
        def __getitem__(cls, key):
            return cls._state[key]
        @classmethod
        def __setitem__(cls, key, value):
            cls._state[key] = value
        @classmethod
        def __contains__(cls, key):
            return key in cls._state
    
    @staticmethod
    def spinner(msg):
        class Ctx:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return Ctx()
    
    @staticmethod
    def info(msg): pass
    @staticmethod
    def warning(msg): pass
    @staticmethod
    def error(msg): pass
    @staticmethod
    def success(msg): pass
    @staticmethod
    def write(msg): pass
    @staticmethod
    def plotly_chart(fig, **kwargs):
        # Save to HTML for inspection
        fig.write_html("/tmp/test_plotly_output.html")
        print(f"[mock] Saved figure to /tmp/test_plotly_output.html")

sys.modules['streamlit'] = MockStreamlit()

# Now import app.py components
from app import (
    build_full_car_geometric,
    CoreCarParams,
    CAR_TYPE_PRESETS,
    surface_dict_to_plotly,
)

print("\n=== End-to-End Plotly Rendering Test ===\n")

# Get preset
preset = CAR_TYPE_PRESETS["sedan"]

# Build params (convert mm to m, derive overhangs)
length_m = preset["length"] / 1000.0
width_m = preset["width"] / 1000.0
height_m = preset["height"] / 1000.0
wheelbase_m = preset["wheelbase"] / 1000.0
wheel_arch_m = preset["wheel_arch"] / 1000.0

total_oh = length_m - wheelbase_m
front_oh = round(total_oh * 0.45, 3)
rear_oh = round(total_oh - front_oh, 3)

params = CoreCarParams(
    length=length_m,
    width=width_m,
    height=height_m,
    wheelbase=wheelbase_m,
    front_overhang=front_oh,
    rear_overhang=rear_oh,
    hood_angle=preset["hood_angle"],
    roof_arc=preset["roof_arc"],
    windshield_angle=preset["windshield_angle"],
    rear_window_angle=preset["rear_window_angle"],
    wheel_arch_bulge=wheel_arch_m,
    waistline_ratio=preset["waistline"],
)

print(f"Params: L={params.length}m, W={params.width}m, H={params.height}m")

# Build geometry
print("\nBuilding full car geometry...")
parts = build_full_car_geometric(params)
print(f"Built {len(parts)} parts")

# Create a simple test figure with first 3 parts
traces = []
for i, (part_name, part_data) in enumerate(parts.items()):
    if i >= 3:
        break
    
    verts = part_data["vertices"]
    faces = part_data["faces"]
    print(f"\nPart {i}: {part_name}")
    print(f"  Vertices: {verts.shape}, dtype={verts.dtype}")
    print(f"  Faces: {faces.shape}, dtype={faces.dtype}")
    print(f"  Verts range X: [{verts[:,0].min():.3f}, {verts[:,0].max():.3f}]")
    print(f"  Verts range Y: [{verts[:,1].min():.3f}, {verts[:,1].max():.3f}]")
    print(f"  Verts range Z: [{verts[:,2].min():.3f}, {verts[:,2].max():.3f}]")
    
    # Create trace with .tolist()
    trace = go.Mesh3d(
        x=verts[:, 0].tolist(),
        y=verts[:, 1].tolist(),
        z=verts[:, 2].tolist(),
        i=faces[:, 0].tolist(),
        j=faces[:, 1].tolist(),
        k=faces[:, 2].tolist(),
        name=part_name,
        color="royalblue",
        opacity=0.8,
        flatshading=True,
    )
    traces.append(trace)
    print(f"  Trace created: {trace.name}")

# Create figure
fig = go.Figure(data=traces)
fig.update_layout(
    title="Test Plotly Render",
    scene=dict(
        aspectmode="data",
        xaxis=dict(title="X (m)"),
        yaxis=dict(title="Y (m)"),
        zaxis=dict(title="Z (m)"),
        camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    height=600,
)

# Save to HTML
output_path = "/app/data/所有对话/主对话/EVOLUTION_AI_DEMO/test_plotly_e2e.html"
fig.write_html(output_path)
print(f"\n=== Test figure saved to: {output_path} ===")

# Check file size
file_size = os.path.getsize(output_path)
print(f"File size: {file_size} bytes ({file_size/1024:.1f} KB)")

# Inspect HTML content
with open(output_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Check for bdata (binary data) which indicates Plotly 6.x serialization
if 'bdata' in html_content:
    print("\n⚠️  WARNING: HTML contains 'bdata' (binary data serialization)")
    print("   This may cause issues with older Plotly.js versions")
else:
    print("\n✓ HTML does not contain 'bdata' (uses standard JSON arrays)")

# Check for mesh data
if '"type":"mesh3d"' in html_content:
    print("✓ HTML contains mesh3d traces")
else:
    print("⚠️  WARNING: HTML does not contain mesh3d traces")

# Check for actual coordinate data
if '"x":[' in html_content and '"y":[' in html_content:
    print("✓ HTML contains coordinate arrays")
else:
    print("⚠️  WARNING: HTML may not contain coordinate data")

# Show a snippet of the data section
import re
mesh_match = re.search(r'"type":"mesh3d".{0,500}', html_content)
if mesh_match:
    print(f"\nFirst mesh3d trace snippet:")
    print(mesh_match.group(0)[:300])

print("\n=== Test complete ===")
