"""Smoke tests: import the drivers and instantiate them without hardware, asserting
the interfaces they claim.

The Cython extension (flidriver) is compiled from the vendored libfli C source during
install, but device enumeration/opening only happens inside open(), so instantiation
is safe with no FLI hardware attached.
"""

from pyobs.interfaces import IAbortable, IBinning, ICamera, ICooling, IFilters, ITemperatures, IWindow
from pyobs.modules import Module

from pyobs_fli import FliCamera, FliFilterWheel


def test_instantiate_camera() -> None:
    camera = FliCamera()
    assert isinstance(camera, Module)
    assert isinstance(camera, ICamera)
    assert isinstance(camera, IWindow)
    assert isinstance(camera, IBinning)
    assert isinstance(camera, ICooling)
    assert isinstance(camera, ITemperatures)
    assert isinstance(camera, IAbortable)


def test_instantiate_filter_wheel() -> None:
    wheel = FliFilterWheel(filter_names=["A", "B", "C"])
    assert isinstance(wheel, Module)
    assert isinstance(wheel, IFilters)
