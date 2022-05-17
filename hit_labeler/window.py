#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pickle
import json

from pyqtgraph    import LabelItem
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore

class Window(QtGui.QMainWindow):
    def __init__(self, layout, data_manager):
        super().__init__()

        self.createAction()
        self.createMenuBar()
        self.connectAction()

        self.layout       = layout
        self.data_manager = data_manager

        self.timestamp = self.data_manager.get_timestamp()
        self.username  = self.data_manager.username

        self.num_cxi = len(self.data_manager.path_cxi_list)

        self.idx_cxi = 0

        self.setupButtonFunction()
        self.setupButtonShortcut()

        self.dispImg()

        return None


    def config(self):
        self.setCentralWidget(self.layout.area)
        self.resize(700, 700)
        self.setWindowTitle(f"Hit labeler | Player: {self.username}")

        return None


    def setupButtonFunction(self):
        self.layout.btn_next_cxi.clicked.connect(self.nextQry)
        self.layout.btn_prev_cxi.clicked.connect(self.prevQry)
        self.layout.btn_label.clicked.connect(self.labelCXI)

        return None


    def setupButtonShortcut(self):
        # w/ buttons
        self.layout.btn_next_cxi.setShortcut("N")
        self.layout.btn_prev_cxi.setShortcut("P")
        self.layout.btn_label.setShortcut("L")

        # w/o buttons
        QtGui.QShortcut(QtCore.Qt.Key_G, self, self.goEventDialog)

        return None


    ###############
    ### DIPSLAY ###
    ###############
    def dispImg(self):
        # Let idx_cxi bound within reasonable range....
        self.idx_cxi = min(max(0, self.idx_cxi), self.num_cxi - 1)

        img_cxi = self.data_manager.get_img(self.idx_cxi)

        # Display images...
        self.layout.viewer_cxi.setImage(img_cxi, levels = [0, 1])
        self.layout.viewer_cxi.setHistogramRange(0, 1)
        self.layout.viewer_cxi.getView().autoRange()

        # Display title...
        self.layout.viewer_cxi.getView().setTitle(f"Sequence number: {self.idx_cxi + 1}/{self.num_cxi}")

        return None


    ##################
    ### NAVIGATION ###
    ##################
    def nextQry(self):
        self.idx_cxi = min(self.num_cxi - 1, self.idx_cxi + 1)    # Right bound
        self.dispImg()

        return None


    def prevQry(self):
        self.idx_cxi = max(0, self.idx_cxi - 1)    # Left bound
        self.dispImg()

        return None


    def labelCXI(self):
        # Fetch label from the GUI user prompt
        label_str, is_ok = QtGui.QInputDialog.getText(self, "Enter new label", "Enter new label")

        # Process the OK event
        if is_ok and len(label_str) > 0:
            fl_cxi = self.data_manager.path_cxi_list[self.idx_cxi][0]
            self.data_manager.res_dict[fl_cxi] = label_str

            print(f"{fl_cxi} has a label: {label_str}.")

        return None


    #################################
    ### SAVE AND RESTORE PROGRESS ###
    #################################
    def saveStateDialog(self):
        path_pickle, is_ok = QtGui.QFileDialog.getSaveFileName(self, 'Save File', f'{self.timestamp}.pickle')

        if is_ok:
            obj_to_save = ( self.data_manager.path_cxi_list,
                            self.data_manager.state_random,
                            self.data_manager.res_dict,
                            self.idx_cxi,
                            self.timestamp )

            with open(path_pickle, 'wb') as fh:
                pickle.dump(obj_to_save, fh, protocol = pickle.HIGHEST_PROTOCOL)

            print(f"State saved")

        return None


    def loadStateDialog(self):
        path_pickle = QtGui.QFileDialog.getOpenFileName(self, 'Save File')[0]

        if os.path.exists(path_pickle):
            with open(path_pickle, 'rb') as fh:
                obj_saved = pickle.load(fh)
                self.data_manager.path_cxi_list  = obj_saved[0]
                self.data_manager.state_random   = obj_saved[1]
                self.data_manager.res_dict       = obj_saved[2]
                self.idx_cxi                     = obj_saved[3]
                self.timestamp                   = obj_saved[4]

            self.dispImg()

        return None


    def exportLabelDialog(self):
        path_json, is_ok = QtGui.QFileDialog.getSaveFileName(self, 'Save File', f'{self.timestamp}.label.json')

        if is_ok:
            # Write a new json file
            with open(path_json,'w') as fh:
                json.dump(self.data_manager.res_dict, fh)
                print(f"{path_json} has been updated.")

        return None


    def goEventDialog(self):
        idx, is_ok = QtGui.QInputDialog.getText(self, "Enter the event number to go", "Enter the event number to go")

        if is_ok:
            self.idx_cxi = int(idx) - 1    # seqi to python 0-based idx

            # Bound idx within a reasonable range
            self.idx_cxi = min(max(0, self.idx_cxi), self.num_cxi - 1)

            self.dispImg()

        return None


    def createMenuBar(self):
        menuBar = self.menuBar()

        # File menu
        fileMenu = QtWidgets.QMenu("&File", self)
        menuBar.addMenu(fileMenu)

        fileMenu.addAction(self.loadAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.exportLabelAction)

        # Go menu
        goMenu = QtWidgets.QMenu("&Go", self)
        menuBar.addMenu(goMenu)

        goMenu.addAction(self.goAction)

        return None


    def createAction(self):
        self.loadAction = QtWidgets.QAction(self)
        self.loadAction.setText("&Load State")

        self.saveAction = QtWidgets.QAction(self)
        self.saveAction.setText("&Save State")

        self.exportLabelAction = QtWidgets.QAction(self)
        self.exportLabelAction.setText("&Export Labels")

        self.goAction = QtWidgets.QAction(self)
        self.goAction.setText("&Event")

        return None


    def connectAction(self):
        self.saveAction.triggered.connect(self.saveStateDialog)
        self.exportLabelAction.triggered.connect(self.exportLabelDialog)
        self.loadAction.triggered.connect(self.loadStateDialog)

        self.goAction.triggered.connect(self.goEventDialog)

        return None
