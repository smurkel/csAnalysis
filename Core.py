from PIL import Image
import numpy as np
import time
from datetime import datetime
import glob
import os

CS_LOG_INFO = True
CS_LOG_WARNING = True
CS_LOG_ERROR = True

tictocTime = 0.0

def CS_INFO(message):
    if CS_LOG_INFO:
        print('\033[94m' + message)


def CS_WARNING(message):
    if CS_LOG_WARNING:
        print('\033[93m' + message)


def CS_ERROR(message):
    if CS_LOG_ERROR:
        raise Exception(message)

def tic():
    global tictocTime
    tictocTime = time.time()


def toc():
    global tictocTime
    timeElapsed = (time.time() - tictocTime) * 1000.0
    return timeElapsed


def timestamp():
    now = datetime.now()
    timestamp = now.strftime("%H%M%S")
    return timestamp


def datestamp():
    now = datetime.now()
    datestamp = now.strftime("%Y%m%d")
    return datestamp



class Path:
    def __init__(self, path):
        path = path.replace("\\", "/")
        self.path = path
        mark = self.path.rfind("/")
        self.root = self.path[:mark + 1]
        mark = self.path.rfind("/")
        mark2 = self.path.rfind(".")
        self.title = self.path[mark + 1:mark2]
        self.name = self.title
        mark = self.path.rfind(".")
        self.type = self.path[mark:]

    def __str__(self):
        return self.path


def Load(path):
    if isinstance(path, Path):
        path = path.path
    """Default expected expected is .tiff. So Load() defaults to LoadTiff() or LoadFolder()"""
    if (path[-4:] == ".tif") or (path[-5:] == ".tiff"):
        return LoadTiff(path)
    elif path[-1:] == "/":
        return LoadFolder(path)
    else:
        CS_ERROR("Invalid file path")


def LoadTiff(path):
    if isinstance(path, Path):
        path = path.path
    CS_INFO("Loading: "+path)
    _data = Image.open(path)
    _frame = np.asarray(_data)

    width = _frame.shape[0]
    height = _frame.shape[1]
    depth = _data.n_frames
    data = np.zeros((width, height, depth), dtype=np.float32)
    for f in range(0, depth):
        _data.seek(f)
        data[:, :, f] = np.asarray(_data)

    data = np.squeeze(data)
    return data

def LoadFolder(path):
    paths = glob.glob(path+"*.tiff") + glob.glob(path+"*.tif")
    _data = Image.open(paths[0])
    _frame = np.asarray(_data)

    width = _frame.shape[0]
    height = _frame.shape[1]
    depth = len(paths)
    data = np.zeros((width, height, depth), dtype=np.float32)
    for f in range(0, len(paths)):
        CS_INFO("Loading "+paths[f])
        _data = Image.open(paths[f])
        data[:, :, f] = np.asarray(_data)
    return data

def Save(imgArray, path):
    """Default filetype is .tiff. Other functions to be added later, maybe, would be e.g. SavePng"""
    return SaveTiff(imgArray, path)

def SaveTiff(array, path):
    CS_INFO("Saving: "+path)
    if not (path[-5:] == ".tiff" or path[-4:] == ".tif"):
        path += ".tiff"
    root = path.rfind("/")
    root = path[:root]
    if not os.path.exists(root):
        os.makedirs(root)
    img_list = []
    if isinstance(array, list):
        if len(array)==1:
            img = Image.fromarray(array[0].astype(np.int16))
            img.save(path)
        else:
            for img in array:
                img_list.append(Image.fromarray(img))

    elif isinstance(array, type(np.zeros((1,1,1)))):
        for f in range(0, np.shape(array)[2]):
            img_list.append(Image.fromarray(array[:, :, f]))
        img_list[0].save(path, compression=None, save_all=True, append_images=img_list[1:])
    else:
        raise RuntimeError("data to save is not a python list or numpy array")
    img_list[0].save(path, compression=None, save_all=True, append_images=img_list[1:])