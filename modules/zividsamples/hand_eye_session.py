"""
Read and write hand-eye data in the Zivid Studio Hand-Eye session format.

Zivid Studio stores a hand-eye calibration as a session folder on disk. This module is a small,
GUI-free reader and writer for that same on-disk layout, so console samples produce data that Zivid
Studio can open, and can read data that Studio (or another session-format sample) produced.

The session layout this module reads and writes is:

    <session>/
      session.yml                               # session metadata (see HandEyeSession)
      Calibration/
        robot_pose_NN.yaml                       # 4x4 robot pose, millimeters (Zivid Matrix4x4 YAML)
        calibration_object_pose_NN.zdf           # the capture at that pose
        hand_eye_transform.yaml                  # the calibrated transform (Zivid Matrix4x4 YAML)
        hand_eye_residuals.yaml                  # per-pose residuals
      pose_pair_selection.yaml                   # pose IDs excluded from the calibration
      Warmup/  Infield/
      Calibration/Verification-{Projection,Stitching,Touch}/

Pose IDs start at 1 and the file suffix is the ID zero-padded to at least two digits (robot_pose_01,
robot_pose_02, ... robot_pose_100). Sessions from the Python Hand-Eye GUI use unpadded suffixes
(robot_pose_1); those are read as well. The authoritative robot pose for computation is always the
4x4 matrix in robot_pose_NN.yaml.

This module does not implement the live Studio session manager (no fixed-objects, verification or
warmup writers); it covers the data a calibration sample produces and consumes.

For more information about hand-eye calibration, check out:
https://support.zivid.com/en/latest/academy/applications/hand-eye.html

"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from json import dumps as json_quote
from json import loads as json_parse
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import yaml
import zivid
from zividsamples.save_load_matrix import assert_affine_matrix_and_save, load_and_assert_affine_matrix
from zividsamples.save_residuals import save_residuals

SESSION_FILE_NAME = "session.yml"
LEGACY_SESSION_FILE_NAME = "session_info.json"
SESSION_DATAMODEL_VERSION = 1
DATE_FORMAT = "%Y%m%d_%H%M%S"

CALIBRATION_SUBFOLDER = "Calibration"
SESSION_SUBFOLDERS = [
    "Warmup",
    "Infield",
    CALIBRATION_SUBFOLDER,
    f"{CALIBRATION_SUBFOLDER}/Verification-Projection",
    f"{CALIBRATION_SUBFOLDER}/Verification-Stitching",
    f"{CALIBRATION_SUBFOLDER}/Verification-Touch",
]

HAND_EYE_TRANSFORM_FILE_NAME = "hand_eye_transform.yaml"
HAND_EYE_RESIDUALS_FILE_NAME = "hand_eye_residuals.yaml"
POSE_PAIR_SELECTION_FILE_NAME = "pose_pair_selection.yaml"


class CalibrationObjectType(Enum):
    """Calibration object the session was collected with."""

    CHECKERBOARD = "checkerboard"
    MARKERS = "markers"


class RotationFormat(Enum):
    """Rotation representation used for a robot pose, matching the Studio session values."""

    EULER = "euler"
    ANGLE_AXIS = "angleAxis"
    ROTATION_VECTOR = "rotationVector"
    QUATERNION = "quaternion"
    ROTATION_MATRIX = "rotationMatrix"


@dataclass
class MarkerConfiguration:
    """Marker-based calibration object configuration (only meaningful for CalibrationObjectType.MARKERS)."""

    dictionary: str = ""
    marker_ids: List[int] = field(default_factory=list)


@dataclass
class RobotPoseRotation:
    """The rotation format last selected in the UI; the default for new poses only.

    Each pose stores its own 4x4 matrix, so this never overrides stored pose data.
    """

    rotation_format: RotationFormat = RotationFormat.QUATERNION
    euler_sequence: str = "XYZ"
    intrinsic: bool = True
    degrees: bool = True
    quaternion_scalar_first: bool = False


@dataclass
class PosePair:
    """One captured (robot pose, calibration-object capture) sample from a session."""

    pose_id: int
    robot_pose: np.ndarray
    frame_path: Path


def _now_stamp() -> str:
    """Return the current time formatted as the session timestamp.

    Returns:
        Current local time formatted yyyyMMdd_HHmmss

    """
    return datetime.now().strftime(DATE_FORMAT)


def _session_date(value: object) -> str:
    """Return a session timestamp as text, also when YAML parsed an unquoted one as an integer.

    YAML 1.1 allows "_" in integers, so an unquoted 20261111_101010 is read as 20261111101010.

    Args:
        value: Timestamp as read from session.yml

    Returns:
        Timestamp formatted yyyyMMdd_HHmmss

    """
    text = str(value)
    if isinstance(value, int):
        text = f"{text[:8]}_{text[8:]}"
    datetime.strptime(text, DATE_FORMAT)
    return text


def _yaml_bool(value: bool) -> str:
    """Format a boolean the way the Zivid datamodel serializer does.

    Args:
        value: Boolean to format

    Returns:
        "yes" or "no"

    """
    return "yes" if value else "no"


def _pose_suffix(pose_id: int) -> str:
    """Format a pose ID as the file suffix (zero-padded to at least two digits).

    Args:
        pose_id: Positive pose identifier

    Returns:
        Zero-padded pose suffix, e.g. "01" or "100"

    """
    return f"{pose_id:02d}"


def _pose_suffix_from_path(path: Path) -> str:
    """Extract the pose suffix from a session file name, exactly as written.

    Zivid Studio and this module zero-pad the suffix (robot_pose_01), while the Python Hand-Eye GUI
    does not (robot_pose_1), so the suffix is kept as text to find the matching capture.

    Args:
        path: File path whose stem ends in _<suffix>

    Returns:
        The pose suffix, e.g. "01" or "1"

    """
    return path.stem.rsplit("_", 1)[1]


@dataclass
class HandEyeSession:
    """A Zivid Studio hand-eye session on disk.

    Create a new session with `create`, or open an existing one with `open`. Pose pairs, the
    calibrated transform and its residuals are written into the Calibration subfolder.
    """

    root: Path
    name: str
    created_date: str
    last_modified_date: str
    eye_in_hand: bool = True
    low_dof: bool = False
    calibration_object: CalibrationObjectType = CalibrationObjectType.CHECKERBOARD
    marker_configuration: MarkerConfiguration = field(default_factory=MarkerConfiguration)
    robot_pose_rotation: RobotPoseRotation = field(default_factory=RobotPoseRotation)

    @classmethod
    def create(
        cls,
        root: Path,
        eye_in_hand: bool,
        *,
        calibration_object: CalibrationObjectType = CalibrationObjectType.CHECKERBOARD,
        marker_configuration: Optional[MarkerConfiguration] = None,
        low_dof: bool = False,
        name: Optional[str] = None,
    ) -> "HandEyeSession":
        """Create a new session folder with its subfolders and session.yml.

        Args:
            root: Session folder to create (its name becomes the session name unless `name` is given)
            eye_in_hand: True for eye-in-hand, False for eye-to-hand
            calibration_object: Calibration object type used in this session
            marker_configuration: Marker configuration, required for CalibrationObjectType.MARKERS
            low_dof: True for low-DOF calibration against a fixed calibration object
            name: Human-readable session name; defaults to the folder name

        Returns:
            The created session

        Raises:
            RuntimeError: If the folder already holds a session

        """
        root = Path(root)
        if (root / SESSION_FILE_NAME).exists():
            raise RuntimeError(f"{root} already holds a hand-eye session; choose a new folder")
        stamp = _now_stamp()
        session = cls(
            root=root,
            name=name if name is not None else root.name,
            created_date=stamp,
            last_modified_date=stamp,
            eye_in_hand=eye_in_hand,
            low_dof=low_dof,
            calibration_object=calibration_object,
            marker_configuration=marker_configuration if marker_configuration is not None else MarkerConfiguration(),
        )
        for subfolder in SESSION_SUBFOLDERS:
            (root / subfolder).mkdir(parents=True, exist_ok=True)
        session.save()
        return session

    @classmethod
    def open(cls, root: Path) -> "HandEyeSession":
        """Open an existing session folder.

        Reads session.yml, or imports a legacy session_info.json if that is all that exists.

        Args:
            root: Existing session folder

        Returns:
            The opened session

        Raises:
            RuntimeError: If the folder holds neither session.yml nor session_info.json

        """
        root = Path(root)
        session_file = root / SESSION_FILE_NAME
        if session_file.exists():
            return cls._from_session_yml(root, session_file)
        legacy_file = root / LEGACY_SESSION_FILE_NAME
        if legacy_file.exists():
            return cls._from_legacy_json(root, legacy_file)
        raise RuntimeError(f"{root} is not a hand-eye session folder (no {SESSION_FILE_NAME})")

    @classmethod
    def _from_session_yml(cls, root: Path, session_file: Path) -> "HandEyeSession":
        with open(session_file, encoding="utf-8") as file:
            model = yaml.safe_load(file)["HandEyeSession"]
        marker_model = model.get("MarkerConfiguration") or {}
        rotation_model = model.get("RobotPoseRotation") or {}
        return cls(
            root=root,
            name=model["SessionName"],
            created_date=_session_date(model["CreatedDate"]),
            last_modified_date=_session_date(model["LastModifiedDate"]),
            eye_in_hand=bool(model["EyeInHand"]),
            low_dof=bool(model["LowDof"]),
            calibration_object=CalibrationObjectType(model["CalibrationObject"]),
            marker_configuration=MarkerConfiguration(
                dictionary=marker_model.get("Dictionary", ""),
                marker_ids=list(marker_model.get("MarkerIds") or []),
            ),
            robot_pose_rotation=RobotPoseRotation(
                rotation_format=RotationFormat(rotation_model.get("Format", RotationFormat.QUATERNION.value)),
                euler_sequence=rotation_model.get("EulerSequence", "XYZ"),
                intrinsic=bool(rotation_model.get("Intrinsic", True)),
                degrees=bool(rotation_model.get("Degrees", True)),
                quaternion_scalar_first=bool(rotation_model.get("QuaternionScalarFirst", False)),
            ),
        )

    @classmethod
    def _from_legacy_json(cls, root: Path, legacy_file: Path) -> "HandEyeSession":
        model = json_parse(legacy_file.read_text(encoding="utf-8"))
        configuration = model.get("hand_eye_configuration")
        if configuration is None or "eye_in_hand" not in configuration or "calibration_object" not in configuration:
            raise RuntimeError(
                f"{legacy_file} does not say whether the session is eye-in-hand and which calibration object it "
                "uses; open the session in the Python Hand-Eye GUI and capture a pose pair to save it"
            )
        calibration_object = {
            "Checkerboard": CalibrationObjectType.CHECKERBOARD,
            "Markers": CalibrationObjectType.MARKERS,
        }[configuration["calibration_object"]]
        return cls(
            root=root,
            name=model["name"],
            created_date=model["created_date"],
            last_modified_date=model["last_modified_date"],
            eye_in_hand=bool(configuration["eye_in_hand"]),
            calibration_object=calibration_object,
            marker_configuration=MarkerConfiguration(
                dictionary=configuration.get("marker_dictionary") or "",
                marker_ids=list(configuration.get("marker_ids") or []),
            ),
        )

    @property
    def calibration_dir(self) -> Path:
        """Path to the session's Calibration subfolder.

        Returns:
            The Calibration subfolder path

        """
        return self.root / CALIBRATION_SUBFOLDER

    def save(self) -> None:
        """Write session.yml, refreshing the last-modified timestamp."""
        self.last_modified_date = _now_stamp()
        (self.root / SESSION_FILE_NAME).write_text(self._to_session_yaml(), encoding="utf-8")

    def _to_session_yaml(self) -> str:
        lines = [
            f"__version__: {SESSION_DATAMODEL_VERSION}",
            "HandEyeSession:",
            f"  SessionName: {json_quote(self.name)}",
            f"  CreatedDate: {json_quote(self.created_date)}",
            f"  LastModifiedDate: {json_quote(self.last_modified_date)}",
            f"  EyeInHand: {_yaml_bool(self.eye_in_hand)}",
            f"  LowDof: {_yaml_bool(self.low_dof)}",
            f"  CalibrationObject: {self.calibration_object.value}",
            "  MarkerConfiguration:",
            f"    Dictionary: {json_quote(self.marker_configuration.dictionary)}",
        ]
        marker_ids = ", ".join(str(marker_id) for marker_id in self.marker_configuration.marker_ids)
        lines.append(f"    MarkerIds: [{marker_ids}]")
        rotation = self.robot_pose_rotation
        lines.extend(
            [
                "  RobotPoseRotation:",
                f"    Format: {rotation.rotation_format.value}",
                f"    EulerSequence: {json_quote(rotation.euler_sequence)}",
                f"    Intrinsic: {_yaml_bool(rotation.intrinsic)}",
                f"    Degrees: {_yaml_bool(rotation.degrees)}",
                f"    QuaternionScalarFirst: {_yaml_bool(rotation.quaternion_scalar_first)}",
            ]
        )
        return "\n".join(lines) + "\n"

    def save_pose_pair(self, pose_id: int, robot_pose: np.ndarray, frame: zivid.Frame) -> None:
        """Save one pose pair (robot pose and calibration-object capture) into Calibration.

        Args:
            pose_id: Positive pose identifier; its files are suffixed with this ID
            robot_pose: 4x4 robot pose in millimeters
            frame: The capture of the calibration object at this robot pose

        """
        suffix = _pose_suffix(pose_id)
        assert_affine_matrix_and_save(robot_pose, self.calibration_dir / f"robot_pose_{suffix}.yaml")
        frame.save(self.calibration_dir / f"calibration_object_pose_{suffix}.zdf")

    def load_pose_pairs(self) -> List[PosePair]:
        """Load the complete pose pairs in the Calibration folder, sorted by pose ID.

        A pose pair is complete when both robot_pose_NN.yaml and calibration_object_pose_NN.zdf exist.
        Pose pairs excluded in pose_pair_selection.yaml (for example in Zivid Studio) are left out.

        Returns:
            Pose pairs sorted by ascending pose ID

        """
        excluded_pose_ids = set(self.load_excluded_pose_ids())
        pose_pairs = []
        for pose_path in self.calibration_dir.glob("robot_pose_*.yaml"):
            suffix = _pose_suffix_from_path(pose_path)
            if not suffix.isdigit():
                continue
            pose_id = int(suffix)
            if pose_id in excluded_pose_ids:
                continue
            frame_path = self.calibration_dir / f"calibration_object_pose_{suffix}.zdf"
            if not frame_path.exists():
                continue
            pose_pairs.append(
                PosePair(
                    pose_id=pose_id,
                    robot_pose=load_and_assert_affine_matrix(pose_path),
                    frame_path=frame_path,
                )
            )
        return sorted(pose_pairs, key=lambda pair: pair.pose_id)

    def save_calibration_result(self, result: zivid.calibration.HandEyeOutput) -> None:
        """Save the calibrated transform and its per-pose residuals into Calibration.

        Args:
            result: A valid hand-eye calibration result

        """
        assert_affine_matrix_and_save(result.transform(), self.calibration_dir / HAND_EYE_TRANSFORM_FILE_NAME)
        save_residuals(result.residuals(), self.calibration_dir / HAND_EYE_RESIDUALS_FILE_NAME)

    def load_hand_eye_transform(self) -> np.ndarray:
        """Load the calibrated hand-eye transform.

        Returns:
            The 4x4 hand-eye transform

        """
        return load_and_assert_affine_matrix(self.calibration_dir / HAND_EYE_TRANSFORM_FILE_NAME)

    def load_excluded_pose_ids(self) -> List[int]:
        """Read the pose IDs excluded from the calibration.

        Returns:
            Excluded pose IDs, or an empty list if no selection file exists

        """
        selection_file = self.root / POSE_PAIR_SELECTION_FILE_NAME
        if not selection_file.exists():
            return []
        with open(selection_file, encoding="utf-8") as file:
            selection: Dict = yaml.safe_load(file) or {}
        return list(selection.get("excluded") or [])
