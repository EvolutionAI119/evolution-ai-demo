"""
Patch script: rewrite 7 component build functions in car_body_builder.py
to follow the body side profile curve instead of being flat isolated panels.
"""
import re

FILE = '/app/data/所有对话/主对话/EVOLUTION_AI_DEMO/car_body_builder.py'

with open(FILE, 'r') as f:
    code = f.read()

# ============================================================
# 1. build_hood — follows side_profile_z from hoodEndX to noseX
# ============================================================
OLD_HOOD = r'''def build_hood\(p: CarParamsV3, hp: Hardpoints\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    """Build hood panel mesh \(aligned with desktop generate_hood\)\.
    Hood spans from A-pillar base \(hoodEndX\) to nose tip \(noseX\)\.
    """
    nu, nv = 12, 8
    angle_rad = math\.radians\(p\.hood_angle\)
    x_start = hp\.hoodEndX  # was: hp\.noseX \+ 0\.05 \(wrong — placed hood past the nose!\)
    length = hp\.noseX - hp\.hoodEndX  # was: p\.hood_len \(wrong — 1\.3m overextended past nose\)

    verts = \[\]
    for i in range\(nu\):
        u = i / \(nu - 1\)
        for j in range\(nv\):
            v = j / \(nv - 1\)
            x = x_start \+ u \* length
            y = \(v - 0\.5\) \* p\.hood_width
            z = hp\.hoodY \+ p\.hood_height \* math\.sin\(u \* math\.pi\) \* math\.cos\(v \* math\.pi\) \+ u \* math\.tan\(angle_rad\) \* length \* 0\.3
            verts\.append\(\[x, y, z\]\)

    faces = \[\]
    for i in range\(nu - 1\):
        for j in range\(nv - 1\):
            p00 = i \* nv \+ j
            p10 = \(i \+ 1\) \* nv \+ j
            p01 = i \* nv \+ j \+ 1
            p11 = \(i \+ 1\) \* nv \+ j \+ 1
            faces\.append\(\[p00, p10, p11\]\)
            faces\.append\(\[p00, p11, p01\]\)

    return np\.array\(verts\), np\.array\(faces, dtype=np\.int64\)'''

