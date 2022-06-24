import logging
from typing import Tuple, Any, Optional, Dict, List

from pyobs.mixins import MotionStatusMixin
from pyobs.modules import Module
from pyobs.interfaces import IFilters, IFitsHeaderBefore
from pyobs_fli.flibase import FliBaseMixin

log = logging.getLogger(__name__)


class FliFilterWheel(Module, FliBaseMixin, MotionStatusMixin, IFilters, IFitsHeaderBefore):
    """A pyobs module for FLI filter wheels."""

    __module__ = "pyobs_fli"

    def __init__(self, filter_names: List[str], **kwargs: Any):
        """Initializes a new FliFilterWheel.

        Args:
            filter_names: Names of filters.
        """
        Module.__init__(self, **kwargs)
        FliBaseMixin.__init__(**kwargs)

        # variables
        self._filter_names = filter_names

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        await FliBaseMixin.open(self)

        # check
        if self._driver is None:
            raise ValueError("No driver found.")

    async def close(self) -> None:
        """Close the module."""
        await Module.close(self)

        # not open?
        if self._driver is not None:
            # close connection
            self._driver.close()
            self._driver = None

    async def list_filters(self, **kwargs: Any) -> List[str]:
        """List available filters.

        Returns:
            List of available filters.
        """
        return self._filter_names

    async def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If an invalid filter was given.
            MoveError: If filter wheel cannot be moved.
        """

        # get filter pos and set it
        pos = self._filter_names.index(filter_name)
        self._driver.set_filter_pos(pos)

    async def get_filter(self, **kwargs: Any) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """

        # get filter pos and return filter name
        pos = self._driver.get_filter_pos()
        return self._filter_names[pos]

    async def init(self, **kwargs: Any) -> None:
        """Initialize device.

        Raises:
            InitError: If device could not be initialized.
        """
        pass

    async def park(self, **kwargs: Any) -> None:
        """Park device.

        Raises:
            ParkError: If device could not be parked.
        """
        pass

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        pass

    async def is_ready(self, **kwargs: Any) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            Whether device is ready
        """
        return True

    async def get_fits_header_before(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        pass


__all__ = ["FliFilterWheel"]
