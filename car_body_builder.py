"""
EVOLUTION AI — V2.1 Parametric Car Body Builder
================================================
Implements the full V2.1 algorithm:
  1. Hardpoint derivation from 22-dimensional parameters
  2. Side-profile curve (smoothstep interpolation)
  3. Planform width curve (smoothstep)
  4. Cross-section sweep (50 stations × 24 points)
  5. Hyper-ellipse cross-sections with wheel-arch cutting
  6. Triangle mesh generation

Author: EVOLUTION AI Team
Version: 2.1
"""
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


# ===================================================================
# 22-Dimensional Parameter System
# ===================================================================
@dataclass
class CarParams22:
    """22-dimensional car parameter set for V2.1 algorithm."""

    # --- Basic dimensions (7D) ---
    L: float = 4.800          # overall length [m]
    W: float = 1.850          # overall width [m]
    H: float = 1.450          # overall height [m]
    WB: float = 2.800         # wheelbase [m]
    hood_len: float = 1.050   # hood length [m]
    cabin_len: float = 1.800  # cabin/greenhouse length [m]
    trunk_len: float = 0.950  # trunk length [m]

    # --- Posture / attitude (5D) ---
    GC: float = 0.150         # ground clearance [m]
    hood_angle: float = 12.0  # hood tilt angle [deg]
    roof_arc: float = 0.50    # roof curvature factor [0..1]
    windshield_rake: float = 28.0  # windshield rake angle [deg]
    rear_glass_angle: float = 25.0 # rear glass angle [deg]

    # --- Surface features (8D) ---
    fender_prominence: float = 0.04   # fender bulge outward [m]
    waist_line: float = 0.75          # waistline height ratio [0..1]
    shoulder_line: float = 0.015      # shoulder line ridge [m]
    overall_arc: float = 0.5          # global body curvature [0..1]
    glass_darkness: float = 0.5       # glass opacity [0..1]
    WR: float = 0.320                 # wheel radius [m]
    WW: float = 0.200                 # wheel width [m]
    spoke_count: int = 5              # wheel spoke count

    # --- Detail params (2D) ---
    headlight_w: float = 0.30         # headlight width [m]
    headlight_h: float = 0.10         # headlight height [m]

    # Derived (not user-facing)
    TW: float = 1.580                 # track width [m]
    n_stations: int = 60              # sweep stations
    n_section_pts: int = 28           # points per cross-section

    # Vehicle type tag
    car_type: str = "sedan"


# ===================================================================
# Six Car Type Presets
# ===================================================================
SIX_CAR_PRESETS = {
    "sedan": {
        "L": 4.800, "W": 1.850, "H": 1.450, "WB": 2.800,
        "hood_len": 1.050, "cabin_len": 1.800, "trunk_len": 0.950,
        "GC": 0.150, "WR": 0.320, "TW": 1.580,
        "hood_angle": 12.0, "windshield_rake": 28.0, "rear_glass_angle": 25.0,
        "roof_arc": 0.50, "fender_prominence": 0.04, "waist_line": 0.75,
        "spoke_count": 5,
    },
    "suv": {
        "L": 4.900, "W": 1.950, "H": 1.750, "WB": 2.850,
        "hood_len": 1.100, "cabin_len": 2.000, "trunk_len": 0.800,
        "GC": 0.200, "WR": 0.360, "TW": 1.650,
        "hood_angle": 10.0, "windshield_rake": 25.0, "rear_glass_angle": 22.0,
        "roof_arc": 0.35, "fender_prominence": 0.05, "waist_line": 0.78,
        "spoke_count": 6,
    },
    "coupe": {
        "L": 4.700, "W": 1.850, "H": 1.350, "WB": 2.700,
        "hood_len": 1.100, "cabin_len": 1.500, "trunk_len": 0.850,
        "GC": 0.130, "WR": 0.320, "TW": 1.580,
        "hood_angle": 15.0, "windshield_rake": 33.0, "rear_glass_angle": 35.0,
        "roof_arc": 0.55, "fender_prominence": 0.035, "waist_line": 0.72,
        "spoke_count": 5,
    },
    "mpv": {
        "L": 5.100, "W": 1.900, "H": 1.800, "WB": 3.000,
        "hood_len": 1.000, "cabin_len": 2.400, "trunk_len": 0.700,
        "GC": 0.160, "WR": 0.340, "TW": 1.620,
        "hood_angle": 8.0, "windshield_rake": 22.0, "rear_glass_angle": 18.0,
        "roof_arc": 0.25, "fender_prominence": 0.03, "waist_line": 0.80,
        "spoke_count": 6,
    },
    "sport": {
        "L": 4.500, "W": 1.950, "H": 1.250, "WB": 2.650,
        "hood_len": 1.150, "cabin_len": 1.300, "trunk_len": 0.700,
        "GC": 0.110, "WR": 0.330, "TW": 1.680,
        "hood_angle": 18.0, "windshield_rake": 35.0, "rear_glass_angle": 38.0,
        "roof_arc": 0.60, "fender_prominence": 0.05, "waist_line": 0.70,
        "spoke_count": 5,
    },
    "pickup": {
        "L": 5.500, "W": 1.950, "H": 1.850, "WB": 3.400,
        "hood_len": 1.200, "cabin_len": 1.700, "trunk_len": 1.600,
        "GC": 0.220, "WR": 0.375, "TW": 1.650,
        "hood_angle": 10.0, "windshield_rake": 24.0, "rear_glass_angle": 20.0,
        "roof_arc": 0.30, "fender_prominence": 0.05, "waist_line": 0.78,
        "spoke_count": 6,
    },
}


