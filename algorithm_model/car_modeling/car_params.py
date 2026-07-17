"""
Car parameter dataclass for the full-car modeling pipeline.
Defines all dimensions and styling parameters for a passenger car.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CarParams:
    """Complete car parameters covering dimensions, proportions and styling."""

    # --- Overall dimensions (metres) ---
    length: float = 4.7        # total length
    width: float = 1.85        # total width
    height: float = 1.45       # total height

    # --- Proportions ---
    wheelbase: float = 2.7     # distance between front and rear axle
    front_overhang: float = 0.9
    rear_overhang: float = 1.1

    # --- Body styling ---
    hood_angle: float = 15.0   # engine hood tilt angle (degrees)
    roof_arc: float = 0.5      # roof curvature factor
    windshield_angle: float = 28.0   # front windshield angle (degrees)
    rear_window_angle: float = 25.0  # rear window angle (degrees)

    # --- Detail features ---
    wheel_arch_bulge: float = 0.15  # wheel arch protrusion (m)
    waistline_ratio: float = 0.75   # waistline height as ratio of body height

    # --- Wheel ---
    wheel_radius: float = 0.33
    wheel_width: float = 0.22

    # --- Glass ---
    glass_tint: float = 0.3    # 0=clear, 1=dark

    # --- Surface resolution ---
    surface_u: int = 20
    surface_v: int = 10

    def validate(self) -> bool:
        """Return True if all parameters are within physically plausible ranges."""
        checks = [
            3.5 <= self.length <= 6.0,
            1.5 <= self.width <= 2.3,
            1.1 <= self.height <= 2.1,
            2.0 <= self.wheelbase <= 3.5,
            0 <= self.hood_angle <= 35,
            0.0 <= self.roof_arc <= 1.5,
            15 <= self.windshield_angle <= 45,
            10 <= self.rear_window_angle <= 40,
            0.0 <= self.wheel_arch_bulge <= 0.4,
            0.5 <= self.waistline_ratio <= 0.95,
        ]
        return all(checks)
