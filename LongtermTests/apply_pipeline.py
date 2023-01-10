import os
import subprocess
import time
import shutil
from datetime import datetime
import fnmatch
from termcolor import colored
import yaml

def move_files(parent_dir, run_dir):
    if not os.path.exists(this_run_dir):
        os.mkdir(this_run_dir)
        for file in os.listdir(parent_dir):
            if fnmatch.fnmatch(file, '*.tcal') or fnmatch.fnmatch(file, '*.h5') or fnmatch.fnmatch(file, '*.mon') or fnmatch.fnmatch(file, '*.gui') or fnmatch.fnmatch(file, '*.log'):
                shutil.move(file, this_run_dir)
                print(colored('File %s moved to %s directory' % file, this_run_dir), 'green')
    else:
        print(colored('Directory %s not created.' % this_run_dir), 'red')
        
def remove_files_local(run_dir):
  for file in os.listdir(run_dir):
              if fnmatch.fnmatch(file, '*.gui') or fnmatch.fnmatch(file, '*.tio'):
                  file_rem = os.path.join(run_dir, file)
                  os.remove(file_rem)


with open("longterm.yaml", "r") as lngfile:
  lng = yaml.load(lngfile)

#Chec1 directory with data
parent_dir = lng["chec1"]["data_dir"]
#CHEC_Local directory where to store data
run_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
#tmp_dir = "/d2/DarkBox_tmp/longterm_data/"
tmp_dir = lng["CHEC_Local"]['local_data_dir']
tmp_dir_this = os.path.join(tmp_dir, 'd'+run_dir)


if os.path.exists(tmp_dir_this):
    shutil.rmtree(tmp_dir_this)

os.mkdir(tmp_dir_this)
print(colored(f'Directory {tmp_dir_this} created.\n', 'green'))
print(colored(f'Copying all files locally in directory {tmp_dir_this}', 'cyan'))

subprocess.call(['scp',f'chec1:{parent_dir}*', tmp_dir_this])


#Extract dl1 file for each r1 file in the directory 
print(colored(f'Extracting dl1 files...', 'yellow'))
for file in os.listdir(tmp_dir_this):
    file_red = os.path.join(tmp_dir_this, file)
    if fnmatch.fnmatch(file, '*r1.tio'):
        print(colored('Extracting dl1 file from %s file' % file_red, 'yellow'))
        subprocess.check_output(["python", "/home/cta/Software/CHECLabPy/CHECLabPy/scripts/extract_dl1.py", "-f",  file_red],)


print(colored("Removing *_r0, *_r1 and *_gui files...", "cyan"))
remove_files_local(tmp_dir_this)
print(colored(f"Removing files from directory {parent_dir}...", 'cyan'))
subprocess.check_output(["ssh", "chec1", "python", "/data/Temp/tidyup.py"],)
print(colored(f"Running a quick analysis on {tmp_dir_this} files...", 'cyan'))
for file in os.listdir(tmp_dir_this):
    file_red = os.path.join(tmp_dir_this, file)
    if fnmatch.fnmatch(file, '*dl1.h5'):
        print(colored('Quick analysis on %s file' % file, 'yellow'))
        subprocess.check_output(["python", "/home/cta/Software/DarkBox/CHECS_Script/quick_camera_analysis.py", "-i",  file, "-d", tmp_dir_this],)