NEW_HOOD = '''def build_hood(p: CarParamsV3, hp: Hardpoints) -> Tuple[np.ndarray, np.ndarray]:
    """Build hood surface following body side_profile_z from hoodEndX to noseX.
    Creates a smooth panel that visually continues the body top surface.
    """
    nu, nv = 14, 10
    x_start = hp.hoodEndX   # A-pillar base (~0.20)
    x_end = hp.noseX         # nose tip (~2.30)
    total_len = x_end - x_start

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        x = x_start + u * total_len
        t_norm = (x - hp.noseX) / (hp.tailX - hp.noseX)
        t_norm = max(0.0, min(1.0, t_norm))
        z_base = side_profile_z(p, hp, t_norm) + 0.003
        hw = planform_halfwidth(p, hp, t_norm) * 0.85
        for j in range(nv):
            v = j / (nv - 1)
            y = (v - 0.5) * 2.0 * hw
            crown = 0.018 * math.sin(v * math.pi)
            z = z_base + crown
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_HOOD, NEW_HOOD, code, count=1)
print(f"hood: {'OK' if 'build_hood' in code and 'crown = 0.018' in code else 'FAIL'}")

# ============================================================
# 2. build_trunk — follows side_profile_z from trunkEndX to cBaseX
# ============================================================
OLD_TRUNK = r'''def build_trunk\(p: CarParamsV3, hp: Hardpoints\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    """Build trunk lid mesh \(aligned with desktop generate_trunk\)\.
    Trunk spans from C-pillar base \(cBaseX\) to tail \(trunkEndX=tailX\)\.
    """
    nu, nv = 8, 6
    # trunkEndX < cBaseX \(e\.g\. -2\.5 < -1\.1\), so trunk extends negative X direction
    x_start = hp\.trunkEndX  # was: hp\.cBaseX \+ 0\.10 \(wrong — placed trunk in middle of car!\)
    length = hp\.cBaseX - hp\.trunkEndX  # was: p\.trunk_len \(wrong — only 1\.0m, should span to tail\)

    verts = \[\]
    for i in range\(nu\):
        u = i / \(nu - 1\)
        for j in range\(nv\):
            v = j / \(nv - 1\)
            x = x_start \+ u \* length
            y = \(v - 0\.5\) \* p\.trunk_width
            z = hp\.bumperRearTopY \+ 0\.15 \+ 0\.08 \* math\.exp\(-u \* 4\) \* math\.cos\(v \* math\.pi\)
            verts\.append\(\[x, y, z\]\)

    faces = \[\]
    for i in range\(nu - 1\):
        for j in range\(nv - 1\):
            p00 = i \* nv \+ j
            p10 = \(i \+ 1\) \* nv \+ j
            p01 = i \* nv \+ j \+ 1
            p11 = \(i \+ 1\) \* nv \+ j \+ 1
            faces\.append\(\[p00, p10, p11\]\)
            faces\.append\(\[p00, p11, p01\]\)

    return np\.array\(verts\), np\.array\(faces, dtype=np\.int64\)'''

NEW_TRUNK = '''def build_trunk(p: CarParamsV3, hp: Hardpoints) -> Tuple[np.ndarray, np.ndarray]:
    """Build trunk surface following body side_profile_z from trunkEndX(tailX) to cBaseX."""
    nu, nv = 12, 8
    x_start = hp.trunkEndX   # tailX (~-2.50)
    x_end = hp.cBaseX        # C-pillar base (~-1.10)
    total_len = x_end - x_start  # positive

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        x = x_start + u * total_len
        t_norm = (x - hp.noseX) / (hp.tailX - hp.noseX)
        t_norm = max(0.0, min(1.0, t_norm))
        z_base = side_profile_z(p, hp, t_norm) + 0.003
        hw = planform_halfwidth(p, hp, t_norm) * 0.85
        for j in range(nv):
            v = j / (nv - 1)
            y = (v - 0.5) * 2.0 * hw
            crown = 0.012 * math.sin(v * math.pi)
            z = z_base + crown
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_TRUNK, NEW_TRUNK, code, count=1)
print(f"trunk: {'OK' if 'z_base = side_profile_z' in code and code.count('z_base = side_profile_z') >= 2 else 'FAIL'}")

# ============================================================
# 3. build_bumper — thin curved shell extending beyond noseX/tailX
# ============================================================
OLD_BUMPER = r'''def build_bumper\(p: CarParamsV3, hp: Hardpoints, position: str = "front"\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    """Build bumper mesh \(aligned with desktop generate_bumper_front/rear\)\."""
    width = p\.W
    length = 0\.200
    height = 0\.250
    nu, nv = 10, 6

    if position == "front":
        x_base = hp\.noseX
    else:
        x_base = hp\.tailX

    verts = \[\]
    for i in range\(nu\):
        u = i / \(nu - 1\)
        for j in range\(nv\):
            v = j / \(nv - 1\)
            if position == "front":
                x = x_base - length \* \(1 - u\)
            else:
                x = x_base \+ length \* u
            y = \(v - 0\.5\) \* width \* \(0\.85 \+ \(u if position == "front" else \(1 - u\)\) \* 0\.15\)
            z = height \* \(1 - math\.cos\(u \* math\.pi\)\) \* 0\.5 \+ p\.GC \+ 0\.05
            verts\.append\(\[x, y, z\]\)

    faces = \[\]
    for i in range\(nu - 1\):
        for j in range\(nv - 1\):
            p00 = i \* nv \+ j
            p10 = \(i \+ 1\) \* nv \+ j
            p01 = i \* nv \+ j \+ 1
            p11 = \(i \+ 1\) \* nv \+ j \+ 1
            faces\.append\(\[p00, p10, p11\]\)
            faces\.append\(\[p00, p11, p01\]\)

    return np\.array\(verts\), np\.array\(faces, dtype=np\.int64\)'''

