import asyncio
import logging
import threading
from collections.abc import Callable
from typing import Any, TypeVar, cast

from pyobs_fli.flidriver import DeviceType

log = logging.getLogger(__name__)

_T = TypeVar("_T")

# FLI SDK calls are blocking and are made directly on the event loop thread (see _run_blocking).
# If the device has gone unresponsive, they can hang indefinitely, so they're bounded with a
# timeout rather than let a single dead device freeze the whole module.
_SDK_CALL_TIMEOUT = 5.0


class FliBaseMixin:
    """A base class for pyobs module for FLI devices."""

    __module__ = "pyobs_fli"

    def __init__(
        self,
        dev_type: DeviceType,
        dev_name: str | None = None,
        dev_path: str | None = None,
        keep_alive_ping: int = 10,
        sdk_call_timeout: float = _SDK_CALL_TIMEOUT,
        **kwargs: Any,
    ):
        """Initializes a new FLI device mixin.

        If neither dev_name nor dev_path are given, the first found device is used.

        Args:
            dev_type: Device type.
            dev_name: Optional name for device.
            dev_path: Optional path to device.
            keep_alive_ping: Interval for keep alive ping.
            sdk_call_timeout: Default timeout for blocking FLI SDK calls.
        """
        from .flidriver import FliDriver  # type: ignore

        # variables
        self._dev_type = dev_type
        self._dev_name = dev_name
        self._dev_path = dev_path
        self._keep_alive_ping = keep_alive_ping
        self._sdk_call_timeout = sdk_call_timeout
        self._driver: FliDriver | None = None
        self._device: Any | None = None

        # keep alive
        self.add_background_task(self._keep_alive)  # type: ignore[attr-defined]

        # forward anything left to the next class in the MRO -- lets a class combining this mixin
        # with Module/BaseCamera (which must run first, since add_background_task above needs it)
        # claim its own kwargs cooperatively instead of this mixin silently absorbing them
        super().__init__(**kwargs)  # type: ignore[call-arg]

    async def _run_blocking(self, func: Callable[[], None], timeout: float | None = None) -> bool:
        """Run a blocking FLI SDK call in a daemon thread, so a hung call can't freeze the module.

        A plain executor isn't used here, since its worker threads are non-daemon and Python joins
        them on interpreter shutdown -- a hung call would then just move the freeze to process exit.

        Args:
            func: Blocking callable to run off the event loop.
            timeout: Seconds to wait for completion. Defaults to sdk_call_timeout.

        Returns:
            True if func completed within timeout, False if it's still running in the background.
        """
        timeout = self._sdk_call_timeout if timeout is None else timeout
        loop = asyncio.get_running_loop()
        future: asyncio.Future[None] = loop.create_future()

        def _complete() -> None:
            # The worker thread may outlive the timeout (wait_for cancels the future on
            # timeout), so guard against a late set_result on an already-completed future --
            # otherwise the loop callback raises InvalidStateError.
            if not future.done():
                future.set_result(None)

        def _wrapper() -> None:
            try:
                func()
            finally:
                loop.call_soon_threadsafe(_complete)

        threading.Thread(target=_wrapper, daemon=True).start()
        try:
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def _run_blocking_or_raise(self, func: Callable[[], _T], timeout: float | None = None) -> _T:
        """Run a blocking FLI SDK call in a thread, returning its result or re-raising what it raised.

        Unlike _run_blocking(), this also carries the callable's return value/exception back to the
        caller -- several FLI calls drive control flow via their return value or a raised ValueError
        (e.g. device enumeration, readout), which a bare fire-and-forget thread call would otherwise
        silently lose.

        Args:
            func: Blocking callable to run off the event loop.
            timeout: Seconds to wait for completion. Defaults to sdk_call_timeout.
        """
        timeout = self._sdk_call_timeout if timeout is None else timeout
        outcome: list[Any] = []

        def _wrapper() -> None:
            try:
                outcome.append(func())
            except BaseException as e:
                outcome.append(e)

        if not await self._run_blocking(_wrapper, timeout=timeout):
            raise TimeoutError(f"Timed out waiting for FLI SDK call after {timeout}s.")
        value = outcome[0]
        if isinstance(value, BaseException):
            raise value
        return cast(_T, value)

    async def open(self) -> None:
        """Open module."""
        from .flidriver import FliDriver

        def _open() -> None:
            # list devices
            devices = FliDriver.list_devices(self._dev_type)
            if len(devices) == 0:
                raise ValueError("No FLI device found.")

            # do we have a device name or path given?
            if self._dev_name is not None or self._dev_path is not None:
                # yes, find matching device
                for dev in devices:
                    if dev.name.decode("utf-8") == self._dev_name or dev.filename.decode("utf-8") == self._dev_path:
                        self._device = dev
                        break
                else:
                    raise ValueError("No matching device found, check dev_name/dev_path.")

            else:
                # no, just pick first one
                self._device = devices[0]

            # open driver
            log.info(
                'Opening connection to "%s" at %s...',
                self._device.name.decode("utf-8"),
                self._device.filename.decode("utf-8"),
            )
            self._driver = FliDriver(self._device)
            self._driver.open()

        await self._run_blocking_or_raise(_open)

    async def close(self) -> None:
        # not open?
        if self._driver is not None:
            # close connection
            driver = self._driver
            if not await self._run_blocking(driver.close):
                log.error("Timed out closing FLI device after %.1fs.", _SDK_CALL_TIMEOUT)
            self._driver = None

    async def _keep_alive(self) -> None:
        """Keep connection to camera alive."""
        from .flidriver import FliDriver

        while True:
            # is there a valid driver?
            if self._driver is not None:
                # then we should be able to call it
                driver = self._driver
                try:
                    await self._run_blocking_or_raise(driver.get_serial_string)
                except (ValueError, OSError):
                    # no? then reopen driver
                    log.warning("Lost connection to camera, reopening it.")

                    def _reopen() -> None:
                        driver.close()
                        self._driver = FliDriver(self._device)
                        self._driver.open()

                    await self._run_blocking_or_raise(_reopen)

            await asyncio.sleep(self._keep_alive_ping)


__all__ = ["FliBaseMixin"]
