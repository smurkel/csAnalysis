import config as cfg
import params as prm
from pystackreg import StackReg
import numpy as np
from skimage import transform
from Core import *
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
import copy

def OnUpdate():
    if cfg.registration_running:
        IterateRegistration()

def ApplyFilter():

    filterValue = False
    if cfg.selection_selected_option == 1:
        filterValue = True
    for img in prm.current_project.active_images:
        if cfg.selection_selected_option == 2:
            if cfg.selection_filter not in img.title:
                img.use = False
        else:
            if cfg.selection_filter in img.title:
                img.use = filterValue
    prm.current_project.update()

def ApplyRange():
    if cfg.selection_selected_option_range == 2:
        for img in prm.current_project.active_images:
            img.use = False
        for i in range(max([0, cfg.selection_range[0] - 1]), min([cfg.selection_range[1], prm.current_project.n_images])):
            prm.current_project.active_images[i].use = True
    else:
        filterValue = False
        if cfg.selection_selected_option_range == 1:
            filterValue = True
        for i in range(max([0, cfg.selection_range[0] - 1]), min([cfg.selection_range[1], prm.current_project.n_images])):
                prm.current_project.active_images[i].use = filterValue
    prm.current_project.update()

def BakeSelection():
    prm.current_project.active_images = [img for img in prm.current_project.active_images if img.use]
    prm.current_project.update()

def UndoBake():
    prm.current_project.active_images = copy.copy(prm.current_project.all_images)
    prm.current_project.update()

def ClearFilters():
    for img in prm.current_project.active_images:
        img.use = True
    prm.current_project.update()

def StartRegistration():
    # generate pairs
    prm.registration_pairs = list()
    for i in range(0, prm.current_project.n_images):
        prm.current_project.active_images[i].registrationtemplate = False
        if cfg.registration_matching_selected_option == 0:
            if i == 0:
                prm.current_project.active_images[i].registrationtemplate = True
            prm.registration_pairs.append([i, 0])
        elif cfg.registration_matching_selected_option == 1:
            prm.registration_pairs.append([i, i-1])
        elif cfg.registration_matching_selected_option == 2:
            if i == cfg.registration_matching_selected_frame:
                prm.current_project.active_images[i].registrationtemplate = True
            prm.registration_pairs.append([i, cfg.registration_matching_selected_frame])
    cfg.registration_running = True
    cfg.registration_imgs_to_reg_total = len(prm.registration_pairs)
    cfg.registration_imgs_registered = 0

def IterateRegistration():
    def registerImgs(img, ref):
        sr = StackReg(StackReg.TRANSLATION)
        fulltransform = sr.register(ref, img)
        return fulltransform

    reg_pairs = list()
    lastIteration = False
    for i in range(cfg.registration_parallel_processes):
        if len(prm.registration_pairs) == 0:
            lastIteration = True
            if len(reg_pairs) == 0:
                FinishRegistration()
                return
            break
        reg_pairs.append(prm.registration_pairs[0])
        prm.registration_pairs.pop(0)


    for pair in reg_pairs:
        prm.current_project.active_images[pair[0]].getData()
        prm.current_project.active_images[pair[1]].getData()

    results = Parallel(n_jobs=cfg.registration_parallel_processes)(delayed(registerImgs)(prm.current_project.active_images[pair[0]].getData(), prm.current_project.active_images[pair[1]].getData()) for pair in reg_pairs)
    i = 0
    for result in results:
        prm.current_project.active_images[reg_pairs[i][0]].fulltransform = result
        i += 1


    for pair in reg_pairs:
        prm.current_project.active_images[pair[0]].clearData()
        prm.current_project.active_images[pair[1]].clearData()
    cfg.registration_imgs_registered += len(results)
    if lastIteration:
        FinishRegistration()

def FinishRegistration():
    # Now set each image's transform to the cumulative transform in case of registration mode 'each to previous'
    if cfg.registration_matching_selected_option == 1:
        cumulative_transform = prm.current_project.active_images[0].fulltransform
        for img in prm.current_project.active_images:
            cumulative_transform = np.matmul(img.fulltransform, cumulative_transform)
            img.fulltransform = cumulative_transform

    prm.current_project.registered = True
    prm.registered = True
    cfg.registration_running = False