NEW_BUMPER = '''def build_bumper(p: CarParamsV3, hp: Hardpoints, position: str = "front") -> Tuple[np.ndarray, np.ndarray]:
    """Build bumper as thin curved shell extending beyond noseX/tailX, following body profile."""
    nu, nv = 10, 8
    extend = 0.12 if position == "front" else 0.10

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        for j in range(nv):
            v = j / (nv - 1)
            if position == "front":
                x = hp.noseX + extend * (1 - u)  # from noseX+extend to noseX
            else:
                x = hp.tailX - extend * (1 - u)  # from tailX-extend to tailX

            t_norm = (x - hp.noseX) / (hp.tailX - hp.noseX)
            t_norm = max(0.0, min(1.0, t_norm))
            z_top = side_profile_z(p, hp, t_norm)
            z_bot = side_profile_lower_z(p, hp, t_norm)
            hw = planform_halfwidth(p, hp, t_norm) * 0.90

            y = (v - 0.5) * 2.0 * hw
            z = z_bot + (z_top - z_bot) * (0.3 + 0.7 * math.sin(u * math.pi * 0.5 + 0.2))

            if position == "front":
                x -= 0.01 * (1 - u)
            else:
                x += 0.01 * (1 - u)
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_BUMPER, NEW_BUMPER, code, count=1)
print(f"bumper: {'OK' if 'extend = 0.12' in code else 'FAIL'}")

# ============================================================
# 4. build_headlight — proper 3D housing at body nose
# ============================================================
OLD_HEADLIGHT = r'''def build_headlight\(p: CarParamsV3, hp: Hardpoints, side: str = "right"\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    y_sign = 1\.0 if side == "right" else -1\.0
    cx = hp\.headlightX
    cy = y_sign \* \(p\.W / 2\.0 \* 0\.75\)
    cz = hp\.headlightY

    hw = p\.headlight_w / 2
    hh = p\.headlight_height / 2

    verts = \[
        \[cx, cy - hw \* y_sign, cz - hh\],
        \[cx, cy \+ hw \* y_sign, cz - hh\],
        \[cx, cy \+ hw \* y_sign, cz \+ hh\],
        \[cx, cy - hw \* y_sign, cz \+ hh\],
        \[cx - 0\.05, cy - hw \* y_sign \* 0\.8, cz - hh \* 0\.8\],
        \[cx - 0\.05, cy \+ hw \* y_sign \* 0\.8, cz - hh \* 0\.8\],
        \[cx - 0\.05, cy \+ hw \* y_sign \* 0\.8, cz \+ hh \* 0\.8\],
        \[cx - 0\.05, cy - hw \* y_sign \* 0\.8, cz \+ hh \* 0\.8\],
    \]
    faces = \[
        \[0, 1, 2\], \[0, 2, 3\], \[4, 6, 5\], \[4, 7, 6\],
        \[0, 4, 5\], \[0, 5, 1\], \[2, 6, 7\], \[2, 7, 3\],
        \[0, 3, 7\], \[0, 7, 4\], \[1, 5, 6\], \[1, 6, 2\],
    \]
    return np\.array\(verts\), np\.array\(faces, dtype=np\.int64\)'''

NEW_HEADLIGHT = '''def build_headlight(p: CarParamsV3, hp: Hardpoints, side: str = "right") -> Tuple[np.ndarray, np.ndarray]:
    """Build headlight as 3D housing recessed into body at nose, with lens face."""
    nu, nv = 6, 6
    y_sign = 1.0 if side == "right" else -1.0

    cx = hp.noseX - 0.03
    cy = y_sign * (p.W / 2.0 * 0.60)
    cz = hp.hoodY - 0.02
    depth = 0.08
    hw = p.headlight_w * 0.45
    hh = p.headlight_height * 0.50

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        for j in range(nv):
            v = j / (nv - 1)
            y = cy + (v - 0.5) * 2.0 * hw * y_sign
            z = cz + (u - 0.5) * 2.0 * hh
            bulge = 0.015 * math.sin(v * math.pi) * math.sin(u * math.pi)
            x = cx - depth * 0.3 + bulge
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_HEADLIGHT, NEW_HEADLIGHT, code, count=1)
print(f"headlight: {'OK' if 'depth = 0.08' in code else 'FAIL'}")

