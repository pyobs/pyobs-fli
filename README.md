FLI module for *pyobs*
======================

This is a [pyobs](https://www.pyobs.org) module for [FLI](http://www.flicamera.com/) cameras and filter wheels.

FLI kernel module
-----------------
The FLI kernel module needs to be installed on the system.


Install *pyobs-fli*
--------------------
Clone the repository:

    git clone https://github.com/pyobs/pyobs-fli.git
    cd pyobs-fli

Install it with [uv](https://docs.astral.sh/uv/):

    uv sync

Alternatively, with plain `venv`/`pip`:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install .


Configuration
-------------
The *FliCamera* class is derived from *BaseCamera* (see *pyobs* documentation) and adds a single new parameter:

    setpoint:
        The initial setpoint in degrees Celsius for the cooling of the camera.

The class works fine with its default parameters, so a basic module configuration would look like this:

    class: pyobs_fli.FliCamera
    name: FLI camera
    setpoint: -20.0

For cameras with an FLI filter wheel, use *FliFilterWheel*, which takes a list of filter names:

    class: pyobs_fli.FliFilterWheel
    name: FLI filter wheel
    filter_names: [Red, Green, Blue, Clear, Halpha]


Dependencies
------------
* [pyobs-core](https://github.com/pyobs/pyobs-core) for the core functionality.
* [Cython](https://cython.org/) for wrapping the FLI SDK.
* [Astropy](http://www.astropy.org/) for FITS file handling.
* [NumPy](http://www.numpy.org/) for array handling.
