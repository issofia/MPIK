import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
from beamanalysis.utils import *
from map_scan2D import *
from scipy.odr import ODR, Model, Data, RealData
from plotting import *
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import yaml
from termcolor import colored 
import os
import time

with open("scan2D_fit.yml", "r") as input:
    inp = yaml.safe_load(input)
    filename = inp["experimental_data"]["file"]
    corr_file = inp["experimental_data"]["correction_file"]
    distance = inp["experimental_data"]["distance"]
    source = inp["experimental_data"]["source"]
    filter = inp["experimental_data"]["filter"]
    sensor_size = inp["instrumental_specs"]["sensor_size"]
    NSB_wave_corr = inp["instrumental_specs"]["NSB_wavelength_correction"] 
    dir = inp["results"]["final_directory"]

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

if source == "NSB":
    z = z + NSB_wave_corr*z


histo, bin_x, bin_y= plot_map_2d(x, y, z, scan_size, scan_step, True, title = f"Scan {filename[-27:-11]} - {distance} m")

sx = abs(d["x"]-d["xreal"])/2
sy = abs(d["y"]-d["yreal"])/2
sz = np.empty(np.shape(z))
sz = eval_power_res(z)
print(colored(f"Power statistics before correction:\nMean power = {np.mean(z)}\nSigma power = {np.std(z)}\nsigma/mean power = {np.std(z)/np.mean(z)}\nBeam uniformity: {np.std(z)/np.mean(z)*100}", "green"))


#Define masks for slicing along 0-axis
mx = ((y> -scan_step/2) & (y< +scan_step/2) & (x > -scan_size + scan_step/2) & (x< scan_size - scan_step/2))
my = ((x>= -scan_step/2) & (x<=scan_step/2) & (y > -scan_size + scan_step/2) & (y< scan_size - scan_step/2))
#Initial 1D parameters

if source == "laser":
    p0x = [np.amax(z[mx]), 0., 0.2, 5]
    p0y = [np.amax(z[my]), 0., 0.2, 5]
else:
    p0x = [np.amax(z), x[np.argmax(z)], 0.2, 5]
    p0y = [np.amax(z), y[np.argmax(z)], 0.2, 5]

print(colored(f"Initial parameters for 1D fit:\np0x = {p0x}\np0y = {p0y}\n", "cyan"))
out_x = odr_1Dfit(super_gaussian1D_odr, p0x, [x[mx], z[mx]], [sx, sz],print_out=False)
out_y = odr_1Dfit(super_gaussian1D_odr, p0y, [y[my], z[my]], [sy, sz],print_out=False)

fit1D_slicezero = plot_initial_fitting(data = [x,y,z], masks = [mx,my], outputs = [out_x, out_y], bins = [bin_x, bin_y], function = super_gaussian1D_odr)


#2D fit
pars_x = out_x.beta
pars_y = out_y.beta
print(colored(f"Obtained 1D fit parameters:\np0x= {pars_x}\np0y = {pars_y}\n","green"))
beta_2D_0 = [np.mean([pars_x[0], pars_y[0]]),
             pars_x[1],
             pars_y[1],
             pars_x[2],
             pars_y[2],
             np.mean([pars_x[3], pars_y[3]])             
             ]

print(colored(f"Initial parameters for 2D FIT: {beta_2D_0}\n", "cyan"))
out2D = odr_2Dfit(function = super_gaussian2D_odr, p0 = beta_2D_0, data = [x,y,z], sigma_data = [sx,sy,sz], print_out=False)

#Correction
R_x, R_y = eval_correction_factors(out2D, [x,y], [sensor_size, distance])
z_corr = z*R_x*R_y
sz_corr = sz*R_x*R_y
out2D_corr = odr_2Dfit(function = super_gaussian2D_odr,  p0 =out2D.beta, data =[x,y,z_corr], sigma_data =[sx,sy,sz_corr], print_out=False)
chi2corr = chi_square(out2D_corr,z_corr)
print_smart_output(output = out2D_corr, cov = False)
print(colored(f"Chi-square (corrected function) = {chi2corr}\n", "green"))

mean_power_corr = np.mean(z_corr)
std_power_corr = np.std(z_corr)
mean_std = std_power_corr/mean_power_corr
print(colored(f"Power statistics after correction:\nMean power = {mean_power_corr}\nSigma power = {std_power_corr}\nsigma/mean power = {mean_std}\nBeam uniformity: {mean_std*100}", "green"))