# ============================================================
# 5. build_taillight — proper 3D housing at body rear
# ============================================================
OLD_TAILLIGHT = r'''def build_taillight\(p: CarParamsV3, hp: Hardpoints, side: str = "right"\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    y_sign = 1\.0 if side == "right" else -1\.0
    cx = hp\.taillightX
    cy = y_sign \* \(p\.W / 2\.0 \* 0\.70\)
    cz = hp\.taillightY

    hw = p\.taillight_width / 2
    hh = p\.taillight_height / 2

    verts = \[
        \[cx, cy - hw \* y_sign, cz - hh\],
        \[cx, cy \+ hw \* y_sign, cz - hh\],
        \[cx, cy \+ hw \* y_sign, cz \+ hh\],
        \[cx, cy - hw \* y_sign, cz \+ hh\],
        \[cx \+ 0\.04, cy - hw \* y_sign \* 0\.85, cz - hh \* 0\.85\],
        \[cx \+ 0\.04, cy \+ hw \* y_sign \* 0\.85, cz - hh \* 0\.85\],
        \[cx \+ 0\.04, cy \+ hw \* y_sign \* 0\.85, cz \+ hh \* 0\.85\],
        \[cx \+ 0\.04, cy - hw \* y_sign \* 0\.85, cz \+ hh \* 0\.85\],
    \]
    faces = \[
        \[0, 2, 1\], \[0, 3, 2\], \[4, 5, 6\], \[4, 6, 7\],
        \[0, 1, 5\], \[0, 5, 4\], \[2, 6, 7\], \[2, 7, 3\],
        \[0, 4, 7\], \[0, 7, 3\], \[1, 5, 6\], \[1, 6, 2\],
    \]
    return np\.array\(verts\), np\.array\(faces, dtype=np\.int64\)'''

