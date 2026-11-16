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
async def test_full_reset_restores_cooling() -> None:
    camera = FliCamera(setpoint=-15.0)
    camera.reset = AsyncMock()  # type: ignore[method-assign]
    camera.set_cooling = AsyncMock()  # type: ignore[method-assign]

    await camera.full_reset()

    camera.reset.assert_awaited_once()
    camera.set_cooling.assert_awaited_once_with(True, -15.0)


@pytest.mark.asyncio
async def test_full_reset_skips_cooling_when_no_setpoint() -> None:
    camera = FliCamera(setpoint=-15.0)
    camera._temp_setpoint = None
    camera.reset = AsyncMock()  # type: ignore[method-assign]
    camera.set_cooling = AsyncMock()  # type: ignore[method-assign]

    await camera.full_reset()

    camera.reset.assert_awaited_once()
    camera.set_cooling.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_blocking_runs_func_and_returns_true() -> None:
    ran: list[bool] = []

    def fast() -> None:
        ran.append(True)

    assert await FliCamera()._run_blocking(fast) is True
    assert ran == [True]


@pytest.mark.asyncio
async def test_run_blocking_times_out() -> None:
    done = threading.Event()

    def slow() -> None:
        done.wait()

    assert await FliCamera()._run_blocking(slow, timeout=0.01) is False
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


def make_cooling_camera(sensor: float = 5.0) -> FliCamera:
    """Camera with a fake driver whose sensor follows the setpoint."""
    from unittest.mock import MagicMock

    camera = FliCamera()
    camera.comm.set_state = AsyncMock()  # type: ignore[method-assign]
    state = {"temp": sensor}

    def set_temperature(value: float) -> None:
        state["temp"] = value + 0.5

    driver = MagicMock()
    driver.set_temperature.side_effect = set_temperature
    driver.get_temp.side_effect = lambda channel: state["temp"]
    driver.get_cooler_power.return_value = 30.0
    camera._driver = driver
    return camera


@pytest.mark.asyncio
async def test_set_cooling_queues_ramp_and_keeps_configured_setpoint() -> None:
    camera = make_cooling_camera()

    await camera.set_cooling(False, 0.0)

    assert camera.cooling_ramping
    assert camera._temp_setpoint == -20.0  # configured default survives, so full_reset() can cool again


@pytest.mark.asyncio
async def test_ramp_starts_at_sensor_temperature_and_steps_down() -> None:
    camera = make_cooling_camera(sensor=5.0)
    await camera.set_cooling(True, 2.0)

    while camera.cooling_ramping:
        await camera._cooling_tick()

    values = [c.args[0] for c in camera._driver.set_temperature.call_args_list]  # type: ignore[union-attr]
    assert values == [5.0, 4.0, 3.0, 2.0]
    assert camera._cooling_enabled is True


@pytest.mark.asyncio
async def test_disable_after_cooling_warms_up_then_sets_20() -> None:
    camera = make_cooling_camera(sensor=5.0)
    await camera.set_cooling(True, 3.0)
    while camera.cooling_ramping:
        await camera._cooling_tick()
    camera._driver.set_temperature.reset_mock()  # type: ignore[union-attr]

    await camera.set_cooling(False, 0.0)
    for _ in range(100):
        if not camera.cooling_ramping:
            break
        await camera._cooling_tick()

    values = [c.args[0] for c in camera._driver.set_temperature.call_args_list]  # type: ignore[union-attr]
    assert values[0] == 4.0  # raised step by step first
    assert values[-1] == 20.0
    assert camera._cooling_enabled is False
    assert camera._temp_setpoint == -20.0
