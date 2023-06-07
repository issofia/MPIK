import matplotlib.pyplot as plt
import numpy as np
import pandas as pd 
from beamanalysis.utils import *
from map_scan2D import *
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D
import yaml

with open("scan2D_fit.yml", "r") as input:
    inp = yaml.safe_load(input)
    filename = inp["experimental_data"]["file"]
    corr_file = inp["experimental_data"]["correction_file"]
    distance = inp["experimental_data"]["distance"]

scan_size, scan_step = get_scan_settings(filename)
d = pd.read_csv(filename, comment="#")


d["power"] = apply_angle_correction(
    d["x"],
    d["y"],
    d["power"],
    distance=distance,
    corr_file=corr_file,
)

x = d["x"]
y = d["y"]
z = d["power"]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
bins_ = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        round(scan_size * 2 / scan_step + 2),
    )
hist, xedges, yedges = np.histogram2d(x, y, bins=bins_)
xpos, ypos = np.meshgrid(xedges[:-1] + 0.25, yedges[:-1] + 0.25, indexing="ij")
xpos = xpos.ravel()
ypos = ypos.ravel()
zpos = 0
dx = dy = 0.5 * np.ones_like(zpos)
dz = hist.ravel()
surf = ax.plot_trisurf(x,y, z,cmap= "plasma",  linewidth=0)
ax.xaxis.set_major_locator(MaxNLocator(10))
ax.yaxis.set_major_locator(MaxNLocator(10))
ax.zaxis.set_major_locator(MaxNLocator(10))
ax.set_xlabel("x [m]")
ax.set_ylabel("y [m]")
ax.set_zlabel("Power [W]")
ax.set_zscale("log")
plt.title(f"Beam profile, distance {distance} m")
fig.tight_layout()
fig.colorbar(surf)

plt.show()