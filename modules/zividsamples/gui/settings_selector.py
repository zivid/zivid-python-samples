"""
Settings Selection

Note: This script requires PyQt5 to be installed.

"""

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Optional, Tuple

import zivid
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from zivid.experimental import PixelMapping, calibration


@dataclass
class SettingsPixelMappingIntrinsics:
    settings_2d3d: zivid.Settings
    pixel_mapping: PixelMapping
    intrinsics: zivid.CameraIntrinsics

    def save_settings(self, qsettings: QSettings):
        qsettings.setValue("settings_2d3d", self.settings_2d3d.serialize())
        qsettings.beginGroup("pixel_mapping")
        qsettings.setValue("row_stride", self.pixel_mapping.row_stride)
        qsettings.setValue("col_stride", self.pixel_mapping.col_stride)
        qsettings.setValue("row_offset", self.pixel_mapping.row_offset)
        qsettings.setValue("col_offset", self.pixel_mapping.col_offset)
        qsettings.endGroup()
        qsettings.setValue("intrinsics", self.intrinsics.serialize())

    @classmethod
    def load_settings(cls, qsettings: QSettings) -> "SettingsPixelMappingIntrinsics":
        settings_2d3d = (
            zivid.Settings()
            if not qsettings.contains("settings_2d3d")
            else zivid.Settings.from_serialized(qsettings.value("settings_2d3d"))
        )
        qsettings.beginGroup("pixel_mapping")
        default_pixel_mapping = PixelMapping()
        pixel_mapping = PixelMapping(
            row_stride=qsettings.value("row_stride", default_pixel_mapping.row_stride, type=int),
            col_stride=qsettings.value("col_stride", default_pixel_mapping.col_stride, type=int),
            row_offset=qsettings.value("row_offset", default_pixel_mapping.row_offset, type=float),
            col_offset=qsettings.value("col_offset", default_pixel_mapping.col_offset, type=float),
        )
        qsettings.endGroup()
        intrinsics = (
            zivid.CameraIntrinsics()
            if not qsettings.contains("intrinsics")
            else zivid.CameraIntrinsics.from_serialized(qsettings.value("intrinsics"))
        )
        return cls(settings_2d3d=settings_2d3d, pixel_mapping=pixel_mapping, intrinsics=intrinsics)


class SettingsForHandEyeGUI:

    def __init__(
        self,
        production: Optional[SettingsPixelMappingIntrinsics] = None,
        hand_eye: Optional[SettingsPixelMappingIntrinsics] = None,
        infield_correction: Optional[SettingsPixelMappingIntrinsics] = None,
    ):
        settings = QSettings("Zivid", "HandEyeGUI")
        settings.beginGroup("camera_settings")
        settings.beginGroup("production")
        self.production = production or SettingsPixelMappingIntrinsics.load_settings(settings)
        settings.endGroup()
        settings.beginGroup("hand_eye")
        self.hand_eye = hand_eye or SettingsPixelMappingIntrinsics.load_settings(settings)
        settings.endGroup()
        settings.beginGroup("infield_correction")
        self.infield_correction = infield_correction or SettingsPixelMappingIntrinsics.load_settings(settings)
        settings.endGroup()
        self.show_dialog = settings.value("show_dialog", True, type=bool)
        settings.endGroup()

    def save_choice(self):
        settings = QSettings("Zivid", "HandEyeGUI")
        settings.beginGroup("camera_settings")
        settings.beginGroup("production")
        self.production.save_settings(settings)
        settings.endGroup()
        settings.beginGroup("hand_eye")
        self.hand_eye.save_settings(settings)
        settings.endGroup()
        settings.beginGroup("infield_correction")
        self.infield_correction.save_settings(settings)
        settings.endGroup()
        settings.setValue("show_dialog", self.show_dialog)
        settings.endGroup()


