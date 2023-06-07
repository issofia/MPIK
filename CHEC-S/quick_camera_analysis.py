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
from matplotlib.colors import ListedColormap
import yaml
import seaborn as sns
sns.set_context("talk")

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




def camera_histo2D(arr, pdfs, quantity, colorMap, title, m, empty_borders):
    
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
    print(f"x = {x}\ny = {y}\nx-min = {x_min}\n x_max = {x_max}\nymin = {y_min}\nymax = {y_max}")
    bins_x = np.linspace(x_min - 0.006/2, x_max + 0.006/2, 49)
    bins_y = np.linspace(y_min - 0.006/2, y_max + 0.006/2, 49)

    #plt.axis('scaled')
    if not empty_borders:
        h, bin_x, bin_y, image = ax.hist2d(
                x[ma],
                y[ma],
                bins = [bins_x, bins_y],
                weights=arr[ma], cmap = colorMap,
                vmin=min(arr[ma]),
                cmin=1e-16
            )
    else:
        h, bin_x, bin_y, image = ax.hist2d(
                x[ma],
                y[ma],
                bins = [bins_x, bins_y],
                weights=arr[ma], cmap = colorMap
            )

    if quantity == "charge_cc":
        lab = "Charge [Arbitrary units]"
    elif quantity == "waveform_mean":
        lab = "Mean waveform [mV]"
    elif quantity == "t_averagewf":
        lab = "Time of average waveform [ns]"
    else:
        lab = quantity
    plt.colorbar(image, ax=ax, label=lab)
    #draw_camera_outline(ax, color="k", lw=2)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    fig.tight_layout()
    plt.title(title)
    pdfs.savefig(fig)

def pdf_plots_module(q, array, n_sigma, filename, j, fig, ax, pdfs, mean, sigma):
    """ Plot the average charge of each pixel of one module.
    """
    plt.plot(array, marker = ".", c = "b", markersize = 3., linewidth = 0)
    pix = range(64)
    m_c = np.mean(array)
    m_c_std = np.std(array)
    #y = m_c
    y = mean
    #y1 = m_c - n_sigma*m_c_std
    #y2 = m_c + n_sigma*m_c_std
    y1 = mean - n_sigma*sigma
    y2 = mean + n_sigma*sigma
    plt.axhline(y2, color = 'gray', linestyle = '--', linewidth = .5, alpha = 0.5, label = f"mean + {n_sigma}\u03C3")
    plt.axhline(y, color = 'gray', linestyle = '-', label = "mean", linewidth = .5, alpha = 0.5)
    plt.axhline(y1, color = 'gray', linestyle = '--', alpha = 0.5, linewidth = .5, label = f"mean - {n_sigma}\u03C3")
    plt.fill_between(pix, y1,y2, alpha = 0.3, color = "gray")
    ax.set_xlabel("Number of Pixel")
    plt.ylim(np.amin(array), np.amax(array) + 20)
    plt.title(f"Cross-Correlation charge - Module {j}  - {filename}")
    if q == "charge_cc":
        ax.set_ylabel(f"Charge [Arbitrary units]")
    elif q == "waveform_mean":
        ax.set_ylabel(f"Mean waveform [mV]")
    elif q == "t_averagewf":
        ax.set_ylabel(f"Time of average waveform [ns]")
    else:
        ax.set_ylabel(q)
    plt.legend(loc = 'lower right')
    pdfs.savefig(fig)

def make_nsigma_plots(df, q, n_sigma, data_dir, filename, pdfs, mean, sigma):
    for j in range(0,32): #iterating over the 32 modules
        fig, ax = plt.subplots()
        av_c = []
        for i in range(j*64, (j+1)*64):
            c = df[q][i]
            av_c.append(np.mean(c))       
        pdf_plots_module(q, av_c, n_sigma, filename, j, fig, ax, pdfs, mean, sigma)


def camera_pixel_study(df, q, n_sigma, mean, sigma):
    # Dictionaries
    map_pixels_dict = {}
    #create bad_pixels dictionary to store the pixels with mean waveform far from the mean (more than n_sigma)
    bad_pixels_dict = {} 
    bad_pixels_arr = []
    pixel_status_arr = []
    # Read and analyse data
    for j in range(0,32): #iterating over the 32 modules
        av_c = []
        for i in range(j*64, (j+1)*64):
            c = df[q][i]
            av_c.append(np.mean(c))        
        map_pixels_dict[j] = np.reshape(av_c, (-1, 8))
        # Find the "bad" pixels and fill the arrays for the txt file and the map
        bad_pixels= []
        m_c = np.mean(av_c)
        m_c_std = np.std(av_c)
        #y1 = m_c - n_sigma*m_c_std
        y1 = mean - n_sigma*sigma
        y2 = mean + n_sigma*sigma
        #y2 = m_c + n_sigma*m_c_std
        for k in range(len(av_c)):
            if av_c[k] > y2 or av_c[k] < y1:
            #if av_c[k] < y1:
                bad_pixels.append(k + j*64)
                bad_pixels_arr.append(k + j*64)
                pixel_status_arr.append(0)
            else:
                pixel_status_arr.append(1)
        bad_pixels_dict[j] = bad_pixels
    
    return bad_pixels_arr, pixel_status_arr, bad_pixels_dict


