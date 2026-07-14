"""
Minimal Streamlit + Plotly 3D test.
Run: streamlit run test_streamlit_plotly.py
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("Plotly 3D Mesh Test")

# Create a simple pyramid mesh
vertices = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [1, 1, 0],
    [0, 1, 0],
    [0.5, 0.5, 1],
])

faces = np.array([
    [0, 1, 4],
    [1, 2, 4],
    [2, 3, 4],
    [3, 0, 4],
    [0, 1, 2],
    [0, 2, 3],
])

# Test 1: With .tolist()
st.subheader("Test 1: Mesh with .tolist()")
trace1 = go.Mesh3d(
    x=vertices[:, 0].tolist(),
    y=vertices[:, 1].tolist(),
    z=vertices[:, 2].tolist(),
    i=faces[:, 0].tolist(),
    j=faces[:, 1].tolist(),
    k=faces[:, 2].tolist(),
    color="royalblue",
    opacity=0.8,
    flatshading=True,
    name="pyramid",
)
fig1 = go.Figure(data=[trace1])
fig1.update_layout(
    scene=dict(
        aspectmode="data",
        xaxis=dict(title="X"),
        yaxis=dict(title="Y"),
        zaxis=dict(title="Z"),
    ),
    height=400,
)
st.plotly_chart(fig1, use_container_width=True)

# Test 2: Without .tolist() (numpy arrays)
st.subheader("Test 2: Mesh without .tolist() (numpy arrays)")
trace2 = go.Mesh3d(
    x=vertices[:, 0],
    y=vertices[:, 1],
    z=vertices[:, 2],
    i=faces[:, 0],
    j=faces[:, 1],
    k=faces[:, 2],
    color="red",
    opacity=0.8,
    flatshading=True,
    name="pyramid",
)
fig2 = go.Figure(data=[trace2])
fig2.update_layout(
    scene=dict(
        aspectmode="data",
        xaxis=dict(title="X"),
        yaxis=dict(title="Y"),
        zaxis=dict(title="Z"),
    ),
    height=400,
)
st.plotly_chart(fig2, use_container_width=True)

# Test 3: Multiple traces
st.subheader("Test 3: Multiple meshes")
traces = []
for i in range(5):
    offset = i * 2
    v = vertices.copy()
    v[:, 0] += offset
    traces.append(go.Mesh3d(
        x=v[:, 0].tolist(),
        y=v[:, 1].tolist(),
        z=v[:, 2].tolist(),
        i=faces[:, 0].tolist(),
        j=faces[:, 1].tolist(),
        k=faces[:, 2].tolist(),
        color=f"hsl({i*60}, 70%, 50%)",
        opacity=0.8,
        name=f"mesh_{i}",
    ))

fig3 = go.Figure(data=traces)
fig3.update_layout(
    scene=dict(aspectmode="data"),
    height=400,
)
st.plotly_chart(fig3, use_container_width=True)

st.success("If you can see all 3 plots above, Streamlit+Plotly is working correctly.")
st.info(f"Streamlit version: {st.__version__}")

# Debug: show the figure JSON
with st.expander("Debug: Figure JSON"):
    st.json(fig1.to_dict())
