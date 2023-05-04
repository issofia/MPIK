import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, MaxNLocator
from beamanalysis.utils import *
from map_scan2D import *
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D
plt.style.use('tableau-colorblind10')


def plot_maps(data, function, fit_output, scan_sets):
    x,y,z = data
    scan_size, scan_step, = scan_sets

    beta = fit_output.beta
    fig, ax = plt.subplots(1,2, figsize=(14, 6))  

    x_grid, y_grid = np.meshgrid(
        np.linspace(np.min(x), np.max(x), 1000), np.linspace(np.min(y), np.max(y), 1000)
    )
    z_fit = function(beta, (x_grid, y_grid)).reshape(x_grid.shape)
    levels = np.linspace(np.min(z_fit), np.max(z_fit), 10)
   
    plot_map_2d(x =x, y = y, z =  z, scan_size= scan_size, scan_step =scan_step, draw_camera=True, ax =ax[0])

    ax[0].set_title("Data + contour from fit")
    ax[0].contour(x_grid, y_grid, z_fit, levels=levels, colors = '#FF800E')
    _, xedges, yedges = plot_map_2d(x =x, y = y, z =  function(beta, (x, y)), scan_size= scan_size, scan_step =scan_step, draw_camera=True, ax =ax[1])
    ax[1].set_title("ODR Fit result")
    fig.tight_layout()
    fig.suptitle("2D SCAN - MAP")

    return xedges, yedges, fig


def plot_initial_fitting(data, masks, function, outputs, bins):
    x,y,z = data
    mx, my = masks
    out_x, out_y = outputs
    bin_x, bin_y = bins
    fig, axs = plt.subplots(1,2, figsize=(12, 4))
    axs[0].hist(x[mx], weights=z[mx], bins=bin_x, histtype='step', label = "Data", linestyle='-')
    axs[0].hist(x[mx], weights=function(out_x.beta, x[mx]), bins=bin_x, histtype='step', label = "ODR Fit",color= '#FF800E')
    axs[0].set_xlabel("x [m]")
    axs[0].set_ylabel("Power [W]")
    axs[0].set_title('Slicing over y-axis - 1D fit')
    axs[0].legend(loc = "lower center")
    axs[1].hist(y[my], weights=z[my], bins=bin_y, histtype='step', label ="Data",linestyle='-')
    axs[1].hist(y[my], weights=function(out_y.beta, y[my]), bins=bin_y, histtype='step', label = "ODR Fit",color= '#FF800E')
    axs[1].set_xlabel('y [m]')
    axs[1].set_ylabel('Power [W]')
    axs[1].set_yscale('log')
    axs[1].set_title('Slicing over x-axis - 1D fit')
    axs[1].legend(loc = "lower center")

    return fig

def plot_zero_slices(data, function, fit_output, scan_sets):
    x,y,z = data
    scan_size, scan_step, = scan_sets
    beta = fit_output.beta
    fig, ax = plt.subplots(1,2, figsize = (12,6))
   
    bins = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        round(scan_size * 2 / scan_step + 2),
    )
    xgr = np.arange(-scan_size, scan_size, scan_step)
    ygr = np.zeros(np.shape(xgr))
    power_fit = function(beta, (xgr, ygr))
    ax[0].hist(xgr, weights =power_fit, bins = bins, histtype = "step", label = "ODR fit",color= '#FF800E')
    ax[0].set_yscale('log')
    ax[0].set_xlabel("x [m]")
    ax[0].set_ylabel("Power [W]")
    ax[0].set_title("Power along y = 0")
    ygr = np.arange(-scan_size, scan_size, scan_step)
    xgr = np.zeros(np.shape(ygr))
    power_fit = function(beta, (xgr, ygr))
    ax[1].hist(ygr, weights =power_fit, bins = bins, histtype = "step", label = "ODR fit",color= '#FF800E')
    ax[1].set_yscale('log')
    ax[1].set_title("Power along x = 0")    

    #DATA (x = 0 and y = 0 slice)
    
    m = ((y> -scan_step/2) & (y< +scan_step/2) & (x > -scan_size + scan_step/2) & (x< scan_size - scan_step/2))
    ax[0].hist(x[m], weights =z[m], bins = bins, histtype = "step", label = "Data",linestyle='-')
    m = ((x>= -scan_step/2) & (x<=scan_step/2) & (y > -scan_size + scan_step/2) & (y< scan_size - scan_step/2))
    ax[1].hist(y[m], weights =z[m], bins = bins, histtype = "step", label = "Data",linestyle='-')
    ax[1].set_xlabel("y [m]")
    ax[1].set_ylabel("Power [W]")
    ax[0].legend(loc = "lower center")
    ax[1].legend(loc = "lower center")
    fig.suptitle("Power along (x,y) = (0, 0)")
    return fig

