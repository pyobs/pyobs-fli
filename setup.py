from distutils.core import setup, Extension
import os
import numpy
from Cython.Build import cythonize

# compile FLI library
os.system('cd lib && make')

# define extension
extensions = [
    Extension(
        'pyobs_fli.flidriver',
        ['pyobs_fli/flidriver.pyx'],
        library_dirs=['lib//'],
        libraries=['fli', 'cfitsio'],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-fPIC']
    )
]

# setup
setup(name='pyobs_fli',
      version='0.1',
      description='pyobs component for FLI cameras',
      packages=['pyobs_fli'],
      ext_modules=cythonize(extensions))
