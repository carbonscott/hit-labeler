#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pyqtgraph.Qt import QtGui

from hit_labeler.layout import MainLayout
from hit_labeler.window import Window
from hit_labeler.data   import PsanaManager

import socket


def run(config_data):
    # Main event loop
    app = QtGui.QApplication([])

    # Layout
    layout = MainLayout()

    # Data
    data_manager = PsanaManager(config_data)

    # Window
    win = Window(layout, data_manager)
    win.config()
    win.show()

    sys.exit(app.exec_())


class ConfigData:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for k, v in kwargs.items(): setattr(self, k, v)

config_data = ConfigData( path_csv = "/reg/data/ana03/scratch/cwang31/spi/labels/2022_0518_1827_35.auto.label.csv",
                          username = os.environ.get('USER'),
                          mode     = "idx",
                          detector = "pnccdFront",
                          seed     = 0, )

run(config_data)