def validate_settings(camera: zivid.Camera, settings: zivid.Settings, show_message_box: bool = True) -> bool:
    try:
        camera.capture_2d_3d(settings)
    except Exception as error:
        if show_message_box:
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
        elif camera.info.model in [
            zivid.CameraInfo.Model.zivid2PlusMR130,
            zivid.CameraInfo.Model.zivid2PlusMR60,
            zivid.CameraInfo.Model.zivid2PlusLR110,
        ]:
            apertures = (5.66, 2.83, 2.83)
            gains = (1.0, 1.0, 1.0)
            exposure_times = (
                timedelta(microseconds=900),
                timedelta(microseconds=5000),
                timedelta(microseconds=20000),
            )
            brightnesses = (2.5, 2.5, 2.5)
        else:
            raise ValueError(f"Unhandled enum value {camera.info.model}")

        return zip(apertures, gains, exposure_times, brightnesses)  # noqa: B905

    updated_settings = zivid.Settings()
    updated_settings.engine = engine
    # Avoid 4x4 sampling for hand-eye calibration
    if str(sampling_pixel) in [
        zivid.Settings.Sampling.Pixel.blueSubsample4x4,
        zivid.Settings.Sampling.Pixel.redSubsample4x4,
        zivid.Settings.Sampling.Pixel.by4x4,
    ]:
        updated_settings.sampling.pixel = {
            zivid.Settings.Sampling.Pixel.blueSubsample4x4: zivid.Settings.Sampling.Pixel.blueSubsample2x2,
            zivid.Settings.Sampling.Pixel.redSubsample4x4: zivid.Settings.Sampling.Pixel.redSubsample2x2,
            zivid.Settings.Sampling.Pixel.by4x4: zivid.Settings.Sampling.Pixel.by2x2,
        }[str(sampling_pixel)]
        if updated_settings.processing.resampling.mode == zivid.Settings.Processing.Resampling.Mode.upsample4x4:
            updated_settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
        elif updated_settings.processing.resampling.mode == zivid.Settings.Processing.Resampling.Mode.upsample2x2:
            updated_settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.disabled
    else:
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
    if camera.info.model in [
        zivid.CameraInfo.Model.zividTwo,
        zivid.CameraInfo.Model.zividTwoL100,
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
    ]:
        updated_settings.color = zivid.Settings2D(
            [
                zivid.Settings2D.Acquisition(
                    brightness=updated_settings.acquisitions[0].brightness,
                    exposure_time=timedelta(microseconds=20000),
                    aperture=2.43,
                    gain=1.0,
                )
            ],
        )
    else:
        updated_settings.color = zivid.Settings2D(
            [
                zivid.Settings2D.Acquisition(
                    brightness=updated_settings.acquisitions[0].brightness,
                    exposure_time=timedelta(microseconds=5000),
                    aperture=2.83,
                    gain=1.0,
                )
            ],
        )
    updated_settings.color.sampling.pixel = zivid.Settings2D.Sampling.Pixel.all
    updated_settings.color.sampling.color = zivid.Settings2D.Sampling.Color.rgb
    return updated_settings


class EngineAndSamplingSelectionWidget(QWidget):

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
        default_sampling_mode = (
            zivid.Settings.Sampling.Pixel.blueSubsample2x2
            if camera.info.model
            in [
                zivid.CameraInfo.Model.zividTwo,
                zivid.CameraInfo.Model.zividTwoL100,
                zivid.CameraInfo.Model.zivid2PlusM130,
                zivid.CameraInfo.Model.zivid2PlusM60,
                zivid.CameraInfo.Model.zivid2PlusL110,
            ]
            else zivid.Settings.Sampling.Pixel.by2x2
        )
        self.sampling_mode_selector.setCurrentText(default_sampling_mode)
        form_layout.addRow("Select Sampling Mode", self.sampling_mode_selector)
        layout.addLayout(form_layout)

        self.setLayout(layout)

    def get_settings(self):
        engine = self.engine_selector.currentText()
        sampling_pixel = self.sampling_mode_selector.currentText()
        return _settings_for_hand_eye(self.camera, engine, sampling_pixel)

    def reject(self):
        engine = self.engine_selector.currentText()
        sampling_pixel = self.sampling_mode_selector.currentText()
        QMessageBox.critical(
            None,
            "Engine and Sampling Selection",
            f"""Engine and Sampling selection is required. Will default to:
  - {'Engine':<20} {engine}
  - {'Sampling Pixel':<18} {sampling_pixel}""",
        )


class PresetSelectionWidget(QWidget):

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

        self.setLayout(layout)

    def update_preset_selector(self, _: int):
        self.preset_selector.clear()
        presets = self.category_selector.currentData().presets
        for preset in presets:
            self.preset_selector.addItem(preset.name, preset)

    def get_settings(self) -> zivid.Settings:
        return self.preset_selector.currentData().settings


class SettingsFromFileWidget(QWidget):

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

        self.setLayout(layout)

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select File", filter="YAML Files (*.yml *.yaml)")
        if file_path:
            if validate_settings_file(self.camera, file_path):
                self.file_path_edit.setText(file_path)

    def get_settings(self) -> zivid.Settings:
        return zivid.Settings.load(self.file_path_edit.text())