def plot_slices(data,function, fit_output, scan_sets,  n_steps): 
    scan_size, scan_step, = scan_sets
    x,y,z = data
    beta = fit_output.beta
    z_fit = function(beta, (x,y))
    sel = 0
    fig, ax = plt.subplots(1,2, figsize = (12,6))
    for sel in np.arange(-scan_size,scan_size+scan_step/2,scan_step*n_steps):
        my = ((y>=sel-scan_step/2) & (y<=sel+scan_step/2))
        ax[0].plot(x[my],z_fit[my], label = sel, color= '#FF800E',)
        ax[0].plot(x[my],z[my],color= '#006BA4',linestyle='-')

        mx = ((x>=sel-scan_step/2) & (x<=sel+scan_step/2))
        ax[1].plot(y[mx],z_fit[mx],label = sel,color= '#FF800E')
        ax[1].plot(y[mx],z[mx],linestyle='-',color= '#006BA4')

    ax[0].set_yscale('log')
    ax[0].set_xlabel("x [m]")
    ax[0].set_ylabel("Power [W]")
    ax[0].set_title("Slicing along y")
    ax[1].set_xlabel("y [m]")
    ax[1].set_ylabel("Power [W]")
    ax[1].set_title("Power along x")
    plt.figtext(0.47, 0.93, "Data", color= '#006BA4',fontsize='large', ha ='right')
    plt.figtext(0.53, 0.93, "Fit",  color= '#FF800E',fontsize='large', ha ='left')
    plt.figtext(0.50, 0.93, ' vs ', fontsize='large', ha ='center')
    fig.suptitle("Power along x and y ")
 
    return fig

def plot_pow_vs_axis(data,function, fit_output, scan_sets):
    x,y,z = data
    z_fit = function(fit_output.beta, (x,y))
    scan_size, scan_step = scan_sets
    bins = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        round(scan_size * 2 / scan_step + 2),
    )
    fig, ax = plt.subplots(1,2, figsize = (12,6))
    ax[0].hist(x, weights = z,  bins = bins, label = "Data", histtype = "step",linestyle='-')
    ax[0].hist(x, weights = z_fit, bins = bins, label = "Fit", histtype = "step",color= '#FF800E')
    ax[0].legend(loc = "lower center")
    ax[0].set_xlabel("x [m]")
    ax[0].set_ylabel("Power [W]")
    ax[0].set_yscale("log")
    ax[1].hist(y, weights = z,bins = bins, label = "Data", histtype = "step",linestyle='-')
    ax[1].hist(y, weights = z_fit, bins = bins, label = "Fit", histtype = "step",color= '#FF800E',)
    ax[1].legend(loc = "lower center")
    ax[1].set_xlabel("y [m]")
    ax[1].set_ylabel("Power [W]")
    ax[1].set_yscale("log")
    fig.suptitle("Power VS x and y axis")

    return fig


def plot_residuals(out, z_true, title):
    
    y = out.y
    residuals = z_true - y
    bins_res = np.linspace(np.amin(residuals), np.amax(residuals), int(len(residuals)/100))
    fig,ax = plt.subplots()
    ax.hist(residuals,  histtype = "step", bins = bins_res)
    ax.set_yscale("log")
    ax.set_xlabel("$\mathregular{z_{true} - z_{fit}\ [W]}$")
    ax.set_ylabel("Counts")
    plt.title(title)

    return fig
    
