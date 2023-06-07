import os
import numpy as np
import pickle
import matplotlib.pylab as plt
from matplotlib import pyplot

def plot_p_nsb_sipm_ph(d, ax, **plt_args):
    ax.set_xlabel("Power NSB (W)")
    ax.set_ylabel("Photon rate on SiPM (Hz)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    plt.scatter(d['p_nsb'], d['sipm_ph'], **plt_args)

def showMeasuments(files):
    """
    Draw #sipm_photons VS PM_CAM (different powermeters) for all the measurements
    :param files: a dictionary containing all the measurement files
    :return:
    """
    fig, ax = plt.subplots()
    for i in files.keys():
        diz = pickle.load(open(files[i],'rb'))
        lbl = diz["Notes"].split()
        plot_p_nsb_sipm_ph(diz, ax, label="PM CAM " + lbl[-1])
    plt.legend()
    plt.show()


def calibrationFit(files, x_meas, y_meas, x_mask):
    """
    Fit data with a line
    :param files: a dictionary containing all the measurement files
    :param x_meas: the data on the x-axis (z.B. p_nsb)
    :param y_meas: the data on the y-axis (z.B. sipm_ph)
    :param x_mask: value which sets the left-side extreme of the fitting range
    :return: two dictionaries, one for the angular coefficient m, one for the intercept q, containing lists with values
    and parameter errors
    """
    fig, ax = plt.subplots()
    dic_m = {}
    dic_q = {}
    k = 0
    for i in files.keys():
        d = pickle.load(open(files[i], 'rb'))
        lbl = d["Notes"].split()
        print("SN PM #"+str(i)+": "+ str(lbl[-1]))
        d[y_meas] *= 1e-09
        x = d[x_meas]
        y = d[y_meas]
        mask = d[x_meas] > x_mask
        #ax.set_xlabel(x_meas)
        #ax.set_ylabel(y_meas)
        ax.set_xlabel("Power NSB [W]")
        ax.set_ylabel("SiPM photon rate [Hz]")
        ax.set_xscale("log")
        ax.set_yscale("log")
        plt.scatter(d[x_meas][mask], d[y_meas][mask], label=  lbl[-1])
        p, V = np.polyfit(x, y, 1, cov=True)
        dic_m[k] = [p[0], np.sqrt(V[0][0])]
        dic_q[k] = [p[1], np.sqrt(V[1][1])]
        plt.plot(x, p[0] * x + p[1], linestyle="--", color="tab:red")
        k+=1
    plt.title("PMs calibration")
    plt.legend()
    #plt.show()
    return dic_m, dic_q


def uniformity(dict, name):
    """
    Check the uniformity of the measurements drawing a plot and fitting data; print the z value (z test)
    :param dict: a dictionary containing some values and their errors (z.B. m and sigma_m)
    :param name: the name to be shown on the y-axis of the plot
    :return:
    """
    meas = []
    y = []
    yerr = []
    for i in dict.keys():
        meas = dict[i]
        y.append(meas[0])
        yerr.append(meas[1])
    x = np.array(range(len(dict)))
    fig, ms = plt.subplots()
    ms.set_xlabel("Fit")
    ms.set_ylabel(name)
    ms.set_ylim(0,1e12)
    plt.title("Slopes")
    plt.scatter(x, y)
    plt.errorbar(x, y, yerr, fmt="o")
    p, V = np.polyfit(x, y, 1, cov=True)
    print("p0_fit: {:.8e} +/- {:.8e}".format(p[0], np.sqrt(V[0][0])))
    print("p1_fit: {:.8e} +/- {:.8e}".format(p[1], np.sqrt(V[1][1])))
    print("\n")
    plt.plot(x, p[0] * x + p[1], linestyle="--", color="tab:red")
    plt.show()
    z = (p[0] - 0) / np.sqrt(V[0][0])
    print("z: " + str(z))


infile = {
    'DEV1': './NSB_d20221006/d20221006_114434_calib/d20221006_114434_NSB_calib.pkl',
    'DEV2': './NSB_d20221006/d20221006_120021_calib/d20221006_120021_NSB_calib.pkl',
    'DEV3': './NSB_d20221006/d20221006_121118_calib/d20221006_121118_NSB_calib.pkl',
    'DEV4': './NSB_d20221006/d20221006_122408_calib/d20221006_122408_NSB_calib.pkl',
    'DEV40': './NSB_d20221006/d20221006_142534_calib/d20221006_142534_NSB_calib.pkl',
    'DEV30': './NSB_d20221006/d20221006_143616_calib/d20221006_143616_NSB_calib.pkl',
    'DEV20': './NSB_d20221006/d20221006_144520_calib/d20221006_144520_NSB_calib.pkl',
    'DEV10': './NSB_d20221006/d20221006_150337_calib/d20221006_150337_NSB_calib.pkl'
}
m,q  = calibrationFit(files = infile, x_meas = "p_nsb", y_meas = "sipm_ph", x_mask = 2e-04)

uniformity(m, "m")
#uniformity(q, "q")