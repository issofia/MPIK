import math
import pickle
import numpy as np
from scipy import constants
import yaml

def power_pm_cam_to_ph_pulse_sipm(power_pm, wavelength, rate, a_sipm, a_pm):
    """Converts the power measured at the PM Cam to the number of photons hitting the
    SiPM for each laser pulse, if the PM Cam and the camera are at the same distance
    from the uniform light source

    Parameters
    ----------
    power_pm : float (or np.array of floats)
        power measured by the PM Cam (W)
    wavelength : float
        light wavelength (m)
    rate : float
        laser rate (Hz)
    a_sipm : float
        SiPM area (mm**2)
    a_pm : float
        PM Cam area (mm**2)

    Returns
    -------
    float
        photon rate hitting the SiPM
    """
    ph_sipm = (
        power_pm
        / (constants.h * constants.c / wavelength)
        * (1 / rate)
        * (a_sipm / a_pm)
    )
    return ph_sipm


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
    """Returns a boolean mask indicating which (x, y) coordinates are inside the SST
    camera

    Parameters
    ----------
    x : np.array
        The x-coordinates of the points, in meters.
    y : np.array
        The y-coordinates of the points, in meters.

    Returns
    -------
    mask : ndarray of bools
        A boolean array of the same shape as x and y, where True indicates that
        the corresponding point is inside the camera field of view, and False
        indicates that it is outside.
    """
    ms = (51.4 + 1.93) / 1000.0
    m = (x >= -3 * ms) & (x <= 3 * ms) & (y >= -3 * ms) & (y <= 3 * ms)
    m = m & ~((x >= -3 * ms) & (x <= -2 * ms) & (y >= -3 * ms) & (y <= -2 * ms))
    m = m & ~((x >= -3 * ms) & (x <= -2 * ms) & (y >= 2 * ms) & (y <= 3 * ms))
    m = m & ~((x >= 2 * ms) & (x <= 3 * ms) & (y >= -3 * ms) & (y <= -2 * ms))
    m = m & ~((x >= 2 * ms) & (x <= 3 * ms) & (y >= 2 * ms) & (y <= 3 * ms))
    return m


def apply_angle_correction(
    x, y, power, distance, corr_file, light_source=(0, 0, 1e-10)
):
    """
    Apply correction factors to power values based on the angle between the light source
    and the points.

    Parameters
    ----------
    x : numpy.ndarray
        X-coordinates of the points (m).
    y : numpy.ndarray
        Y-coordinates of the points (m).
    power : numpy.ndarray
        Power values at each point.
    distance : float
        Distance from the light source to the points (m).
    corr_file : str
        File name of the correction factors, in pickle format.
    light_source : tuple of float, optional
        Coordinates of the light source (m), by default `(0, 0, 1e-10)`.

    Returns
    -------
    numpy.ndarray
        Corrected power values.
    """
    corr_factor = pickle.load(open(corr_file, "rb"))

    # Loop... stupid mode
    for i in range(len(x)):
        angle = eval_angle(p1=light_source, p2=(x[i], y[i], distance))
        c_ = corr_factor["k"][np.argmin(abs(corr_factor["angle"] - angle))]
        power[i] *= c_

    return power


def eval_angle(p1, p2):
    """
    Calculate the angle between two points in 3-dimensional space.

    Parameters
    ----------
    p1 : tuple of float
        Coordinates of point P1.
    p2 : tuple of float
        Coordinates of point P2.

    Returns
    -------
    float
        Angle between points P1 and P2 in degrees. If either point has a magnitude of 0, returns 0.

    """
    dot_product = sum([a * b for a, b in zip(p1, p2)])
    length_p1 = math.sqrt(sum([a**2 for a in p1]))
    length_p2 = math.sqrt(sum([b**2 for b in p2]))
    if length_p1 == 0 or length_p2 == 0:
        return 0
    radians = math.acos(dot_product / (length_p1 * length_p2))
    return math.degrees(radians)

def eval_correction_factors(fit_output, data, exp_parameters):
    sensor_size, distance = exp_parameters
    x0, y0 = fit_output.beta[1], fit_output.beta[2]
    x,y = data
    x,y = x-x0, y-y0
    eps = sensor_size/distance
    ax1 = np.arctan2(x, distance)
    ay1 = np.arctan2(y, distance)
    R_x = (distance*(np.tan(ax1 + eps) - np.tan(ax1)))/sensor_size
    R_y = (distance*(np.tan(ay1 + eps) - np.tan(ay1)))/sensor_size
    return R_x, R_y

def eval_power_res(z):
    with open("scan2D_fit.yml", "r") as input:
        inp = yaml.safe_load(input)
    s_detector = inp["instrumental_specs"]["calibration_uncertainty"]
    newport_acc = inp["instrumental_specs"]["newport_accuracy"]
    newport_res = inp["instrumental_specs"]["newport_resolution"]
    sigma_pow = np.sqrt((s_detector*z)**2 + (newport_acc*z)**2)
    return sigma_pow

def chi_square(out, z_true):
    y = out.y
    residuals = z_true - y
    chi2 = np.sum(residuals**2/y)
    return chi2

def print_smart_output(output, cov):
    """Method that prints the ODR fit output in a neater way.
    Based on the parameters of the 2D supergaussian function (for now).

    Args:
        output (ODR.output): output of ODR fit
        cov (bool): do or do not print the covariance matrix
    """
    beta = output.beta
    std_beta = output.sd_beta
    cov_beta = output.cov_beta

    print(f"Amplitude = {beta[0]} +- {std_beta[0]} W\n"
          f"x0 = {beta[1]} +- {std_beta[1]} m\n"
          f"y0 = {beta[2]} +- {std_beta[2]} m\n"
          f"sigma_x = {beta[3]} +- {std_beta[3]} m\n"
          f"sigma_y = {beta[4]} +- {std_beta[4]} m\n"
          f"n = {beta[5]} +- {std_beta[5]}\n"
          )
          
    if cov:
        print(f"Covariance matrix = {cov_beta}\n")