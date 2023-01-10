"""Scan on trigger delays
07/11/2022

This script performs a scan on a range of different trigger delays, acquires data, applies the calibration 
(pedestal file) and reads the r1.tio files evaluating the mean waveform of a pixel over all the events.
The average waveform plot gets saved for each Run* file.

"""

from darkboxmanager_grpc import DBMClient
import numpy as np
from termcolor import colored
import time 
import os
import subprocess
import matplotlib.pylab as plt
import shutil
import CHECCameraClient.camera_client as cc
import CHECCameraClient.client_utils as cu
from CHECLabPy.core.io import TIOReader

def get_lid_status(cs):
    resp = cs.check_lid()[-20:]
    if str(resp).find('fully opened') != -1:
        status = 'open'
    elif str(resp).find('fully closed') != -1:
        status = 'closed'
    elif str(resp).find('opening') != -1:
        status = 'opening'
    elif str(resp).find('closing') != -1:
        status = 'closing'
    return status



c = DBMClient(server_ip='149.217.10.193', port=50051)

# Set FW to a bright position
#c.set_fw_photons(2000)

# Delays to scan (ns)
#delays = np.arange(0,1000.1,50)
# delays = np.arange(250,350.1,5)
delays=np.array([315])
#delays = np.arange(-1000, 0.1,50)

# Set trigger rate
#c.set_trigger_rate(100)

# Create camera instance
server_ip = '192.168.100.95'
client_ip = '192.168.100.100'



print('Creating ControlCS object')
cs = cc.ControlCS(client_ip=client_ip,server_ip=server_ip, auto_connect=True)

print('Creating ClientTools object')
ct = cc.ClientTools(cs)
""" 
#LID control
lid_status = get_lid_status(cs)
if lid_status == 'closed':
    print("Lid is closed.\nOpening lid and waiting while it opens...")
    cs.open_lid()
    time.sleep(70)
elif lid_status == 'open':
    print("Lid is open.")
elif lid_status == 'opening':
    print("Lid is opening.\nWaiting 70s...")
    time.sleep(70)
    print(get_lid_status(cs))
elif lid_status == 'closing':
    print("Lid is closing.\nWaiting 70s before trying to open lid...")
    time.sleep(70)
    cs.open_lid()
    print('Opening lid.\n Waiting 70s...')
    time.sleep(70)
    print(get_lid_status(cs))

if get_lid_status(cs) != 'open':
    print("Lid is not open.\nExiting...")
    exit() """

rdir = 'Results'

def_obs = "/home/cta/Software/CHECSInterface/trunk/config/ASTRI/observing-mpik_longterm.cfg"
# def_hv = "/home/cta/Software/CHECSInterface/trunk/config/hvSettings/hvSetting.cfg"
def_hv = "/home/cta/Software/CHECSInterface/trunk/config/ASTRI/hv/hv_astri_50pe100mv.cfg"
fobs = def_obs
fhv = def_hv

print(colored("Connecting to CS", 'yellow'))
print(cs.get_state())
if cs.get_state() != "Ready":
    print(colored("The camera is not in Ready", 'red'))
    
else:
    print('Camera is in ready')


if cs.go2('ready', fname = "/home/cta/Software/CHECSInterface/trunk/config/ASTRI/ready-auto_obs-mpik.cfg"):
    print(colored("--> Loading ready file succeded", 'green'))
else:
    print(colored("--> Loading ready file failed", 'red'))
    exit()

print(colored("Begin scan", 'yellow'))
data_dir, frn_name = cu.get_paths_from_config(fobs, host="cta@"+server_ip)
fped_name = "/data/Temp/Run16025_ped.tcal"
#fped_name = os.path.join(data_dir,'')

if not ct.ccs.hv_set_dac(fname=fhv):
    print("Acquire run: Setting HV DAC failed")
time.sleep(1)  # CS #!!

if not ct.ccs.hv_on(fname=fhv):
    print("Acquire run: Setting HV ON failed")
time.sleep(1)  # CS #!!

run_numbers = []

for j, delay in enumerate(delays):
    # Set trigger delay
    print(f'Setting trigger delay to {delay} ns')
    c.set_trigger_delay(delay)

    # start trigger
    print(f'Starting trigger')
    c.start_trigger()
    time.sleep(1)

    # take data
    run_number = cu.get_run_number(frn_name, host="cta@"+server_ip)        
    print(colored("Loop %i (delay %i ns) of %i: Run%05i" % (j+1, delay, len(delays), run_number), 'yellow'))
    run_numbers.append(run_number)

    print(colored("Acquiring data with hvsetting file: %s" % fhv, 'cyan'))

    if not ct.obs(f_obs=fobs,obs_time=1):
        print(colored("Acquiring data failed - quitting", 'red'))
        cs.disconnect_cs()
        exit()

    # stop trigger
    print(f'Stopping trigger')
    c.stop_trigger()

    ct.apply_calibration(data_dir, run_number, fped_name, with_TF=False, host = server_ip)

if not ct.ccs.hv_off():
    print("Setting HV OFF failed")



    
""" #LID control
lid_status = get_lid_status(cs)
if lid_status == 'closed':
    print("Lid is closed.")
elif lid_status == 'open':
    print("Lid is open.\nClosing lid...")
    cs.close_lid()
    time.sleep(70)
    print(get_lid_status(cs))
elif lid_status == 'opening':
    print("Lid is opening.\nWaiting 70s and then closing lid...")
    time.sleep(70)
    cs.close_lid()
elif lid_status == 'closing':
    print("Lid is closing.\nWaiting 70s...")
    time.sleep(70)
    print(get_lid_status(cs)) """

cs.disconnect_cs()


print('Copying r1 locally')
if os.path.exists('./tmp/'):
    shutil.rmtree('./tmp/')

os.mkdir('./tmp/')

for run_number in run_numbers:
    r1file = os.path.join(data_dir, "Run%05i_r1.tio" % run_number)

    subprocess.call(['scp',f'{server_ip}:{r1file}','./tmp/'])

if not os.path.exists(rdir):
    os.mkdir(rdir)

n_pixel=0
for i,run_number in enumerate(run_numbers):
    r1file_tmp = "./tmp/Run%05i_r1.tio" % run_number
    reader = TIOReader(r1file_tmp)
    wf = [ev[n_pixel] for ev in reader]
    av = np.mean(wf,axis = 0)
    
    fig,ax=plt.subplots()
    plt.title("Run %05i, delay = %.2f, pixel %d" % (run_number, delays[i], n_pixel))
    plt.plot(av)
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Amplitude')
    plt.savefig(os.path.join(rdir,"Run%05i_r1.png" % run_number))

shutil.rmtree('./tmp/')
