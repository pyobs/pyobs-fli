# distutils: language = c++

import time
from collections import namedtuple

import numpy as np
cimport numpy as np
np.import_array()

from libfli cimport *


DeviceInfo = namedtuple('DeviceInfo', ['domain', 'filename', 'name'])

cdef class FliDriver:
    @staticmethod
    def list_devices():
        # some variables
        cdef flidomain_t domain
        cdef char filename[1024]
        cdef char name[1024]

        # create list of USB camera
        if FLICreateList(FLIDOMAIN_USB | FLIDEVICE_CAMERA) != 0:
            raise ValueError('Could not create list of FLI cameras.')

        # init list of devices
        devices = []

        # get first camera
        if FLIListFirst(&domain, <char*>filename, 1024, <char*>name, 1024) == 0:
            # store first device
            devices.append(DeviceInfo(domain=domain, filename=filename, name=name))

            # loop other devices
            while FLIListNext(&domain, <char*>filename, 1024, <char*>name, 1024) == 0:
                # store device
                devices.append(DeviceInfo(domain=domain, filename=filename, name=name))

        # clean up and return
        FLIDeleteList()
        return devices

    cdef object _device_info
    cdef flidev_t _device

    def __init__(self, device_info: DeviceInfo):
        # store
        self._device_info = device_info

    def open(self):
        # open device
        res = FLIOpen(&self._device, self._device_info.filename, self._device_info.domain)
        if res != 0:
            raise ValueError('Could not open device.')

    def close(self):
        """Close device"""
        FLIClose(self._device)

    def get_window_binning(self):
        # variables
        cdef long width, hoffset, hbin, height, voffset, vbin
        
        # get dimensions
        res = FLIGetReadoutDimensions(self._device, &width, &hoffset, &hbin, &height, &voffset, &vbin)
        if res != 0:
            raise ValueError('Could not query readout dimensions.')

        # return window and binning
        return {'left': hoffset, 'top': voffset, 'width': width, 'height': height}, {'x': hbin, 'y': vbin}

    def get_full_frame(self):
        # variables
        cdef long ul_x, ul_y, lr_x, lr_y

        # get area
        res = FLIGetVisibleArea(self._device, &ul_x, &ul_y, &lr_x, &lr_y)
        if res != 0:
            raise ValueError('Could not query visible area.')

        # return it
        return {'left':ul_x, 'top': ul_y, 'width': lr_x -  ul_x, 'height': lr_y - ul_y}

    def set_binning(self, x, y):
        # set x binning
        res = FLISetHBin(self._device, x)
        if res != 0:
            raise ValueError('Could not set x binning.')

        # set y binning
        res = FLISetVBin(self._device, y)
        if res != 0:
            raise ValueError('Could not set y binning.')

    def set_window(self, left, top, width, height):
        # set window
        res = FLISetImageArea(self._device, left, top, left + width, top + height)
        if res != 0:
            raise ValueError('Could not set window.')

    def init_exposure(self, open_shutter):
        # set TDI
        res = FLISetTDI(self._device, 0, 0)
        if res != 0:
            raise ValueError('Could not set TDI.')

        # set frame type
        res = FLISetFrameType(self._device, FLI_FRAME_TYPE_NORMAL if open_shutter else FLI_FRAME_TYPE_DARK)
        if res != 0:
            raise ValueError('Could not set frame type.')

    def set_exposure_time(self, exptime):
        # set exptime
        res = FLISetExposureTime(self._device, exptime)
        if res != 0:
            raise ValueError('Could not set exposure time.')

    def start_exposure(self):
        # expose
        res = FLIExposeFrame(self._device)
        if res != 0:
            raise ValueError('Could not start exposure.')

    def is_exposure_finished(self):
        # variables
        cdef long status, timeleft

        # get status
        res = FLIGetDeviceStatus(self._device, &status)
        if res != 0:
            raise ValueError('Could not fetch device status.')
        res = FLIGetExposureStatus(self._device, &timeleft)
        if res != 0:
            raise ValueError('Could not fetch remaining exposure time.')

        # finished?
        return (status == FLI_CAMERA_STATUS_UNKNOWN and timeleft == 0) or \
               (status != FLI_CAMERA_STATUS_UNKNOWN and status & FLI_CAMERA_DATA_READY)

    def get_ccd_temp(self):
        # variables
        cdef double temp

        # get it
        res = FLIReadTemperature(self._device, FLI_TEMPERATURE_CCD, &temp)
        if res != 0:
            raise ValueError('Could not fetch CCD temperature.')

        # return it
        return temp

    def get_cooler_power(self):
        # variables
        cdef double power

        # get it
        res = FLIGetCoolerPower(self._device, &power)
        if res != 0:
            raise ValueError('Could not fetch cooler power.')

        # return it
        return power
