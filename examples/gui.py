#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pyqtgraph.Qt import QtGui

from hit_labeler.layout import MainLayout
from hit_labeler.window import Window
from hit_labeler.data   import DataManager

import socket


def run(config_data):
    # Main event loop
    app = QtGui.QApplication([])

    # Layout
    layout = MainLayout()

    # Data
    data_manager = DataManager(config_data)

    # Window
    win = Window(layout, data_manager)
    win.config()
    win.show()

    sys.exit(app.exec_())


class ConfigData:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for k, v in kwargs.items(): setattr(self, k, v)

config_data = ConfigData( path_csv   = "/reg/data/ana03/scratch/cwang31/amo10510/cxi_list.csv",
                          drc_root   = "/reg/data/ana03/scratch/cwang31/amo10510/",
                          username   = os.environ.get('USER'),
                          seed       = 0, )

run(config_data)