def apply_preset(car_type: str) -> CarParams22:
    """Create CarParams22 from a named preset."""
    p = CarParams22()
    preset = SIX_CAR_PRESETS.get(car_type, SIX_CAR_PRESETS["sedan"])
    for k, v in preset.items():
        setattr(p, k, v)
    p.car_type = car_type
    return p


# ===================================================================
# Smoothstep Interpolation Utilities
# ===================================================================
def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Hermite smoothstep between edge0 and edge1."""
    t = max(0.0, min(1.0, (x - edge0) / max(edge1 - edge0, 1e-9)))
    return t * t * (3.0 - 2.0 * t)


def smoothstep5(edge0: float, edge1: float, x: float) -> float:
    """Quintic smoothstep (smoother C2 continuity)."""
    t = max(0.0, min(1.0, (x - edge0) / max(edge1 - edge0, 1e-9)))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ===================================================================
# 1. Hardpoint Derivation
# ===================================================================
@dataclass
class Hardpoints:
    """All derived key-point coordinates for the car body."""
    # Wheel centres
    fwx: float = 0.0       # front wheel centre X
    rwx: float = 0.0       # rear wheel centre X
    wcy: float = 0.0       # wheel centre Y (= ground clearance + wheel radius)
    fwz: float = 0.0       # front wheel centre Z (lateral offset)

    # Height key points
    noseTipY: float = 0.0  # nose tip (front bumper top)
    hoodY: float = 0.0     # hood height
    waistY: float = 0.0    # waistline height

    # A-pillar
    aBaseX: float = 0.0
    aTopY: float = 0.0
    aTopX: float = 0.0

    # C-pillar
    cBaseX: float = 0.0
    cTopX: float = 0.0
    cTopY: float = 0.0

    # Width key points
    frontFenderW: float = 0.0
    cabinW: float = 0.0
    rearFenderW: float = 0.0

    # Roof
    roofY: float = 0.0

    # Key X-positions
    noseX: float = 0.0     # frontmost point
    tailX: float = 0.0     # rearmost point
    hoodEndX: float = 0.0  # hood/windshield junction
    roofFrontX: float = 0.0
    roofRearX: float = 0.0
    trunkEndX: float = 0.0


def derive_hardpoints(p: CarParams22) -> Hardpoints:
    """
    Derive all hardpoints from the 22-D parameter set.
    This is the single source of truth for body proportions.
    """
    hp = Hardpoints()

    # ---- Wheel centres ----
    hp.fwx = p.WB / 2.0                       # front axle X
    hp.rwx = -p.WB / 2.0 + (p.L - p.WB) / 2.0 - (p.L - p.WB) / 2.0  # simplified
    # Actually: rear wheel centre = fwx - WB
    hp.rwx = hp.fwx - p.WB

    hp.wcy = p.GC + p.WR                       # wheel centre height
    hp.fwz = p.TW / 2.0 + p.WR * 0.0          # wheel lateral offset (track/2)

    # ---- Height key points ----
    hp.noseTipY = p.GC + 0.08 + p.WR * 0.15   # nose tip / bumper top
    hp.hoodY = p.GC + 0.43 + p.overall_arc * 0.05  # hood surface height
    hp.waistY = p.GC + p.waist_line * (p.H - p.GC) # waistline height

    # ---- Roof height ----
    hp.roofY = p.H * 0.96                      # roof peak

    # ---- A-pillar derivation ----
    hp.aBaseX = hp.fwx - p.hood_len + 0.10     # A-pillar base behind front axle
    aa_rad = math.radians(p.windshield_rake)
    hp.aTopX = hp.aBaseX - (hp.roofY - hp.waistY) / max(math.tan(aa_rad), 0.1)
    hp.aTopY = hp.roofY

    # ---- C-pillar derivation ----
    hp.cBaseX = hp.rwx + 0.30                  # C-pillar base
    hp.cTopX = hp.cBaseX - 0.15 - p.roof_arc * 0.20
    hp.cTopY = hp.aTopY - 0.03

    # ---- Width key points (half-widths) ----
    hp.frontFenderW = p.W / 2.0 * 0.95
    hp.cabinW = p.W / 2.0 * 0.86              # tumblehome reduction
    hp.rearFenderW = p.W / 2.0 * 0.95

    # ---- X-extents ----
    hp.noseX = p.WB / 2.0 + (p.L - p.WB) * 0.45   # front overhang
    hp.tailX = -(p.L - hp.noseX)                     # rear overhang
    hp.hoodEndX = hp.aBaseX                           # hood ends at A-pillar
    hp.roofFrontX = hp.aTopX
    hp.roofRearX = hp.cTopX
    hp.trunkEndX = hp.tailX

    return hp


# ===================================================================
# 2. Side Profile Curve (Z-height along X, normalized t ∈ [0,1])
# ===================================================================
def side_profile_z(p: CarParams22, hp: Hardpoints, t: float) -> float:
    """
    Returns the upper-body Z-height at normalised position t ∈ [0,1].
    t=0 is the nose, t=1 is the tail.

    Uses smoothstep interpolation between 6 key zones:
      Nose (t<0.08) → Hood (0.08-0.20) → A-Pillar (0.20-0.40) →
      Roof (0.40-0.60) → C-Pillar (0.60-0.80) → Tail (0.80-1.0)
    """
    t = clamp(t, 0.0, 1.0)

    # Key heights
    z_nose = hp.noseTipY
    z_hood = hp.hoodY
    z_waist = hp.waistY
    z_roof = hp.roofY
    z_tail = hp.noseTipY + p.overall_arc * 0.05  # rear bumper top

    if t < 0.08:
        # Nose: rise from ground to hood
        s = smoothstep5(0.0, 0.08, t)
        return lerp(p.GC * 0.5, z_hood, s)

    elif t < 0.20:
        # Hood: hood surface, slight rise
        s = smoothstep(0.08, 0.20, t)
        return lerp(z_hood, z_waist, s * 0.15)  # mostly flat, slight rise

    elif t < 0.40:
        # A-Pillar: waistline → roof (windshield region)
        s = smoothstep5(0.20, 0.40, t)
        return lerp(z_waist, z_roof, s)

    elif t < 0.60:
        # Roof: nearly flat with slight crown
        s = smoothstep(0.40, 0.60, t)
        crown = p.roof_arc * 0.015 * math.sin(s * math.pi)
        return z_roof + crown

    elif t < 0.80:
        # C-Pillar: roof → rear descent
        s = smoothstep5(0.60, 0.80, t)
        rear_drop = lerp(z_roof, z_waist, s)
        return rear_drop

    else:
        # Tail: smooth descent to rear bumper
        s = smoothstep5(0.80, 1.0, t)
        return lerp(z_waist, z_tail, s)


def side_profile_lower_z(p: CarParams22, hp: Hardpoints, t: float) -> float:
    """
    Returns the lower-body Z-height at normalised position t.
    This defines the rocker/sill line.
    """
    t = clamp(t, 0.0, 1.0)
    z_sill = p.GC + 0.01
    z_nose_bottom = p.GC
    z_rear_bottom = p.GC

    # Front: slight upward sweep
    if t < 0.10:
        s = smoothstep(0.0, 0.10, t)
        return lerp(z_nose_bottom + 0.02, z_sill, s)
    elif t > 0.90:
        # Rear: slight upward sweep
        s = smoothstep(0.90, 1.0, t)
        return lerp(z_sill, z_rear_bottom + 0.03, s)
    else:
        return z_sill


# ===================================================================
# 3. Planform Width Curve
# ===================================================================
def planform_halfwidth(p: CarParams22, hp: Hardpoints, t: float) -> float:
    """
    Returns the body half-width at normalised position t ∈ [0,1].
    t=0 is the nose, t=1 is the tail.

    Zones:
      Nose (t<0.05): narrow → full width
      Front Fender (0.05-0.25): maximum width with fender bulge
      Front Door (0.25-0.38): transition to cabin width
      Cabin (0.38-0.62): tumblehome (narrower)
      Rear Door (0.62-0.75): transition to rear fender
      Rear Fender (0.75-0.92): maximum width
      Tail (0.92-1.00): narrow down
    """
    t = clamp(t, 0.0, 1.0)

    max_w = p.W / 2.0 * 0.95   # max half-width
    cab_w = p.W / 2.0 * 0.86   # cabin half-width (tumblehome)
    nose_w = p.W / 2.0 * 0.35  # nose half-width
    tail_w = p.W / 2.0 * 0.40  # tail half-width
    fender_bulge = p.fender_prominence

    if t < 0.05:
        s = smoothstep5(0.0, 0.05, t)
        return lerp(nose_w * 0.6, nose_w, s)

    elif t < 0.15:
        # Nose widening to front fender
        s = smoothstep(0.05, 0.15, t)
        return lerp(nose_w, max_w + fender_bulge, s)

    elif t < 0.25:
        # Front fender max width zone
        s = (t - 0.15) / 0.10
        return max_w + fender_bulge * math.sin(s * math.pi) * 0.5

    elif t < 0.38:
        # Transition to cabin (A-pillar region)
        s = smoothstep(0.25, 0.38, t)
        return lerp(max_w + fender_bulge * 0.3, cab_w, s)

    elif t < 0.62:
        # Cabin: tumblehome (narrow)
        s = (t - 0.38) / 0.24
        # Slight belly in the middle of cabin
        belly = 0.008 * math.sin(s * math.pi)
        return cab_w + belly

    elif t < 0.75:
        # Rear transition (C-pillar area)
        s = smoothstep(0.62, 0.75, t)
        return lerp(cab_w, max_w + fender_bulge * 0.3, s)

    elif t < 0.92:
        # Rear fender
        s = (t - 0.75) / 0.17
        return max_w + fender_bulge * math.sin(s * math.pi) * 0.5

    else:
        # Tail narrowing
        s = smoothstep5(0.92, 1.0, t)
        return lerp(max_w * 0.9, tail_w, s)


# ===================================================================
# 4. Cross-Section Generator (Hyper-Ellipse)
# ===================================================================
def generate_cross_section(
    p: CarParams22,
    hp: Hardpoints,
    x_pos: float,
    t_norm: float,
    n_pts: int = 28,
) -> np.ndarray:
    """
    Generate a single cross-section at X position x_pos.
    Returns array of shape (n_pts, 3) — XYZ points forming a closed section.

    The section maps theta ∈ [0, 2π] to a (y, z) closed curve:
      - theta=0 → top-center (roof)
      - theta=π/2 → right-side at mid-height
      - theta=π → bottom-center (floor)
      - theta=3π/2 → left-side at mid-height

    Full body height spans [z_lower, z_upper], full width spans [-half_w, +half_w].
    """
    pts = np.zeros((n_pts, 3))

    z_upper = side_profile_z(p, hp, t_norm)
    z_lower = side_profile_lower_z(p, hp, t_norm)
    half_w = planform_halfwidth(p, hp, t_norm)

    body_height = z_upper - z_lower
    z_mid = (z_upper + z_lower) / 2.0

    # Super-ellipse exponent (controls roundness)
    # Higher = more rectangular, lower = more circular
    n_exp = 2.5 + p.overall_arc * 1.5  # range ~2.5 to 4.0

    for i in range(n_pts):
        theta = 2.0 * math.pi * i / n_pts  # 0 to 2π

        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        # --- Z mapping (vertical) ---
        # sin_t > 0 → upper half, sin_t < 0 → lower half
        # Use power curve to flatten bottom
        if sin_t >= 0:
            # Upper: smooth arc from mid to top
            z_power = 1.0 / max(n_exp * 0.7, 1.0)
            z_frac = sin_t ** z_power
            z = z_mid + body_height * 0.5 * z_frac
        else:
            # Lower: flatter bottom (higher power = flatter)
            z_power = 1.0 / max(n_exp * 1.2, 1.0)
            z_frac = (-sin_t) ** z_power
            z = z_mid - body_height * 0.5 * z_frac

        # --- Y mapping (horizontal/lateral) ---
        # cos_t determines lateral position
        y_power = 1.0 / max(n_exp, 1.0)
        y_abs = half_w * (abs(cos_t) ** y_power)
        y = y_abs if cos_t >= 0 else -y_abs

        # Shoulder line: slight outward ridge near upper body
        z_frac_height = (z - z_lower) / max(body_height, 0.01)
        if 0.55 < z_frac_height < 0.85:
            shoulder_blend = math.sin((z_frac_height - 0.55) / 0.30 * math.pi)
            if abs(y) > 0.01:
                y_sign = 1.0 if y > 0 else -1.0
                y += y_sign * p.shoulder_line * shoulder_blend

        # Tumblehome: upper portion narrows inward
        if z_frac_height > 0.65:
            tumble_frac = (z_frac_height - 0.65) / 0.35
            tumble_amount = 0.025 * tumble_frac * (1.0 - p.overall_arc * 0.3)
            if y > 0:
                y = max(0.05, y - tumble_amount)
            elif y < 0:
                y = min(-0.05, y + tumble_amount)

        # Roof curvature: slight dome at top
        if z_frac_height > 0.90:
            roof_frac = (z_frac_height - 0.90) / 0.10
            z += p.roof_arc * 0.012 * (1.0 - (2.0 * abs(y) / max(half_w, 0.1)) ** 2) * roof_frac

        pts[i, 0] = x_pos
        pts[i, 1] = y
        pts[i, 2] = z

    return pts


# ===================================================================
# 5. Wheel Arch Cutting
# ===================================================================
def apply_wheel_arch_cut(
    pts: np.ndarray,
    hp: Hardpoints,
    p: CarParams22,
    axle_x: float,
) -> np.ndarray:
    """
    Cut wheel arch into cross-section points.
    Points inside the wheel arch circle are pushed outward or removed.
    """
    arch_radius = p.WR * 1.18  # arch slightly larger than wheel
    arch_center_y = 0.0        # arch centered on body side
    arch_center_z = hp.wcy

    result = pts.copy()
    for i in range(len(result)):
        x, y, z = result[i]
        dx = abs(x - axle_x)

        # Only affect points near the axle
        if dx > arch_radius * 1.3:
            continue

        # Check if point is in the wheel arch zone (lower body near wheel)
        arch_half_span = arch_radius * 1.2
        if dx < arch_half_span:
            # Arch profile: semicircular cutout
            arch_depth = math.sqrt(max(0, arch_radius**2 - dx**2))
            arch_z_top = arch_center_z + arch_depth * 0.85

            # If point is below the arch curve and near the wheel laterally
            if z < arch_z_top and abs(y) < arch_radius * 1.1:
                # Push the point down/outward to create arch shape
                arch_factor = 1.0 - (dx / arch_half_span) ** 2
                z_target = arch_center_z - p.WR * 0.1  # bottom of arch

                if z > z_target and z < arch_z_top:
                    # Smooth transition into arch
                    blend = smoothstep(arch_z_top, z_target, z)
                    # Push outward slightly
                    if abs(y) > 0:
                        sign = 1.0 if y > 0 else -1.0
                        result[i, 1] = y + sign * 0.005 * blend * arch_factor

    return result


# ===================================================================
# 6. Full Body Sweep
# ===================================================================
def build_body_sweep(p: CarParams22, hp: Hardpoints) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sweep cross-sections along the car length to generate the full body mesh.

    Returns:
        vertices: np.ndarray of shape (N, 3)
        faces: np.ndarray of shape (M, 3)
    """
    n_stations = p.n_stations
    n_pts = p.n_section_pts

    # Station positions along car length
    x_start = hp.noseX
    x_end = hp.tailX
    x_stations = np.linspace(x_start, x_end, n_stations)

    all_vertices = []
    station_indices = []  # index offset for each station

    for si, x_pos in enumerate(x_stations):
        # Normalized t: 0 at nose, 1 at tail
        t_norm = (x_pos - x_start) / (x_end - x_start) if abs(x_end - x_start) > 1e-9 else 0.5

        # Generate cross-section
        section = generate_cross_section(p, hp, x_pos, t_norm, n_pts)

        # Apply wheel arch cutting for front and rear axles
        section = apply_wheel_arch_cut(section, hp, p, hp.fwx)
        section = apply_wheel_arch_cut(section, hp, p, hp.rwx)

        offset = len(all_vertices)
        station_indices.append(offset)
        for pt in section:
            all_vertices.append(pt)

    vertices = np.array(all_vertices)

    # --- Generate triangle faces ---
    faces = []

    for si in range(n_stations - 1):
        idx_curr = station_indices[si]
        idx_next = station_indices[si + 1]

        for pi in range(n_pts):
            pi_next = (pi + 1) % n_pts

            # Current section points
            c0 = idx_curr + pi
            c1 = idx_curr + pi_next
            # Next section points
            n0 = idx_next + pi
            n1 = idx_next + pi_next

            # Two triangles per quad
            faces.append([c0, n0, n1])
            faces.append([c0, n1, c1])

    # Cap front (nose) and rear (tail) with fan triangulation
    # Front cap
    front_center = len(vertices)
    # Add center vertex for front cap
    t_front = 0.0
    z_front = side_profile_z(p, hp, 0.0)
    z_front_lo = side_profile_lower_z(p, hp, 0.0)
    vertices_list = list(vertices)
    vertices_list.append([hp.noseX, 0.0, (z_front + z_front_lo) / 2])

    first_station = station_indices[0]
    for pi in range(n_pts):
        pi_next = (pi + 1) % n_pts
        faces.append([front_center, first_station + pi_next, first_station + pi])

    # Rear cap
    rear_center = len(vertices_list)
    t_rear = 1.0
    z_rear = side_profile_z(p, hp, 1.0)
    z_rear_lo = side_profile_lower_z(p, hp, 1.0)
    vertices_list.append([hp.tailX, 0.0, (z_rear + z_rear_lo) / 2])

    last_station = station_indices[-1]
    for pi in range(n_pts):
        pi_next = (pi + 1) % n_pts
        faces.append([rear_center, last_station + pi, last_station + pi_next])

    vertices = np.array(vertices_list)
    faces_arr = np.array(faces, dtype=np.int64)

    return vertices, faces_arr


