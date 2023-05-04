import numpy as np
from scipy.odr import ODR, Model,  RealData

def gaussian_tilt(xy, amplitude, x0, y0, sigma_x, sigma_y, theta_x, theta_y):
    """Returns a 2D Gaussian function with optional tilting and shifting.

    Parameters
    ----------
    xy : array_like, shape (2, ...)
        The x and y coordinates at which to evaluate the Gaussian function.
    amplitude : float
        The maximum value of the Gaussian function.
    x0 : float
        The x-coordinate of the center of the Gaussian function.
    y0 : float
        The y-coordinate of the center of the Gaussian function.
    sigma_x : float
        The standard deviation of the Gaussian function in the x-direction.
    sigma_y : float
        The standard deviation of the Gaussian function in the y-direction.
    theta_x : float
        The angle of rotation (in radians) of the Gaussian function in the x-direction.
    theta_y : float
        The angle of rotation (in radians) of the Gaussian function in the y-direction.

    Returns
    -------
    gauss : ndarray, shape same as xy
        A 2D array of the same shape as `xy`, where each element contains the value of the
        Gaussian function at the corresponding (x, y) coordinates. The Gaussian function
        is calculated as `amplitude * exp(-(a*x**2 + 2*b*x*y + c*y**2))`, where `a`, `b`,
        and `c` are constants determined by the input parameters.
    """
    x, y = xy
    x, y = x - x0, y - y0
    a = np.cos(theta_x)**2/(2*sigma_x**2) + np.sin(theta_y)**2/(2*sigma_y**2)
    b = -np.sin(2*theta_x)/(4*sigma_x**2) + np.sin(2*theta_y)/(4*sigma_y**2)
    c = np.sin(theta_x)**2/(2*sigma_x**2) + np.cos(theta_y)**2/(2*sigma_y**2)
    gauss = amplitude*np.exp( -(a*x**2 + 2*b*x*y + c*y**2))
    return gauss




def odr_1Dfit(function, p0, data, sigma_data, print_out):
    """This method performs a one-dimensional fit on data with the suggested function
        using the ODR pack which allows to take into account the experimental errors on data.

    Args:
        function (method): the function that should best describe experimental data
        p0 (array, list): list or array that contains the initial suggested parameters
        data (array, list): experimental data
        sigma_data (array, list): experimental errors on data

    Returns:
        ODR.output: fit output, containing information such as fit parameters,
                    errors on fit parameters, covariance matrix, residual covariance, etc...
    """
    x,y = data
    sx, sy = sigma_data
    mod = Model(function)
    mydata = RealData(x, y, sx=sx, sy=sy)
    myodr = ODR(mydata, mod, beta0=p0)
    out = myodr.run()
    if print_out:
        out.pprint()
    return out

def odr_2Dfit(function, p0, data, sigma_data, print_out):
    """This method performs a two-dimensional fit on data with the suggested function
        using the ODR pack which allows to take into account the experimental errors on data.

    Args:
        function (method): the function that should best describe experimental data
        p0 (array, list): list or array that contains the initial suggested parameters
        data (array, list): experimental data (x,y,z)
        sigma_data (array, list): experimental errors on data

    Returns:
        ODR.output: fit output, containing information such as fit parameters,
                    errors on fit parameters, covariance matrix, residual covariance, etc...
    """
    x,y,z = data
    sx,sy,sz = sigma_data
    mydata = RealData(np.vstack((x, y)), z, sx=np.vstack((sx, sy)), sy = sz)
    model = Model(function)
    odr = ODR(mydata, model, beta0=p0)
    out = odr.run()
    if print_out:
        out.pprint()
    return out



def super_gaussian1D_odr(B, x):
    """One-dimensional "supergaussian" distribution; 
        a more general formulation of a Gaussian function with a flat-top and Gaussian fall-off .
        It corresponds to a "standard" gaussian distribution with n=1.

    Args:
        B (array): parameters
        x (array): x-coordinates

    Returns:
        array: f(x), Supergaussian 
    """
    A, x0, wx, n = B
    x = x - x0
    argx = 0.5*(x/wx)**2
    return A*np.exp(-(argx)**n)

def super_gaussian2D_odr(B, xy):
    """Two-dimensional "supergaussian"; 
    "elliptical Gaussian distribution"
    It corresponds to a "standard" 2D gaussian distribution with n=1.

    Args:
        B (array): parameters
        xy (tuple): x and y coordinates

    Returns:
        array: f(x,y), 2D supergaussian
    """
    x,y = xy
    A, x0, y0, wx,wy, n = B
    x = x - x0
    y = y - y0
    argx = 0.5*(x/wx)**2
    argy = 0.5*(y/wy)**2
    E = -(argx + argy)**n
    return A*np.exp(E)