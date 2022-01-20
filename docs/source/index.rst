pyobs-fli
#########

This is a `pyobs <https://www.pyobs.org>`_ (`documentation <https://docs.pyobs.org>`_) module for FLI cameras.


Example configuration
*********************

This is an example configuration, tested on a FLI 230PL::

    class: pyobs_fli.FliCamera

    # filename pattern
    filenames: /cache/pyobs-ef01-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}00.fits

    # cooling
    setpoint: -20.0

    # additional fits headers
    fits_headers:
      'DET-PIXL': [0.015, 'Size of detector pixels (square) [mm]']
      'DET-NAME': ['E2V 230-42 Bi BBAR', 'Name of detector']
      'DET-GAIN': [1.83, 'Detector gain [e-/ADU]']
      'DET-RON': [12.1, 'Detector readout noise [e-]']
      'DET-SATU': [117767, 'Detector saturation limit [e-]']

    # opto-mechanical centre
    centre: [1115.5, 1047.5]

    # rotation (east of north)
    rotation: -2.98

    # location
    timezone: utc
    location:
      longitude: 9.944333
      latitude: 51.560583
      elevation: 201.

    # communication
    comm:
      jid: test@example.com
      password: ***

    # virtual file system
    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.HttpFile
          upload: http://localhost:37075/


Available classes
*****************

There is one single class for FLI cameras.

AsiCamera
=========
.. autoclass:: pyobs_fli.FliCamera
   :members:
   :show-inheritance:
