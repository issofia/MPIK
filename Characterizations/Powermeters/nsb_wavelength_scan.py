# IN darkboxmanager/subsystems/nsb.py

def _set_wavelength_pm_nsb(self,wavelength):
    """Set the NSB Power Meter wavelength"""
    self._pm_nsb.set_wavelength(wavelength)

def _set_wavelength_pm_cam(self,wavelength):
    """Set the Camera Power Meter wavelength"""
    self._pm_cam.set_wavelength(wavelength)

def wavelength_scan(
        self,
        w_min=397,
        w_max=413,
        w_n=16,
        t=10,
        read_pm_cam=False,
        out_folder="",
    ):
    """Perform a NSB LED wavelength scan between the LED wavelengths `w_min` and
    `w_max`, with 'w_n' steps.

    If `read_pm_cam` is True, also data from PM Cam will be taken.
    If not already connected, the function takes care of initialising it, but it
    will not close the connection after data acquisition.

    Parameters
    ----------
    w_min : float
        minimum LED wavelength for the scan (nm), by default 397
    w_max : float
        maximum LED wavelength for the scan (nm), by default 413
    w_n : int
        number of LED wavelengths for the scan (log spaced), by default 16
    t_min : float
        duration (s) of each measurement, by default 10
    read_pm_cam : bool, optional
        read also PM Cam data, by default False
    real_time_plot : bool, optional
        save plot in real time, by default False
    out_folder : str, optional
        output folder, if empty files will be stored in a subfolder of the one given
        in the configuration file, by default ""

    Returns
    -------
    str
        output file
    """
    check_folder(self._out_folder)

    # Initialise PM cam if will be used
    self._scan_started = True
    if read_pm_cam and self._pm_cam == None:
        self._init_pm_cam()

    self._led.turn_led_on_safe()
    if out_folder == "":
        base_name = f"d{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_folder_scan = os.path.join(self._out_folder, f"{base_name}_wavelength_scan")
    else:
        base_name = os.path.basename(out_folder.rstrip("/")).rstrip("_wavelength_scan")
        out_folder_scan = out_folder
    check_folder(out_folder_scan)

    time.sleep(5)

    p_nsb, p_nsb_err = np.array([]), np.array([])
    p_cam, p_cam_err = np.array([]), np.array([])

    # Define scan LED wavelenght
    
    w_led = np.linspace(w_min, w_max, w_n, dtype=int)*1e-09

    # Init folders
    out_folder_PM_NSB = os.path.join(out_folder_scan, "./PM_NSB/")
    check_folder(out_folder_PM_NSB)
    out_folder_PM_CAM = os.path.join(out_folder_scan, "./PM_CAM/")
    check_folder(out_folder_PM_CAM)

    t_wait = 5

    # Start Scan
    for wave, i in enumerate(w_led):
        self._set_wavelength_pm_nsb(wave)
        self._set_wavelength_pm_cam(wave)
        self._log_info(f"Reading data for {t_wait} seconds while LED stabilizing")
        self._pm_nsb.read_data_t_thread(None, t_wait)
        if read_pm_cam:
            self._pm_cam.read_data_t_thread(None, t_wait)
        # Wait for the measurement to finish
        while not self._pm_nsb.meas_done:
            time.sleep(1)
        if read_pm_cam:
            while not self._pm_cam.meas_done:
                time.sleep(1)
        self._pm_nsb.reset_meas()
        self._pm_cam.reset_meas()

        # Now acquire real data

        # PM NSB
        fn_nsb = os.path.join(out_folder_PM_NSB, f"{base_name}_PM_NSB_{i}.txt")
        self._pm_nsb.read_data_t_thread(fn=fn_nsb, t=t)

        # PM CAM
        if read_pm_cam:
            fn_cam = os.path.join(out_folder_PM_CAM, f"{base_name}_PM_CAM_{i}.txt")
            self._pm_cam.read_data_t_thread(fn=fn_cam, t=t)

        # Wait for the measurement to finish
        while not self._pm_nsb.meas_done:
            time.sleep(1)
        _, p_nsb_ = np.loadtxt(fn_nsb, unpack=True)
        p_nsb = np.append(p_nsb, np.mean(p_nsb_))
        p_nsb_err = np.append(p_nsb_err, np.std(p_nsb_) / np.sqrt(len(p_nsb_)))

        if read_pm_cam:
            # Wait for the measurement to finish
            while not self._pm_cam.meas_done:
                time.sleep(1)
            _, p_cam_ = np.loadtxt(fn_cam, unpack=True)
            p_cam = np.append(p_cam, np.mean(p_cam_))
            p_cam_err = np.append(p_cam_err, np.std(p_cam_) / np.sqrt(len(p_cam_)))

        self._pm_nsb.reset_meas()
        self._pm_cam.reset_meas()

        
    self._led.turn_led_off_safe()

    # Save results
    if read_pm_cam:
        res_ = np.c_[w_led, p_nsb, p_cam]
        header_ = "LED_wavelength (nm)\tPM_NSB (W)\tPM_CAM (W)"
    else:
        res_ = np.c_[w_led, p_nsb]
        header_ = "LED_wavelength (nm)\tPM_NSB (W)"
    w_scan = os.path.join(out_folder_scan, f"{base_name}_wavelength_scan.txt")
    np.savetxt(w_scan, res_, header=header_)
    self._log_info(f"Saved data: {w_scan}")
    self._scan_started = False

    return  w_scan


def run_wavelength_scan(self):
    """Run wavelength scan

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    try:
        self._reset_error()
        check_folder(self._out_folder)
        self._log_info("Run a wavelength scan on NSB")
        base_name = f"d{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_folder_w_scan = os.path.join(self._out_folder, f"{base_name}_wavelength_scan")
        w_scan = self.wavelength_scan(
            w_min=float(self._cfg["nsb"]["w_scan"]["w_min"]),
            w_max=float(self._cfg["nsb"]["w_scan"]["w_max"]),
            w_n=int(self._cfg["nsb"]["w_scan"]["w_n"]),
            t=float(self._cfg["nsb"]["w_scan"]["t"]),
            read_pm_cam=True,
            out_folder=out_folder_w_scan,
        )
        self._close_pm_cam()
        return True
    except Exception as e:
        self._log_error(f"NSB wavelength scan failed: {e}")
        self._close_pm_cam()
        return False
    




#IN /darkboxmanager/darkboxmanager.py


def wavelength_scan_nsb(self):
    """Run wavelength scan on NSB SubSystem

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    if "nsb" not in self._subsystems:
        self._log_error("NSB SubSystem not added to DarkBoxManager")
        return False
    else:
        if not self._nsb.successfully_created:
            self._log_error("NSB SubSystem not available")
            return False
        else:
            if self.pm_cam_in_use:
                self._log_warning("PM Cam already in use, disconnecting it")
                self._pm_cam.close()
            res = self._nsb.run_wavelength_scan()
            return res
        

#IN darkboxmanager/gui.py

#addition in

self._nsb_cmd_dict = {
            "select": "Select",
            "start": "Start NSB",
            "stop": "Stop NSB",
            "update_nsb": "Update NSB level",
            "calibrate": "Calibrate",
            "wavelength_scan": "Wavelength scan",
            "start_monitor": "Start NSB monitor",
            "stop_monitor": "Stop NSB monitor",
        }

#in _run_nsb(self):

elif nsb_cmd == self._nsb_cmd_dict["wavelength_scan"]:
    self.dbm.wavelength_scan_nsb()


#in config/darkbox.yaml
#in nsb:


w_scan:
    w_min: 397 # minimum PM wavelength for the calibration (nm)
    w_max: 413 # maximum PM wavelength for the calibration (nm)
    w_n: 16 # number of PM wavelengths for the scan (lin spaced)
    t: 10 # duration (s) of each measurement





#OPPURE
#Sempre da aggiungere in darkboxmanager/subsystems/nsb.py

def _set_wavelength_pm_nsb(self,wavelength):
    """Set the NSB Power Meter wavelength"""
    self._pm_nsb.set_wavelength(wavelength)

def _set_wavelength_pm_cam(self,wavelength):
    """Set the Camera Power Meter wavelength"""
    self._pm_cam.set_wavelength(wavelength)


#Da modificare in nsb? Però non vogliamo salvare i dati sempre, solo ora
def start_nsb_monitor(self, write_to_file = False):
    """Start NSB monitor if not already started"""
    if write_to_file:
        check_folder(self._out_folder)
        base_name = f"d{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        fn = os.path.join(self._out_folder, f"{base_name}_PM_NSB.txt")
    else:
        fn = ""
    if not self._pm_nsb.taking_data:
        self._log_info("Starting NSB monitor")
        self._pm_nsb.start_read_data_thread(fn=fn)
    else:
        self._log_warning("NSB monitor already started")

from darkboxmanager.rpc.client import DBMClient
import numpy as np
from termcolor import colored
import time 
import os
import subprocess
import matplotlib.pylab as plt
import shutil

meas_time = 5
w_min = 397
w_max = 413
step = 1

c = DBMClient(server_ip='149.217.10.193', port=50051)
c.start_nsb()
wavelengths = np.arange(w_min, w_max, step)

for wavelength in wavelengths:
    c.set_wavelength_pm_nsb(wavelength)
    time.sleep(1)
    c.start_nsb_monitor(True) 
    time.sleep(meas_time)
    #add wavelength to filename...
    c.stop_nsb_monitor() 


c.stop_nsb()
