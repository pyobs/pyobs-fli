"""Tests for the FITS header the GUI writes."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

try:
    from pyobs_fli.gui import FliTemperature, make_header
except ImportError as e:  # no Qt extras, or the camera library is not installed
    pytest.skip(f"GUI cannot be imported: {e}", allow_module_level=True)


class FakeDriver:
    name = "FLI ProLine"

    def get_temp(self, which: FliTemperature) -> float:
        return {FliTemperature.CCD: -9.5, FliTemperature.BASE: 21.0}[which]

    def get_cooler_power(self) -> float:
        return 50.0


DATE = datetime(2026, 11, 17, 10, 0, 0, tzinfo=UTC)
DATA = np.array([[1, 2], [3, 6]], dtype=np.uint16)


def test_header_has_the_module_keys() -> None:
    h = make_header(FakeDriver(), DATE, 5.0, (10, 20, 100, 100), (2, 2), DATA)  # type: ignore[arg-type]
    assert h["EXPTIME"] == 5.0 and h["DATE-OBS"] == "2026-11-17T10:00:00.000000"
    assert h["INSTRUME"] == "FLI ProLine"
    assert h["DET-TEMP"] == -9.5 and h["DET-TBAS"] == 21.0 and h["DET-COOL"] == 50.0 and "DET-TSET" not in h
    assert h["DET-BIN1"] == 2 and h["XORGSUBF"] == 20 and h["YORGSUBF"] == 40
    assert (h["DATAMIN"], h["DATAMAX"], h["DATAMEAN"]) == (1.0, 6.0, 3.0)
