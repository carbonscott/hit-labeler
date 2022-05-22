#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import h5py
import numpy as np
import random
from datetime import datetime

from hit_labeler.utils  import set_seed

class DataManager:
    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_csv = config_data.path_csv
        self.drc_root = config_data.drc_root
        self.username = config_data.username
        self.seed     = config_data.seed

        # Internal variables...
        self.path_cxi_list = []
        self.img_state_dict = {}
        self.res_dict = {}

        self.timestamp = self.get_timestamp()

        set_seed(self.seed)

        self.load_cxi_handler()

        self.state_random = [random.getstate(), np.random.get_state()]

        return None


    def get_timestamp(self):
        now = datetime.now()
        timestamp = now.strftime("%Y_%m%d_%H%M_%S")

        return timestamp


    def load_cxi_handler(self):
        with open(self.path_csv, 'r') as fh: 
            lines = csv.reader(fh)
            next(lines)
            for i, path_cxi in enumerate(lines):
                self.path_cxi_list.append(path_cxi)

        return None


    def get_img(self, idx):
        fl_xtc   = self.path_cxi_list[idx][0]
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


    def save_random_state(self):
        self.state_random = (random.getstate(), np.random.get_state())

        return None


    def set_random_state(self):
        state_random, state_numpy = self.state_random
        random.setstate(state_random)
        np.random.set_state(state_numpy)

        return None
