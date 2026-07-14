#!/usr/bin/env python3
"""
Generate complete HTML with all 34 car parts for browser verification.
This bypasses Streamlit to isolate the issue.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import plotly.graph_objects as go
from plotly.offline import plot

# Mock Streamlit
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
    def write(msg): pass

sys.modules['streamlit'] = MockStreamlit()

from app import (
    build_full_car_geometric,
    CoreCarParams,
    CAR_TYPE_PRESETS,
    surface_dict_to_plotly,
    PART_STYLES,
    PART_STYLES_DEFAULT,
)

print("=== Generating complete car HTML visualization ===\n")

# Build params
preset = CAR_TYPE_PRESETS["sedan"]
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

# Create traces
traces = []
total_verts = 0
total_faces = 0

for part_name, part_data in parts.items():
    verts = part_data["vertices"]
    faces = part_data["faces"]
    nv = len(verts)
    nf = len(faces)
    total_verts += nv
    total_faces += nf
    
    print(f"  {part_name}: {nv} vertices, {nf} faces")
    
    # Get color from PART_STYLES
    color, opacity = PART_STYLES.get(part_name, PART_STYLES_DEFAULT)
    
    trace = surface_dict_to_plotly(
        part_data, name=part_name, color=color, opacity=opacity
    )
    traces.append(trace)

print(f"\nTotal: {total_verts} vertices, {total_faces} faces")

# Create figure
fig = go.Figure(data=traces)
fig.update_layout(
    title="EVOLUTION AI - Complete Car (34 parts)",
    scene=dict(
        aspectmode="data",
        xaxis=dict(title="X (m)"),
        yaxis=dict(title="Y (m)"),
        zaxis=dict(title="Z (m)"),
        camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    height=800,
    showlegend=True,
)

# Save to HTML
output_path = "/app/data/所有对话/主对话/EVOLUTION_AI_DEMO/complete_car_visualization.html"
fig.write_html(output_path, include_plotlyjs='cdn')
print(f"\n=== HTML saved to: {output_path} ===")

file_size = os.path.getsize(output_path)
print(f"File size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")

print("\n✓ Please open this HTML file in your browser to verify:")
print(f"  file://{output_path}")
print("\nIf the car renders correctly, the issue is with Streamlit integration.")
print("If it's blank/white, the issue is with the data or Plotly configuration.")
