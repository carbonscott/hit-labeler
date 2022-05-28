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
        self.path_csv = config_data.path_csv
        self.drc_root = config_data.drc_root
        self.username = config_data.username
        self.seed     = config_data.seed

        # Internal variables...
        self.path_img_list = []

        set_seed(self.seed)

        self.load_cxi_handler()

        return None


    def load_cxi_handler(self):
        with open(self.path_csv, 'r') as fh: 
            lines = csv.reader(fh)
            next(lines)
            for i, path_cxi in enumerate(lines):
                self.path_img_list.append(path_cxi)

        return None


    def get_img(self, idx):
        fl_xtc   = self.path_img_list[idx][0]
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
        self.path_csv = config_data.path_csv
        self.mode     = config_data.mode
        self.detector = config_data.detector
        self.username = config_data.username
        self.seed     = config_data.seed

        # Internal variables...
        self.path_img_list = []

        self.psana_imgreader_dict = {}
        self.entry_list = []

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

                tag_img = (' '.join(line), )
                self.path_img_list.append(tag_img)

                k = (i, tag_img)
                label = line[-1]
                self.res_dict[k] = label

        return None


    def get_img(self, idx):
        exp, run, event_num, label = self.entry_list[idx]

        # Form a minimal basename to describe a dataset...
        basename = (exp, run)

        # Initiate image accessing layer...
        if not basename in self.psana_imgreader_dict:
            psana_imgreader = PsanaImg(exp, run, self.mode, self.detector)
            self.psana_imgreader_dict[basename] = psana_imgreader

        img = self.psana_imgreader_dict[basename].get(int(event_num), mode = 'image')

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
