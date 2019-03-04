FLI module for *pytel*
======================

FLI kernel module
-----------------
The FLI kernel module needs to be installed in the system.


Install *pytel-fli*
-------------------
Clone the repository:

    git clone https://github.com/thusser/pytel-fli.git


Install dependencies:

    cd pytel-fli
    pip3 install -r requirements
        
And install it:

    python3 setup.py install


Configuration
-------------
The *FliCamera* class is derived from *BaseCamera* (see *pytel* documentation) and adds a single new parameter:

    setpoint:
        The initial setpoint in degrees Celsius for the cooling of the camera.

The class works fine with its default parameters, so a basic module configuration would look like this:

    module:
      class: pytel_fli.FliCamera
      name: FLI camera

Dependencies
------------
* **pytel** for the core funcionality. It is not included in the *requirements.txt*, so needs to be installed 
  separately.
* [Cython](https://cython.org/) for wrapping the SBIG Universal Driver.
* [Astropy](http://www.astropy.org/) for FITS file handling.
* [NumPy](http://www.numpy.org/) for array handling.