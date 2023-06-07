import os
from sysconfig import parse_config_h
import numpy as np
import pickle
import matplotlib.pylab as plt
from matplotlib import pyplot
from numpy import ndarray
from scipy.odr import *

sigma_x_rel = 0.25e-02  # relative accuracy on x measurements; for p_nsb = 0.25e-02
x_mask = 2e-04  # mask on x-axis; for p_nsb VS sipm_ph = 2e-04 (meas. 06/10/22)


def line(p, x):
    return p[0] * x + p[1]

def setModel(func):
    return Model(func)


#files = {
     #'DEV2': './d20221006/d20221006_120021_calib/d20221006_120021_NSB_calib.pkl',
     #'DEV20': './d20221006/d20221006_144520_calib/d20221006_144520_NSB_calib.pkl'
#}

#files = {
    #'DEV3': './d20221006/d20221006_121118_calib/d20221006_121118_NSB_calib.pkl',
    #'DEV30': './d20221006/d20221006_143616_calib/d20221006_143616_NSB_calib.pkl',
#}

files = {
    'DEV4': './NSB_d20221006/d20221006_122408_calib/d20221006_122408_NSB_calib.pkl',
    'DEV40': './NSB_d20221006/d20221006_142534_calib/d20221006_142534_NSB_calib.pkl',
}



def calibration_fit(diz, x_meas, y_meas, x_mask, sigma_x_rel, function, draw):
    """
    Get the dictionary containing the files; fit the data y_meas VS x_meas with a line;
    calculate the mean value for m and for q and their corresponding errors
    :param dict: dictionary containing the files
    :param x_meas: name of the x-value to get from files z.B. "p_nsb"
    :param y_meas: name of the x-value to get from files z.B. "sipm_ph"
    :param x_mask: mask value (where to cut data)
    :param sigma_x_rel: relative error on the x-values z.B. 0.25e-02 for p_nsb
    :param function: fitting function (here: line)
    :return: mean value for m and its sigma
    """
    sum_m = 0
    sum_sm = 0
    sum_q = 0
    sum_sq = 0
    fig, ax = plt.subplots()
    n_keys = len(diz)
    
    for i in diz.keys():
        d = pickle.load(open(diz[i], 'rb'))
        d[y_meas]*=1e-09
        lbl = d["Notes"].split()
        sn = lbl[-1]
        mask = d[x_meas] > x_mask
        x_err = np.full(len(d[x_meas][mask]), sigma_x_rel*d[x_meas][mask])
        min_p = d[x_meas].min()
        max_p = d[x_meas].max()
        # fitting (ODR)
        model = setModel(function)
        data = RealData(d[x_meas][mask], d[y_meas][mask], sx= x_err, sy=None)
        #myodr = ODR(data, model, beta0=[0., 0.], ifixb = [1,0])
        myodr = ODR(data, model, beta0 = [0.,0.])
        output = myodr.run()
        #output.pprint()
        # calculating mean values
        sum_m = sum_m + output.beta[0]
        sum_sm += output.sd_beta[0]
        sum_q += output.beta[1]
        sum_sq += output.sd_beta[1]
        # plotting
        plt.scatter(d[x_meas][mask], d[y_meas][mask], label=lbl[-1])
        plt.errorbar(d[x_meas][mask], d[y_meas][mask], x_err, fmt="o")
        #plt.plot(d[x_meas][mask], output.beta[0] * d[x_meas][mask] + output.beta[1], linestyle="--", color="tab:red")

    m = sum_m / n_keys
    sigma_m = sum_sm / n_keys
    q = sum_q /n_keys
    sigma_q = sum_sq /n_keys
    #print("m = "+str(f"{m:.6e}")+" +- "+str(f"{sigma_m:.6e}"))
    #print("q = "+str(f"{q:.6e}")+" +- "+str(f"{sigma_q:.6e}"))
    z_q = q/sigma_q
   
    if - 1.96 <= z_q <= 1.96:
        print("Intercept q compatible with 0.")
    else:
        print("Intercept q not compatible with 0. (z_q = "+str(z_q)+")")
    
    par = [m, q]
    par_p = [m + sigma_m, q + sigma_q]
    par_m = [m - sigma_m, q - sigma_q]
    
    # draw the plot if desired
    if draw:
        if x_meas == "p_nsb":
            ax.set_xlabel("NSB Power (W)")
        else:
            ax.set_xlabel(x_meas)
        if y_meas == "sipm_ph":
            ax.set_ylabel("SiPM photon rate (Hz)")
        else:
            ax.set_ylabel(y_meas)
        ax.set_xscale("log")
        ax.set_yscale("log")
        y0 = line(par, d[x_meas][mask])
        y1 = line(par_p, d[x_meas][mask])
        y2 = line(par_m, d[x_meas][mask])
        plt.plot(d[x_meas][mask], y0, 'b')
        plt.plot(d[x_meas][mask], y1, 'r--')
        plt.plot(d[x_meas][mask], y2, 'r--')
        plt.title("PM "+sn)
        plt.fill_between(d[x_meas][mask], y1, y2, facecolor="gray", alpha=0.15)
        #plt.legend()
        #plt.show()
    return m, sigma_m, q, sigma_q, sn, min_p, max_p


def rate(x, param):
    """
    Calculate the corresponding rate (Hz) to a x-value (Power, W) using the calibration parameters (calibrationFit result)
    :param x: power (W)
    :param param: fit parameters
    :return: rate
    """

    m = param[0]
    s_m = param[1]
    q = param[2]
    s_q = param[3]
    r = m* x + q
    y0 = line([m, q], x)
    y1 = line([m + s_m, q + s_q], x)
    y2 = line([m - s_m, q - s_q], x)
    #print("abs(y1-y2)/2 = " +str(abs(y1-y2)/2))
    sigma_r = np.sqrt((x ** 2) * s_m ** 2 + s_q**2 + m ** 2 * sigma_x_rel*x ** 2)

    print("Rate(p_NSB =  "+str(x)+" W) (prop.errors): " + str(r/1e06) + " \pm " + str(sigma_r/1e06) + " MHz")
    print("sigma_rate/rate: "+str(sigma_r/r))
    print("Rate(p_NSB =  "+str(x)+" W) (1sigma band): " + str(r/1e06) + " \pm " + str(abs(y1-y2)/2/1e06) + " MHz")
    print("sigma_rate/rate: "+str(abs(y1-y2)/2/r))


def power(rate, param):
    m = param[0]
    q = param[2]
    return (rate - q)/m

def saveCalibration(param):
    calib = os.path.join("", f"NSB_calib_params_PM_{param[4]}.pkl")
    results = {
        "Notes": "NSB calibration results. Linear fit: sipm_ph = m * p_nsb + q (scipy.ODR)",
        "PM_Cam_SN": param[4],
        "m": param[0],
        "sigma_m": param[1],
        "q": param[2],
        "sigma_q": param[3],
    }
    pickle.dump(results, open(calib, "wb"))
    print(f"Saved data: {calib}")


parameters = calibration_fit(files, "p_nsb", "sipm_ph", x_mask, sigma_x_rel, line, True)
print("[m, sigma_m, q, sigma_q]: "+str(parameters))
#rate(3e-02, parameters)
#saveCalibration(parameters)

m = parameters[0]
q = parameters[2]

rate(parameters[5], parameters)
rate(parameters[6], parameters)

#print("m "+ f"{m:.5e}")
#print("q "+ f"{q:.5e}")

d = pickle.load(open("./NSB_calib_params_PM_2952.pkl",'rb'))
#print(d)



