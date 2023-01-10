import pandas as pd
import os
import matplotlib.pylab as plt
import argparse
import matplotlib as mpl
import numpy as np
from darkboxmanager.utils import *

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-i", "--files", type=str, help=".csv filename (with path)", required=True
)
args = parser.parse_args()


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


def print_mean_std(l, wavelength=405e-9, rate=1e6, a_sipm=36, a_pm=83.3):
    print(f"Mean     = {np.mean(l):.2e} W")
    print(f"Std      = {np.std(l):.2e} W")
    print(f"Std/Mean = {np.std(l)/np.mean(l)*100:.2f} %")
    ph = power_pm_cam_to_ph_pulse_sipm(np.mean(l), wavelength, rate, a_sipm, a_pm)
    print(f"Mean ph  = {ph:.2f}")


def plot_map_2d(x, y, z, scan_size, scan_step):
    fig, ax = plt.subplots()
    bins_ = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        int(scan_size * 2 / scan_step + 2),
    )
    h, bin_x, bin_y, image = ax.hist2d(
        x,
        y,
        bins=bins_,
        weights=z,
    )
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    plt.title(f"Robot Arm scan")
    plt.colorbar(image, ax=ax, label="Power [W]")
    draw_camera_outline(ax, color="k", lw=2)
    fig, ax = plt.subplots()
    ax.set_xlabel("x [m]")
    ax.set_ylabel("Power [W]")
    plt.hist(bin_x[1:], weights=h[int(62 / 2)], histtype="step")


def get_scan_settings(filename):
    with open(filename) as f:
        for line in f:
            if line.startswith("#"):
                if "scan_size" in line:
                    scan_size = float(line.split("=")[-1].strip(", \n"))
                elif "scan_step" in line:
                    scan_step = float(line.split("=")[-1].strip(", \n"))
    return scan_size, scan_step


if __name__ == "__main__":

    filename = args.files

    scan_size, scan_step = get_scan_settings(filename)

    d = pd.read_csv(filename, comment="#")

    print("All region")
    print_mean_std(d["power"])

    # Select only a region
    r1 = 0.2
    m1 = np.sqrt(d["x"] ** 2 + d["y"] ** 2) < r1
    print(f"Selection r<{r1} m")
    print_mean_std(d["power"][m1])
    # Select only a region
    r2 = 0.1
    m2 = np.sqrt(d["x"] ** 2 + d["y"] ** 2) < r2
    print(f"Selection r<{r2} m")
    print_mean_std(d["power"][m2])

    name = filename.strip("./d.csv")

    plot_map_2d(d["x"], d["y"], d["power"], scan_size, scan_step)
    # plot_map_2d(d["xreal"], d["yreal"], d["power"], scan_size, scan_step)
    # plot_map_2d(d["x"][m1], d["y"][m1], d["power"][m1], scan_size, scan_step)

    m = inside_camera_mask(d["x"], d["y"])
    print(f"Selection inside camera")
    print_mean_std(d["power"][m])
    plot_map_2d(d["x"][m], d["y"][m], d["power"][m], scan_size, scan_step)

    plt.show()