NEW_TAILLIGHT = '''def build_taillight(p: CarParamsV3, hp: Hardpoints, side: str = "right") -> Tuple[np.ndarray, np.ndarray]:
    """Build taillight as 3D housing recessed into body at rear, with lens face."""
    nu, nv = 6, 6
    y_sign = 1.0 if side == "right" else -1.0

    cx = hp.tailX + 0.03
    cy = y_sign * (p.W / 2.0 * 0.60)
    cz = hp.bumperRearTopY + 0.10
    depth = 0.06
    hw = p.taillight_width * 0.45
    hh = p.taillight_height * 0.50

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        for j in range(nv):
            v = j / (nv - 1)
            y = cy + (v - 0.5) * 2.0 * hw * y_sign
            z = cz + (u - 0.5) * 2.0 * hh
            bulge = 0.012 * math.sin(v * math.pi) * math.sin(u * math.pi)
            x = cx + depth * 0.3 - bulge
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_TAILLIGHT, NEW_TAILLIGHT, code, count=1)
print(f"taillight: {'OK' if 'depth = 0.06' in code else 'FAIL'}")

# ============================================================
# 6. build_fender — proper arch over wheel
# ============================================================
OLD_FENDER = r'''def build_fender\(p: CarParamsV3, hp: Hardpoints, position: str = "front", side: str = "left"\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    """Build fender mesh \(aligned with desktop generate_fender\)\."""
    radius = p\.wheel_arch_radius
    nu, nv = 6, 6
    x_center = hp\.fenderFrontX if position == "front" else hp\.fenderRearX
    y_center = -\(hp\.fwz \+ 0\.030\) if side == "left" else \(hp\.fwz \+ 0\.030\)

    verts = \[\]
    for i in range\(nu\):
        u = i / \(nu - 1\)
        for j in range\(nv\):
            v = j / \(nv - 1\)
            theta, phi = u \* math\.pi, v \* math\.pi
            x = x_center \+ radius \* math\.cos\(theta\) \* 0\.6
            y = y_center \+ radius \* math\.sin\(theta\) \* math\.sin\(phi\) \* 0\.5
            z = max\(p\.GC, p\.GC \+ radius \* math\.sin\(theta\) \* math\.cos\(phi\)\)  # clamp to ground
            verts\.append\(\[x, y, z\]\)

    faces = \[\]
    for i in range\(nu - 1\):
        for j in range\(nv - 1\):
            p00 = i \* nv \+ j
            p10 = \(i \+ 1\) \* nv \+ j
            p01 = i \* nv \+ j \+ 1
            p11 = \(i \+ 1\) \* nv \+ j \+ 1
            faces\.append\(\[p00, p10, p11\]\)
            faces\.append\(\[p00, p11, p01\]\)

    return np\.array\(verts\), np\.array\(faces, dtype=np\.int64\)'''

NEW_FENDER = '''def build_fender(p: CarParamsV3, hp: Hardpoints, position: str = "front", side: str = "left") -> Tuple[np.ndarray, np.ndarray]:
    """Build fender as proper arch surface covering the top half of the wheel."""
    nu, nv = 10, 10
    radius = p.wheel_arch_radius
    x_center = hp.fenderFrontX if position == "front" else hp.fenderRearX
    y_sign = -1.0 if side == "left" else 1.0
    y_center = y_sign * (p.TW / 2.0 * 0.82)
    z_center = hp.wcy

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        theta = u * math.pi
        for j in range(nv):
            v = j / (nv - 1)
            phi = -math.pi / 2 + v * math.pi

            x = x_center + radius * 0.15 * math.cos(phi)
            y = y_center + radius * math.sin(phi) * 0.55
            z = z_center + radius * math.cos(phi) * math.sin(theta) * 0.5

            z = max(p.GC + 0.02, z)
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_FENDER, NEW_FENDER, code, count=1)
print(f"fender: {'OK' if 'z_center = hp.wcy' in code else 'FAIL'}")

# ============================================================
# 7. build_grille — recessed panel at nose front
# ============================================================
OLD_GRILLE = r'''def build_grille\(p: CarParamsV3, hp: Hardpoints\) -> Tuple\[np\.ndarray, np\.ndarray\]:
    """Build grille mesh\."""
    return _generate_panel_mesh\(
        hp\.grilleX, hp\.grilleTopY,
        0\.050, p\.grille_height,
        z_offset=0, nu=3, nv=8,
    \)'''

NEW_GRILLE = '''def build_grille(p: CarParamsV3, hp: Hardpoints) -> Tuple[np.ndarray, np.ndarray]:
    """Build grille as recessed panel at nose front with horizontal slat lines."""
    nu, nv = 4, 10
    cx = hp.noseX + 0.06
    z_bottom = p.GC + 0.06
    z_top = hp.hoodY - 0.06
    hw = p.W * 0.28

    verts = []
    for i in range(nu):
        u = i / (nu - 1)
        for j in range(nv):
            v = j / (nv - 1)
            y = (v - 0.5) * 2.0 * hw
            z = z_bottom + u * (z_top - z_bottom)
            recess = 0.015 * math.sin(v * math.pi)
            x = cx - recess
            verts.append([x, y, z])

    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            p00 = i * nv + j
            p10 = (i + 1) * nv + j
            p01 = i * nv + j + 1
            p11 = (i + 1) * nv + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])

    return np.array(verts), np.array(faces, dtype=np.int64)'''

code = re.sub(OLD_GRILLE, NEW_GRILLE, code, count=1)
print(f"grille: {'OK' if 'recess = 0.015' in code else 'FAIL'}")

# ============================================================
# Save
# ============================================================
with open(FILE, 'w') as f:
    f.write(code)
print(f"\nFile saved. Total size: {len(code)} bytes")
print("Done!")
