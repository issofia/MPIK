import os
import yaml
from termcolor import colored
import math
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import mpl_toolkits.mplot3d.art3d as art3d
from matplotlib.patches import Circle, PathPatch, Rectangle
from beamanalysis.utils import *
from map_scan2D import *



def line(x,y):
    p,  V = np.polyfit(x, y, 1, cov = True)
    return p, V

                
def find_beam_line(data_dir, dicx, corr_file):
    """ This method finds the maximum power values and their corresponding coordinates (x,y), then proceeds to fit these points
        with a linear model.            
    Args:
        data_dir (_type_): directory where the scan 2D files are held
        dicx (_type_): dictionary containing the filenames and distances
        corr_file (_type_): file for applying angular correction

    Returns:
        data: (x,y) coordinates of the maximum power values
        pars: fit parameters
        cov: covariance matrix
    """
    maxs = []
    x_maxs = []
    y_maxs = []
    if os.path.exists(data_dir):    
        for scanfile, distance in zip(dicx["filename"], dicx["distance"]):
            filename = os.path.join(data_dir, scanfile)
            print(colored(f'Reading {scanfile} from {data_dir} directory; distance = {distance} m' , 'green'))
            d = pd.read_csv(filename, comment="#")
            d["power"] = apply_angle_correction(
                d["x"],
                d["y"],
                d["power"],
                distance=distance,
                corr_file=corr_file,
            )

            maxs.append(max(d["power"]))
            x_maxs.append(float(d["x"][d["power"] == max(d["power"])]))
            y_maxs.append(float(d["y"][d["power"] == max(d["power"])]))

        pars, cv= line(x_maxs, y_maxs)
        data = [x_maxs, y_maxs]

        return data, pars, cv    
    else:
        print(colored(f"Directory {data_dir} doesn't exist.", 'red'))
        exit()   
       

def draw_darkbox():
    """This method draws a 3D plot rappresenting the darkbox.
    Returns:
        fig,ax
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    #generics
    ax.set_xlabel('z [m]')
    ax.set_ylabel('x [m]')
    ax.set_zlabel('y [m]')
    ax.set_zlim(-1.,1.)
    ax.set_xlim(0.,4)
    ax.set_ylim(-1.,1.)

    #Add elements
    #Source
    ax.text(0., 0., -0.5, "Source", zdir="x", size=10)
    source = Circle((0., 0.), 0.01, color = "r")
    ax.add_patch(source)
    art3d.pathpatch_2d_to_3d(source, z=0, zdir="x")
    #Camera
    ax.text(4., 0., -0.5, "Camera", zdir="x", size=10)
    camera = Rectangle((-0.3,-0.3), 0.6,0.6, color = "red", alpha = 0.3)
    ax.add_patch(camera)
    art3d.pathpatch_2d_to_3d(camera, z=4., zdir="x")

    return fig, ax




def plot_beam_line(ax, data, distances, pars, cv):
    """This method plots the fitted line obtained by data.

    Args:
        ax (axis): 
        data (list): list containing (x,y) coordinates
        distances (array): array containing distances
        pars (array): fit parameters
        cv (array): covariance matrix
    """
    # Plot the data and the line
    x = np.array(data[0])
    y = np.array(data[1])
    ax.scatter(distances, x, y, c='black', marker='x', s = 13)
    xdb = np.linspace(- pars[1] - math.sqrt(cv[1][1]),pars[1] + math.sqrt(cv[1][1]),100)
    zdb = np.linspace(0.,4.,100)
    x = np.sort(np.append(x, xdb), axis = None)
    distances = np.sort(np.append(distances, zdb), axis = None)
    ax.plot(distances, x, pars[0]*x + pars[1], c = "blue", alpha = 0.7)
    #ax.plot(distances, x, (pars[0]+ math.sqrt(cv[0][0]))*x + pars[1], c = "red", alpha = 0.7)
    #ax.plot(distances, x, (pars[0]-math.sqrt(cv[0][0]))*x + pars[1], c = "orange", alpha = 0.7)

    plt.title("Laser beam")
    plt.show()


def z_alignment_test(pars, cv):
    """This method performs a rapid Z test to check the fit parameters compatibility with the desired ones (0,0)

    Args:
        pars (array): array containing fit parameters
        cv (array): covariance matrix
    """
    m = pars[0]
    q = pars[1]
    z_m = (m/math.sqrt(cv[0][0]))
    z_q = (q/math.sqrt(cv[1][1]))

    print(colored(f"Beam line: y = {m}*x + {q}\nSlope m = {m} +- {math.sqrt(cv[0][0])}\nIntercept q = {q} +- {math.sqrt(cv[1][1])} [meters]\nCompatibility of (m,q) with (0.,0.):\n- z_m = {z_m}\n- z_q = {z_q}", 'cyan'))





with open("beam_alignment.yml", "r") as beamfile:
  bmf = yaml.load(beamfile)

files_descrip = bmf["data"]["files_desc"]
corr_file = bmf["data"]["corr_file"]
data_dir = bmf["data"]["scan_dir"]
dicx = pd.read_csv(files_descrip, comment="#", delimiter = ";")
data, parameters, covmat = find_beam_line(data_dir, dicx, corr_file)

z_alignment_test(parameters, covmat)

fig, ax = draw_darkbox()
plot_beam_line(ax,data, dicx["distance"], parameters, covmat)