def PlotMovement():
    x = list()
    y = list()
    for img in prm.current_project.active_images:
        x.append(img.fulltransform[0][2])
        y.append(img.fulltransform[1][2])
    x = np.array(x) * prm.current_project.pixelsize
    y = np.array(y) * prm.current_project.pixelsize
    frameNumber = np.array(range(0, prm.current_project.n_images))
    plt.plot(frameNumber, x, linewidth=1, marker='o', color=(0.2, 0.3, 0.8, 0.7), markeredgecolor=(0.2, 0.3, 0.8, 0.7), markerfacecolor=(0.2, 0.3, 0.8, 0.7), markersize=3, label = 'x axis')
    plt.plot(frameNumber, y, linewidth=1, marker='o', color=(0.8, 0.2, 0.3, 0.7), markeredgecolor=(0.8, 0.2, 0.3, 0.7), markerfacecolor=(0.8, 0.2, 0.3, 0.7), markersize=3, label = 'y axis')
    plt.title("Image translation vs. frame number")
    plt.xlabel("Frame number")
    plt.ylabel("Movement (nm)")
    plt.legend()
    plt.show()

def PlotMovementSpectrum():
    x = list()
    y = list()
    for img in prm.current_project.active_images:
        x.append(img.fulltransform[0][2])
        y.append(img.fulltransform[1][2])
    x = np.array(x)
    y = np.array(y)
    t = np.array(range(0, prm.current_project.n_images)) * cfg.frametime
    spectrum_x = np.abs(np.fft.fft(x))**2
    spectrum_y = np.abs(np.fft.fft(y))**2
    w = np.fft.fftfreq(x.size, cfg.frametime / 1000.0)
    idx = np.argsort(w)
    idx = idx[int(len(idx)/2):]
    plt.plot(w[idx], spectrum_x[idx], linewidth=1, color=(0.5, 0.0, 0.0), label="X")
    plt.plot(w[idx], spectrum_y[idx], linewidth=1, color=(0.0, 0.5, 0.0), label="Y")
    plt.title("Spectrum of sample movement")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Amplitude (nm)")
    plt.legend()
    plt.show()

def PlotIntensity():
    i = list()
    for img in prm.current_project.active_images:
        dx = img.fulltransform[0][2]
        dy = img.fulltransform[0][2]
        roi = [prm.current_project.roi[0] + dx, prm.current_project.roi[1] + dy, prm.current_project.roi[2] + dx, prm.current_project.roi[3] + dy]
        roi[0] = max([0, roi[0]])
        roi[1] = max([0, roi[1]])
        roi[2] = min([prm.current_project.width, roi[2]])
        roi[3] = min([prm.current_project.width, roi[3]])
        imgdata = img.getROI((roi[0], roi[1], roi[2], roi[3]))
        intensity = np.mean(imgdata)
        i.append(intensity)
    print(i)
    frameNumber = np.array(range(0, prm.current_project.n_images))
    plt.plot(frameNumber, i, linewidth = 2, color = (0.0, 0.0, 0.0, 1.0))
    plt.title("Bulk fluorescence intensity vs. frame number")
    plt.xlabel("Frame number")
    plt.ylabel("Fluorescence (a.u.)")
    plt.xlim([0, prm.current_project.n_images])
    plt.show()


def SaveRegistration(filepath):
    # Compute total translation for each image

    transforms = list()
    stack = np.zeros((prm.current_project.width, prm.current_project.height, prm.current_project.n_images))
    i = 0
    for img in prm.current_project.active_images:
        imgData = img.load()
        imgtransform = np.array(img.fulltransform)
        tform = transform.AffineTransform(imgtransform)
        regimg = transform.warp(imgData, tform, preserve_range=True)
        stack[:, :, i] = regimg
        i+=1
    Save(stack, filepath+".tif")


def SaveMovement(filepath):
    i = 0
    with open(filepath+".txt", "a") as file:
        for img in prm.current_project.active_images:
            dx = img.fulltransform[0][2]
            dy = img.fulltransform[1][2]
            file.write(f"{i}\t{dx}\t{dy}\n")
            i+=1







