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




## # This only works for very old dataset
## class CxiManager(DataManager):
## 
##     def __init__(self, config_data):
##         super().__init__()
## 
##         # Imported variables...
##         self.path_csv = getattr(config_data, 'path_csv', None)
##         self.drc_root = getattr(config_data, 'drc_root', None)
##         self.username = getattr(config_data, 'username', None)
##         self.seed     = getattr(config_data, 'seed'    , None)
## 
##         # Internal variables...
##         self.img_tag_list = []
##         self.MANAGER = 'cxi'
## 
##         set_seed(self.seed)
## 
##         self.load_cxi_handler()
## 
##         return None
## 
## 
##     def load_cxi_handler(self):
##         with open(self.path_csv, 'r') as fh: 
##             lines = csv.reader(fh)
##             next(lines)
##             for i, line in enumerate(lines):
##                 path_cxi = line[0]
##                 self.img_tag_list.append(path_cxi)
## 
##         return None
## 
## 
##     def get_img(self, idx):
##         fl_xtc   = self.img_tag_list[idx]
##         path_xtc = os.path.join(self.drc_root, fl_xtc)
##         with h5py.File(path_xtc, 'r') as fh:
##             img0 = fh.get('entry_1/data_3/data')[()]
##             img1 = fh.get('entry_1/data_4/data')[()]
## 
##         img = np.concatenate((img0, img1), axis = 0)
## 
##         # Save random state...
##         # Might not be useful for this labeler
##         if not idx in self.img_state_dict:
##             self.save_random_state()
##             self.img_state_dict[idx] = self.state_random
##         else:
##             self.state_random = self.img_state_dict[idx]
##             self.set_random_state()
## 
##         img = (img - np.mean(img)) / np.std(img)
## 
##         return img




class CxiManager(DataManager):

    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_cxi  = getattr(config_data, 'path_cxi' , None)
        self.username  = getattr(config_data, 'username' , None)
        self.seed      = getattr(config_data, 'seed'     , None)
        self.trans     = getattr(config_data, 'trans'    , None)
        self.psana_img = getattr(config_data, 'psana_img', None)

        # Internal variables...
        self.img_tag_list = []
        self.MANAGER = 'cxi'

        set_seed(self.seed)

        self.load_cxi_handler()

        return None


    def load_cxi_handler(self):
        multipanel_list = []
        with h5py.File(self.path_cxi, 'r') as fh:
            entry_list = sorted([ item for item in fh.keys() if item.startswith('entry_') ], key = lambda x: int(x.split('_')[1]))
            for entry in entry_list:
                entry_value = fh.get(entry)
                data_list = sorted([ item for item in entry_value.keys() if item.startswith('data_') ], key = lambda x: int(x.split('_')[1]))
                for data in data_list:
                    key_data = f"{entry}/{data}/data"
                    num_multipanel = fh.get(key_data).shape[0]
                    multipanel_list.extend( ( key_data, i) for i in range(num_multipanel) )

        self.img_tag_list = multipanel_list

        return None


    def get_img(self, idx):
        key_data, idx_data = self.img_tag_list[idx]

        with h5py.File(self.path_cxi, 'r') as fh:
            multipanel = fh.get(key_data)[idx_data]

        _placeholder_event_num = 0
        img = self.psana_img.get(_placeholder_event_num, multipanel)

        # Apply any possible transformation...
        if self.trans is not None: img = self.trans(img)

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
        self.path_cxi = getattr(config_data, 'path_cxi', None)
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
        with open(self.path_cxi, 'r') as fh: 
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


    def get_panels(self, idx):
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

        return imgs


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




class SkopiH5Manager(DataManager):

    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_cxi  = getattr(config_data, 'path_cxi' , None)
        self.drc_root  = getattr(config_data, 'drc_root' , None)
        self.username  = getattr(config_data, 'username' , None)
        self.panels    = getattr(config_data, 'panels'   , None)
        self.seed      = getattr(config_data, 'seed'     , None)
        self.trans     = getattr(config_data, 'trans'    , None)
        self.psana_img = getattr(config_data, 'psana_img', None)

        # Internal variables...
        self.img_tag_list = []
        self.MANAGER = 'skopih5'

        self.KEY_TO_IMG = 'photons'

        set_seed(self.seed)

        self.load_skopih5_handler()

        return None


    def load_skopih5_handler(self):
        counter = 0
        with open(self.path_cxi, 'r') as fh: 
            lines = csv.reader(fh)
            next(lines)
            for i, (basename, label, drc) in enumerate(lines):
                fl_skopih5 = f"{basename}.h5"

                path_skopih5 = os.path.join(drc, fl_skopih5)

                # Record number of image per skopi h5 file...
                num_img = 0

                # Read each h5 file...
                with h5py.File(path_skopih5, 'r') as fh:
                    img_dataset = fh.get(self.KEY_TO_IMG, None)

                    if img_dataset is not None:
                        num_img = img_dataset.shape[0]

                # Construct a tag for each image...
                img_tag_list = []
                for idx_img in range(num_img):
                    img_tag = (path_skopih5, idx_img)

                    img_tag_list.append(img_tag)

                    k = (counter, img_tag)
                    self.res_dict[k] = label

                    counter += 1

                self.img_tag_list.extend(img_tag_list)


        return None


    def get_img_by_psana(self, idx):
        path_skopih5, idx_img = self.img_tag_list[idx]

        with h5py.File(path_skopih5, 'r') as fh:
            multipanel_list = fh.get(self.KEY_TO_IMG)
            multipanel      = multipanel_list[idx_img]

        _placeholder_event_num = 0
        img = self.psana_img.get(_placeholder_event_num, multipanel)

        # Apply any possible transformation...
        if self.trans is not None: img = self.trans(img)

        return img


    def get_img(self, idx):
        img = self.get_mosaic(idx) if self.psana_img is None else self.get_img_by_psana(idx)

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
        path_skopih5, idx_img = self.img_tag_list[idx]

        with h5py.File(path_skopih5, 'r') as fh:
            img_dataset = fh.get(self.KEY_TO_IMG)
            imgs = img_dataset[idx_img]

        # Filter images...
        imgs = self.filter_panels(imgs)

        # Apply any possible transformation...
        if self.trans is not None: imgs = self.trans(imgs)

        # Form a mosaic...
        img_mosaic = self.form_mosaic(imgs)

        return img_mosaic
