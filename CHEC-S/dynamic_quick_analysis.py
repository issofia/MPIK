import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from CHECLabPy.core.io import DL1Reader
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import gridspec
import fnmatch
from termcolor import colored
from camera_utils import *
import seaborn as sns
sns.set_context("talk")

#data_dir = './DynamicRange/d20221115/dl1s_batch/'
#results_dir = './DynamicRange/d20221115/'
#file = 'Run15812_dl1.h5'

data_dir = './MyData/longterm_data/d20221220_160846/dl1s/'
results_dir = './MyData/longterm_data/d20221220_160846/'
#file = 'Run16178_dl1.h5'
plots = False
n_photons = np.array([round(float(i),2) for i in np.logspace(0,3+1/3,11)])    

mean_waves = []
std_waves = []
mean_charges = []
std_charges = []
quantities = [ "waveform_mean", "charge_cc"]
runs = [16171,16172,16173,16174,16175,16176,16177,16178]
n_pixel=0
if len(n_photons) == len(os.listdir(data_dir)):
    print(f"OK")
# Open a file with access mode 'a'
file_object = open(os.path.join(data_dir,'means.txt'), 'w')
file_object.write("MEAN_WAVEFORMs, STD_WAVEFORM, MEAN_CHARGECC, STD_CHARGECC\n")
#print(os.listdir(data_dir))
#print(n_photons)
#file = os.path.join(data_dir, filename)
for run in runs:
    file = f'Run{run}_dl1.h5'
    print(colored('Analyzing data from %s file' % file, 'yellow'))
    filename = file.split('_')[0]
    print(f"filename = {filename}")
    file = os.path.join(data_dir, file)
    try:
        read = DL1Reader(file)
    except Exception as e:
        print(f"Couldn't open file {file}: {e}.\nContinuing on scan...")

    try:
        #Get camera mapping
        m = read.mapping
        #Load data as pandas dataframe
        d = read.load_entire_table()

        #output_pdf = os.path.join(data_dir,f"{filename}_{run}_plots.pdf")
        #print(f"Plots will be saved in {output_pdf} file.")
        #pplots = PdfPages(output_pdf)
        for quantity in quantities:
            #Group data by pixel number
            df = d[d.duplicated('pixel', keep=False)].groupby('pixel')[quantity].apply(list).reset_index()
            #Quick mean values for quantity
            a = []
            for i in range(len(df[quantity])):
                a.append(np.mean(df[quantity][i]))
            a = np.array(a)
            mean_arr = np.mean(a)
            std_arr = np.std(a)
            print(f"\nQuick mean values for {quantity}:")
            print("Mean = ", mean_arr)
            print("Std = ", std_arr)
            print("Std/Mean ", np.std(a)/np.mean(a) *100, " %\n")
            if quantity == "charge_cc":
                mean_charges.append(mean_arr)
                std_charges.append(std_arr)
            else:
                mean_waves.append(mean_arr)
                std_waves.append(std_arr)
            if quantity != "t_averagewf" and plots:
                im = camera_histo2D(a, None, quantity, colorMap= "viridis", title = quantity, m = m)
                im.savefig(os.path.join(data_dir,f"{filename}_{quantity}.pdf"))
    except Exception as e:
        print({e})

file_object.write(f"{mean_waves}\t{std_waves}\t{mean_charges}\t{std_charges}\n")
print(f"Mean charges = {mean_charges}\nStd charges = {std_charges}\nMean waves = {mean_waves}\nStd waves = {std_waves}")
# Close the file
file_object.close()
n_photons = np.array([10,   21,   46,  100,  215,  464, 1000, 2154])
pde = 0.4
spe = np.divide(mean_charges, pde*n_photons)
print(f"spe = {spe}")
spe_mean = np.mean(spe)
print(f"mean_spe = {spe_mean}")

wave, ax = plt.subplots(figsize = (10,8))
plt.errorbar(n_photons, mean_waves, std_waves)
ax.set_ylabel("Mean waveform [mV]")
ax.set_title("Mean waveform")
ax.set_xlabel("Number of photons")
wave.tight_layout()
chargecc, ax = plt.subplots(figsize = (10,8))
plt.errorbar(n_photons, mean_charges, std_charges)
ax.set_title("Charge")
#ax.set_ylabel("Mean charge [cross-correlated units]")
ax.set_ylabel("Charge [Arbitrary units]")
ax.set_xlabel("Number of photons")
chargecc.tight_layout()




wave.savefig(os.path.join(data_dir,f"dynamic_range_waveform.pdf"))
chargecc.savefig(os.path.join(data_dir,f"dynamic_range_chargecc.pdf"))
wave.savefig(os.path.join(data_dir,f"dynamic_range_waveform.png"))
chargecc.savefig(os.path.join(data_dir,f"dynamic_range_chargecc.png"))

#plt.show()