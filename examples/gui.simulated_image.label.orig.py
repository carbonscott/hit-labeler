#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pyqtgraph.Qt import QtGui

from hit_labeler.layout import MainLayout
from hit_labeler.window import Window
from hit_labeler.data   import SkopiH5Manager
from hit_labeler.utils  import PsanaImg

import socket

## from image_preprocess import DatasetPreprocess


def run_app(config_data):
    # Main event loop
    app = QtGui.QApplication([])

    # Layout
    layout = MainLayout()

    # Data
    data_manager = SkopiH5Manager(config_data)

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


exp           = 'amo06516'
run           = '102'
mode          = 'idx'
detector_name = 'Camp.0:pnCCD.0'

psana_img = PsanaImg( exp           = exp,
                      run           = run,
                      mode          = mode,
                      detector_name = detector_name, )

config_data = ConfigData( path_csv  = "/reg/data/ana03/scratch/cwang31/spi/simulated.pnccd_panel.v2.datasets.csv",
                          username  = os.environ.get('USER'),
                          seed      = 0,
                          panels    = [0, 1, 2, 3],
                          trans     = None, 
                          psana_img = psana_img )
## config_data.psana_img = None

run_app(config_data)
