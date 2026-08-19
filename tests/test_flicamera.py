"""Unit tests for the non-hardware logic in FliCamera: constructor defaults, the
window/binning setters, and the _run_blocking/_run_blocking_or_raise thread wrappers.

Hardware I/O (opening, exposing, reading out) is out of scope here.
"""

import asyncio
import threading
from unittest.mock import AsyncMock

import pytest
from pyobs.interfaces import IBinning, IWindow

from pyobs_fli import FliCamera


def test_constructor_defaults() -> None:
    camera = FliCamera()
    assert camera._temp_setpoint == -20.0
    assert camera._cooling_enabled is False
    assert camera._window == (0, 0, 0, 0)
    assert camera._binning == (1, 1)
    assert camera._driver is None


def test_constructor_threads_fli_kwargs_cooperatively() -> None:
    """Regression test for the cooperative-super()-chain fix: FliCamera(BaseCamera, FliBaseMixin,
    ...) used to call BaseCamera.__init__ and FliBaseMixin.__init__ explicitly with the same
    unfiltered kwargs -- FliBaseMixin-only kwargs like dev_path must still reach FliBaseMixin
    through the single super().__init__() call, not get lost or leak to object.__init__()."""
    from pyobs_fli.flidriver import DeviceType

    camera = FliCamera(dev_name="cam1", dev_path="/dev/fliusb0", keep_alive_ping=5)
    assert camera._dev_type == DeviceType.CAMERA
    assert camera._dev_name == "cam1"
    assert camera._dev_path == "/dev/fliusb0"
    assert camera._keep_alive_ping == 5
    assert camera._driver is None


@pytest.mark.asyncio
async def test_set_window() -> None:
    camera = FliCamera()
    camera.comm.set_state = AsyncMock()  # type: ignore[method-assign]

    await camera.set_window(10, 20, 100, 200)

    assert camera._window == (10, 20, 100, 200)
    assert camera.comm.set_state.await_args is not None
    interface, state = camera.comm.set_state.await_args.args
    assert interface is IWindow
    assert (state.x, state.y, state.width, state.height) == (10, 20, 100, 200)


@pytest.mark.asyncio
async def test_set_binning() -> None:
    camera = FliCamera()
    camera.comm.set_state = AsyncMock()  # type: ignore[method-assign]

    await camera.set_binning(2, 3)

    assert camera._binning == (2, 3)
    assert camera.comm.set_state.await_args is not None
    interface, state = camera.comm.set_state.await_args.args
    assert interface is IBinning
    assert (state.x, state.y) == (2, 3)


@pytest.mark.asyncio
async def test_run_blocking_runs_func_and_returns_true() -> None:
    ran: list[bool] = []

    def fast() -> None:
        ran.append(True)

    assert await FliCamera._run_blocking(fast) is True
    assert ran == [True]


@pytest.mark.asyncio
async def test_run_blocking_times_out() -> None:
    done = threading.Event()

    def slow() -> None:
        done.wait()

    assert await FliCamera._run_blocking(slow, timeout=0.01) is False
    done.set()
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_run_blocking_or_raise_returns_value() -> None:
    camera = FliCamera()
    assert await camera._run_blocking_or_raise(lambda: 42) == 42


@pytest.mark.asyncio
async def test_run_blocking_or_raise_reraises() -> None:
    camera = FliCamera()

    def boom() -> int:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        await camera._run_blocking_or_raise(boom)
