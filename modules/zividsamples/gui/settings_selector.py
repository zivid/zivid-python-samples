"""
Settings Selection

Note: This script requires PyQt5 to be installed.

"""

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Optional, Tuple

import zivid
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)
from zivid.experimental import PixelMapping, calibration


@dataclass
class Settings:
    settings_3d: Optional[zivid.Settings] = None
    settings_3d_for_hand_eye: Optional[zivid.Settings] = None
    settings_2d: Optional[zivid.Settings2D] = None
    pixel_mapping: Optional[PixelMapping] = None
    intrinsics: Optional[zivid.CameraIntrinsics] = None


def validate_settings(camera: zivid.Camera, settings: zivid.Settings) -> bool:
    try:
        camera.capture(settings)
    except Exception as error:
        QMessageBox.critical(None, "Invalid Settings", str(error))
        return False
    return True


def validate_settings_file(camera: zivid.Camera, settings_path: Path) -> bool:
    try:
        settings = zivid.Settings.load(settings_path)
    except Exception as error:
        QMessageBox.critical(None, "Invalid File", str(error))
        return False
    return validate_settings(camera, settings)


def _settings_for_hand_eye(
    camera: zivid.Camera, engine: zivid.Settings.Engine, sampling_pixel: zivid.Settings.Sampling.Pixel
) -> zivid.Settings:

    def _get_exposure_values(camera: zivid.Camera) -> Iterable[Tuple[float, float, timedelta, float]]:
        if camera.info.model in [zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100]:
            apertures = (5.66, 2.38, 1.8)
            gains = (1.0, 1.0, 1.0)
            exposure_times = (
                timedelta(microseconds=1677),
                timedelta(microseconds=5000),
                timedelta(microseconds=100000),
            )
            brightnesses = (1.8, 1.8, 1.8)
        elif camera.info.model in [
            zivid.CameraInfo.Model.zivid2PlusM130,
            zivid.CameraInfo.Model.zivid2PlusM60,
            zivid.CameraInfo.Model.zivid2PlusL110,
        ]:
            apertures = (5.66, 2.8, 2.37)
            gains = (1.0, 1.0, 1.0)
            exposure_times = (
                timedelta(microseconds=1677),
                timedelta(microseconds=20000),
                timedelta(microseconds=100000),
            )
            brightnesses = (2.2, 2.2, 2.2)
        else:
            raise ValueError(f"Unhandled enum value {camera.info.model}")

        return zip(apertures, gains, exposure_times, brightnesses)  # noqa: B905

    updated_settings = zivid.Settings()
    updated_settings.engine = engine
    updated_settings.sampling.color = zivid.Settings.Sampling.Color.rgb
    updated_settings.sampling.pixel = sampling_pixel
    exposure_values = _get_exposure_values(camera)
    for aperture, gain, exposure_time, brightness in exposure_values:
        updated_settings.acquisitions.append(
            zivid.Settings.Acquisition(
                aperture=aperture,
                exposure_time=exposure_time,
                brightness=brightness,
                gain=gain,
            )
        )
    filters = updated_settings.processing.filters
    filters.smoothing.gaussian.enabled = True
    filters.smoothing.gaussian.sigma = 5.0
    filters.noise.removal.enabled = True
    filters.noise.removal.threshold = 7.0
    filters.noise.suppression.enabled = True
    filters.noise.repair.enabled = True
    filters.outlier.removal.enabled = True
    filters.outlier.removal.threshold = 5.0
    filters.reflection.removal.enabled = True
    filters.reflection.removal.mode = zivid.Settings.Processing.Filters.Reflection.Removal.Mode.global_
    filters.cluster.removal.enabled = True
    filters.cluster.removal.max_neighbor_distance = 3
    filters.cluster.removal.min_area = 100
    filters.experimental.contrast_distortion.correction.enabled = False
    filters.experimental.contrast_distortion.removal.enabled = False
    filters.experimental.contrast_distortion.removal.threshold = 0.5
    filters.hole.repair.enabled = True
    filters.hole.repair.hole_size = 0.2
    filters.hole.repair.strictness = 1
    color = updated_settings.processing.color
    color.gamma = 1.0
    updated_settings.processing.color.experimental.mode = zivid.Settings.Processing.Color.Experimental.Mode.automatic
    return updated_settings


class EngineAndSamplingSelectionDialog(QDialog):

    def __init__(self, camera: zivid.Camera):
        super().__init__()
        self.camera = camera

        self.setWindowTitle("Select Engine and Sampling Mode")
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.engine_selector = QComboBox(self)
        self.engine_selector.addItems(zivid.Settings.Engine.valid_values())
        self.engine_selector.setCurrentText(zivid.Settings.Engine.stripe)
        form_layout.addRow("Select Engine", self.engine_selector)
        self.sampling_mode_selector = QComboBox(self)
        self.sampling_mode_selector.addItems(zivid.Settings.Sampling.Pixel.valid_values())
        self.sampling_mode_selector.setCurrentText(zivid.Settings.Sampling.Pixel.blueSubsample2x2)
        form_layout.addRow("Select Sampling Mode", self.sampling_mode_selector)
        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)

        layout.addWidget(self.button_box)

        self.setLayout(layout)


