"""Scan on trigger delays
07/11/2022

This script performs a scan on a range of different number of photons, acquires data, applies the calibration 
(pedestal file) and reads the r1.tio files evaluating the mean waveform of a pixel over all the events.
The average waveform plot gets saved for each Run* file.

"""

from darkboxmanager_grpc import DBMClient
import numpy as np
from termcolor import colored
import time 
import os, sys
import subprocess
import matplotlib.pylab as plt
import shutil
import CHECCameraClient.camera_client as cc
import CHECCameraClient.client_utils as cu
from CHECLabPy.core.io import TIOReader
import argparse
import yaml

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

with open("longterm.yaml", "r") as lngfile:
  lng = yaml.load(lngfile)
  
  

parser = argparse.ArgumentParser(description = 'Run a dynamic range')
parser.add_argument('-d', '--directory', help = "Directory where the pedestal file is")
parser.add_argument('-ped', '--pedestal', help = "Pedestal file")

args = parser.parse_args()
run_dir = args.directory
ped_file = args.pedestal
#local_dir = '/home/cta/Software/DarkBox/CHECS_Script/'

c = DBMClient(server_ip=lng["longterm"]["dbm_ip"], port=lng["longterm"]["port"])

# Photons to scan 
#n_photons = np.array([10,100,1000])
delay_trig =lng["longterm"]["trigger_delay"]
n_photons = np.array([round(float(i),2) for i in np.logspace(0,3+1/3,11)])
times = np.geomspace(10,1,len(n_photons))
#times = np.array([1,1,1])
# Set trigger rate
c.set_trigger_rate(lng["dynamicrange"]["trigger_rate_dr"])

# Set delay
c.set_trigger_delay(delay_trig)

# Create camera instance
server_ip = lng["camera"]["server_ip"]
client_ip = lng["camera"]["client_ip"]
#server_ip = '192.168.100.95'
#client_ip = '192.168.100.100'

print(colored('Creating ControlCS object', 'yellow'))
cs = cc.ControlCS(client_ip=client_ip,server_ip=server_ip, auto_connect=True)
print(colored('Creating ClientTools object', 'yellow'))
ct = cc.ClientTools(cs)

rdir = 'Results'

#def_obs = "/home/cta/Software/CHECSInterface/trunk/config/ASTRI/observing-mpik_longterm.cfg"
#def_hv = "/home/cta/Software/CHECSInterface/trunk/config/ASTRI/hv/hv_astri_50pe100mv.cfg"
def_obs = lng["dynamicrange"]["def_obs"]
def_hv = lng["dynamicrange"]["def_hv"]
def_ready = lng["dynamicrange"]["def_ready"]
fobs = def_obs
fhv = def_hv

print(colored("Connecting to CS", 'yellow'))
if cs.get_state() != "Ready":
    print(colored("The camera is not in Ready", 'red'))
else:
    print(colored('Camera is in ready', 'green'))

if not cs.go2("ready",def_ready):
    print(colored("--> Loading ready file failed", 'red'))
    exit()



# start trigger
print(colored(f'Starting trigger', 'yellow'))
c.start_trigger()

warmup_time = lng["dynamicrange"]["warm_up"]

print(colored(f"Waiting {warmup_time} minutes for the laser to warm up...", 'yellow'))
time.sleep(warmup_time*60)
#time.sleep(60)

#LID control
lid_status = get_lid_status(cs)
if lid_status == 'closed':
    print(colored("Lid is closed.\nOpening lid and waiting while it opens...", 'yellow'))
    cs.open_lid()
    time.sleep(70)
elif lid_status == 'open':
    print(colored("Lid is already open.", 'green'))
elif lid_status == 'opening':
    print(colored("Lid is opening.\nWaiting 70s...", 'yellow'))
    time.sleep(70)
    print(get_lid_status(cs))
elif lid_status == 'closing':
    print(colored("Lid is closing.\nWaiting 70s before trying to open lid...", 'yellow'))
    time.sleep(70)
    cs.open_lid()
    print(colored('Opening lid.\n Waiting 70s...', 'yellow'))
    time.sleep(70)
    print(get_lid_status(cs))

if get_lid_status(cs) != 'open':
    print("Lid not open.\nExiting...")
    exit()

print(colored("Begin scan", 'yellow'))
data_dir, frn_name = cu.get_paths_from_config(fobs, host="cta@"+server_ip)
ped_source = os.path.join(run_dir, ped_file)
#subprocess.call(['scp',f'{'192.168.100.100'}:{ped_file}',tmp_dir])
#cu.ssh_file(ped_file, tmp_dir, 'chec1', send = True)


if not ct.ccs.hv_set_dac(fname=fhv):
    print(colored("Acquire run: Setting HV DAC failed", 'red'))
time.sleep(1)  # CS #!!

if not ct.ccs.hv_on(fname=fhv):
    print(colored("Acquire run: Setting HV ON failed", 'red'))
time.sleep(1)  # CS #!!

run_numbers = []

for j, n_ph in enumerate(n_photons):
    print(colored(f'Setting n_ph to {n_ph}', 'yellow'))
    c.set_fw_photons(n_ph)

    
    time.sleep(1)

    # take data
    run_number = cu.get_run_number(frn_name, host="cta@"+server_ip)        
    print(colored("Loop %i (n_ph %i) of %i: Run%05i" % (j+1, n_ph, len(n_photons), run_number), 'yellow'))
    run_numbers.append(run_number)

    print(colored("Acquiring data with hvsetting file: %s" % fhv, 'cyan'))

    if not ct.obs(f_obs=fobs, obs_time=times[j]):
        print(colored("Acquiring data failed - quitting", 'red'))
        cs.disconnect_cs()
        exit()

    ct.apply_calibration(data_dir, run_number, ped_source, with_TF=False, host = server_ip)
    
# stop trigger
print(colored(f'Stopping trigger', 'yellow'))
c.stop_trigger()
if not ct.ccs.hv_off():
    print(colored("Setting HV OFF failed", 'red'))

print(colored('Copying r1 locally', 'yellow'))
#tmp_dir = "/d2/DarkBox_tmp/tmp/"
tmp_dir = lng["CHEC_Local"]["tmp_dir"]
if os.path.exists(tmp_dir):
    shutil.rmtree(tmp_dir)

os.mkdir(tmp_dir)

if not os.path.exists(rdir):
    os.mkdir(rdir)

n_pixel=0
for i,run_number in enumerate(run_numbers):
    r1file = os.path.join(data_dir, "Run%05i_r1.tio" % run_number)
    subprocess.call(['scp',f'{server_ip}:{r1file}',tmp_dir])

    r1file_tmp = os.path.join(tmp_dir,"Run%05i_r1.tio" % run_number)
    reader = TIOReader(r1file_tmp)
    wf = [ev[n_pixel] for ev in reader]
    print(f"Number of events: {len(wf)}")
    av = np.mean(wf,axis = 0)
    
    fig,ax=plt.subplots()
    plt.title("Run %05i, n_ph = %.2f, pixel %d" % (run_number, n_photons[i], n_pixel))
    plt.plot(av)
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Amplitude')
    plt.savefig(os.path.join(rdir,"Run%05i_r1.png" % run_number))

    os.remove(r1file_tmp)           

shutil.rmtree(tmp_dir) 

#LID control
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
    print(get_lid_status(cs))

cs.disconnect_cs()

