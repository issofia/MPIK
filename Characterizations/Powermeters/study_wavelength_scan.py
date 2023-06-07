import numpy as np
import matplotlib.pyplot as plt
import argparse
from scipy.constants import *
plt.style.use('tableau-colorblind10')


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-i", "--file", type=str, help=".txt input file (with path)", required=True
)

args = parser.parse_args()
filename = args.file
base_name = filename.split("/")[2][:-4]
peak_wave = 400 #nm

time_meas, wave, mean_power, std_power = np.loadtxt(filename, unpack=True)

peak_w = find_nearest(wave, peak_wave)
print(f"Nearest value: {peak_w} nm")

qe_relative = (mean_power[wave == peak_w]/mean_power)*(peak_w/wave)

#print(f"qe_relative = {qe_relative}")
respons_rel = qe_relative * (wave/peak_w)
constant_q = elementary_charge/(Planck/1.6e-19) * speed_of_light/1e09
print(f"e = {elementary_charge}\nh = {Planck}\nh in eV = {(Planck/1.6e-19)}\ne/h in eV = {elementary_charge/(Planck/1.6e-19)}\nc = {speed_of_light/1e09}\nconstant q = {constant_q}")
#respons_rel = qe_relative * (peak_w/wave)

fig,ax = plt.subplots(figsize = (8,6))
ax.errorbar(wave, mean_power, yerr=std_power, elinewidth = 2., ecolor = "#FF800E")
ax.set_ylabel("Power (W)")
ax.set_xlabel("$\mathregular{\lambda}\ (nm)$")
plt.title("Power VS wavelength")
fig.savefig(f"./Plots/power_vs_wave_{base_name}.png")
fig,ax = plt.subplots(figsize = (8,6))
ax.plot(wave, qe_relative)
ax.set_yscale('log')
ax.set_ylabel("Normalized QE")
ax.set_xlabel("$\mathregular{\lambda}\ (nm)$")
plt.title("Relative Q.E. VS wavelength")
fig.savefig(f"./Plots/rel_qe_vs_wave_{base_name}.png")


fig,ax = plt.subplots()
ax.plot(wave, respons_rel)
ax.set_yscale('log')
ax.set_ylabel("Normalized responsivity")
ax.set_xlabel("$\mathregular{\lambda} \ (nm)$")
plt.title("Responsivity VS wavelength")
fig.savefig(f"./Plots/responsivity_rel_wave_{base_name}.png")


plt.show()
#fig.savefig(f"{filename}_plot.pdf")