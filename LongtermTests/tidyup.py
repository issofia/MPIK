import os
import shutil
from termcolor import colored


def remove_files_chec1(data_dir):
	if os.path.exists(data_dir):
		for file in os.listdir(data_dir):
			f = os.path.join(data_dir, file)
			print(colored(f'Removing file {file} from {data_dir} directory' , 'green'))
			os.remove(f)
	else:
		print(colored(f"Directory {data_dir} doesn't exist.", 'red'))



data_dir = "/data/Temp/longterm/"
remove_files_chec1(data_dir)