def make_histo(arr, pdfs):
    fig, ax = plt.subplots()
    bins = np.linspace(np.amin(arr), np.amax(arr), int(len(arr)/2))
    ax.hist(arr, bins = bins, histtype = "step")
    ax.set_xlabel("Time [ns]")
    ax.set_ylabel("Counts")
    ax.set_title("Time of average waveform")
    pdfs.savefig()
    


#MAIN 
""" yfile = "/home/cta/Software/DarkBox/CHECS_Script/longterm.yaml"

with open(yfile, "r") as lngfile:
  lng = yaml.load(lngfile) """


#n_sigma = lng["analysis"]["n_sigma"]

n_sigma = 3
parser = argparse.ArgumentParser(description="")
parser.add_argument("-i", "--files", type=str, help=".h5 (dl1) filename (with path)", required=True)
parser.add_argument( "-d", "--dir", type = str, help="Directory of  output files", required = True)


args = parser.parse_args()
filename = args.files
data_dir = args.dir
name = filename.split("/")[-1]
print(name)
name = name.split("_dl1.h5")[0]
print(name)

path_file = filename
#path_file = os.path.join(data_dir, filename)
#Create a Reader 
r = DL1Reader(path_file)
#Get camera mapping
m = r.mapping
#Load data as pandas dataframe
d = r.load_entire_table()

output_pdf = os.path.join(data_dir,f"{name}_plots.pdf")
print(f"Plots will be saved in {output_pdf} file.")
#PDF
pplots = PdfPages(output_pdf)
#SUMUP dictionary
camera_status = {}

quantities = [ "waveform_mean", "t_averagewf","charge_cc"]
plot_charge_single_histos = False

for quantity in quantities:
    #Group data by pixel number
    df = d[d.duplicated('pixel', keep=False)].groupby('pixel')[quantity].apply(list).reset_index()
    #Quick mean values for quantity
    a = []
    for i in range(len(df[quantity])):
        a.append(np.mean(df[quantity][i]))
    a = np.array(a)

    print(f"\nQuick mean values for {quantity}:")
    print("Mean = ", np.mean(a))
    print("Std = ", np.std(a))
    print("Std/Mean ", np.std(a)/np.mean(a) *100, " %\n")

    if quantity != "t_averagewf":
        if quantity == "charge_cc":
            title_ = "Charge"
        else:
            title_ = "Time"
        camera_histo2D(a, pplots, quantity, colorMap= "viridis", title = title_, m = m, empty_borders = False)


    #Register in sumup dictionary
    camera_status[f"Mean_{quantity}"] = np.mean(a)
    camera_status[f"Std_{quantity}"] = np.std(a)
    camera_status[f"Std_{quantity}/mean_{quantity}"] = np.std(a)/np.mean(a)


    if quantity == "t_averagewf":
        make_histo(a,pplots)

    if quantity == "charge_cc":
        bad_pixels, pixel_status, bad_pixels_dict = camera_pixel_study(df, quantity, n_sigma, np.mean(a), np.std(a))
        pixel_status = np.array(pixel_status)
        print(f"PIXEL_STATUS = {pixel_status}")
        print("\nBad Pixels: ", len(bad_pixels), "\nPercentage: ", len(bad_pixels)/2048 *100, " %\n")
        camera_histo2D(pixel_status, pplots, "Pixel status", colorMap=ListedColormap(["red", "chartreuse"]), title = "Pixel status",m = m, empty_borders = True)
        if plot_charge_single_histos:
            make_nsigma_plots(df, quantity, n_sigma, data_dir, filename, pplots, np.mean(a), np.std(a))
        pplots.close()
        camera_status["n_bad_pix"] = len(bad_pixels)
        camera_status["n_bad_pix/n_tot"] =  len(bad_pixels)/2048 

        #if len(bad_pixels_dict) != 0:
        with open(os.path.join(data_dir, f"{name}_sumup.txt"), 'w') as f: 
            f.write(f"Quick stats about the camera health:\n\n")
            for key, value in camera_status.items(): 
                    f.write('%s:  %s\n' % (key, value))
            f.write("\n\n")
            f.write(f"Pixels that have charge_cc that falls out of the +- {n_sigma}\u03C3 interval [module, n_pixs]:\n\n")
            for key, value in bad_pixels_dict.items(): 
                f.write('%s:  %s\n' % (key, value))