#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import h5py
import numpy as np
import random
from datetime import datetime

from hit_labeler.utils  import set_seed, PsanaImg

class DataManager:
    def __init__(self):
        super().__init__()

        # Internal variables...
        self.res_dict       = {}
        self.img_state_dict = {}

        self.timestamp = self.get_timestamp()

        self.state_random = [random.getstate(), np.random.get_state()]

        return None


    def get_timestamp(self):
        now = datetime.now()
        timestamp = now.strftime("%Y_%m%d_%H%M_%S")

        return timestamp


    def save_random_state(self):
        self.state_random = (random.getstate(), np.random.get_state())

        return None


    def set_random_state(self):
        state_random, state_numpy = self.state_random
        random.setstate(state_random)
        np.random.set_state(state_numpy)

        return None




class CxiManager(DataManager):

    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_csv = getattr(config_data, 'path_csv', None)
        self.drc_root = getattr(config_data, 'drc_root', None)
        self.username = getattr(config_data, 'username', None)
        self.seed     = getattr(config_data, 'seed'    , None)

        # Internal variables...
        self.img_tag_list = []
        self.MANAGER = 'cxi'

        set_seed(self.seed)

        self.load_cxi_handler()

        return None


    def load_cxi_handler(self):
        with open(self.path_csv, 'r') as fh: 
            lines = csv.reader(fh)
            next(lines)
            for i, path_cxi in enumerate(lines):
                self.img_tag_list.append(path_cxi)

        return None


    def get_img(self, idx):
        fl_xtc   = self.img_tag_list[idx][0]
        path_xtc = os.path.join(self.drc_root, fl_xtc)
        with h5py.File(path_xtc, 'r') as fh:
            img0 = fh.get('entry_1/data_3/data')[()]
            img1 = fh.get('entry_1/data_4/data')[()]

        img = np.concatenate((img0, img1), axis = 0)

        # Save random state...
        # Might not be useful for this labeler
        if not idx in self.img_state_dict:
            self.save_random_state()
            self.img_state_dict[idx] = self.state_random
        else:
            self.state_random = self.img_state_dict[idx]
            self.set_random_state()

        img = (img - np.mean(img)) / np.std(img)

        return img




class PsanaManager(DataManager):

    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_csv = getattr(config_data, 'path_csv', None)
        self.mode     = getattr(config_data, 'mode'    , None)
        self.detector = getattr(config_data, 'detector', None)
        self.username = getattr(config_data, 'username', None)
        self.seed     = getattr(config_data, 'seed'    , None)
        self.trans    = getattr(config_data, 'trans'   , None)
        self.panels   = getattr(config_data, 'panels'  , None)

        # Internal variables...
        self.img_tag_list = []
        self.MANAGER = 'psana'

        self.psana_imgreader_dict = {}
        self.entry_list = []

        self.psana_mode = 'calib' if self.panels else 'image'
        self.psana_read_img = {
            'image' : self.get_assemble,
            'calib' : self.get_mosaic,
        }

        set_seed(self.seed)

        self.load_imglabel_handler()

        return None


    def load_imglabel_handler(self):
        # Read csv file of datasets...
        with open(self.path_csv, 'r') as fh: 
            lines = csv.reader(fh)

            # Skip the header...
            next(lines)

            # Read each line/dataset...
            for i, line in enumerate(lines): 
                self.entry_list.append(line)

                exp, run, event_num, label = line

                tag_img = exp, int(run), int(event_num)
                self.img_tag_list.append(tag_img)

                k = (i, tag_img)
                self.res_dict[k] = label

        return None


    def form_mosaic(self, imgs, **kwargs):
        ''' Stitch images in imgs to form a single mosaic.
        ''' 
        # Get the size of each image...
        size_y, size_x = imgs[0].shape

        # Make room for stiching along y-axis...
        img_mosaic = np.zeros((size_y * len(imgs), size_x), dtype = np.float32)

        # Stiching...
        for i, img in enumerate(imgs):
            img_mosaic[i * size_y : i * size_y + size_y] = img 

        return img_mosaic


    def filter_panels(self, imgs, **kwargs):
        imgs_filtered = imgs
        if self.panels is not None:
            imgs_filtered = [ imgs[i] for i in self.panels ]

        return imgs_filtered


    def get_mosaic(self, idx):
        exp, run, event_num, label = self.entry_list[idx]

        # Form a minimal basename to describe a dataset...
        basename = (exp, run)

        # Initiate image accessing layer...
        if not basename in self.psana_imgreader_dict:
            psana_imgreader = PsanaImg(exp, run, self.mode, self.detector)
            self.psana_imgreader_dict[basename] = psana_imgreader

        imgs = self.psana_imgreader_dict[basename].get(int(event_num), mode = 'calib')

        # Filter images...
        imgs = self.filter_panels(imgs)

        # Apply any possible transformation...
        if self.trans is not None: imgs = self.trans(imgs)

        # Form a mosaic...
        img_mosaic = self.form_mosaic(imgs)

        return img_mosaic


    def get_assemble(self, idx):
        exp, run, event_num, label = self.entry_list[idx]

        # Form a minimal basename to describe a dataset...
        basename = (exp, run)

        # Initiate image accessing layer...
        if not basename in self.psana_imgreader_dict:
            psana_imgreader = PsanaImg(exp, run, self.mode, self.detector)
            self.psana_imgreader_dict[basename] = psana_imgreader

        img = self.psana_imgreader_dict[basename].get(int(event_num), mode = 'image')

        # Apply any possible transformation...
        if self.trans is not None: img = self.trans(img)

        return img


    def get_img(self, idx):
        psana_mode = self.psana_mode

        img = self.psana_read_img[psana_mode](idx)

        # Save random state...
        # Might not be useful for this labeler
        if not idx in self.img_state_dict:
            self.save_random_state()
            self.img_state_dict[idx] = self.state_random
        else:
            self.state_random = self.img_state_dict[idx]
            self.set_random_state()

        img = (img - np.mean(img)) / np.std(img)

        return img