class PresetSelectionDialog(QDialog):

    def __init__(self, camera: zivid.Camera):
        super().__init__()
        self.camera = camera

        self.setWindowTitle("Select Preset")
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.category_selector = QComboBox(self)
        categories = zivid.presets.categories(camera.info.model)
        for category in categories:
            self.category_selector.addItem(category.name, category)
        self.category_selector.currentIndexChanged.connect(self.update_preset_selector)
        form_layout.addRow("Select Category", self.category_selector)
        self.preset_selector = QComboBox(self)
        for preset in categories[0].presets:
            self.preset_selector.addItem(preset.name, preset)
        form_layout.addRow("Select Preset", self.preset_selector)
        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setText("Use")
        self.button_box.button(QDialogButtonBox.Cancel).setText("Do not use")
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def update_preset_selector(self, _: int):
        self.preset_selector.clear()
        presets = self.category_selector.currentData().presets
        for preset in presets:
            self.preset_selector.addItem(preset.name, preset)


class SettingsFromFileDialog(QDialog):

    def __init__(self, camera: zivid.Camera):
        super().__init__()
        self.camera = camera

        self.setWindowTitle("Load Settings from File")
        layout = QVBoxLayout(self)

        self.file_path_edit = QLineEdit(self)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.file_path_edit)
        input_layout.addWidget(QPushButton("Browse", clicked=self.open_file_dialog))
        layout.addLayout(input_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setText("Yes")
        self.button_box.button(QDialogButtonBox.Cancel).setText("No")
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select File", filter="YAML Files (*.yml *.yaml)")
        if file_path:
            if validate_settings_file(self.camera, file_path):
                self.file_path_edit.setText(file_path)


def get_engine_and_sampling_pixel(camera: zivid.Camera) -> Tuple[str, str]:
    engine_and_sampling_dialog = EngineAndSamplingSelectionDialog(camera)
    engine = engine_and_sampling_dialog.engine_selector.currentText()
    sampling_pixel = engine_and_sampling_dialog.sampling_mode_selector.currentText()
    if engine_and_sampling_dialog.exec_() != QDialog.Accepted:
        QMessageBox.critical(
            None,
            "Engine and Sampling Selection",
            f"""Engine and Sampling selection is required. Will default to:
  - {'Engine':<20} {engine}
  - {'Sampling Pixel':<18} {sampling_pixel}""",
        )
    return (
        engine_and_sampling_dialog.engine_selector.currentText(),
        engine_and_sampling_dialog.sampling_mode_selector.currentText(),
    )


def get_preset_settings(camera: zivid.Camera) -> Optional[zivid.Settings]:
    preset = PresetSelectionDialog(camera)
    if preset.exec_() == QDialog.Accepted:
        return preset.preset_selector.currentData().settings
    return None


def get_settings_from_file(camera: zivid.Camera) -> Optional[zivid.Settings]:
    file_dialog = SettingsFromFileDialog(camera)
    if file_dialog.exec_() == QDialog.Accepted:
        file_path = file_dialog.file_path_edit.text()
        return zivid.Settings.load(file_path)
    return None


def _connect_if_not_connected(camera: zivid.Camera) -> bool:
    if camera.state.connected is False:
        camera.connect()
        if camera.state.connected is False:
            QMessageBox.critical(None, "Camera Connection Error", "Could not connect to camera")
            return False
        return True
    return True


def select_settings(camera: zivid.Camera) -> Optional[zivid.Settings]:
    if _connect_if_not_connected(camera) is False:
        return None
    settings = get_preset_settings(camera)
    return get_settings_from_file(camera) if settings is None else settings


def select_settings_for_hand_eye(camera: zivid.Camera) -> Settings:
    settings = select_settings(camera)
    engine, sampling_pixel = (
        get_engine_and_sampling_pixel(camera) if settings is None else (settings.engine, settings.sampling.pixel)
    )
    hand_eye_settings = _settings_for_hand_eye(camera, engine, sampling_pixel)
    settings_3d = hand_eye_settings if settings is None else settings
    settings_2d = zivid.Settings2D(
        [
            zivid.Settings2D.Acquisition(
                brightness=0.0,
                exposure_time=timedelta(microseconds=20000),
                aperture=2.43,
            )
        ]
    )
    return Settings(
        settings_3d=settings_3d,
        settings_3d_for_hand_eye=hand_eye_settings,
        settings_2d=settings_2d,
        pixel_mapping=calibration.pixel_mapping(camera, settings_3d),
        intrinsics=calibration.intrinsics(camera, settings_2d),
    )
