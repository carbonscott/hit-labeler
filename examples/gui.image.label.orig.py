#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pyqtgraph.Qt import QtGui

from hit_labeler.layout import MainLayout
from hit_labeler.window import Window
from hit_labeler.data   import PsanaManager

import socket

## from image_preprocess import DatasetPreprocess


def run(config_data):
    # Main event loop
    app = QtGui.QApplication([])

    # Layout
    layout = MainLayout()

    # Data
    data_manager = PsanaManager(config_data)

    ## # Data transformation
    ## img = data_manager.get_img(0)
    ## dataset_preproc = DatasetPreprocess(img)
    ## trans = dataset_preproc.config_trans()
    ## data_manager.trans = trans

    # Window
    win = Window(layout, data_manager)
    win.config()
    win.show()

    sys.exit(app.exec_())


class ConfigData:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for k, v in kwargs.items(): setattr(self, k, v)

config_data = ConfigData( path_csv = "/reg/data/ana03/scratch/cwang31/spi/labels/2022_0603_2226_44.auto.label.csv",
                          username = os.environ.get('USER'),
                          mode     = "idx",
                          detector = "pnccdFront",
                          seed     = 0,
                          ## panels   = [0, 1, 2],
                          trans    = None, )

run(config_data)
