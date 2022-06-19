#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pickle
import csv

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

        self.timestamp = self.data_manager.timestamp
        self.username  = self.data_manager.username
        self.MANAGER   = self.data_manager.MANAGER

        self.num_img = len(self.data_manager.img_tag_list)

        self.idx_img = 0
        self.is_filter_enabled = False
        self.idx_filtered_list = {}
        self.idx_filtered_dict = {}

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
        self.layout.btn_next_img.clicked.connect(self.nextImg)
        self.layout.btn_prev_img.clicked.connect(self.prevImg)
        self.layout.btn_label.clicked.connect(self.labelImg)

        return None


    def setupButtonShortcut(self):
        # w/ buttons
        self.layout.btn_next_img.setShortcut("N")
        self.layout.btn_prev_img.setShortcut("P")
        self.layout.btn_label.setShortcut("L")

        # w/o buttons
        QtGui.QShortcut(QtCore.Qt.Key_G, self, self.goEventDialog)

        return None


    ###############
    ### DIPSLAY ###
    ###############
    def dispImg(self):
        # Let idx_img bound within reasonable range....
        self.idx_img = min(max(0, self.idx_img), self.num_img - 1)

        img = self.data_manager.get_img(self.idx_img)

        # Display images...
        self.layout.viewer_img.setImage(img, levels = [0, 1])
        self.layout.viewer_img.setHistogramRange(0, 1)
        self.layout.viewer_img.getView().autoRange()

        # Display title...
        self.layout.viewer_img.getView().setTitle(f"Sequence number: {self.idx_img}/{self.num_img - 1}")

        return None


    ##################
    ### NAVIGATION ###
    ##################
    def nextImg(self):
        if self.is_filter_enabled:
            # If the current image has the filtered label???
            if self.idx_img in self.idx_filtered_dict:
                self.idx_img = self.idx_filtered_dict[self.idx_img]["next"]

            # Otherwise, find the nearest next event or revert to the initial event...
            else:
                try: idx_nearest_next = next(filter(lambda x: x > self.idx_img, self.idx_filtered_list))
                except StopIteration: idx_nearest_next = self.idx_filtered_list[0]
                self.idx_img = idx_nearest_next
        else:
            # Support rollover...
            idx_next = self.idx_img + 1
            self.idx_img = idx_next if idx_next < self.num_img else 0

        self.dispImg()

        return None


    def prevImg(self):
        idx_img_current = self.idx_img

        if self.is_filter_enabled:
            # If the current image has the filtered label???
            if self.idx_img in self.idx_filtered_dict:
                self.idx_img = self.idx_filtered_dict[self.idx_img]["prev"]

            # Otherwise, find the nearest prev event or revert to the initial event...
            else:
                try: idx_nearest_prev = next(filter(lambda x: x > self.idx_img, reversed(self.idx_filtered_list)))
                except StopIteration: idx_nearest_prev = self.idx_filtered_list[-1]
                self.idx_img = idx_nearest_prev
        else:
            # Support rollover...
            idx_prev = self.idx_img - 1
            self.idx_img = idx_prev if -1 < idx_prev else self.num_img - 1

        # Update image only when next/prev event is found???
        if idx_img_current != self.idx_img:
            self.dispImg()

        return None


    def labelCXIImg(self, label_str):
        img_tag = self.data_manager.img_tag_list[self.idx_img]

        k = (self.idx_img, img_tag)
        self.data_manager.res_dict[k] = label_str

        print(f"{self.idx_img}, {img_tag} has a label: {label_str}.")

        return None


    def labelPsanaImg(self, label_str):
        img_tag = self.data_manager.img_tag_list[self.idx_img]

        k = (self.idx_img, img_tag)
        self.data_manager.res_dict[k] = label_str

        print(f"{self.idx_img}, {img_tag} has a label: {label_str}.")

        return None


    def labelSkopiH5(self, label_str):
        img_tag = self.data_manager.img_tag_list[self.idx_img]

        k = (self.idx_img, img_tag)
        self.data_manager.res_dict[k] = label_str

        print(f"{self.idx_img}, {img_tag} has a label: {label_str}.")

        return None


    def labelImg(self):
        # Fetch label from the GUI user prompt
        label_str, is_ok = QtGui.QInputDialog.getText(self, "Enter new label", "Enter new label")

        # Process the OK event
        if is_ok and len(label_str) > 0:
            label_img_option = self.MANAGER
            label_img_dict = { 
                'cxi'     : self.labelCXIImg,
                'psana'   : self.labelPsanaImg,
                'skopih5' : self.labelSkopiH5,
            }
            label_img_dict[label_img_option](label_str)

        return None


    ################
    ### MENU BAR ###
    ################
    def saveStateDialog(self):
        path_pickle, is_ok = QtGui.QFileDialog.getSaveFileName(self, 'Save File', f'{self.timestamp}.pickle')

        if is_ok:
            obj_to_save = ( self.data_manager.img_tag_list,
                            self.data_manager.state_random,
                            self.data_manager.res_dict,
                            self.idx_img,
                            self.timestamp )

            with open(path_pickle, 'wb') as fh:
                pickle.dump(obj_to_save, fh, protocol = pickle.HIGHEST_PROTOCOL)

            print(f"State saved")

        return None


    def loadStateDialog(self):
        path_pickle = QtGui.QFileDialog.getOpenFileName(self, 'Open File')[0]

        if os.path.exists(path_pickle):
            with open(path_pickle, 'rb') as fh:
                obj_saved = pickle.load(fh)
                self.data_manager.img_tag_list  = obj_saved[0]
                self.data_manager.state_random  = obj_saved[1]
                self.data_manager.res_dict      = obj_saved[2]
                self.idx_img                    = obj_saved[3]
                self.timestamp                  = obj_saved[4]

            self.disableFilter()
            self.dispImg()

        return None


    def loadCXILabel(self, path_csv):
        # Fetch all tag-label pairs...
        img_label_dict = {}
        with open(path_csv, 'r') as fh:
            lines = csv.reader(fh)

            # Skip the header...
            next(lines)

            # Read each line...
            for line in lines:
                seqi, img_tag, label = line

                img_label_dict[img_tag] = label

        # An intermediate step to locate key in res_dict...
        img_tag_dict = {}
        for i, img_tag in enumerate(self.data_manager.img_tag_list):
            img_tag_dict[img_tag] = (i, img_tag)

        # Update labels for existing tags...
        for img_tag, label in img_label_dict.items():
            # Form the key to look up label in res_dict...
            k = img_tag_dict.get(img_tag, None)

            # Assign new label...
            if k is not None:
                self.data_manager.res_dict[k] = label

        return None


    def loadPsanaLabel(self, path_csv): pass


    def loadSkopiH5Label(self, path_csv): pass


    def loadLabelDialog(self):
        path_csv, is_ok = QtGui.QFileDialog.getOpenFileName(self, 'Load label file', f'{self.timestamp}.label.csv')

        if is_ok:
            load_option = self.MANAGER
            load_label_dict = { 
                'cxi'     : self.loadCXILabel,
                'psana'   : self.loadPsanaLabel,
                'skopih5' : self.loadSkopiH5Label,
            }
            load_label_dict[load_option](path_csv)

        return None


    def exportCXILabel(self, path_csv):
        # Write a new csv file
        with open(path_csv,'w') as fh:
            fieldnames = ["seqi", "path", "label"]
            csv_writer = csv.DictWriter(fh, fieldnames = fieldnames)

            csv_writer.writeheader()
            for (k_idx, k_fl), v in self.data_manager.res_dict.items():
                csv_writer.writerow({ "seqi" : k_idx, "path" : k_fl, "label" : v })
            print(f"{path_csv} has been updated.")

        return None


    def exportPsanaLabel(self, path_csv):
        # Write a new csv file
        with open(path_csv,'w') as fh:
            fieldnames = ["exp", "run", "event_num", "label"]
            csv_writer = csv.writer(fh)
            csv_writer.writerow(fieldnames)

            for (_, tag_img), label in self.data_manager.res_dict.items():
                exp, run, event_num = tag_img
                csv_writer.writerow([exp, run, event_num, label])
            print(f"{path_csv} has been updated.")

        return None


    def exportSkopiH5Label(self, path_csv):
        # Write a new csv file
        with open(path_csv,'w') as fh:
            fieldnames = ["path_skopih5", "idx", "label"]
            csv_writer = csv.writer(fh)
            csv_writer.writerow(fieldnames)

            for (_, tag_img), label in self.data_manager.res_dict.items():
                path_skopih5, idx_img = tag_img
                csv_writer.writerow([path_skopih5, idx_img, label])
            print(f"{path_csv} has been updated.")

        return None


    def exportLabelDialog(self):
        path_csv, is_ok = QtGui.QFileDialog.getSaveFileName(self, 'Save File', f'{self.timestamp}.label.csv')

        if is_ok:
            export_option = self.MANAGER
            export_label_dict = { 
                'cxi'     : self.exportCXILabel,
                'psana'   : self.exportPsanaLabel,
                'skopih5' : self.exportSkopiH5Label,
            }
            export_label_dict[export_option](path_csv)

        return None


    def goEventDialog(self):
        idx, is_ok = QtGui.QInputDialog.getText(self, "Enter the event number to go", "Enter the event number to go")

        if is_ok:
            self.idx_img = int(idx)

            # Bound idx within a reasonable range
            self.idx_img = min(max(0, self.idx_img), self.num_img - 1)

            self.dispImg()

        return None


    def enableFilter(self):
        label_str, is_ok = QtGui.QInputDialog.getText(self, "Enable filtering model", "What's the label to filter")

        idx_filtered_list = []
        idx_filtered_dict = {}
        if is_ok:
            # Find all indices associated to one label...
            idx_filtered_list = sorted([ int(k_idx) for (k_idx, k_fl), v in self.data_manager.res_dict.items() if v == label_str ])

            # Build up a lookup table for quickly accessing the filtered next/prev event number
            for i, v in enumerate(idx_filtered_list):
                idx_filtered_dict[v] = { "prev" : idx_filtered_list[max(0, i - 1)],
                                         "next" : idx_filtered_list[min(len(idx_filtered_list) - 1, i + 1)] }

            if idx_filtered_list:
                # Confirm availability of filtered events...
                self.is_filter_enabled = True

                # Allow rollover on both ends...
                end_left = idx_filtered_list[0]
                end_rght = idx_filtered_list[-1]
                idx_filtered_dict[end_left]["prev"] = end_rght
                idx_filtered_dict[end_rght]["next"] = end_left

                # Save the filtered record...
                self.idx_filtered_list = idx_filtered_list
                self.idx_filtered_dict = idx_filtered_dict

                # Start to display it...
                self.idx_img = idx_filtered_list[0]
                self.dispImg()
            else:
                print("Warning!!! There is no images with label '{label_str}'.".format( label_str = label_str ))

        return None


    def disableFilter(self):
        self.is_filter_enabled = False
        self.idx_filtered_dict = {}

        return None


    def createMenuBar(self):
        menuBar = self.menuBar()

        # File menu
        fileMenu = QtWidgets.QMenu("&File", self)
        menuBar.addMenu(fileMenu)

        fileMenu.addAction(self.loadAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.loadLabelAction)
        fileMenu.addAction(self.exportLabelAction)

        # Go menu
        goMenu = QtWidgets.QMenu("&Go", self)
        menuBar.addMenu(goMenu)

        goMenu.addAction(self.goAction)

        # Filter menu
        filterMenu = QtWidgets.QMenu("&Filter", self)
        menuBar.addMenu(filterMenu)

        filterMenu.addAction(self.filterEnableAction)
        filterMenu.addAction(self.filterDisableAction)

        return None


    def createAction(self):
        self.loadAction = QtWidgets.QAction(self)
        self.loadAction.setText("&Load State")

        self.saveAction = QtWidgets.QAction(self)
        self.saveAction.setText("&Save State")

        self.loadLabelAction = QtWidgets.QAction(self)
        self.loadLabelAction.setText("&Load Labels")

        self.exportLabelAction = QtWidgets.QAction(self)
        self.exportLabelAction.setText("&Export Labels")

        self.goAction = QtWidgets.QAction(self)
        self.goAction.setText("&Event")

        self.filterEnableAction = QtWidgets.QAction(self)
        self.filterEnableAction.setText("&Enable")

        self.filterDisableAction = QtWidgets.QAction(self)
        self.filterDisableAction.setText("&Disable")

        return None


    def connectAction(self):
        self.loadAction.triggered.connect(self.loadStateDialog)
        self.saveAction.triggered.connect(self.saveStateDialog)
        self.loadLabelAction.triggered.connect(self.loadLabelDialog)
        self.exportLabelAction.triggered.connect(self.exportLabelDialog)

        self.goAction.triggered.connect(self.goEventDialog)

        self.filterEnableAction.triggered.connect(self.enableFilter)
        self.filterDisableAction.triggered.connect(self.disableFilter)

        return None