# ===================================================================
# 7. Greenhouse (Upper Cabin / Glass Area) Builder
# ===================================================================
def build_greenhouse(p: CarParams22, hp: Hardpoints) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build the greenhouse (A-pillar to C-pillar glass area) as a separate mesh.
    This is slightly inset from the body to represent the glass region.
    """
    n_stations = 30
    n_pts = 20

    # Greenhouse spans from A-pillar top to C-pillar top
    x_start = hp.aTopX + 0.05
    x_end = hp.cTopX - 0.05
    if x_start <= x_end:
        x_start, x_end = x_end, x_start  # ensure correct order

    x_stations = np.linspace(x_start, x_end, n_stations)

    all_vertices = []
    station_indices = []

    for si, x_pos in enumerate(x_stations):
        t_norm = (x_pos - hp.noseX) / (hp.tailX - hp.noseX) if abs(hp.tailX - hp.noseX) > 1e-9 else 0.5
        t_norm = clamp(t_norm, 0.0, 1.0)

        z_upper = side_profile_z(p, hp, t_norm)
        z_lower = hp.waistY + 0.02  # window bottom at waistline
        half_w = planform_halfwidth(p, hp, t_norm) * 0.92  # inset for glass

        offset = len(all_vertices)
        station_indices.append(offset)

        for i in range(n_pts):
            theta = math.pi * i / max(n_pts - 1, 1)  # 0 to π (upper half only)

            cos_t = math.cos(theta)
            sin_t = math.sin(theta)

            # Glass curve: arc from waistline up to roof
            z = z_lower + (z_upper - z_lower) * sin_t
            y = half_w * cos_t

            # Slight inward offset from body
            z += 0.002
            y *= 0.97

            all_vertices.append([x_pos, y, z])

    vertices = np.array(all_vertices) if all_vertices else np.zeros((1, 3))
    faces = []

    for si in range(n_stations - 1):
        idx_curr = station_indices[si]
        idx_next = station_indices[si + 1]

        for pi in range(n_pts - 1):
            c0 = idx_curr + pi
            c1 = idx_curr + pi + 1
            n0 = idx_next + pi
            n1 = idx_next + pi + 1

            faces.append([c0, n0, n1])
            faces.append([c0, n1, c1])

    faces_arr = np.array(faces, dtype=np.int64) if faces else np.zeros((1, 3), dtype=np.int64)
    return vertices, faces_arr


# ===================================================================
# 8. Wheel Mesh Builder
# ===================================================================
def build_wheel(cx: float, cy: float, cz: float,
                radius: float, width: float, n_spokes: int = 5,
                n_seg: int = 24) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a detailed wheel mesh: tire + rim + spokes.
    Returns (vertices, faces).
    """
    half_w = width / 2
    tire_r = radius
    rim_r = radius * 0.65
    hub_r = radius * 0.25
    spoke_inner = hub_r
    spoke_outer = rim_r * 0.95

    verts = []
    faces = []

    # --- Tire outer surface ---
    for ring_y in [-half_w, half_w]:
        base = len(verts)
        for s in range(n_seg):
            angle = 2 * math.pi * s / n_seg
            verts.append([
                cx + tire_r * math.cos(angle),
                cy + ring_y,
                cz + tire_r * math.sin(angle)
            ])
        # Connect to next ring
        if ring_y > -half_w:
            prev_base = base - n_seg
            for s in range(n_seg):
                s_next = (s + 1) % n_seg
                faces.append([prev_base + s, base + s, base + s_next])
                faces.append([prev_base + s, base + s_next, prev_base + s_next])

    # --- Tire sidewall caps ---
    for ring_y, sign in [(-half_w, -1), (half_w, 1)]:
        base = len(verts)
        # Outer ring
        for s in range(n_seg):
            angle = 2 * math.pi * s / n_seg
            verts.append([
                cx + tire_r * math.cos(angle),
                cy + ring_y,
                cz + tire_r * math.sin(angle)
            ])
        # Inner ring (rim edge)
        for s in range(n_seg):
            angle = 2 * math.pi * s / n_seg
            verts.append([
                cx + rim_r * math.cos(angle),
                cy + ring_y,
                cz + rim_r * math.sin(angle)
            ])
        # Connect rings
        for s in range(n_seg):
            s_next = (s + 1) % n_seg
            if sign > 0:
                faces.append([base + s, base + n_seg + s, base + n_seg + s_next])
                faces.append([base + s, base + n_seg + s_next, base + s_next])
            else:
                faces.append([base + s, base + s_next, base + n_seg + s_next])
                faces.append([base + s, base + n_seg + s_next, base + n_seg + s])

    # --- Hub disc on outer face ---
    hub_center = len(verts)
    verts.append([cx, cy + half_w * 0.55, cz])
    hub_ring = len(verts)
    for s in range(n_seg):
        angle = 2 * math.pi * s / n_seg
        verts.append([
            cx + hub_r * math.cos(angle),
            cy + half_w * 0.55,
            cz + hub_r * math.sin(angle)
        ])
    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        faces.append([hub_center, hub_ring + s_next, hub_ring + s])

    # --- Spokes ---
    spoke_w_angle = 2 * math.pi / n_spokes * 0.3
    for sp in range(n_spokes):
        center_angle = 2 * math.pi * sp / n_spokes
        a1 = center_angle - spoke_w_angle / 2
        a2 = center_angle + spoke_w_angle / 2

        spoke_base = len(verts)
        # Inner left, inner right, outer left, outer right
        verts.append([cx + spoke_inner * math.cos(a1), cy + half_w * 0.5, cz + spoke_inner * math.sin(a1)])
        verts.append([cx + spoke_inner * math.cos(a2), cy + half_w * 0.5, cz + spoke_inner * math.sin(a2)])
        verts.append([cx + spoke_outer * math.cos(a1), cy + half_w * 0.5, cz + spoke_outer * math.sin(a1)])
        verts.append([cx + spoke_outer * math.cos(a2), cy + half_w * 0.5, cz + spoke_outer * math.sin(a2)])

        faces.append([spoke_base, spoke_base + 2, spoke_base + 3])
        faces.append([spoke_base, spoke_base + 3, spoke_base + 1])

    if verts:
        return np.array(verts), np.array(faces, dtype=np.int64)
    return np.zeros((1, 3)), np.zeros((1, 3), dtype=np.int64)


