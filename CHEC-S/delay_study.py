from CHECLabPy.core.io import TIOReader, waveform
import sys
import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
import commonTools
from matplotlib import gridspec
import glob
import contextlib
from PIL import Image
from contextlib import ExitStack


def plot_delays_pixel(data_dir, run_numbers, delays, n_pixel):
    """
    Plot the mean waveform on one pixel (mean over all events) for every trigger delay value (r1 file) or just a subset of values
    """
    for i, run_number in enumerate(run_numbers):
        fig,ax=plt.subplots()

        r1file = os.path.join(data_dir, "Run%05i_r1.tio" % run_number)
        reader = TIOReader(r1file)
        d = np.array(reader)
        av = np.mean(d[:,n_pixel], axis = 0)
        plt.title(f"Pixel {n_pixel}, Delay = {delays[i]} ns")
        plt.plot(av)
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [mV]')
        #ax.set_ylim(0, avmax + 20.)
        ax.set_ylim(-400., 3000.)
        plt.savefig(os.path.join(data_dir,"Run%05i_r1.png" % run_number))

    #plt.legend()
    #plt.show()

def plot_delays_pixels(data_dir, run_numbers, delays, n_pixs):
    """
    Plot the mean waveform on one pixel (mean over all events) for every trigger delay value (r1 file) or just a subset of values
    """
    for i, run_number in enumerate(run_numbers):
        fig,ax=plt.subplots()

        r1file = os.path.join(data_dir, "Run%05i_r1.tio" % run_number)
        reader = TIOReader(r1file)
        d = np.array(reader)
        for j in range(len(n_pixs)):
            av = np.mean(d[:,n_pixs[j]], axis = 0)
            plt.plot(av, label = f"Pixel {n_pixs[j]}")
        plt.title("Delay = %.2f ns" % delays[i])
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [mV]')
        ax.set_ylim(-400., 3000.)
        plt.legend(loc = "upper left")
        plt.savefig(os.path.join(data_dir,"Run%05i_r1.png" % run_number))

def plot_peaks(data_dir, file, range_arr, delay):
    r1file =  os.path.join(data_dir, file)
    reader = TIOReader(r1file)
    fig, ax = plt.subplots()
    for n_pixel in range_arr:
        wf = [ev[n_pixel] for ev in reader] #cercare modo per velocizzare questo processo. Riguardare com'è fatto il file
    
        av = np.mean(wf, axis = 0)
        #print(av)
        plt.plot(av)
    ax.set_xlabel('Time [ns]')
    ax.set_ylabel('Amplitude [mV]')
    file_name = file.strip(".tio")
    plt.title(f"Trigger delay {delay} ns ({file_name})")

    plt.show()


def createMovie(title, fp_in_dir):
    # filepaths
    fp_in = os.path.join(fp_in_dir, "Run*.png")
    #fp_in = "./TriggerDelay/d20221108/from0to1000ns_stepsize50/Run*.png"
    fp_out = os.path.join(fp_in_dir, f"{title}.gif")

    # use exit stack to automatically close opened images
    with ExitStack() as stack:

        # lazily load images
        imgs = (stack.enter_context(Image.open(f))
                for f in sorted(glob.glob(fp_in)))

        # extract  first image from iterator
        img = next(imgs)
        img.save(fp=fp_out, format='GIF', append_images=imgs,
                save_all=True, duration=200, loop=0)
    print(f"Image {fp_out} saved.")

#data_dir = "./TriggerDelay/d20221108"
data_dir = "./TriggerDelay/d20221216/"
#data_dir = "./TriggerDelay/d20221108/from0to1000ns_stepsize50"
run_numbers = np.arange(15667, 15727.1,1)
#run_numbers = np.arange(15970, 15975.1,1)
#delays = np.arange(300,340.1,5)
#run_numbers = np.arange(15646, 15666.1,1)
#run_numbers = np.arange(15562, 15583,1)
run_numbers = [15970]
delays = [300]
fp_in = data_dir
n_pixel = 0
#npixs = [0, 10, 100, 1000]
#npixs = [25, 96, 130]
npixs = [25, 577, 1278, 1812] # pixels on corners and one of one central module 
#delays = np.arange(0,1000.1,50)
#delays = np.arange(270,340.1,5)
#plot_delays_pixel(data_dir, run_numbers, delays, n_pixel)
plot_delays_pixels(data_dir, run_numbers, delays, npixs)
createMovie(f"image_{delays}_pixels{n_pixel}", fp_in)
#createMovie(f"image_{delays}_pixels{npixs}", fp_in)
#createMovie(f"image_from150to450ns_pixels{npixs}")
#File with delay 325 ns
#file = "Run15567_r1.tio"
#range_arr = range(20)
#plot_peaks(data_dir, file, range_arr, 325)



#2D pixel health check -- ideas
#0) for loop on pixels; for loop on events to get mean waveform; then I have to get the peak value which I expect
#to be at least > 800-900 DAC Counts. 
#1) CHEC-S upside down.. check
#File with delay 325 ns
"""
r1file =  os.path.join(data_dir, "Run15567_r1.tio")
reader = TIOReader(r1file)
dix = {}
peaks = []
#for n_pixel in range(reader.n_pixels):
for n_pixel in range(4):
    wf = [ev[n_pixel] for ev in reader]
    av = np.mean(wf, axis = 0)
    peak = np.max(av)
    #dix[n_pixel] = peak
    peaks.append(peak)

# NO
for j in range(0,32): #iterating over the 32 modules
    dix[j] = np.take(peaks, [j*64, (j+1)*64])
print(peaks)
p = np.reshape(peaks, (2,2))
print(p)
tmat = np.flip(commonTools.tm)"""
 


