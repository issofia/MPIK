import os
import subprocess
import time 
from datetime import datetime
from darkboxmanager_grpc import DBMClient
from termcolor import colored 
import CHECCameraClient.camera_client as cc
import CHECCameraClient.client_utils as cu
import yaml


def send_subpr(cmmd, sub_args = []):
    out = subprocess.check_output(
            ["bash","bash_scripts/run_bash.sh", cmmd, sub_args],
        )
    return out


def bootup(cmmd):
    out = subprocess.check_output(
            ["bash","bash_scripts/run_bash.sh", cmmd],
        )
    return out

def bootup_loop(n_times):
    for i in range(n_times):
        try:
            print(colored(f"Waiting for {sleeptime} seconds before turning camera ON", 'yellow'))
            time.sleep(sleeptime)
            print(colored(f"Trying to turn ON camera --- Iteration n. {i}", 'yellow'))
            out_on = bootup('on')
            print(colored(f"Waiting for {sleeptime} seconds before turning camera OFF", 'yellow'))
            time.sleep(sleeptime)
            print(colored(f"Trying to turn OFF camera --- Iteration n. {i}", 'yellow'))

            out_off = bootup('off')

            successful = True
        except:
            successful = False
            print(colored("Something went wrong.", 'red'))
    return successful


def get_last_r0_file(data_dir):
    out = subprocess.check_output(['ssh', 'chec1', 'ls', data_dir])
    
    r0_name = str(out[-16:]).strip("b'\\n")
    if r0_name.startswith('Run') and r0_name.endswith('_r0.tio'):
        return os.path.join(data_dir, r0_name)
    else:
        print(colored("Couldn't find the r0 file.", 'red')) #think something better

def get_last_ped_tcal(data_dir):
    out = subprocess.check_output(['ssh', 'chec1', 'ls', data_dir])
    a = str(out[-50:])
    if '_ped.tcal' in a:
        b = a.find('_ped.tcal')
        c = []
        for i in range(-5,0):
            c.append(a[b+i])
        ped_file = 'Run'+''.join(c)+'_ped.tcal'
        return os.path.join(data_dir,ped_file)
    else:
        print(colored("Couldn't find a recent .tcal file.\nExiting...", 'red'))
        exit()


def pedestal_run(client_DBM, trigger_rate, delay_trig):
    #turn on trigger
    client_DBM.set_trigger_rate(trigger_rate) 
    client_DBM.set_trigger_delay(delay_trig+200)#for pedestal run
    print(colored(f"Starting trigger, rate {trigger_rate}, delay {delay_trig + 200}", 'cyan'))
    client_DBM.start_trigger()
    time.sleep(1)
    try:
        subprocess.check_output(
            ["bash","bash_scripts/run_bash.sh", 'ped'],
        )
        print(colored(f"Stopping trigger", 'cyan'))
        client_DBM.stop_trigger()
        successful = True
    except:
        print(colored("Something went wrong in running a pedestal measurement.", 'red'))
        successful = False

    return successful


with open("longterm.yaml", "r") as lngfile:
  lng = yaml.load(lngfile)

n_times = lng["longterm"]["n_times"]
sleeptime = lng["longterm"]["sleeptime"]
delay_trig = lng["longterm"]["trigger_delay"]
trigger_rate_ped = 500
warmup_time = lng["dynamicrange"]["warm_up"]
#Data directory
data_dir = lng["chec1"]["data_dir"]

#parent_dir = '/data/Temp/'
#run_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
#this_run_dir =  os.path.join(parent_dir, run_dir)
#subprocess.call(['ssh', 'chec1', 'mkdir',this_run_dir])


#Camera 
server_ip = lng["camera"]["server_ip"]
client_ip = lng["camera"]["client_ip"]
dbm_ip = lng["longterm"]["dbm_ip"]
start_time = datetime.now()

print(colored(f"Creating DBM client with IP {dbm_ip}", "yellow"))
client_DBM =DBMClient(dbm_ip)
#c.power_on_camera_plug()


if not bootup_loop(n_times):
    print(colored("Something went wrong in booting up the camera.\nExiting...", 'red'))
    exit()
else:
#if True: 
    print(colored("Bootup loop completed.\nWaiting 15 s...", 'green'))
    time.sleep(15)  
    print(colored("Turning camera ON for data taking...", 'yellow'))
    try: 
        out_on = bootup('on')
        try:
            pedestal_run(client_DBM, trigger_rate_ped, delay_trig)
            print(colored("Getting the last r0 file",'yellow'))
            r0_ped = get_last_r0_file(data_dir)
            print(colored(f"Last file found: {r0_ped}", 'cyan'))
            print(colored("Generating pedestal...", 'yellow'))
            
            try:
                subprocess.check_output(
                    ["bash","bash_scripts/run_bash.sh", 'gen_ped', r0_ped],
                )
                ped_file = get_last_ped_tcal(data_dir)
                print(colored(f'Pedestal generated: {ped_file}', 'green'))
                try:
                    #Connect and disconnect Control CS 
                    subprocess.check_output(
                                ["bash","bash_scripts/run_bash.sh", 'condis'],
                    )
                    print(colored(f"Running a dynamic range scan.\nWaiting {warmup_time} minutes for the laser to warm up...", 'yellow'))
                    subprocess.check_output(["python", "/home/cta/Software/DarkBox/CHECS_Script/dynamicrange.py", "-d", data_dir, "-ped", ped_file])
                except:
                    print(colored("Couldn't run a dynamic range scan.", 'red'))
            except:
                print(colored("Couldn't generate pedestal", 'red'))
            
        except:
            successful = False
            print(colored("Couldn't take pedestal run.", 'red'))
        
    except:
        successful = False
        print(colored("Something went wrong in turning ON camera.\nTrying to turn OFF...", 'red'))


print(colored("Turning OFF camera...", 'yellow'))
out_off = bootup('off')

end_time = datetime.now()
print(colored("Exiting script.", 'cyan'))
print(colored(f'Execution time: {format(end_time - start_time)}', 'cyan'))

#c.power_off_camera_plug()