# ===================================================================
# 9. Headlight / Taillight Builders
# ===================================================================
def build_headlight(p: CarParams22, hp: Hardpoints, side: str = "right") -> Tuple[np.ndarray, np.ndarray]:
    """Build a headlight mesh."""
    y_sign = 1.0 if side == "right" else -1.0
    cx = hp.noseX - 0.02
    cy = y_sign * (p.W / 2.0 * 0.75)
    cz = hp.hoodY - 0.02

    hw = p.headlight_w / 2
    hh = p.headlight_h / 2

    verts = [
        [cx, cy - hw * y_sign, cz - hh],
        [cx, cy + hw * y_sign, cz - hh],
        [cx, cy + hw * y_sign, cz + hh],
        [cx, cy - hw * y_sign, cz + hh],
        [cx - 0.05, cy - hw * y_sign * 0.8, cz - hh * 0.8],
        [cx - 0.05, cy + hw * y_sign * 0.8, cz - hh * 0.8],
        [cx - 0.05, cy + hw * y_sign * 0.8, cz + hh * 0.8],
        [cx - 0.05, cy - hw * y_sign * 0.8, cz + hh * 0.8],
    ]
    faces = [
        [0, 1, 2], [0, 2, 3],  # front
        [4, 6, 5], [4, 7, 6],  # back
        [0, 4, 5], [0, 5, 1],  # bottom
        [2, 6, 7], [2, 7, 3],  # top
        [0, 3, 7], [0, 7, 4],  # left
        [1, 5, 6], [1, 6, 2],  # right
    ]
    return np.array(verts), np.array(faces, dtype=np.int64)


