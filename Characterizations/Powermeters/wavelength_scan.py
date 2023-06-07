from newport844peusb import Newport_844PEUSB
from aimttiplp import AimTTiPLP
import numpy as np
import time
import matplotlib.pylab as plt
import os, sys
plt.style.use('tableau-colorblind10')


if __name__ == "__main__":

    lambda_min = 200 #nm
    lambda_max = 1100 
    step = 45
    n_meas = 10.
    wavelengths = np.arange(lambda_min, lambda_max, step)

    data_dir = "Meas/01/" #which directory?
    base_name = f'd{time.strftime("%Y%m%d_%H%M%S")}_wavelength_scan'

    n = Newport_844PEUSB(idVendor=0x0BD3, idProduct=0xE502)

    time.sleep(1)

    out_file = os.path.join(data_dir, f"{base_name}.txt")

    with open(out_file, "a") as f:
        f.write("# Time (s)\tWavelength (nm)\tPower (W)\tStd_dev_power (W)\n")
    with open(out_file, "a") as f:
        for wavelength in wavelengths:
            n.set_wavelength(wavelength)
            time.sleep(5)
            meas = []
            try:
                for i in np.range(n_meas):
                    p_ = float(n.read_one_measurement())
                    meas.append(p_)

                mean_meas = np.mean(meas)
                std_meas = np.std(meas)
                t_ = float(time.time())
                s_ = f"{t_}\t{wavelength}\t{mean_meas}\t{std_meas}"
                f.write(f"{s_}\n")
            except:
                print("Measure failed")
                pass
            time.sleep(1)


    #Read the output file and plot
    time_meas, wave, mean_power, std_power = np.loadtxt(out_file, comments="#", delimiter=" ", unpack=True)
    
    fig,ax = plt.subplots()

    ax.errorbar(wave, mean_power, yerr=std_power, elinewidth = 1.5)
    ax.set_ylabel("Power (W)")
    ax.set_xlabel("$\mathregular{\lambda} (nm)$")
    plt.title("Scan on wavelengths")
    fig.savefig(f"{base_name}_plot.pdf")