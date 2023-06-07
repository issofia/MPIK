import sys
import os
import shutil
import numpy as np
from datetime import date, datetime
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import colors as mcolors
from CHECLabPy.core.io import DL1Reader
import pandas as pd
import argparse
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import gridspec

def draw_camera_outline(ax, **plot_opt):
    """Draw camera outline

    Parameters
    ----------
    ax : matplotlib.pylab.axis
        axis on which draw the camera outline
    **plot_opt : variuos
        options for plot
    """
    ms = (51.4 + 1.93) / 1000.0
    ax.plot([-3 * ms, -3 * ms], [-2 * ms, +2 * ms], **plot_opt)
    ax.plot([+3 * ms, +3 * ms], [-2 * ms, +2 * ms], **plot_opt)
    ax.plot([-2 * ms, -2 * ms], [-3 * ms, -2 * ms], **plot_opt)
    ax.plot([+2 * ms, +2 * ms], [-3 * ms, -2 * ms], **plot_opt)
    ax.plot([-2 * ms, -2 * ms], [+2 * ms, +3 * ms], **plot_opt)
    ax.plot([+2 * ms, +2 * ms], [+2 * ms, +3 * ms], **plot_opt)
    ax.plot([-2 * ms, +2 * ms], [-3 * ms, -3 * ms], **plot_opt)
    ax.plot([-2 * ms, +2 * ms], [+3 * ms, +3 * ms], **plot_opt)
    ax.plot([-3 * ms, -2 * ms], [+2 * ms, +2 * ms], **plot_opt)
    ax.plot([-3 * ms, -2 * ms], [-2 * ms, -2 * ms], **plot_opt)
    ax.plot([+2 * ms, +3 * ms], [+2 * ms, +2 * ms], **plot_opt)
    ax.plot([+2 * ms, +3 * ms], [-2 * ms, -2 * ms], **plot_opt)


def inside_camera_mask(x, y):
    ms = (51.4 + 1.93) / 1000.0
    m = (x >= -3 * ms) & (x <= 3 * ms) & (y >= -3 * ms) & (y <= 3 * ms)
    m = m & ~((x >= -3 * ms) & (x <= -2 * ms) & (y >= -3 * ms) & (y <= -2 * ms))
    m = m & ~((x >= -3 * ms) & (x <= -2 * ms) & (y >= 2 * ms) & (y <= 3 * ms))
    m = m & ~((x >= 2 * ms) & (x <= 3 * ms) & (y >= -3 * ms) & (y <= -2 * ms))
    m = m & ~((x >= 2 * ms) & (x <= 3 * ms) & (y >= 2 * ms) & (y <= 3 * ms))
    return m


parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-i", "--files", type=str, help=".h5 (dl1) filename (with path)", required=True
)

args = parser.parse_args()
filename = args.files
#Create a Reader 
r = DL1Reader(filename)
#Get camera mapping
m = r.mapping
#Load data as pandas dataframe
d = r.load_entire_table()
#Group data by pixel number
df = d[d.duplicated('pixel', keep=False)].groupby('pixel')['charge_cc'].apply(list).reset_index()
#Evaluate the mean value on all events per pixel
a = []
for i in range(len(df["charge_cc"])):
    a.append(np.mean(df["charge_cc"][i]))
a = np.array(a)
#Draw histo2D
fig, ax = plt.subplots()
fig.set_size_inches(8.5,7.)
x = np.array(m["xpix"])
y = np.array(m["ypix"])
ma = inside_camera_mask(x,y)
x_min = np.amin(x)
x_max = np.amax(x)
y_max =np.amax(y)
y_min = np.amin(y)
bins_x = np.linspace(x_min - 0.006/2, x_max + 0.006/2, 49)
bins_y = np.linspace(y_min - 0.006/2, y_max + 0.006/2, 49)
h, bin_x, bin_y, image = ax.hist2d(
        x[ma],
        y[ma],
        bins = [bins_x, bins_y],
        weights=a[ma],
    )

plt.colorbar(image, ax=ax, label="Charge")
draw_camera_outline(ax, color="k", lw=2)
ax.set_xlabel("x [m]")
ax.set_ylabel("y [m]")
plt.title(filename[-15:-7])
fig.savefig(filename[-15:-7]+"cameraimage.png")
plt.show()