def build_taillight(p: CarParams22, hp: Hardpoints, side: str = "right") -> Tuple[np.ndarray, np.ndarray]:
    """Build a taillight mesh."""
    y_sign = 1.0 if side == "right" else -1.0
    cx = hp.tailX + 0.02
    cy = y_sign * (p.W / 2.0 * 0.70)
    cz = hp.waistY - 0.05

    hw = p.headlight_w / 2 * 0.8
    hh = p.headlight_h / 2 * 0.7

    verts = [
        [cx, cy - hw * y_sign, cz - hh],
        [cx, cy + hw * y_sign, cz - hh],
        [cx, cy + hw * y_sign, cz + hh],
        [cx, cy - hw * y_sign, cz + hh],
        [cx + 0.04, cy - hw * y_sign * 0.85, cz - hh * 0.85],
        [cx + 0.04, cy + hw * y_sign * 0.85, cz - hh * 0.85],
        [cx + 0.04, cy + hw * y_sign * 0.85, cz + hh * 0.85],
        [cx + 0.04, cy - hw * y_sign * 0.85, cz + hh * 0.85],
    ]
    faces = [
        [0, 2, 1], [0, 3, 2],
        [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4],
        [2, 6, 7], [2, 7, 3],
        [0, 4, 7], [0, 7, 3],
        [1, 5, 6], [1, 6, 2],
    ]
    return np.array(verts), np.array(faces, dtype=np.int64)


