#!/usr/bin/env python

import sys
import os
import imghdr
import labelimageb
import tensorflow
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GdkPixbuf
from enum import Enum


class Handler:
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

    def onDialogOpenButtonOkClicked(self, button):
        global canvas
        global current_directory
        path = dialog_open.get_filename()
        if path != 'None':
            path = os.path.realpath(path)
            if os.path.isfile(path):
                current_directory = os.path.dirname(path)
            else:
                current_directory = path
            image_data_list = getImageDataListOfDirectory(path)
            canvas.setImageDataList(image_data_list)
            canvas.setCurrentImageNumber(0)
            canvas.loadCurrentImage()
            canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_ORIGINAL)
            canvas.refreshImageView()
        dialog_open.hide()


    def onDialogOpenButtonCancelClicked(self, button):
        dialog_open.hide()


    def onButtonDirectoryClicked(self, button):
        global current_directory
        dialog_open.set_current_folder(current_directory)
        response = dialog_open.run()


    def onButtonPreviousClicked(self, button):
        canvas.loadPreviousImage()
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_BEST_FIT)
        canvas.refreshImageView()


    def onButtonNextClicked(self, button):
        canvas.loadNextImage()
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_BEST_FIT)
        canvas.refreshImageView()


    def onButtonRotateLeftClicked(self, button):
        canvas.rotatateCompositePixbuf(Canvas.RotationType.ROTATION_LEFT)
        canvas.refreshImageView()


    def onButtonRotateRightClicked(self, button):
        canvas.rotatateCompositePixbuf(Canvas.RotationType.ROTATION_RIGHT)
        canvas.refreshImageView()


    def onButtonFlipVerticalClicked(self, button):
        canvas.beginTensorflowAnalysis()

    def onButtonZoomOriginalClicked(self, button):
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_ORIGINAL)
        canvas.refreshImageView()


    def onButtonZoomBestFitClicked(self, button):
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_BEST_FIT)
        canvas.refreshImageView()


    def onButtonZoomInClicked(self, button):
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_IN)
        canvas.refreshImageView()


    def onButtonZoomOutClicked(self, button):
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_OUT)
        canvas.refreshImageView()


