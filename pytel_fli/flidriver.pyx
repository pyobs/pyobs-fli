# distutils: language = c++

import time
import numpy as np
cimport numpy as np
np.import_array()

cimport libfli


cdef class FliDriver:
    @staticmethod
    def list_devices(self):
        # some variables
        cdef libfli.flidomain_t domain
        cdef char filename[1024]
        cdef size_t fnlen = 0
        cdef char name[1024]
        cdef size_t namelen = 0

        # create list of USB camera
        if libfli.FLICreateList(libfli.FLIDOMAIN_USB | libfli.FLIDEVICE_CAMERA) != 0:
            raise ValueError('Could not create list of FLI cameras.')

        # init list of devices
        devices = []

        # get first camera
        if libfli.FLIListFirst(&domain, <char*>filename, fnlen, <char*>name, namelen) == 0:
            print('*%s* *%s*' % (filename, name))

        # clean up and return
        libfli.FLIDeleteList()
        return devices

    def __init__(self):
        self._device = None