# ===================================================================
# 10. Full Car Assembly
# ===================================================================
def build_full_car_v21(p: CarParams22) -> Dict[str, dict]:
    """
    Build complete car model using V2.1 algorithm.
    Returns dict mapping part names to {"vertices": ndarray, "faces": ndarray}.
    """
    hp = derive_hardpoints(p)
    parts = {}

    # --- Main body shell ---
    body_verts, body_faces = build_body_sweep(p, hp)
    parts["body"] = {"vertices": body_verts, "faces": body_faces}

    # --- Greenhouse (glass area) ---
    gh_verts, gh_faces = build_greenhouse(p, hp)
    parts["greenhouse"] = {"vertices": gh_verts, "faces": gh_faces}

    # --- Wheels ---
    wheel_positions = [
        ("wheel_fr", hp.fwx, p.TW / 2.0),
        ("wheel_fl", hp.fwx, -p.TW / 2.0),
        ("wheel_rr", hp.rwx, p.TW / 2.0),
        ("wheel_rl", hp.rwx, -p.TW / 2.0),
    ]
    for name, wx, wy in wheel_positions:
        wv, wf = build_wheel(wx, wy, hp.wcy, p.WR, p.WW, p.spoke_count)
        parts[name] = {"vertices": wv, "faces": wf}

    # --- Headlights ---
    hl_r_v, hl_r_f = build_headlight(p, hp, "right")
    hl_l_v, hl_l_f = build_headlight(p, hp, "left")
    parts["headlight_right"] = {"vertices": hl_r_v, "faces": hl_r_f}
    parts["headlight_left"] = {"vertices": hl_l_v, "faces": hl_l_f}

    # --- Taillights ---
    tl_r_v, tl_r_f = build_taillight(p, hp, "right")
    tl_l_v, tl_l_f = build_taillight(p, hp, "left")
    parts["taillight_right"] = {"vertices": tl_r_v, "faces": tl_r_f}
    parts["taillight_left"] = {"vertices": tl_l_v, "faces": tl_l_f}

    return parts


