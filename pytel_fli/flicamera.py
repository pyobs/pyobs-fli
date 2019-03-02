import logging
import math
import threading
from datetime import datetime
import time
import numpy as np
from astropy.io import fits

from pytel.interfaces import ICamera, ICameraWindow, ICameraBinning, ICooling
from pytel.modules.camera.basecamera import BaseCamera, CameraException
from .flidriver import FliDriver


log = logging.getLogger(__name__)


class FliCamera(BaseCamera, ICamera, ICameraWindow, ICameraBinning, ICooling):
    pass
