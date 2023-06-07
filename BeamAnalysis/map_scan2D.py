import argparse

import matplotlib.pylab as plt
import numpy as np
import pandas as pd

from beamanalysis.utils import *
import seaborn as sns
#sns.set_context("notebook")
sns.set_context("paper")

def print_mean_std(l, wavelength=405e-9, rate=1e6, a_sipm=36, a_pm=83.3):
    print(f"Mean     = {np.mean(l):.2e} W")
    print(f"Std      = {np.std(l):.2e} W")
    print(f"Std/Mean = {np.std(l)/np.mean(l)*100:.2f} %")
    print(f"Min/Max  = {np.min(l)/np.max(l)*100:.2f} %")
    ph = power_pm_cam_to_ph_pulse_sipm(np.mean(l), wavelength, rate, a_sipm, a_pm)
    print(f"Mean ph  = {ph:.2f}")


def plot_map_2d(x, y, z, scan_size, scan_step, draw_camera=True, ax=None, title = None):
    sns.set_context("notebook")

    if ax == None:
        fig, ax = plt.subplots()
    bins_ = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        round(scan_size * 2 / scan_step + 2),
    )
    z[z < 0] = 0  # set negative values to 0
    h, bin_x, bin_y, image = ax.hist2d(
        x,
        y,
        bins=bins_,
        weights=z + 1e-16,
        vmin=min(z),
        cmin=1e-16
    )
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    plt.title(title)
    # current_cmap = mpl.cm.get_cmap()
    # current_cmap.set_bad(color="white")
    plt.colorbar(image, ax = ax, label="Power [W]")
    if draw_camera:
        draw_camera_outline(ax, color="k", lw=2)
    
    # fig, ax = plt.subplots()
    # ax.set_xlabel("x [m]")
    # ax.set_ylabel("Power [W]")
    # plt.hist(bin_x[1:], weights=h[int((scan_size * 2 / scan_step + 2)/2)], histtype="step")
    #plt.show()
    return h, bin_x, bin_y

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

    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-i", "--file", type=str, help=".csv filename (with path)", required=True
    )
    parser.add_argument(
        "-c", "--draw_camera", action="store_true", help="Draw Camera", required=False
    )
    parser.add_argument(
        "-cf",
        "--corr_file",
        type=str,
        help="File with angle correction",
        required=False,
        default="",
    )
    parser.add_argument(
        "-d",
        "--distance",
        type=float,
        help="Distance from light source",
        required=False,
        default=-1,
    )
    args = parser.parse_args()

    filename = args.file
    

    scan_size, scan_step = get_scan_settings(filename)

    d = pd.read_csv(filename, comment="#")

    if args.distance != -1 and args.corr_file != "":
        print("Apply angle correction")
        d["power"] = apply_angle_correction(
            d["x"],
            d["y"],
            d["power"],
            distance=args.distance,
            corr_file=args.corr_file,
        )
    else:
        print("No angle correction applied")

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

    plot_map_2d(d["x"], d["y"], d["power"], scan_size, scan_step, args.draw_camera)
    # plot_map_2d(d["xreal"], d["yreal"], d["power"], scan_size, scan_step, args.draw_camera)
    # plot_map_2d(d["x"][m1], d["y"][m1], d["power"][m1], scan_size, scan_step, args.draw_camera)

    if args.draw_camera:
        m = inside_camera_mask(d["x"], d["y"])
        print(f"Selection inside camera")
        print_mean_std(d["power"][m])
    #     plot_map_2d(d["x"][m], d["y"][m], d["power"][m], scan_size, scan_step, args.draw_camera)

    plt.show()