def plot_residuals_2D(out, function, xy, z_true, scan_sets, title):
    scan_size, scan_step = scan_sets
    x,y = xy
    z_fit = function(out.beta, (x,y))
    residuals = z_true - z_fit
    fig, axs = plt.subplots()
    bins_ = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        round(scan_size * 2 / scan_step + 2),
    )
    _, _, _, image = axs.hist2d(
        x,
        y,
        bins=bins_,
        weights= residuals,
    )
    axs.set_xlabel("x [m]")
    axs.set_ylabel("y [m]")
    plt.colorbar(image, ax = axs, label="$\mathregular{z_{true} - z_{fit}}$")
    plt.title(title)
    fig.tight_layout()
    return fig

def plot_correction_factors(factors):
    Rx, Ry = factors    
    fig, ax = plt.subplots(1,2, figsize = (12,6))
    binx = np.linspace(np.amin(Rx), np.amax(Rx), int(len(Rx)/50))
    ax[0].hist(Rx,  histtype = "step", bins = binx)
    ax[0].set_yscale("log")
    ax[0].set_xlabel("$\mathregular{Correction\ factor\ along\ x}$")
    ax[0].set_ylabel("Counts")
    biny = np.linspace(np.amin(Ry), np.amax(Ry), int(len(Ry)/50))
    ax[1].hist(Ry, histtype = "step", bins = biny)
    ax[1].set_yscale("log")
    ax[1].set_xlabel("$\mathregular{Correction\ factor\ along\ y}$")
    ax[1].set_ylabel("Counts")
    fig.suptitle("Correction factors distribution")
    return fig


def plot_res_percentage(out, function, xy, z_true, title):
    x,y = xy
    z_fit = function(out.beta, (x,y))
    pe = (z_true/z_fit)
    fig, axs = plt.subplots()
    bins = np.linspace(np.amin(pe), np.amax(pe), int(len(pe)/100))
    axs.hist(pe, histtype = "step", bins = bins)
    axs.set_yscale("log")
    axs.set_xlabel("$\mathregular{z_{true}/z_{fit}}$")
    axs.set_ylabel("Counts")
    plt.title(title)

    return fig

def plot_res_percentage2D(out, function, xy, z_true, scan_sets, title):
    scan_size, scan_step = scan_sets
    x,y = xy
    z_fit = function(out.beta, (x,y))
    pe = (z_true/z_fit)
    fig, axs = plt.subplots()
    bins_ = np.linspace(
        -scan_size - scan_step / 2,
        scan_size + scan_step / 2,
        round(scan_size * 2 / scan_step + 2),
    )
    _, _, _, image = axs.hist2d(
        x,
        y,
        bins=bins_,
        weights= pe,
    )
    axs.set_xlabel("x [m]")
    axs.set_ylabel("y [m]")
    plt.colorbar(image, ax = axs, label="$\mathregular{z_{true}/z_{fit}}$")
    plt.title(title)
    fig.tight_layout()
    return fig



def plot_3D_beam(data,scan_sets):
    x,y,z = data
    scan_size, scan_step = scan_sets
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    bins_ = np.linspace(
            -scan_size - scan_step / 2,
            scan_size + scan_step / 2,
            round(scan_size * 2 / scan_step + 2),
        )
    _, xedges, yedges = np.histogram2d(x, y, bins=bins_)
    xpos, ypos = np.meshgrid(xedges[:-1] + 0.25, yedges[:-1] + 0.25, indexing="ij")
    xpos = xpos.ravel()
    ypos = ypos.ravel()
    surf = ax.plot_trisurf(x,y, z,cmap= "viridis",  linewidth=0)
    ax.xaxis.set_major_locator(MaxNLocator(10))
    ax.yaxis.set_major_locator(MaxNLocator(10))
    ax.zaxis.set_major_locator(MaxNLocator(10))
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("Power [W]")
    ax.set_zscale("log")
    fig.tight_layout()
    fig.colorbar(surf)
    #fig.show()

    return fig