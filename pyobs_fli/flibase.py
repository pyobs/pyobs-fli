import asyncio
import logging
from typing import Any, Optional


log = logging.getLogger(__name__)


class FliBaseMixin:
    """A base class for pyobs module for FLI devices."""

    __module__ = "pyobs_fli"

    def __init__(
        self, dev_name: Optional[str] = None, dev_path: Optional[str] = None, keep_alive_ping: int = 10, **kwargs: Any
    ):
        """Initializes a new FliCamera.

        If neither dev_name nor dev_path are given, the first found device is used.

        Args:
            dev_name: Optional name for device.
            dev_path: Optional path to device.
        """
        from .flidriver import FliDriver  # type: ignore

        # variables
        self._dev_name = dev_name
        self._dev_path = dev_path
        self._keep_alive_ping = keep_alive_ping
        self._driver: Optional[FliDriver] = None
        self._device: Optional[Any] = None

        # keep alive
        self.add_background_task(self._keep_alive)

    async def open(self) -> None:
        """Open module."""
        from .flidriver import FliDriver

        # list devices
        devices = FliDriver.list_devices()
        if len(devices) == 0:
            raise ValueError("No FLI device found.")

        # open first one
        self._device = devices[0]
        log.info(
            'Opening connection to "%s" at %s...',
            self._device.name.decode("utf-8"),
            self._device.filename.decode("utf-8"),
        )
        self._driver = FliDriver(self._device)
        try:
            self._driver.open()
        except ValueError as e:
            raise ValueError("Could not open FLI camera: %s", e)

    async def close(self) -> None:
        # not open?
        if self._driver is not None:
            # close connection
            self._driver.close()
            self._driver = None

    async def _keep_alive(self) -> None:
        """Keep connection to camera alive."""
        from .flidriver import FliDriver

        while True:
            # is there a valid driver?
            if self._driver is not None:
                # then we should be able to call it
                try:
                    self._driver.get_model()
                except ValueError:
                    # no? then reopen driver
                    log.warning("Lost connection to camera, reopening it.")
                    self._driver.close()
                    self._driver = FliDriver(self._device)

            await asyncio.sleep(self._keep_alive_ping)


__all__ = ["FliBaseMixin"]