import os
from termcolor import colored
import yaml
from datetime import datetime



  
start_time = datetime.now()

yfile = "/home/cta/Software/DarkBox/CHECS_Script/longterm.yaml"

with open(yfile, "r") as lngfile:
  lng = yaml.load(lngfile)


n_iter = lng["longterm"]["n_longterm_times"]

print(colored(f"----- Longterm test -----\nNumber of iterations: {n_iter}", 'cyan'))

for i in range(n_iter):
    try:
        print(colored(f"Iteration n. {i}\n", 'cyan'))
        print(colored("Launching 'longterm_test.py...", 'cyan'))
        os.system('python /home/cta/Software/DarkBox/CHECS_Script/longterm_test.py')
        successfull = True
    except:
        print(colored(f"Longterm loop failed at iteration n. {i}.\nExiting...", 'red'))
        successfull = False
        exit()
#if True:
    if successfull:
        print(colored("Launching 'apply_pipeline.py'...", 'cyan'))
        os.system('python /home/cta/Software/DarkBox/CHECS_Script/apply_pipeline.py')
        print(colored(f"Iteration n. {i} ended.\nWaiting 1 minute(s) before starting next iteration...", 'cyan'))
        time.sleeptime(60)  
        
    


#TODO: add quick analysis ?



end_time = datetime.now()
print(colored("Exiting script 'run_longterm.py'", 'cyan'))
print(colored(f'Execution time of script: {format(end_time - start_time)}', 'cyan'))