import asyncio
import logging
import math
from datetime import UTC, datetime
from typing import Any

import numpy as np
from pyobs.images import Image
from pyobs.interfaces import IAbortable, IBinning, ICamera, ICooling, ITemperatures, IWindow
from pyobs.interfaces.IBinning import BinningCapabilities, BinningState
from pyobs.interfaces.ICooling import CoolingState
from pyobs.interfaces.ITemperatures import SensorReading, TemperaturesState
from pyobs.interfaces.IWindow import WindowCapabilities, WindowState
from pyobs.modules.camera.basecamera import BaseCamera
from pyobs.utils.enums import ExposureStatus

from .flibase import FliBaseMixin
from .flidriver import DeviceType

log = logging.getLogger(__name__)


class FliCamera(FliBaseMixin, BaseCamera, ICamera, IWindow, IBinning, ICooling, ITemperatures, IAbortable):
    """A pyobs module for FLI cameras."""

    __module__ = "pyobs_fli"

    def __init__(self, setpoint: float = -20.0, **kwargs: Any):
        """Initializes a new FliCamera.

        Args:
            setpoint: Cooling temperature setpoint.
        """
        BaseCamera.__init__(self, **kwargs)
        FliBaseMixin.__init__(self, dev_type=DeviceType.CAMERA, **kwargs)

        self._temp_setpoint: float | None = setpoint
        self._cooling_enabled = False
        self._full_frame = (0, 0, 0, 0)
        self._window = (0, 0, 0, 0)
        self._binning = (1, 1)

        self.add_background_task(self._poll_cooling)

    async def open(self) -> None:
        """Open module."""
        await BaseCamera.open(self)
        await FliBaseMixin.open(self)

        if self._driver is None:
            raise ValueError("No driver found.")

        serial = self._driver.get_serial_string()
        log.info("Connected to camera with serial number: %s", serial)

        self._window, self._binning = self._driver.get_window_binning()
        self._full_frame = self._driver.get_full_frame()

        if self._temp_setpoint is not None:
            await self.set_cooling(True, self._temp_setpoint)

        await self.comm.set_capabilities(
            IWindow,
            WindowCapabilities(
                full_frame_x=self._full_frame[0],
                full_frame_y=self._full_frame[1],
                full_frame_width=self._full_frame[2],
                full_frame_height=self._full_frame[3],
            ),
        )
        await self.comm.set_state(
            IWindow, WindowState(x=self._window[0], y=self._window[1], width=self._window[2], height=self._window[3])
        )
        await self.comm.set_capabilities(
            IBinning,
            BinningCapabilities(
                binnings=[
                    BinningState(x=1, y=1),
                    BinningState(x=2, y=2),
                    BinningState(x=3, y=3),
                    BinningState(x=4, y=4),
                ]
            ),
        )
        await self.comm.set_state(IBinning, BinningState(x=self._binning[0], y=self._binning[1]))

    async def close(self) -> None:
        """Close the module."""
        await BaseCamera.close(self)
        await FliBaseMixin.close(self)

    async def set_window(self, left: int, top: int, width: int, height: int, **kwargs: Any) -> None:
        """Set the camera window."""
        self._window = (left, top, width, height)
        log.info("Setting window to %dx%d at %d,%d...", width, height, left, top)
        await self.comm.set_state(IWindow, WindowState(x=left, y=top, width=width, height=height))

    async def set_binning(self, x: int, y: int, **kwargs: Any) -> None:
        """Set the camera binning."""
        self._binning = (x, y)
        log.info("Setting binning to %dx%d...", x, y)
        await self.comm.set_state(IBinning, BinningState(x=x, y=y))

    async def _expose(self, exposure_time: float, open_shutter: bool, abort_event: asyncio.Event) -> Image:
        from .flidriver import FliTemperature

        if self._driver is None:
            raise ValueError("No camera driver.")

        log.info("Set binning to %dx%d.", self._binning[0], self._binning[1])
        self._driver.set_binning(*self._binning)

        width = int(math.floor(self._window[2]) / self._binning[0])
        height = int(math.floor(self._window[3]) / self._binning[1])
        log.info(
            "Set window to %dx%d (binned %dx%d) at %d,%d.",
            self._window[2],
            self._window[3],
            width,
            height,
            self._window[0],
            self._window[1],
        )
        self._driver.set_window(self._window[0], self._window[1], width, height)

        self._driver.init_exposure(open_shutter)
        self._driver.set_exposure_time(int(exposure_time * 1000.0))

        log.info(
            "Starting exposure with %s shutter for %.2f seconds...", "open" if open_shutter else "closed", exposure_time
        )
        date_obs = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")

        self._driver.start_exposure()
        await self._wait_exposure(abort_event, exposure_time, open_shutter)

        log.info("Exposure finished, reading out...")
        await self._change_exposure_status(ExposureStatus.READOUT)
        width = int(math.floor(self._window[2] / self._binning[0]))
        height = int(math.floor(self._window[3] / self._binning[1]))
        img = np.zeros((height, width), dtype=np.uint16)
        for row in range(height):
            img[row, :] = self._driver.grab_row(width)

        image = Image(img)  # type: ignore[arg-type]
        image.header["DATE-OBS"] = (date_obs, "Date and time of start of exposure")
        image.header["EXPTIME"] = (exposure_time, "Exposure time [s]")
        image.header["DET-TEMP"] = (self._driver.get_temp(FliTemperature.CCD), "CCD temperature [C]")
        image.header["DET-COOL"] = (self._driver.get_cooler_power(), "Cooler power [percent]")
        image.header["DET-TSET"] = (self._temp_setpoint, "Cooler setpoint [C]")
        image.header["INSTRUME"] = (self._driver.name, "Name of instrument")
        image.header["XBINNING"] = image.header["DET-BIN1"] = (self._binning[0], "Binning factor used on X axis")
        image.header["YBINNING"] = image.header["DET-BIN2"] = (self._binning[1], "Binning factor used on Y axis")
        image.header["XORGSUBF"] = (self._window[0], "Subframe origin on X axis")
        image.header["YORGSUBF"] = (self._window[1], "Subframe origin on Y axis")
        image.header["DATAMIN"] = (float(np.min(img)), "Minimum data value")
        image.header["DATAMAX"] = (float(np.max(img)), "Maximum data value")
        image.header["DATAMEAN"] = (float(np.mean(img)), "Mean data value")

        self.set_biassec_trimsec(image.header, *self._driver.get_visible_frame())

        log.info("Readout finished.")
        return image

    async def _wait_exposure(self, abort_event: asyncio.Event, exposure_time: float, open_shutter: bool) -> None:
        while True:
            if abort_event.is_set():
                await self._change_exposure_status(ExposureStatus.IDLE)
                raise InterruptedError("Aborted exposure.")
            if self._driver.is_exposing():
                break
            await asyncio.sleep(0.01)

    async def _abort_exposure(self) -> None:
        if self._driver is None:
            raise ValueError("No camera driver.")
        self._driver.cancel_exposure()

    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        """Enables/disables cooling and sets setpoint."""
        if self._driver is None:
            raise ValueError("No camera driver.")

        if enabled:
            log.info("Enabling cooling with a setpoint of %.2f°C...", setpoint)
        else:
            log.info("Disabling cooling and setting setpoint to 20°C...")

        self._temp_setpoint = setpoint if enabled else None
        self._cooling_enabled = enabled
        self._driver.set_temperature(float(setpoint) if setpoint is not None else 20.0)
        await self.comm.set_state(
            ICooling, CoolingState(setpoint=setpoint if setpoint is not None else 20.0, power=None, enabled=enabled)
        )

    async def _poll_cooling(self) -> None:
        """Background task: periodically reads cooling and temperature state."""
        from .flidriver import FliTemperature

        while True:
            try:
                if self._driver is not None:
                    t_ccd = self._driver.get_temp(FliTemperature.CCD)
                    t_base = self._driver.get_temp(FliTemperature.BASE)
                    power = self._driver.get_cooler_power()
                    setpoint = self._temp_setpoint if self._temp_setpoint is not None else 20.0
                    await self.comm.set_state(
                        ICooling, CoolingState(setpoint=setpoint, power=round(power), enabled=self._cooling_enabled)
                    )
                    await self.comm.set_state(
                        ITemperatures,
                        TemperaturesState(
                            readings=[
                                SensorReading(name="CCD", value=t_ccd),
                                SensorReading(name="Base", value=t_base),
                            ]
                        ),
                    )
            except Exception:
                pass
            await asyncio.sleep(10)


__all__ = ["FliCamera"]
