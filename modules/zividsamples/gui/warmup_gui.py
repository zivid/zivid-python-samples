"""
Warmup GUI tab for the Hand Eye GUI


"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import pyqtgraph as pg
import zivid
from nptyping import Float32, NDArray, Shape
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from scipy.signal import savgol_filter
from zividsamples.camera_verification import (
    RandomCaptureCycle,
    VerificationAndState,
    capture_and_measure,
    capture_and_measure_from_frame,
)
from zividsamples.paths import get_data_file_path


class TimeAxisItem(pg.AxisItem):
    """Custom axis that formats time in HH:mm:ss."""

    def tickStrings(self, values, _, __):
        return [str(timedelta(seconds=int(v))) for v in values]


class StepSnappingSlider(QSlider):

    def _round_to_step(self, val):
        return round(val / self.singleStep()) * self.singleStep()

    def keyPressEvent(self, ev):
        if ev:
            if ev.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_PageUp, Qt.Key_PageDown):
                value = self.value()

                if ev.key() == Qt.Key_Left:
                    value = self._round_to_step(value - self.singleStep())
                elif ev.key() == Qt.Key_Right:
                    value = self._round_to_step(value + self.singleStep())
                elif ev.key() == Qt.Key_PageUp:
                    value = self._round_to_step(value + self.pageStep())
                elif ev.key() == Qt.Key_PageDown:
                    value = self._round_to_step(value - self.pageStep())

                value = max(self.minimum(), min(self.maximum(), value))
                self.setValue(value)
                return
        super().keyPressEvent(ev)


class QRangeSlider(QWidget):
    rangeChanged = pyqtSignal(int, int)

    def __init__(
        self,
        *,
        range_min: int = 0,
        range_max: int = 100,
        initial_min_val: int = 20,
        initial_max_val: int = 80,
        step_for_min_val: int = 1,
        step_for_max_val: int = 1,
    ):
        super().__init__()

        self.step_for_min_val = step_for_min_val
        self.step_for_max_val = step_for_max_val
        self.range_min = range_min
        self.range_max = range_max

        self.setup_widgets(initial_min_val, initial_max_val)
        self.setup_layout()
        self.connect_signals()

    def setup_widgets(self, initial_min_val: int, initial_max_val: int):
        self.min_slider = StepSnappingSlider(Qt.Horizontal)
        self.min_val_input = QLineEdit()
        self.max_slider = StepSnappingSlider(Qt.Horizontal)
        self.max_val_input = QLineEdit()

        self.min_slider.setRange(self.range_min, self.range_max)
        self.max_slider.setRange(self.range_min, self.range_max)
        self.min_slider.setSingleStep(self.step_for_min_val)
        self.max_slider.setSingleStep(self.step_for_max_val)
        self.min_slider.setValue(initial_min_val)
        self.max_slider.setValue(initial_max_val)

        self.update_text()

    def setup_layout(self):
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        layout = QVBoxLayout()
        top_layout.addWidget(QLabel("Min:"))
        top_layout.addWidget(self.min_slider)
        top_layout.addWidget(self.min_val_input)
        bottom_layout.addWidget(QLabel("Max:"))
        bottom_layout.addWidget(self.max_slider)
        bottom_layout.addWidget(self.max_val_input)
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def connect_signals(self):
        self.min_slider.valueChanged.connect(self.slider_min_val_changed)
        self.max_slider.valueChanged.connect(self.slider_max_val_changed)
        self.min_val_input.editingFinished.connect(self.min_val_input_changed)
        self.max_val_input.editingFinished.connect(self.max_val_input_changed)

    def update_text(self):
        self.min_val_input.setText(f"{self.min_slider.value():6.0f} ms")
        self.max_val_input.setText(f"{self.max_slider.value():6.0f} ms")

    def slider_min_val_changed(self):
        min_val = self.min_slider.value()

        if min_val > self.max_slider.value():
            self.max_slider.setValue(min_val)

        self.update_text()

        self.rangeChanged.emit(self.min_slider.value(), self.max_slider.value())

    def slider_max_val_changed(self):
        max_val = self.max_slider.value()

        if max_val < self.min_slider.value():
            self.min_slider.setValue(max_val)

        self.update_text()

        self.rangeChanged.emit(self.min_slider.value(), self.max_slider.value())

    def min_val_input_changed(self):
        try:
            min_val = int(self.min_val_input.text().strip("ms"))
            if min_val < self.range_min:
                min_val = self.range_min
            elif min_val > self.range_max:
                min_val = self.range_max
            self.min_slider.setValue(min_val)
        except ValueError:
            self.update_text()

    def max_val_input_changed(self):
        try:
            max_val = int(self.max_val_input.text().strip("ms"))
            if max_val < self.range_min:
                max_val = self.range_min
            elif max_val > self.range_max:
                max_val = self.range_max
            self.max_slider.setValue(max_val)
        except ValueError:
            self.update_text()

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.append(self.min_slider)
        widgets.append(self.min_val_input)
        widgets.append(self.max_slider)
        widgets.append(self.max_val_input)
        return widgets


class WarmupData:
    _empty_df_template = pd.DataFrame(
        {
            "timestamp": pd.Series(dtype="datetime64[ns]"),
            "temperature": pd.Series(dtype="float"),
            "local_trueness": pd.Series(dtype="float"),
            "distance": pd.Series(dtype="float"),
            "smoothed_temperature": pd.Series(dtype="float"),
            "savitzky_golay_derivative": pd.Series(dtype="float"),
            "average_rate_of_change": pd.Series(dtype="float"),
        }
    )

    def __init__(self, temperature_change_threshold_degrees_per_minute: float = 2.0):
        self.temperature_change_threshold_degrees_per_minute = temperature_change_threshold_degrees_per_minute
        self.df = self._empty_df_template.copy()
        self.serial_number = None
        self.window_size = 11

    # pylint: disable=too-many-positional-arguments
    def add_data(
        self,
        serial_number: str,
        timestamp: datetime,
        temperature: float,
        local_trueness: Optional[float],
        distance: Optional[float],
    ):
        if self.serial_number is None:
            self.serial_number = serial_number
        elif self.serial_number != serial_number:
            raise ValueError("Data from different cameras cannot be mixed")

        new_entry = {
            "timestamp": timestamp,
            "temperature": temperature,
            "local_trueness": local_trueness if local_trueness is not None else np.nan,
            "distance": distance if distance is not None else np.nan,
            "smoothed_temperature": np.nan,
            "savitzky_golay_derivative": np.nan,
            "average_rate_of_change": np.nan,
        }

        new_entry_df = pd.DataFrame([new_entry]).astype(self.df.dtypes.to_dict())  # type: ignore
        if self.df.empty:
            self.df = new_entry_df
        else:
            self.df = pd.concat([self.df, new_entry_df], ignore_index=True)
        self._update_rate_of_change()

    def _update_rate_of_change(self):
        if len(self.df) < self.window_size:
            return

        self.df["smoothed_temperature"] = savgol_filter(
            self.df["temperature"], window_length=self.window_size, polyorder=2
        )
        self.df["savitzky_golay_derivative"] = (
            savgol_filter(self.df["temperature"], window_length=self.window_size, polyorder=2, deriv=1) * 60
        )  # Convert to degrees per minute
        elapsed_time = (self.df["timestamp"] - self.df["timestamp"].iloc[0]).dt.to_pytimedelta()[-1]
        rolling_window = "1min"
        if elapsed_time > timedelta(minutes=5):
            rolling_window = "2min"
        if elapsed_time > timedelta(minutes=10):
            rolling_window = "5min"
        self.df["average_rate_of_change"] = (
            self.df.set_index("timestamp")["savitzky_golay_derivative"]
            .rolling(rolling_window)
            .mean()
            .reset_index(drop=True)  # type: ignore
        )

    def x_data(self) -> NDArray[Shape["N"], Float32]:  # type: ignore
        return (self.df["timestamp"] - self.df["timestamp"].iloc[0]).dt.total_seconds().to_numpy()

    def x_data_for_local_trueness(self) -> NDArray[Shape["N"], Float32]:  # type: ignore
        all_xdata = self.df["timestamp"] - self.df["timestamp"].iloc[0]
        return all_xdata[pd.notna(self.df["local_trueness"])].dt.total_seconds().to_numpy()

    def local_trueness_data(self) -> NDArray[Shape["N"], Float32]:  # type: ignore
        return self.df["local_trueness"][pd.notna(self.df["local_trueness"])].to_numpy()  # type: ignore

    def average_distance_to_calibration_board(self) -> float:
        if self.df.empty:
            return 0.0
        return np.nanmean(self.df["distance"].to_numpy())  # type: ignore

    def temperature_data(self) -> NDArray[Shape["N"], Float32]:  # type: ignore
        return self.df["temperature"].to_numpy()

    def rate_of_change_data(self) -> NDArray[Shape["N"], Float32]:  # type: ignore
        return self.df["average_rate_of_change"].to_numpy()

    def temperature_is_stable(self) -> bool:
        now = self.df["timestamp"].iloc[-1]
        one_minute_ago = now - timedelta(minutes=1)
        last_minute_of_data = self.df[self.df["timestamp"] >= one_minute_ago]
        max_rate_of_change_in_the_last_minute = last_minute_of_data["average_rate_of_change"].max()
        if self.has_enough_data_to_analyze():
            return (
                self.df["average_rate_of_change"].iloc[-1] is not None
                and max_rate_of_change_in_the_last_minute <= self.temperature_change_threshold_degrees_per_minute
            )
        return False

    def temperature_is_changing_fast(self) -> bool:
        return self.df["average_rate_of_change"].iloc[-1] > 2 * self.temperature_change_threshold_degrees_per_minute

    def is_real_camera(self) -> bool:
        return (self.serial_number is not None) and self.serial_number != "F1"

    def has_data(self) -> bool:
        return not self.df.empty

    def has_enough_data_to_plot(self) -> bool:
        return len(self.df) > 1

    def has_enough_data_to_analyze(self) -> bool:
        return len(self.df) > self.window_size

    def clear(self):
        self.df = self._empty_df_template.copy()
        self.serial_number = None

    def write_to_csv(self):
        self.df.to_csv(
            f"camera_{self.serial_number}_warmup_{datetime.now().isoformat('_', 'seconds').replace(':','-')}.csv",
            index=False,
        )


class WarmUpGUI(QWidget):
    warmup_finished = pyqtSignal(bool)
    warmup_start_requested: pyqtSignal = pyqtSignal()
    instructions_updated: pyqtSignal = pyqtSignal()
    information_updated: pyqtSignal = pyqtSignal()
    update_graph_signal: pyqtSignal = pyqtSignal()
    description: List[str]
    instruction_steps: Dict[str, bool]

    # pylint: disable=too-many-positional-arguments
    def __init__(self, parent=None):
        super().__init__(parent)

        temperature_change_threshold_degrees_per_minute = 2.0

        self.description = [
            "For optimal performance the camera should warm up for a few minutes until it has reached the temperature expected during normal operation.",
            "Factory calibration accounts for changes in temperature, and thermal stabilization works to maintain stable temperature.",
            "However, thermal stabilization is only operational when the camera is powered.",
            f"The warm-up will automatically stop when the change in temperature is less than {temperature_change_threshold_degrees_per_minute} °C/min for 1 minute.",
        ]

        camera_parameters_path = get_data_file_path("camera_parameters.json")
        self.camera_parameters = pd.read_json(camera_parameters_path, orient="index")

        self.random_capture_cycle = RandomCaptureCycle()
        self.ready_to_start = False
        self.started = False
        self.equilibrium_reached = False
        self.stop_requested = False
        self.full_history_of_results: WarmupData = WarmupData(
            temperature_change_threshold_degrees_per_minute=temperature_change_threshold_degrees_per_minute
        )
        self.last_local_trueness_measurement: Optional[float] = None
        self.last_measured_distance: float = 0.0
        self.last_rate_of_change_measurement: Optional[float] = None
        self.last_measured_temperature: Optional[float] = None
        self.last_measured_temperature_dmd: Optional[float] = None
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(
            ready=self.ready_to_start, started=self.started, equilibrium_reached=self.equilibrium_reached
        )

    def create_widgets(self):
        self.warmup_button = QPushButton("Start Warmup")
        self.warmup_button.setObjectName("Warmup-start_warmup_button")
        self.capture_interval_slider = QRangeSlider(
            range_min=500,
            range_max=20000,
            initial_min_val=int(self.random_capture_cycle.min_capture_interval.total_seconds() * 1000),
            initial_max_val=int(self.random_capture_cycle.max_capture_interval.total_seconds() * 1000),
            step_for_min_val=50,
            step_for_max_val=1000,
        )
        self.information_area = QTextEdit()
        self.information_area.setAcceptRichText(True)
        self.information_area.setReadOnly(True)
        self.information_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.information_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.information_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.information_area.hide()

        self.plot_widget_layout = pg.GraphicsLayoutWidget()
        self.plot_widget_layout.setWindowTitle("Temperature and Local Trueness")

        self.time_axis_temp = TimeAxisItem(orientation="bottom")
        self.time_axis_roc = TimeAxisItem(orientation="bottom")

        self.temperature_plot = self.plot_widget_layout.addPlot(row=0, col=0, axisItems={"bottom": self.time_axis_temp})
        self.temperature_plot.setLabel("left", "Temperature", units="°C")
        self.temperature_plot.setYRange(15, 45)

        self.rate_of_change_plot = self.plot_widget_layout.addPlot(
            row=1, col=0, axisItems={"bottom": self.time_axis_roc}
        )
        self.rate_of_change_plot.setLabel("left", "Rate of Change", units="°C/min")
        self.rate_of_change_plot.setXLink(self.temperature_plot)  # Link x-axis with the main plot

        self.plot_data_item_temperature = self.temperature_plot.plot([], [], pen="r")

        self.plot_data_item_temperature_rate_of_change = self.rate_of_change_plot.plot([], [], pen="y")
        self.rate_of_change_plot.getAxis("left").setLogMode(True)
        self.rate_of_change_plot.getAxis("left").enableAutoSIPrefix(False)
        self.rate_of_change_plot.addItem(
            pg.InfiniteLine(
                pos=np.log10(self.full_history_of_results.temperature_change_threshold_degrees_per_minute),
                angle=0,  # 0 degrees for a horizontal line
                pen=pg.mkPen("r", width=1, style=Qt.DashLine),
            )
        )

    def setup_layout(self):
        layout = QVBoxLayout()
        top_panel = QVBoxLayout()
        middle_panel = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        top_panel.addWidget(self.plot_widget_layout)
        layout.addLayout(top_panel)
        middle_panel.addWidget(self.capture_interval_slider)
        middle_panel.addWidget(self.information_area)
        layout.addLayout(middle_panel)
        bottom_layout.addWidget(self.warmup_button)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def connect_signals(self):
        self.warmup_button.clicked.connect(self.on_warmup_button_clicked)
        self.capture_interval_slider.rangeChanged.connect(self.update_capture_interval)
        self.update_graph_signal.connect(self.update_graph)
        self.information_updated.connect(self.update_information_text)

    def update_instructions(self, ready: bool, started: bool, equilibrium_reached: bool):
        self.ready_to_start = ready
        self.started = started
        self.equilibrium_reached = equilibrium_reached
        self.instruction_steps = {}
        self.instruction_steps["[Optional] Capture Calibration Board"] = self.ready_to_start
        self.instruction_steps["Start Warmup"] = self.started
        self.instruction_steps["Warmup Completed"] = self.equilibrium_reached
        self.instructions_updated.emit()

    def toggle_use_robot(self, _: bool):
        return

    def update_information_text(self):
        if self.last_local_trueness_measurement is not None:
            self.information_area.clear()
            text = "<table cellpadding='5' style='border-collapse: collapse; width: 100%;; margin-top: 10px;'>"
            text += "<style>td:nth-child(2) {text-align: right;}</style>"
            text += f"<tr><td>Last measured local trueness</td><td>{self.last_local_trueness_measurement * 100:6.2f} %</td></tr>"
            text += f"<tr><td>Last measured temperature</td><td>{self.last_measured_temperature:6.2f} °C</td></tr>"
            last_rate_of_change_measurement_str = (
                "(Not enough data yet)"
                if self.last_rate_of_change_measurement is None
                else f"{self.last_rate_of_change_measurement:6.2f} °C/min"
            )
            text += f"<tr><td>Last measured rate-of-change</td><td>{last_rate_of_change_measurement_str}</td></tr>"
            text += "</table>"
            self.information_area.setText(text)
            self.information_area.show()
            self.information_area.setFixedHeight(int(self.information_area.document().size().height()) + 10)
            self.information_area.updateGeometry()
            self.information_area.repaint()

    def update_capture_interval(self, min_val, max_val):
        self.random_capture_cycle.min_capture_interval = timedelta(seconds=min_val / 1000)
        self.random_capture_cycle.max_capture_interval = timedelta(seconds=max_val / 1000)
        self.information_updated.emit()

    def on_warmup_button_clicked(self):
        if self.started:
            self.stop_warmup()
        else:
            self.warmup_start_requested.emit()

    def capture_for_warmup(
        self,
        camera: zivid.Camera,
        settings: zivid.Settings,
    ) -> VerificationAndState:
        frame = camera.capture(settings)
        return VerificationAndState(
            verification=None,
            state=camera.state,
            time=frame.info.time_stamp,
            info=camera.info,
        )

    def stop_warmup(self):
        if self.started:
            self.stop_requested = True
            while self.stop_requested:
                time.sleep(0.1)

    def start_warmup(self, camera: zivid.Camera, production_settings: zivid.Settings):
        try:
            self.warmup_button.setText("Stop Warmup")
            self.warmup_button.setStyleSheet("background-color: yellow; color: black;")
            initial_result = capture_and_measure(camera)
            if initial_result.verification is not None:
                self.last_local_trueness_measurement = initial_result.verification.local_dimension_trueness()
                self.last_measured_distance = self.full_history_of_results.average_distance_to_calibration_board()
            if self.full_history_of_results.has_enough_data_to_analyze():
                self.last_rate_of_change_measurement = self.full_history_of_results.rate_of_change_data()[-1]
            self.last_measured_temperature = initial_result.state.temperature.lens
            self.last_measured_temperature_dmd = initial_result.state.temperature.dmd
            self.information_updated.emit()
            self.clear_plots()
            self.equilibrium_reached = False
            self.stop_requested = False
            QTimer.singleShot(
                100,
                lambda: threading.Thread(
                    target=self.warmup_cycle,
                    args=(
                        camera,
                        production_settings,
                    ),
                ).start(),
            )
        except RuntimeError as ex:
            QMessageBox.critical(self, "Error", str(ex))
            self.warmup_button.setText("Re-start Warmup")
            self.warmup_button.setStyleSheet("")
            self.end_warmup(equilibrium_reached=False)

    def warmup_cycle(self, camera: zivid.Camera, production_settings: zivid.Settings):
        self.update_instructions(ready=self.ready_to_start, started=True, equilibrium_reached=self.equilibrium_reached)
        trueness_measurement_interval = timedelta(
            seconds=max(20, self.random_capture_cycle.max_capture_interval.total_seconds())
        )
        start_time = last_trueness_measurement_time = datetime.now()
        while not self.equilibrium_reached and self.stop_requested is False:
            try:
                time_before = datetime.now()
                elapsed_since_last_trueness_measurement = time_before - last_trueness_measurement_time
                result = (
                    capture_and_measure(camera)
                    if elapsed_since_last_trueness_measurement >= trueness_measurement_interval
                    else self.capture_for_warmup(camera, production_settings)
                )
                if elapsed_since_last_trueness_measurement >= trueness_measurement_interval:
                    last_trueness_measurement_time = time_before
                if camera.info.serial_number == "F1":
                    break
                self.full_history_of_results.add_data(
                    result.info.serial_number,
                    result.time,
                    float(result.state.temperature.lens),
                    result.local_dimension_trueness(),
                    result.distance(),
                )
                self.update_graph_signal.emit()
                if result.verification is not None:
                    self.last_local_trueness_measurement = result.verification.local_dimension_trueness()
                    self.last_measured_distance = self.full_history_of_results.average_distance_to_calibration_board()
                    if not self.ready_to_start:
                        self.update_instructions(
                            ready=True, started=self.started, equilibrium_reached=self.equilibrium_reached
                        )
                if self.full_history_of_results.has_enough_data_to_analyze():
                    self.last_rate_of_change_measurement = self.full_history_of_results.rate_of_change_data()[-1]
                self.last_measured_temperature = result.state.temperature.lens
                self.last_measured_temperature_dmd = result.state.temperature.dmd
                self.information_updated.emit()
                self.equilibrium_reached = self.full_history_of_results.temperature_is_stable()
                time_after = datetime.now()
                time_left = self.random_capture_cycle.capture_interval() - (time_after - time_before)
                if time_left.total_seconds() > 0:
                    if (
                        self.full_history_of_results.has_enough_data_to_analyze()
                        and self.full_history_of_results.temperature_is_changing_fast()
                    ):
                        time.sleep(0.1)
                    else:
                        time.sleep(time_left.total_seconds())
                else:
                    time.sleep(0.1)
                if datetime.now() - start_time > timedelta(minutes=2):
                    trueness_measurement_interval = timedelta(seconds=30)
                if datetime.now() - start_time > timedelta(minutes=5):
                    trueness_measurement_interval = timedelta(seconds=60)
            except RuntimeError as e:
                QMessageBox.critical(None, "Error", str(e))
                time.sleep(2)
        self.end_warmup(self.equilibrium_reached)

    def end_warmup(self, equilibrium_reached: bool):
        self.started = False
        self.stop_requested = False
        self.equilibrium_reached = equilibrium_reached
        self.update_instructions(
            ready=self.ready_to_start, started=self.started, equilibrium_reached=self.equilibrium_reached
        )
        self.warmup_button.setText("Re-start Warmup")
        self.warmup_button.setStyleSheet("")
        self.warmup_finished.emit(self.equilibrium_reached)

        if self.full_history_of_results.has_data():
            if self.full_history_of_results.is_real_camera():
                self.full_history_of_results.write_to_csv()
            self.full_history_of_results.clear()

    def approximate_value_at_distance(self, camera: zivid.Camera, distance: float):
        approx_value = 0
        values_a = self.camera_parameters.loc[camera.info.model_name]["key_c"]
        for i, val_a in enumerate(values_a):
            approx_value += val_a * (distance**i)
        return approx_value

    def get_warn_about_trueness_str(self, camera: zivid.Camera) -> str:
        if self.equilibrium_reached:
            if self.last_local_trueness_measurement is None:
                return "Note: No calibration board was detected during warmup, so we cannot verify the local trueness."
            expected_dimension_trueness_70_percentile = self.approximate_value_at_distance(
                camera, self.last_measured_distance
            )
            if self.last_local_trueness_measurement > expected_dimension_trueness_70_percentile:
                return f"""
