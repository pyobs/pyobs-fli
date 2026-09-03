import logging
from itertools import chain
from typing import Any

import pyobs.utils.exceptions as exc
from pyobs.events import FilterChangedEvent
from pyobs.interfaces import IFilters, IFitsHeaderBefore, IReady
from pyobs.interfaces.IFilters import FiltersCapabilities, FilterState
from pyobs.interfaces.IReady import ReadyState
from pyobs.mixins import FilterHeaderMixin, MotionStatusMixin
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus

from pyobs_fli.flibase import FliBaseMixin
from pyobs_fli.flidriver import DeviceType

log = logging.getLogger(__name__)

# A physical filter move can take far longer than a typical SDK call (a long rotation
# can be several seconds), so give it its own generous, configurable deadline instead of
# the short SDK-call default.
_FILTER_MOVE_TIMEOUT = 120.0


class FliFilterWheel(FilterHeaderMixin, Module, FliBaseMixin, MotionStatusMixin, IFilters, IFitsHeaderBefore):
    """A pyobs module for FLI filter wheels."""

    __module__ = "pyobs_fli"

    def __init__(
        self,
        filter_names: list[str] | list[list[str]],
        filter_move_timeout: float = _FILTER_MOVE_TIMEOUT,
        **kwargs: Any,
    ):
        """Initializes a new FliFilterWheel.

        Args:
            filter_names: Names of filters.
            filter_move_timeout: Seconds to wait for a filter move to complete.
        """
        super().__init__(dev_type=DeviceType.FILTERWHEEL, motion_status_interfaces=["IFilters"], **kwargs)

        self._filter_names: list[list[str]] = (
            [filter_names] if isinstance(filter_names[0], str) else filter_names  # type: ignore[arg-type,list-item]
        )

        self._filter_move_timeout = filter_move_timeout
        self._current_filter = ""

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        await FliBaseMixin.open(self)
        await MotionStatusMixin.open(self)

        if self._driver is None:
            raise ValueError("No driver found.")

        driver = self._driver
        serial = await self._run_blocking_or_raise(driver.get_serial_string)
        log.info("Connected to filter wheel with serial number: %s", serial)

        await self._change_motion_status(MotionStatus.IDLE)

        if self._comm:
            await self.comm.register_event(FilterChangedEvent)

        all_filters = list(chain.from_iterable(self._filter_names))
        await self.comm.set_capabilities(IFilters, FiltersCapabilities(filters=all_filters))

        pos = await self._run_blocking_or_raise(driver.get_filter_pos)
        self._current_filter = self._resolve_filter_name(pos)
        await self.comm.set_state(IFilters, FilterState(filter=self._current_filter))
        await self.comm.set_state(IReady, ReadyState(ready=True))

    async def close(self) -> None:
        """Close the module."""
        await Module.close(self)
        await FliBaseMixin.close(self)

    def _resolve_filter_name(self, pos: int) -> str:
        div, mod = divmod(pos, 7)
        try:
            if mod == 0:
                return self._filter_names[0][0] if div == 0 else self._filter_names[1][div - 1]
            else:
                return self._filter_names[0][7 - mod]
        except IndexError:
            return ""

    async def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter."""
        if filter_name in self._filter_names[0]:
            p = self._filter_names[0].index(filter_name)
            pos = 0 if p == 0 else 7 - p
        elif filter_name in self._filter_names[1]:
            p = self._filter_names[1].index(filter_name)
            pos = 7 * (p + 1)
        else:
            raise exc.ModuleError("Filter not found")

        log.info("Setting filter to %s at position %d...", filter_name, pos)
        await self._change_motion_status(MotionStatus.SLEWING)
        driver = self._driver

        def _set() -> None:
            driver.set_filter_pos(pos)

        try:
            # A physical filter move can legitimately take far longer than a typical SDK
            # call, so bound it with a dedicated, configurable move timeout rather than the
            # short SDK-call default -- which cut off long rotations mid-move.
            await self._run_blocking_or_raise(_set, timeout=self._filter_move_timeout)

            # Confirm the wheel actually reports the requested position before declaring
            # success, so an SDK call that returned without the wheel having arrived can't
            # leave the published filter state silently wrong.
            actual = await self._run_blocking_or_raise(driver.get_filter_pos)
            if actual != pos:
                raise exc.MoveError(f"Filter wheel reported position {actual} after moving to {pos}.")
        except Exception:
            # Don't leave the wheel stuck reporting "slewing" after a failed move.
            await self._change_motion_status(MotionStatus.ERROR)
            raise

        self._current_filter = filter_name
        await self._change_motion_status(MotionStatus.POSITIONED)
        await self.comm.send_event(FilterChangedEvent(filter_name))
        await self.comm.set_state(IFilters, FilterState(filter=filter_name))

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: str | None = None, **kwargs: Any) -> None:
        pass


__all__ = ["FliFilterWheel"]
