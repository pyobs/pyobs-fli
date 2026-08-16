"""Unit tests for the non-hardware logic in FliFilterWheel: filter-name normalization,
position <-> name mapping, and set_filter position computation.

Hardware I/O (moving the wheel) is mocked out.
"""

from unittest.mock import MagicMock

import pytest
from pyobs.utils import exceptions as exc

from pyobs_fli import FliFilterWheel

_TWO_WHEELS = [["A", "B", "C", "D", "E", "F", "G"], ["H", "I", "J"]]


def test_constructor_single_wheel() -> None:
    wheel = FliFilterWheel(filter_names=["A", "B", "C"])
    assert wheel._filter_names == [["A", "B", "C"]]


def test_constructor_two_wheels() -> None:
    wheel = FliFilterWheel(filter_names=_TWO_WHEELS)
    assert wheel._filter_names == _TWO_WHEELS


@pytest.mark.parametrize(
    ("pos", "expected"),
    [
        (0, "A"),
        (1, "G"),
        (6, "B"),
        (7, "H"),
        (8, "G"),
        (14, "I"),
    ],
)
def test_resolve_filter_name(pos: int, expected: str) -> None:
    wheel = FliFilterWheel(filter_names=_TWO_WHEELS)
    assert wheel._resolve_filter_name(pos) == expected


@pytest.mark.asyncio
async def test_set_filter_first_wheel() -> None:
    wheel = FliFilterWheel(filter_names=_TWO_WHEELS)
    wheel._driver = MagicMock()
    wheel._driver.set_filter_pos = MagicMock()

    async def fake_run(func, timeout: float = 5.0) -> None:
        func()

    wheel._run_blocking_or_raise = fake_run  # type: ignore[method-assign]

    await wheel.set_filter("A")
    wheel._driver.set_filter_pos.assert_called_once_with(0)
    assert wheel._current_filter == "A"


@pytest.mark.asyncio
async def test_set_filter_second_wheel() -> None:
    wheel = FliFilterWheel(filter_names=_TWO_WHEELS)
    wheel._driver = MagicMock()
    wheel._driver.set_filter_pos = MagicMock()

    async def fake_run(func, timeout: float = 5.0) -> None:
        func()

    wheel._run_blocking_or_raise = fake_run  # type: ignore[method-assign]

    await wheel.set_filter("H")
    wheel._driver.set_filter_pos.assert_called_once_with(7)
    assert wheel._current_filter == "H"


@pytest.mark.asyncio
async def test_set_filter_unknown_filter() -> None:
    wheel = FliFilterWheel(filter_names=_TWO_WHEELS)
    with pytest.raises(exc.ModuleError):
        await wheel.set_filter("nope")