Warning:
Local trueness is {self.last_local_trueness_measurement * 100:.2f} %. The 70-percentile value at {self.last_measured_distance / 1000:.1f} m is {expected_dimension_trueness_70_percentile * 100:.2f} %.
We recommend that you perform Infield Correction."""
        return ""

    def clear_plots(self):
        self.plot_data_item_temperature.clear()
        self.plot_data_item_temperature_rate_of_change.clear()

    def update_graph(self):

        def round_down_to_nearest_5(x):
            return 5 * np.floor(x / 5)

        def round_up_to_nearest_5(x):
            return 5 * np.ceil(x / 5)

        if self.full_history_of_results.has_enough_data_to_plot():
            self.plot_data_item_temperature.setData(
                self.full_history_of_results.x_data(), self.full_history_of_results.temperature_data()
            )
            self.temperature_plot.setYRange(
                round_down_to_nearest_5(min(self.full_history_of_results.temperature_data())) - 5,
                round_up_to_nearest_5(max(self.full_history_of_results.temperature_data())) + 5,
            )

        if self.full_history_of_results.has_enough_data_to_analyze():
            rate_of_change_data = np.log10(np.abs(self.full_history_of_results.rate_of_change_data()))
            self.plot_data_item_temperature_rate_of_change.setData(
                self.full_history_of_results.x_data(),
                rate_of_change_data,
            )
            self.rate_of_change_plot.setYRange(0.01, np.nanmax(rate_of_change_data) * 1.1)

    def process_capture(self, frame: zivid.Frame, _, __):  # type: ignore
        if not self.started:
            try:
                test_result = capture_and_measure_from_frame(frame)
                if test_result.verification is not None:
                    self.last_local_trueness_measurement = test_result.verification.local_dimension_trueness()
                    self.last_measured_distance = self.full_history_of_results.average_distance_to_calibration_board()
                self.last_measured_temperature = test_result.state.temperature.lens
                self.update_information_text()
                self.update_instructions(ready=True, started=self.started, equilibrium_reached=self.equilibrium_reached)
                self.warmup_button.setEnabled(True)
            except RuntimeError as ex:
                QMessageBox.critical(self, "Error", str(ex))
                raise ex

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.capture_interval_slider.get_tab_widgets_in_order())
        widgets.append(self.warmup_button)
        return widgets
