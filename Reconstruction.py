from itertools import count
from PIL import Image
from Core import *
import glob
import re
import config as cfg
import params as prm
import numpy as np
from OpenGLClasses import *
from skimage import transform
import Renderer
import copy

class srImage:
    _idgen = count(0)

    def __init__(self, path, frame=None):
        self.path = path
        self.title = self.path[self.path.rfind('/')+1:]
        self.cycle = 0
        self.frame = frame
        self.framenumber = 0
        self.data = None
        self.transform = [0.0, 0.0]
        self.fulltransform = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        self.id = next(self._idgen)
        self.use = True
        self.registrationtemplate = False
        self.actbkg = None
        self.lastincycle = None

    def getData(self):
        if self.data is None:
            self.data = self.load()
        return self.data

    def getROI(self, roi):
        img = Image.open(self.path)
        return np.array(img.crop([*roi]))


    def clearData(self):
        if not self.registrationtemplate:
            self.data = None

    def load(self, full = False, primary = True):
        def transformImg(imgData, imgtransform):
            tform = transform.AffineTransform(imgtransform)
            return transform.warp(imgData, tform)

        # Use load() when the image data is needed externally, but should not be saved in RAM afterwards.
        img = Image.open(self.path)
        if self.frame:
            img.seek(self.frame)
        if full:
            imgdata = np.array(img)
        else:
            imgdata = np.array(img.crop([*prm.current_project.roi]))
        print(cfg.fltr_applied)
        # Apply filters
        if not primary:
            return imgdata
        if cfg.fltr_applied == 0:
            return imgdata
        if cfg.fltr_applied == 1:
            if self.framenumber == 0:
                return np.zeros((prm.stackwidth, prm.stackheight))
            background = prm.current_project.active_images[self.framenumber - 1]
            eff_transform = copy.deepcopy(self.fulltransform)
            eff_transform[0][2] -= background.fulltransform[0][2]
            eff_transform[1][2] -= background.fulltransform[1][2]
            tform = transform.AffineTransform(eff_transform)
            registered_background = transform.warp(background.load(full = full, primary = False), tform, preserve_range=True).astype(np.uint16)
            registered_background = np.clip(registered_background, a_min = 0, a_max = 65535)
            retimg = imgdata - registered_background + cfg.fltr_neg_offset
            if cfg.fltr_neg_selected == 0:
                retimg[retimg<0] = 0
            elif cfg.fltr_neg_selected == 1:
                retimg = np.abs(retimg)
            return retimg


    def __eq__(self, other):
        return self.id == other.id

class Project:
    def __init__(self, path):
        self.path = path
        self.active_images = list()
        self.all_images = list()
        self.n_images = 0
        self.particles = None
        self.n_particles = 0
        self.current_img = 0
        self.current_img_id = 0
        self.current_img_data = None
        self.framesselected = False
        self.registered = False
        self.pixelsize = 64.0
        self.framespercycle = 10
        self.width = 2048
        self.height = 2048
        self.roi = (0, 0, 1, 1)
        if self.path:
            self.create()

    def setCurrentImage(self, index):
        self.current_img_data = self.active_images[index].load(full = True)
        self.current_img_id = index
        self.current_img = self.active_images[index]

    def create(self):
        imgformat = self.path[self.path.rfind('.'):]
        data = Image.open(self.path)
        _frame = np.asarray(data)
        self.width, self.height = np.shape(_frame)
        self.roi = (0, 0, self.width, self.height)
        prm.stackwidth = self.width
        prm.stackheight = self.height
        frameCount = data.n_frames
        if frameCount == 1:
            directory = Path(self.path).root
            def numericalSort(value):
                numbers = re.compile(r'(\d+)')
                parts = numbers.split(value)
                parts[1::2] = map(int, parts[1::2])
                return parts
            files = sorted(glob.glob(directory+"*"+imgformat), key = numericalSort)
            for file in files:
                self.n_images += 1
                _img = srImage(file)
                _img.framenumber = self.n_images - 1
                self.active_images.append(_img)
                self.all_images.append(_img)
        else:
            for f in range(frameCount):
                self.n_images += 1
                _img = srImage(self.path, frame = f)
                _img.framenumber = self.n_images - 1
                self.active_images.append(_img)
                self.all_images.append(_img)

        self.setCurrentImage(0)
        self.genTimelineTexture()

    def update(self):
        self.n_images = len(self.active_images)
        if cfg.current_frame > (self.n_images - 1):
            cfg.current_frame = self.n_images-1
        self.genTimelineTexture()
        self.setCurrentImage(min([self.n_images - 1,self.current_img_id]))
        Renderer.BindImage(self.current_img_data)

    def setFramesPerCycle(self, len_cycle):
        self.framespercycle = len_cycle
        i = 0
        lastInCycle = None
        for i in range(self.n_images):
            if lastInCycle is None:
                self.all_images[i].actbkg = self.all_images[i]
            else:
                self.all_images[i].actbkg = lastInCycle
            if i % self.framespercycle == (self.framespercycle - 1):
                lastInCycle = self.all_images[i]
                self.all_images[i].lastincycle = True


    def setFrameState(self, state, frame = None):
        if not frame:
            if self.current_img.use == state:
                return
            else:
                self.current_img.use = state
                self.updateTimelineTexture(self.current_img_id)
        else:
            if self.active_images[frame].use == state:
                return
            else:
                self.active_images[frame].use = state
                self.updateTimelineTexture(frame)

    def genTimelineTexture(self):
        prm.timelineTexData = np.zeros((self.n_images, 1, 4))
        i = 0
        for img in self.active_images:
            if img.use:
                prm.timelineTexData[i, 0, :] = cfg.clr_fstate_use
            else:
                prm.timelineTexData[i, 0, :] = cfg.clr_fstate_discard
            i+=1
        prm.timelineTex = Texture(format = "rgba32f", interp = True)
        prm.timelineTex.update(prm.timelineTexData)

    def updateTimelineTexture(self, frame):
        newColor = cfg.clr_fstate_discard
        if self.active_images[frame].use:
            newColor = cfg.clr_fstate_use
        prm.timelineTexData[frame, 0, :] = newColor
        prm.timelineTex.setPixel((frame, 0), newColor)