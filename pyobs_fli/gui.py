"""Standalone PySide6 GUI driving FliDriver directly, for testing a FLI camera without a full
pyobs module.

Unverified against real FLI hardware.
"""

import asyncio
import sys
import time

import numpy as np
import qasync  # type: ignore[import-untyped]
from astropy.io import fits
from pyobs.utils.enums import ImageFormat
from pyobs.utils.gui.camera import (
    BinningWidget,
    DataDisplayWidget,
    ExposeWidget,
    ExposureTimeWidget,
    ImageFormatWidget,
    ListPickerDialog,
)
from pyobs.utils.gui.camera.windowingwidget import WindowingWidget
from PySide6 import QtCore, QtWidgets  # type: ignore[import-untyped]

from .flidriver import DeviceInfo, FliDriver, FliTemperature  # type: ignore[import-untyped]


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, device_info: DeviceInfo) -> None:
        super().__init__()
        self.setWindowTitle("FLI Camera")

        self._driver = FliDriver(device_info)
        self._driver.open()

        _, binning = self._driver.get_window_binning()
        full_frame = self._driver.get_full_frame()

        self._abort_event = asyncio.Event()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        global_layout = QtWidgets.QHBoxLayout(central)

        controls = QtWidgets.QGroupBox("Controls")
        global_layout.addWidget(controls)
        layout = QtWidgets.QVBoxLayout(controls)

        self._window_widget = WindowingWidget(full_frame[2], full_frame[3])
        layout.addWidget(self._window_widget)

        binnings = [(1, 1), (2, 2), (3, 3), (4, 4)]
        self._binning_widget = BinningWidget(binnings)
        self._binning_widget.binning_changed.connect(self._window_widget.set_binning)
        if binning in binnings:
            self._binning_widget.combo_binnings.setCurrentIndex(binnings.index(binning))
        layout.addWidget(self._binning_widget)

        self._format_widget = ImageFormatWidget([ImageFormat.INT16])
        layout.addWidget(self._format_widget)

        self._exposure_time = ExposureTimeWidget()
        layout.addWidget(self._exposure_time)

        self._expose_widget = ExposeWidget()
        self._expose_widget.expose_clicked.connect(self._expose_clicked)
        self._expose_widget.abort_clicked.connect(self._abort_clicked)
        layout.addWidget(self._expose_widget)

        temp_group = QtWidgets.QGroupBox("Temperature")
        temp_layout = QtWidgets.QFormLayout(temp_group)
        self._label_ccd = QtWidgets.QLabel("—")
        self._label_base = QtWidgets.QLabel("—")
        self._label_power = QtWidgets.QLabel("—")
        temp_layout.addRow("CCD:", self._label_ccd)
        temp_layout.addRow("Base:", self._label_base)
        temp_layout.addRow("Cooler:", self._label_power)
        layout.addWidget(temp_group)
        layout.addStretch()

        self._data_display = DataDisplayWidget()
        global_layout.addWidget(self._data_display)

        self._temp_timer = QtCore.QTimer()
        self._temp_timer.timeout.connect(self._refresh_temp)
        self._temp_timer.start(5000)
        self._refresh_temp()

    def _refresh_temp(self) -> None:
        try:
            ccd = self._driver.get_temp(FliTemperature.CCD)
            base = self._driver.get_temp(FliTemperature.BASE)
            power = self._driver.get_cooler_power()
            self._label_ccd.setText(f"{ccd:.1f} °C")
            self._label_base.setText(f"{base:.1f} °C")
            self._label_power.setText(f"{power:.0f} %")
        except Exception:
            pass

    @qasync.asyncSlot(int)  # type: ignore[misc]
    async def _expose_clicked(self, count: int) -> None:
        left, top, width, height = self._window_widget.values
        idx = self._binning_widget.combo_binnings.currentIndex()
        xbin, ybin = self._binning_widget._binnings[idx]  # noqa: SLF001
        exposure_time = self._exposure_time.value

        loop = asyncio.get_running_loop()

        def _prepare() -> None:
            self._driver.set_binning(xbin, ybin)
            self._driver.set_window(left * xbin, top * ybin, width, height)
            self._driver.init_exposure(True)
            self._driver.set_exposure_time(int(exposure_time * 1000.0))

        def _readout() -> np.ndarray:
            img = np.zeros((height, width), dtype=np.uint16)
            for row in range(height):
                img[row, :] = self._driver.grab_row(width)
            return img

        for i in range(count):
            if self._abort_event.is_set():
                break

            self._expose_widget.start_exposure(exposure_time)
            await loop.run_in_executor(None, _prepare)
            await loop.run_in_executor(None, self._driver.start_exposure)

            if await self._wait_exposure():
                await loop.run_in_executor(None, self._driver.cancel_exposure)
                break

            data = await loop.run_in_executor(None, _readout)

            image = fits.PrimaryHDU(data)
            image.header["EXPTIME"] = (exposure_time, "Exposure time [s]")
            image.header["XBINNING"] = (xbin, "Binning factor used on X axis")
            image.header["YBINNING"] = (ybin, "Binning factor used on Y axis")
            self._data_display.set_data(image)
            self._expose_widget.set_exposures_left(count - i - 1)
            self._refresh_temp()

        self._expose_widget.set_exposures_left(0)
        self._abort_event.clear()

    async def _wait_exposure(self) -> bool:
        """Return True if the exposure was aborted, False if data is ready."""
        loop = asyncio.get_running_loop()

        def _wait() -> bool:
            while True:
                if self._abort_event.is_set():
                    return True
                if self._driver.is_data_ready():
                    return False
                time.sleep(0.01)

        return await loop.run_in_executor(None, _wait)

    def _abort_clicked(self) -> None:
        self._abort_event.set()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._temp_timer.stop()
        self._driver.close()
        super().closeEvent(event)


async def async_main(app: QtWidgets.QApplication) -> None:
    devices = FliDriver.list_devices()
    if not devices:
        QtWidgets.QMessageBox.critical(None, "Error", "No FLI camera found.")
        return

    if len(devices) > 1:
        picker = ListPickerDialog([d.name.decode("utf-8") for d in devices])
        if picker.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        device = devices[picker.comboBox().currentIndex()]
    else:
        device = devices[0]

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    window = MainWindow(device)
    window.show()

    await app_close_event.wait()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    asyncio.run(async_main(app), loop_factory=qasync.QEventLoop)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
