"""
Automatically find 2D acquisition settings for a 2D capture using a Zivid calibration board.

This sample uses the Zivid calibration board (ZVDA-CB01) to find acquisition settings (exposure time, aperture and gain)
for a 2D capture automatically, given the ambient light in the scene. It calibrates against the white squares on the
checkerboard, trying to find acquisition settings so that the intensity values on the white squares are roughly the same
as the true whites of the checkerboard. The projector is turned OFF when finding 2D acquisition settings, meaning it will
calibrate with the ambient light present in the scene you are capturing.

Place the calibration board at the furthest or closest distance you want to image, and make sure the calibration board
is in view of the camera. Be aware that very low, very high or uneven ambient light may make it difficult to detect the
calibration board checkers and find good settings.

Change the steps in _adjust_acquisition_settings_2d() if you want to re-prioritize which acquisition settings to tune first.

"""

import argparse
from datetime import timedelta
from pathlib import Path
from typing import Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import zivid


def _options() -> argparse.Namespace:
    """Configure and take command line arguments from user.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(
        description=(
            "Find 2D capture settings automatically with a Zivid calibration board\n"
            "Example:\n"
            "\t1) $ python auto_2d_acquisition_settings.py --dfr 500 --s\n"
            "\t2) $ python auto_2d_acquisition_settings.py --dfr 500 --e\n\n"
            "In 1), the desired focus range starts at the checkerboard and goes 500mm away from the camera.\n"
            "In 2), the desired focus range ends at the checkerboard and goes 500mm towards the camera."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--dfr",
        "--desired-focus-range",
        type=float,
        required=True,
        dest="desired_focus_range",
        help="Distance from checkerboard that should be in focus",
    )

    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument(
        "--s",
        "--checkerboard-at-start-of-range",
        dest="checkerboard_at_start_of_range",
        help="Set checkerboard to closest imaging distance",
        action="store_true",
    )
    type_group.add_argument(
        "--e",
        "--checkerboard-at-end-of-range",
        dest="checkerboard_at_end_of_range",
        help="Set checkerboard to farthest imaging distance",
        action="store_true",
    )

    return parser.parse_args()


def _capture_rgb(camera: zivid.Camera, settings_2d: zivid.Settings2D) -> np.ndarray:
    """Capture a 2D image and extract RGB values.

    Args:
        camera: Zivid camera
        settings_2d: Zivid 2D capture settings

    Returns:
        rgb: RGB image (H, W, 3)

    """
    rgb = camera.capture(settings_2d).image_rgba().copy_data()[:, :, :3]
    return rgb


def _capture_assistant_settings(camera: zivid.Camera) -> zivid.Settings:
    """Get settings from capture assistant.

    Args:
        camera: Zivid camera

    Returns:
        Zivid 3D capture settings from capture assistant

    """
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=timedelta(milliseconds=1200),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    return zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)


def _detect_checkerboard(rgb: np.ndarray) -> np.ndarray:
    """Use OpenCV to detect corner coordinates of a (7, 8) checkerboard.

    Args:
        rgb: RGB image (H, W, 3)

    Raises:
        RuntimeError: If checkerboard cannot be detected in image

    Returns:
        Array ((rows-1), (cols-1), 2) of inner-corner coordinates

    """
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    checkerboard_size = (7, 8)
    checkerboard_size_opencv = (checkerboard_size[1] - 1, checkerboard_size[0] - 1)
    chessboard_flags = cv2.CALIB_CB_ACCURACY | cv2.CALIB_CB_EXHAUSTIVE

    success, corners = cv2.findChessboardCornersSB(grayscale, checkerboard_size_opencv, chessboard_flags)
    if not success:
        # Trying histogram equalization for more contrast
        grayscale_equalized = cv2.equalizeHist(grayscale)
        success, corners = cv2.findChessboardCornersSB(grayscale_equalized, checkerboard_size_opencv, chessboard_flags)

    if corners is None:
        raise RuntimeError("Failed to detect checkerboard in image.")

    return corners.flatten().reshape(checkerboard_size_opencv[1], checkerboard_size_opencv[0], 2)


def _get_mask_from_polygons(polygons: np.ndarray, shape: Tuple) -> np.ndarray:
    """Make mask on each channel for pixels filled by polygons.

    Args:
        polygons: (N, 4, 1, 2) array of polygon vertices
        shape: (H, W) of mask

    Returns:
        mask: Mask of bools (H, W), True for pixels fill by polygons

    """
    mask = np.zeros(shape[:2])
    cv2.fillPoly(mask, polygons, 1)
    mask[0, 0] = 0
    return mask


def _make_white_squares_mask(checkerboard_corners: np.ndarray, image_shape: Tuple) -> np.ndarray:
    """Make mask of bools covering pixels containing white checkerboard squares. True for pixels with white checkers,
    False otherwise.

    Args:
        checkerboard_corners: ((rows-1), (cols-1), 2) float array of inner-corner coordinates
        image_shape: (H, W)

    Returns:
        white_squares_mask: Mask of bools (H, W) for pixels containing white checkerboard squares

    """
    number_of_white_squares = (checkerboard_corners.shape[0] // 2) * checkerboard_corners.shape[1]
    white_vertices = np.zeros((number_of_white_squares, 4, 1, 2), dtype=np.int32)
    i = 0
    for row in range(checkerboard_corners.shape[0] - 1):
        for col in range(checkerboard_corners.shape[1] - 1):
            if ((row % 2 == 0) and (col % 2 == 0)) or ((row % 2 == 1) and (col % 2 == 1)):
                white_vertices[i, 0, 0, :] = checkerboard_corners[row, col, :]
                white_vertices[i, 1, 0, :] = checkerboard_corners[row, col + 1, :]
                white_vertices[i, 2, 0, :] = checkerboard_corners[row + 1, col + 1, :]
                white_vertices[i, 3, 0, :] = checkerboard_corners[row + 1, col, :]

                i = i + 1

    white_squares_mask = _get_mask_from_polygons(white_vertices, image_shape)

    return white_squares_mask


def _find_white_mask_from_checkerboard(camera: zivid.Camera) -> Tuple[np.ndarray, float]:
    """Generate a 2D mask of the white checkers on a checkerboard and calculate the distance to it.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If either cannot calculate pose or find checkerboard in image

    Returns:
        white_squares_mask: Mask of bools (H, W) for pixels containing white checkerboard squares
        distance_to_checkerboard: Translation in z from the camera to the checkerboard center

    """
    try:
        settings = _capture_assistant_settings(camera)
        point_cloud = camera.capture(settings).point_cloud()

        checkerboard_pose = zivid.calibration.detect_feature_points(point_cloud).pose().to_matrix()
        distance_to_checkerboard = checkerboard_pose[2, 3]

        rgb = point_cloud.copy_data("rgba")[:, :, :3]
        checkerboard_corners = _detect_checkerboard(rgb)
        white_squares_mask = _make_white_squares_mask(checkerboard_corners, rgb.shape)
    except RuntimeError as exc:
        raise RuntimeError("Unable to find checkerboard, make sure it is in view of the camera.") from exc

    return white_squares_mask, distance_to_checkerboard


def _find_lowest_acceptable_fnum(camera: zivid.Camera, image_distance_near: float, image_distance_far: float) -> float:
    """Find the lowest f-number that gives a focused image, using the camera model and desired focus range.

    Args:
        camera: Zivid camera
        image_distance_near: Closest distance from camera that should be in focus
        image_distance_far: Furthest distance from camera that should be in focus

    Raises:
        RuntimeError: If camera model is not supported

    Returns:
        Lowest acceptable f-number that gives a focused image

    """
    if camera.info.model == zivid.CameraInfo.Model.zividOnePlusSmall:
        focus_distance = 500
        focal_length = 16
        if image_distance_near < 300 or image_distance_far > 1000:
            print(
                f"WARNING: Closest imaging distance ({image_distance_near:.2f}) or farthest imaging distance"
                f"({image_distance_far:.2f}) is outside recommended working distance for camera [300, 1000]"
            )
    elif camera.info.model == zivid.CameraInfo.Model.zividOnePlusMedium:
        focus_distance = 1000
        focal_length = 16
        if image_distance_near < 500 or image_distance_far > 2000:
            print(
                f"WARNING: Closest imaging distance ({image_distance_near:.2f}) or farthest imaging distance"
                f"({image_distance_far:.2f}) is outside recommended working distance for camera [500, 2000]"
            )
    elif camera.info.model == zivid.CameraInfo.Model.zividOnePlusLarge:
        focus_distance = 1800
        focal_length = 16
        if image_distance_near < 1200 or image_distance_far > 3000:
            print(
                f"WARNING: Closest imaging distance ({image_distance_near:.2f}) or farthest imaging distance"
                f"({image_distance_far:.2f}) is outside recommended working distance for camera [1200, 3000]"
            )
    elif camera.info.model == zivid.CameraInfo.Model.zividTwo:
        focus_distance = 700
        focal_length = 8
        if image_distance_near < 300 or image_distance_far > 1300:
            print(
                f"WARNING: Closest imaging distance ({image_distance_near:.2f}) or farthest imaging distance"
                f"({image_distance_far:.2f}) is outside recommended working distance for camera [300, 1300]"
            )
    elif camera.info.model == zivid.CameraInfo.Model.zividTwoL100:
        focus_distance = 1000
        focal_length = 8
        if image_distance_near < 600 or image_distance_far > 1600:
            print(
                f"WARNING: Closest imaging distance ({image_distance_near:.2f}) or farthest imaging distance"
                f"({image_distance_far:.2f}) is outside recommended working distance for camera [600, 1600]"
            )
    else:
        raise RuntimeError("Unsupported camera model in this sample.")

    circle_of_confusion = 0.015

    fnum_near = (
        np.abs(image_distance_near - focus_distance)
        / image_distance_near
        * (focal_length**2 / (circle_of_confusion * (focus_distance - focal_length)))
    )
    fnum_far = (
        np.abs(image_distance_far - focus_distance)
        / image_distance_far
        * (focal_length**2 / (circle_of_confusion * (focus_distance - focal_length)))
    )

    fnum_near = min(max(fnum_near, 1), 32)
    fnum_far = min(max(fnum_far, 1), 32)

    return max(fnum_near, fnum_far, 1.8)


def _find_lowest_exposure_time(camera: zivid.Camera) -> float:
    """Find the lowest exposure time [us] that a given camera can provide.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If camera model is not supported

    Returns:
        Lowest exposure time [us] for given camera

    """
    if camera.info.model == zivid.CameraInfo.Model.zividOnePlusSmall:
        exposure_time = 6500
    elif camera.info.model == zivid.CameraInfo.Model.zividOnePlusMedium:
        exposure_time = 6500
    elif camera.info.model == zivid.CameraInfo.Model.zividOnePlusLarge:
        exposure_time = 6500
    elif camera.info.model == zivid.CameraInfo.Model.zividTwo:
        exposure_time = 1677
    elif camera.info.model == zivid.CameraInfo.Model.zividTwoL100:
        exposure_time = 1677
    else:
        raise RuntimeError("Unsupported camera model in this sample.")

    return exposure_time


def _initialize_settings_2d(aperture: float, exposure_time: float, brightness: float, gain: float) -> zivid.Settings2D:
    """Initialize 2D capture settings.

    Args:
        aperture: Aperture
        exposure_time: Exposure time
        brightness: Projector brightness
        gain: Analog gain

    Returns:
        Zivid 2D capture settings

    """
    return zivid.Settings2D(
        acquisitions=[
            zivid.Settings2D.Acquisition(
                aperture=aperture,
                exposure_time=timedelta(microseconds=exposure_time),
                brightness=brightness,
                gain=gain,
            )
        ],
        processing=zivid.Settings2D.Processing(
            zivid.Settings2D.Processing.Color(gamma=1, balance=zivid.Settings2D.Processing.Color.Balance(1, 1, 1))
        ),
    )


def _compute_max_mean_rgb_from_mask(rgb: np.ndarray, mask: np.ndarray) -> float:
    """Find the maximum value of the mean RGB channels in the masked area of an RGB image.

    Args:
        rgb: (H, W, 3) RGB image
        mask: (H, W) of bools masking the image

    Returns:
        Value of the highest averaged RGB channel from the masked area

    """
    repeated_mask = ~np.repeat(mask[:, :, np.newaxis], rgb.shape[2], axis=2).astype(bool)
    mean_rgb = np.ma.masked_array(rgb, repeated_mask).mean(axis=(0, 1))

    return max(mean_rgb)


def _adjust_acquisition_settings_2d(
    settings_2d: zivid.Settings2D,
    adjustment_factor: float,
    tuning_index: int,
    min_fnum: float,
    min_exposure_time: float,
) -> Tuple[zivid.Settings2D, int]:
    """Iteratively call this function with current adjustment_factor to get the next acquisition settings. The
    algorithm transitions through the following steps if the limit in each step is reached:
        Step 1: Change f-number (min: min_fnum, max: 32)
        Step 2: Change gain (min: 1, max: 2)
        Step 3: Change exposure time (min: min_exposure_time, max: 20000)
        Step 4: Change gain (min: 1, max: 4)
        Step 5: Change exposure time (min: min_exposure_time, max: 100000)
        Step 6: Change gain (min: 1, max: 16)

    Args:
        settings_2d: Zivid 2D settings
        adjustment_factor: Factor to adjust acquisition settings
        tuning_index: Current step in algorithm
        min_fnum: Lower f-number limit
        min_exposure_time: Lower exposure time limit for specific camera

    Returns:
        settings_2d: Updated Zivid 2D settings
        tuning_index: Updated tuning index

    """
    if tuning_index == 1:
        new_aperture = np.clip(settings_2d.acquisitions[0].aperture / adjustment_factor, min_fnum, 32)
        settings_2d.acquisitions[0].aperture = new_aperture
        if new_aperture in (min_fnum, 32):
            tuning_index = 2

    elif tuning_index == 2:
        max_gain = 2
        new_gain = np.clip(settings_2d.acquisitions[0].gain * adjustment_factor, 1, max_gain)
        settings_2d.acquisitions[0].gain = new_gain
        if new_gain in (1, max_gain):
            tuning_index = 3

    elif tuning_index == 3:
        max_exposure_time = 20000
        new_exposure_time = timedelta(
            microseconds=np.clip(
                settings_2d.acquisitions[0].exposure_time.microseconds * adjustment_factor,
                min_exposure_time,
                max_exposure_time,
            )
        )
        settings_2d.acquisitions[0].exposure_time = new_exposure_time
        if new_exposure_time in (
            timedelta(microseconds=min_exposure_time),
            timedelta(microseconds=max_exposure_time),
        ):
            tuning_index = 4

    elif tuning_index == 4:
        max_gain = 4
        new_gain = np.clip(settings_2d.acquisitions[0].gain * adjustment_factor, 1, max_gain)
        settings_2d.acquisitions[0].gain = new_gain
        if new_gain in (1, max_gain):
            tuning_index = 5

    elif tuning_index == 5:
        max_exposure_time = 100000
        new_exposure_time = timedelta(
            microseconds=np.clip(
                settings_2d.acquisitions[0].exposure_time.microseconds * adjustment_factor,
                min_exposure_time,
                max_exposure_time,
            )
        )
        settings_2d.acquisitions[0].exposure_time = new_exposure_time
        if new_exposure_time in (
            timedelta(microseconds=min_exposure_time),
            timedelta(microseconds=max_exposure_time),
        ):
            tuning_index = 6

    elif tuning_index == 6:
        max_gain = 16
        new_gain = np.clip(settings_2d.acquisitions[0].gain * adjustment_factor, 1, max_gain)
        settings_2d.acquisitions[0].gain = new_gain
        if new_gain in (1, max_gain):
            tuning_index = 1

    return settings_2d, tuning_index


def _find_2d_settings_from_mask(camera: zivid.Camera, white_mask: np.ndarray, min_fnum: float) -> zivid.Settings2D:
    """Find 2D acquisition settings automatically from the masked area of white in a RGB image.

    Args:
        camera: Zivid camera
        white_mask: Mask of bools (H, W) for pixels containing the white object to calibrate to
        min_fnum: Lower limit on f-number for the calibrated settings

    Raises:
        RuntimeError: If unable to find settings after sufficient number of tries

    Returns:
        settings_2d: Zivid 2D settings

    """
    min_exposure_time = _find_lowest_exposure_time(camera)

    settings_2d = _initialize_settings_2d(aperture=8, exposure_time=min_exposure_time, brightness=0, gain=1)

    lower_white_range = 210
    upper_white_range = 215
    target_white = np.mean([lower_white_range, upper_white_range])

    tuning_index = 1
    count = 1
    found_final_2d_settings = False
    while not found_final_2d_settings:
        rgb = _capture_rgb(camera, settings_2d)
        max_mean_color = _compute_max_mean_rgb_from_mask(rgb, white_mask)
        if lower_white_range <= max_mean_color <= upper_white_range:
            found_final_2d_settings = True
        else:
            adjustment_factor = float(target_white / max_mean_color)
            settings_2d, tuning_index = _adjust_acquisition_settings_2d(
                settings_2d, adjustment_factor, tuning_index, min_fnum, min_exposure_time
            )

        count = count + 1
        if count > 20:
            raise RuntimeError("Unable to find settings in current lighting")

    return settings_2d


def _print_poor_pixel_distribution(rgb: np.ndarray) -> None:
    """Print distribution of bad pixels (saturated or completely black) in an RGB image.

    Args:
        rgb: RGB image (H, W, 3)

    """
    total_num_pixels = rgb.shape[0] * rgb.shape[1]

    saturated_or = np.sum(np.logical_or(np.logical_or(rgb[:, :, 0] == 255, rgb[:, :, 1] == 255), rgb[:, :, 2] == 255))
    saturated_and = np.sum(
        np.logical_and(np.logical_and(rgb[:, :, 0] == 255, rgb[:, :, 1] == 255), rgb[:, :, 2] == 255)
    )

    black_or = np.sum(np.logical_or(np.logical_or(rgb[:, :, 0] == 0, rgb[:, :, 1] == 0), rgb[:, :, 2] == 0))
    black_and = np.sum(np.logical_and(np.logical_and(rgb[:, :, 0] == 0, rgb[:, :, 1] == 0), rgb[:, :, 2] == 0))

    print("Distribution of saturated (255) and black (0) pixels with final settings:")
    print(f"Saturated pixels (at least one channel): {saturated_or}\t ({100*saturated_or/total_num_pixels:.2f}%)")
    print(f"Saturated pixels (all channels):\t {saturated_and}\t ({100*saturated_and/total_num_pixels:.2f}%)")
    print(f"Black pixels (at least one channel):\t {black_or}\t ({100*black_or/total_num_pixels:.2f}%)")
    print(f"Black pixels (all channels):\t\t {black_and}\t ({100*black_and/total_num_pixels:.2f}%)")


def _plot_image_with_histogram(rgb: np.ndarray, settings_2d: zivid.Settings2D) -> None:
    """Show an RGB image with its histogram (grayscale) in linear scale.

    Args:
        rgb: RGB image (H, W, 3)
        settings_2d: Zivid 2D settings

    """
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    grayscale_raveled = grayscale.ravel()

    fig, axs = plt.subplots(2, 1, figsize=(8, 8), gridspec_kw={"height_ratios": [1, 3]})

    exposure_time = settings_2d.acquisitions[0].exposure_time.microseconds
    aperture = settings_2d.acquisitions[0].aperture
    brightness = settings_2d.acquisitions[0].brightness
    gain = settings_2d.acquisitions[0].gain

    fig.suptitle(
        f"Histogram and image with acquisition settings:\nET: {exposure_time}, A: {aperture:.2f}, B: {brightness}, G: {gain:.2f}"
    )

    axs[0].hist(grayscale_raveled, bins=np.arange(0, 256), color="gray")
    axs[0].yaxis.set_visible(False)

    axs[1].imshow(rgb)
    axs[1].xaxis.set_visible(False)
    axs[1].yaxis.set_visible(False)

    plt.show()


def _main() -> None:
    app = zivid.Application()

    user_options = _options()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Finding the white squares of the checkerboard as white reference ...")
    white_mask, checkerboard_distance = _find_white_mask_from_checkerboard(camera)

    # Determining lowest acceptable f-number to be in focus
    if user_options.checkerboard_at_start_of_range:
        image_distance_near = checkerboard_distance
        image_distance_far = image_distance_near + user_options.desired_focus_range
    else:
        image_distance_far = checkerboard_distance
        image_distance_near = image_distance_far - user_options.desired_focus_range

    min_fnum = _find_lowest_acceptable_fnum(camera, image_distance_near, image_distance_far)

    print("Finding 2D acquisition settings via white mask ...")
    settings_2d = _find_2d_settings_from_mask(camera, white_mask, min_fnum)

    print("Automatic 2D acquisition settings:")
    print(settings_2d.acquisitions[0])

    filename = "Automatic2DAcquisitionSettings.yml"
    print(f"Saving settings to: {Path().resolve() / filename}\n")
    settings_2d.save(filename)

    rgb = _capture_rgb(camera, settings_2d)

    _print_poor_pixel_distribution(rgb)
    _plot_image_with_histogram(rgb, settings_2d)


if __name__ == "__main__":
    _main()