class Canvas():

    class ZoomType(Enum):
        ZOOM_ORIGINAL = 0
        ZOOM_BEST_FIT = 1
        ZOOM_IN = 2
        ZOOM_OUT = 3

    class FlipType(Enum):
        FLIP_HORIZONTAL = 0
        FLIP_VERTICAL = 1

    class RotationType(Enum):
        ROTATION_RIGHT = 0
        ROTATION_LEFT = 1


    image_data_list = []
    image_number = 0

    zoom_level = 1.0
    flip_horizontal = False
    flip_vertical = False
    rotation_level = 0


    def __init__(self, image, viewport):
        self.image = image
        self.viewport = viewport


    def setImageDataList(self, list):
        self.image_data_list = []
        self.image_number = -1
        self.image_data_list = list


    def setCurrentImageNumber(self, number):
        list_length = len(self.image_data_list)
        if list_length > 0:
            max_image_number = list_length - 1
            if number < 0:
                number = max_image_number
            elif number > max_image_number:
                number = 0
            self.image_number = number
        else:
            print("Warning: No images found in directory!")


    def loadCurrentImage(self):
        image_data = self.image_data_list[self.image_number]
        image_file = image_data[0]
        self.image_var = image_file
        print("Image File: {}".format(image_file))
        self.original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_file)
        self.composite_pixbuf = self.original_pixbuf
        zoom_level = 1.0
        rotation_level = 0
        flip_horizontal = False
        flip_vertical = False


    def loadPreviousImage(self):
        self.image_number -= 1
        self.setCurrentImageNumber(self.image_number)
        self.loadCurrentImage()


    def loadNextImage(self):
        self.image_number += 1
        self.setCurrentImageNumber(self.image_number)
        self.loadCurrentImage()


    def refreshImageView(self):
        self.image.set_from_pixbuf(self.composite_pixbuf)


    def zoomCompositePixbuf(self, zoom_type):
        if zoom_type == Canvas.ZoomType.ZOOM_ORIGINAL:
            self.zoom_level = 1.0
        elif zoom_type == Canvas.ZoomType.ZOOM_BEST_FIT:
            if self.rotation_level % 180 == 90:
                zoom_level_height = self.viewport.get_allocated_height() / self.original_pixbuf.get_width()
                zoom_level_width = self.viewport.get_allocated_width() / self.original_pixbuf.get_height()
            else:
                zoom_level_height = self.viewport.get_allocated_height() / self.original_pixbuf.get_height()
                zoom_level_width = self.viewport.get_allocated_width() / self.original_pixbuf.get_width()
            if zoom_level_height <= zoom_level_width:
                self.zoom_level = zoom_level_height
            else:
                self.zoom_level = zoom_level_width
        elif zoom_type == Canvas.ZoomType.ZOOM_IN:
            self.zoom_level *= 1.25
        elif zoom_type == Canvas.ZoomType.ZOOM_OUT:
            self.zoom_level /= 1.25
        else:
            print("Warning: Unknown Canvas.ZoomType: '", zoom_type, "'!")
        self.composite_pixbuf = self.original_pixbuf.scale_simple(
                self.original_pixbuf.get_width() * self.zoom_level,
                self.original_pixbuf.get_height() * self.zoom_level,
                GdkPixbuf.InterpType.BILINEAR)
        if self.flip_horizontal == True:
            self.composite_pixbuf = self.composite_pixbuf.flip(True)
        if self.flip_vertical == True:
            self.composite_pixbuf = self.composite_pixbuf.flip(False)
        if self.rotation_level != 0:
            self.composite_pixbuf = self.composite_pixbuf.rotate_simple(self.rotation_level)


    def flipCompositePixbuf(self, flip_type):
        if flip_type == Canvas.FlipType.FLIP_HORIZONTAL:
            self.composite_pixbuf = self.composite_pixbuf.flip(True)
            if self.flip_horizontal == True:
                self.flip_horizontal = False
            else:
                self.flip_horizontal = True
        elif flip_type == Canvas.FlipType.FLIP_VERTICAL:
            self.composite_pixbuf = self.composite_pixbuf.flip(False)
            if self.flip_vertical == True:
                self.flip_vertical = False
            else:
                self.flip_vertical = True
        else:
            print("Warning: Unknown Canvas.FlipType: '", flip_type, "'!")


    def rotatateCompositePixbuf(self, rotation_type):
        if rotation_type == Canvas.RotationType.ROTATION_LEFT:
            self.rotation_level += 90
            self.composite_pixbuf = self.composite_pixbuf.rotate_simple(90)
        elif rotation_type == Canvas.RotationType.ROTATION_RIGHT:
            self.rotation_level += 270
            self.composite_pixbuf = self.composite_pixbuf.rotate_simple(270)
        else:
            print("Warning: Unknown Canvas.RotationType: '", rotation_type, "'!")
        self.rotation_level %= 360

    def beginTensorflowAnalysis(self):
        tfoutput = labelimageb.test(self.image_var)
        labelimageb.createdialog(self, tfoutput)

builder = Gtk.Builder()
builder.add_from_file("ui-handler.glade")
builder.connect_signals(Handler())

window = builder.get_object("window")
viewer = builder.get_object("viewer")
image = builder.get_object("image")
viewport = builder.get_object("viewport")
dialog_open = builder.get_object("file_chooser_dialog")
tf_analysis = builder.get_object("tf_analysis_dialog")

canvas = Canvas(image, viewport)

current_directory = "~/"


def getImageDataListOfDirectory(path):
    image_list = []
    if os.path.exists(path):
        if os.path.isdir(path) == False:
            path = os.path.dirname(path)
        for file in os.scandir(path):
            if file.is_file():
                image_path = os.path.realpath(path) + '/' + file.name
                image_type = imghdr.what(image_path)
                if image_type in ('jpeg', 'png', 'gif'):
                    image_data = [image_path, image_type]
                    image_list.append(image_data)
    else:
        print("Warning! File or Directory '{}' does not exist!".format(directory))
    return image_list


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "./"
    if os.path.exists(path):
        path = os.path.realpath(path)
        if os.path.isfile(path):
            current_directory = os.path.dirname(path)
        else:
            current_directory = path
        image_data_list = getImageDataListOfDirectory(path)
        canvas.setImageDataList(image_data_list)
        canvas.setCurrentImageNumber(0)
        canvas.loadCurrentImage()
        canvas.zoomCompositePixbuf(Canvas.ZoomType.ZOOM_ORIGINAL)
        canvas.refreshImageView()
    else:
        print("Warning! File or Directory '{}' does not exist!".format(path))

    window.show_all()
    Gtk.main()