# ===================================================================
# 11. Legacy Interface Compatibility
# ===================================================================
def build_full_car_v21_from_legacy_params(legacy_params) -> Dict[str, dict]:
    """
    Convert legacy CarParams (from core/car_surface.py) to V2.1 params
    and build the full car.
    This maintains API compatibility with the existing app.py.
    """
    lp = legacy_params
    p22 = CarParams22()

    # Map legacy params to V2.1
    p22.L = lp.length
    p22.W = lp.width
    p22.H = lp.height
    p22.WB = lp.wheelbase
    p22.hood_len = lp.front_overhang + 0.15
    p22.trunk_len = lp.rear_overhang + 0.10
    p22.cabin_len = max(0.5, p22.L - p22.hood_len - p22.trunk_len)
    p22.GC = lp.wheel_radius * 0.45  # approximate
    p22.hood_angle = lp.hood_angle
    p22.roof_arc = lp.roof_arc
    p22.windshield_rake = lp.windshield_angle
    p22.rear_glass_angle = lp.rear_window_angle
    p22.fender_prominence = lp.wheel_arch_bulge
    p22.waist_line = lp.waistline_ratio
    p22.WR = lp.wheel_radius
    p22.shoulder_line = 0.012
    p22.overall_arc = 0.5

    return build_full_car_v21(p22)


# ===================================================================
# 12. Export utilities
# ===================================================================
def parts_to_obj(parts: Dict[str, dict], offset_map: Optional[Dict[str, Tuple[int, int]]] = None) -> str:
    """Export all parts to OBJ format string."""
    lines = ["# EVOLUTION AI V2.1 Car Body", ""]
    vert_offset = 0

    for name, data in parts.items():
        lines.append(f"o {name}")
        verts = data["vertices"]
        faces = data["faces"]

        for v in verts:
            lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")

        for f in faces:
            lines.append(f"f {f[0]+vert_offset+1} {f[1]+vert_offset+1} {f[2]+vert_offset+1}")

        vert_offset += len(verts)
        lines.append("")

    return "\n".join(lines)