def _connect_if_not_connected(camera: zivid.Camera) -> bool:
    if camera.state.connected is False:
        camera.connect()
        if camera.state.connected is False:
            QMessageBox.critical(None, "Camera Connection Error", "Could not connect to camera")
            return False
        return True
    return True


class SettingsSelectionDialog(QDialog):
    def __init__(self, camera: zivid.Camera, show_dialog: bool):
        super().__init__()
        self.camera = camera
        self.setWindowTitle("Select Camera Settings")

        self.settings_for_hand_eye_gui = SettingsForHandEyeGUI()

        layout = QVBoxLayout(self)

        # --- Stacked widget with the choices ---
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

        # 1) Preset page
        self.preset_widget = PresetSelectionWidget(camera)
        self.stack.addWidget(self.preset_widget)

        # 2) File page
        self.file_widget = SettingsFromFileWidget(camera)
        self.stack.addWidget(self.file_widget)

        # 3) Manual (engine + sampling) page
        self.manual_widget = EngineAndSamplingSelectionWidget(camera)
        self.stack.addWidget(self.manual_widget)

        horizontal_layout = QHBoxLayout()

        # --- Show this dialog ---
        self.show_dialog_checkbox = QCheckBox("Show this dialog")
        self.show_dialog_checkbox.setChecked(show_dialog)
        horizontal_layout.addWidget(self.show_dialog_checkbox)

        # --- OK/Cancel ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        horizontal_layout.addWidget(self.button_box)

        layout.addLayout(horizontal_layout)

    def next_page(self) -> bool:
        index = self.stack.currentIndex() + 1
        if index < self.stack.count():
            self.stack.setCurrentIndex(index)
            return True
        return False

    def accept(self):
        current_widget = self.stack.currentWidget()
        assert current_widget
        if self.stack.currentIndex() < 2:
            production_settings = current_widget.get_settings()
            hand_eye_settings = _settings_for_hand_eye(
                self.camera, production_settings.engine, production_settings.sampling.pixel
            )
        else:
            production_settings = hand_eye_settings = current_widget.get_settings()
        infield_frame = zivid.calibration.capture_calibration_board(self.camera)
        infield_correction_settings = infield_frame.settings
        self.settings_for_hand_eye_gui = SettingsForHandEyeGUI(
            production=SettingsPixelMappingIntrinsics(
                settings_2d3d=production_settings,
                pixel_mapping=calibration.pixel_mapping(self.camera, production_settings),
                intrinsics=calibration.intrinsics(
                    self.camera, production_settings.color if production_settings.color else production_settings
                ),
            ),
            hand_eye=SettingsPixelMappingIntrinsics(
                settings_2d3d=hand_eye_settings,
                pixel_mapping=calibration.pixel_mapping(self.camera, hand_eye_settings),
                intrinsics=calibration.intrinsics(
                    self.camera, hand_eye_settings.color if hand_eye_settings.color else hand_eye_settings
                ),
            ),
            infield_correction=SettingsPixelMappingIntrinsics(
                settings_2d3d=infield_correction_settings,
                pixel_mapping=calibration.pixel_mapping(self.camera, infield_correction_settings),
                intrinsics=calibration.intrinsics(
                    self.camera,
                    (
                        infield_correction_settings.color
                        if infield_correction_settings.color
                        else infield_correction_settings
                    ),
                ),
            ),
        )
        self.settings_for_hand_eye_gui.show_dialog = self.show_dialog_checkbox.isChecked()
        self.settings_for_hand_eye_gui.save_choice()
        super().accept()

    def reject(self):
        if self.next_page():
            return
        self.manual_widget.reject()
        super().reject()

    def get_result(self) -> SettingsForHandEyeGUI:
        return self.settings_for_hand_eye_gui


def select_settings_for_hand_eye(
    camera: zivid.Camera, initial_settings: Optional[SettingsForHandEyeGUI] = None, show_anyway: bool = False
) -> SettingsForHandEyeGUI:
    current_settings = initial_settings or SettingsForHandEyeGUI()
    if not _connect_if_not_connected(camera):
        raise RuntimeError("Cannot configure Hand-Eye settings without camera connected")
    settings_are_valid_for_this_camera = validate_settings(
        camera, current_settings.production.settings_2d3d, show_message_box=False
    )
    if not current_settings.show_dialog and not show_anyway and settings_are_valid_for_this_camera:
        return current_settings
    settings_selector = SettingsSelectionDialog(camera, current_settings.show_dialog)
    settings_selector.exec_()
    return settings_selector.get_result()