#PLOTTING
slices = plot_slices([x,y,z],super_gaussian2D_odr, out2D_corr, [scan_size, scan_step], 10)
corr_histos = plot_correction_factors([R_x, R_y])
xedges, yedges, maps2D = plot_maps([x,y,z_corr], super_gaussian2D_odr, out2D_corr, [scan_size, scan_step])
zero_slices = plot_zero_slices([x,y,z_corr],  super_gaussian2D_odr, out2D_corr, [scan_size, scan_step])
per2D = plot_res_percentage2D(out2D_corr, super_gaussian2D_odr, (x,y), z_corr, [scan_size, scan_step], "Ratio between measured and fitted power - 2DMAP")
map2D = plot_map([x,y,z_corr], super_gaussian2D_odr, out2D_corr, [scan_size, scan_step])
if inp["results"]["plot_3D_beam"]:
    plot_3D = plot_3D_beam([x,y,z_corr], [scan_size, scan_step])
    


#SAVE PLOTS
if not os.path.exists(dir):
    os.mkdir(dir)
base_name = f"{filename[-27:-11]}_{distance}m"
if source == "laser":
    base_name_dir = f'{source}_beam_fit_{base_name}/'
else:
    base_name_dir = f'{source}_{filter}_{base_name}/'

dir = os.path.join(dir, base_name_dir)
map2D.savefig(os.path.join(dir,"map_2D.png"))
per2D.savefig(os.path.join(dir,"ratio_2D.png"))
fit1D_slicezero.savefig(os.path.join(dir,"fit1D_slicezero.png"))
corr_histos.savefig(os.path.join(dir,"corr_histos.svg"))
zero_slices.savefig(os.path.join(dir,"zero_slices.png"))
map2D.savefig(os.path.join(dir,"map_2D.svg"))
per2D.savefig(os.path.join(dir,"ratio_2D.svg"))
fit1D_slicezero.savefig(os.path.join(dir,"fit1D_slicezero.svg"))
zero_slices.savefig(os.path.join(dir,"zero_slices.svg"))
if not os.path.exists(dir):
    os.mkdir(dir)

pdf_file = f"{filename[-27:-11]}_{distance}m.pdf"
output_file = os.path.join(dir, pdf_file)

fn = os.path.join(dir, f"{base_name}_fit_results.txt")
print(colored(f"Saving fit result in {fn} file.\n", "cyan"))
with open(fn,'w') as f:
    f.write(f"***Beam statistics***\n")
    f.write(f"Mean power = {mean_power_corr}\nStd deviation = {std_power_corr}\nStd/mean = {mean_std}\nBeam uniformity = {mean_std*100} %\n")
    f.write(f"\n***Beam model fit results***\n")
    f.write(f"Chi-square: {chi2corr}\n")
    f.write("Parameters = Amplitude (W), x0 (m), y0 (m), sigma_x (m), sigma_y (m), n\n\n")
    f.write('Parameter\tParameter_error\n')
    np.savetxt(f, np.c_[out2D_corr.beta, out2D_corr.sd_beta],fmt = ['%.5e','%.5e'], delimiter='\t')

print(colored(f"Saving plots in {output_file} file.\n", "cyan"))
with PdfPages(output_file) as pdf:
    pdf.savefig(fit1D_slicezero)
    pdf.savefig(corr_histos)
    pdf.savefig(maps2D)
    pdf.savefig(zero_slices)
    pdf.savefig(per2D)
  
    if inp["results"]["plot_3D_beam"]:
        pdf.savefig(plot_3D)

    if distance == 1 or source == "NSB":
        pdf.savefig(slices)


    infod = pdf.infodict()
    infod['Title'] = 'Beam model plots'
    infod['Author'] = 'Isabella Sofia'
    infod['Subject'] = 'Laser and NSB beam fit plots'
    infod['Keywords'] = 'Laser NSB beam fit 2D 1D plots'
    infod['CreationDate'] = datetime.datetime(2023, 4, 19)
    infod['ModDate'] = datetime.datetime.today()


#Rumenta momentanea
""" 
slices.text(0.1,0.01, f"Comparison between histograms representing x and y slices of experimental data and the fit result (starting from 2D fit result).")
maps2D.text(0.1,0.01, f"Comparison between 2D distribution of measured power (left) and 2D fit result (right). Chi-square = {chi2corr}")
zero_slices.text(0.1,0.01, f"Comparison between the power distribution along x = 0 and y = 0 (experimental data and fit result from 2D function).")
power_axis.text(0.1,0.01, f"Comparison between the distribution of measured and fitted power (from 2D fit result).")
"""