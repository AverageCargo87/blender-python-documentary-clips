# Clip 3 'Fire', scene B: path of the burning firebrand (shared by the simulation and the scene).
import math
FPS = 24
DL_B1 = 5.2; ZAPAS = .5                      # duration of shot B1 and the simulation pre-roll before it, s
V_X = 1.25                                   # walking speed, m/s
NF_SIM = int((DL_B1 + ZAPAS) * FPS) + 4
def put_golovni(t):
    """Position of the glowing end of the firebrand at time t (s from the start of shot B1; negative = pre-roll). Moves along +X, bobbing with the steps."""
    x = -.3 + V_X * t
    z = 1.2 + .032 * math.sin(2 * math.pi * 1.75 * t) + .012 * math.sin(2 * math.pi * .6 * t + 1.0)
    y = .025 * math.sin(2 * math.pi * .875 * t + .5)
    return (x, y, z)
