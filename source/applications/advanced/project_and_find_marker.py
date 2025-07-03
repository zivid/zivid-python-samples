"""
Show a marker using the projector, capture a set of 2D images to find the marker coordinates (2D and 3D).

This example shows how a marker can be projected onto a surface using the built-in projector. A 2D capture with
zero brightness is then used to capture an image with the marker. Finally position of the marker is detected,
allowing us to find the 3D coordinates relative to the camera.

"""

from datetime import timedelta
from typing import Tuple

import cv2
import numpy as np
import zivid
import zivid.projection


def _create_background_image(resolution: Tuple[int, int], background_color: Tuple[int, ...]) -> np.ndarray:
    """Create an image of one color.

    Args:
        resolution: (H,W) of image
        background_color: Color of image (RGB, RGBA, BGR, BGRA etc.)

    Returns:
        Image

    """
    return np.full(
        shape=(resolution[0], resolution[1], len(background_color)), fill_value=background_color, dtype=np.uint8
    )


def _create_marker(
    resolution: Tuple[int, int], marker_color: Tuple[int, ...], background_color: Tuple[int, ...]
) -> np.ndarray:
    """Create an image with a marker in the form of a cross.

    Args:
        resolution: (H,W) of image
        marker_color: Color of marker (RGB, RGBA, BGR, BGRA etc.)
        background_color: Color of image (RGB, RGBA, BGR, BGRA etc.)

    Returns:
        Marker image

    """
    marker = _create_background_image(resolution, background_color)
    marker_height, marker_width = marker.shape[:2]
    x = int(resolution[1] / 2)
    y = int(resolution[0] / 2)
    cv2.circle(marker, (x, y), 1, marker_color, -1)
    cv2.line(marker, (x, y + 5), (x, marker_height), marker_color, 1)
    cv2.line(marker, (x, y - 5), (x, 0), marker_color, 1)
    cv2.line(marker, (x + 5, y), (marker_width, y), marker_color, 1)
    cv2.line(marker, (x - 5, y), (0, y), marker_color, 1)

    return marker


def _copy_to_center(source_image: np.ndarray, destination_image: np.ndarray) -> None:
    """Copy source image over to center of destination image.

    Args:
        source_image: Source image
        destination_image: Destination image

    """
    center_x = (destination_image.shape[1] - source_image.shape[1]) // 2
    center_y = (destination_image.shape[0] - source_image.shape[0]) // 2

    area = (center_x, center_y, source_image.shape[1], source_image.shape[0])
    destination_image[area[1] : (area[1] + area[3]), area[0] : (area[0] + area[2])] = source_image


def _normalize(
    marker_image: np.ndarray, illuminated_scene_image: np.ndarray, non_illuminated_scene_image: np.ndarray
) -> np.ndarray:
    """Normalize marker image by an illuminated and non-illuminated background image.

    Args:
        marker_image: Marker image
        illuminated_scene_image: Image of illuminated scene
        non_illuminated_scene_image: Image of non-illuminated scene

    Returns:
        Normalized image

    """
    # We use the difference between the light and dark background images to normalize the marker image
    difference = illuminated_scene_image - non_illuminated_scene_image

    # Avoid divide-by-zero by ignoring pixels with little value difference
    difference_limit = 100
    invalid_difference = difference < difference_limit
    difference[invalid_difference] = 1

    normalized_image = (marker_image - non_illuminated_scene_image) / difference
    normalized_image[invalid_difference] = 0

    return normalized_image


def _cropped_gray_float_image(bgr: np.ndarray, crop_rows: int) -> np.ndarray:
    """Crop BGR image by crop_rows from top and bottom and convert it to float.

    Args:
        bgr: BGR image (H,W,3)
        crop_rows: Number of rows to crop in both directions

    Returns:
        Cropped image converted to float

    """
    rows = bgr.shape[0]
    cropped = bgr[crop_rows : (rows - crop_rows), :]

    gray_image = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    return gray_image.astype(np.float32)


def _projector_to_camera_scale_factor(camera_info: zivid.CameraInfo) -> float:
    """Ratio between camera resolution and projector resolution.

    Args:
        camera_info: Information about camera model, serial number etc.

    Raises:
        ValueError: If unsupported camera model for this code sample

    Returns:
        Ratio between camera resolution and projector resolution

    """
    # Note: these values are approximate and only for use in this demo
    model = camera_info.model
    if model in [zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100]:
        ratio = 1.52
    elif model in [
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ]:
        ratio = 2.47
    else:
        raise ValueError(f"Invalid camera model '{model}'")

    return ratio


def _get_color_settings_for_camera(camera: zivid.Camera) -> zivid.Settings2D.Sampling.Color:
    """Get sampling.color based on camera model.

    Args:
        camera: Zivid camera

    Returns:
        Sampling color to use for camera

    """
    if camera_supports_projection_brightness_boost(camera):
        return zivid.Settings2D.Sampling.Color.grayscale
    return zivid.Settings2D.Sampling.Color.rgb


def camera_supports_projection_brightness_boost(camera: zivid.Camera) -> bool:
    """Check if the given camera model supports the projection brightness boost feature.

    Args:
        camera (zivid.Camera): The Zivid camera instance to check

    Returns:
        bool: True if the camera supports brightness boost, False otherwise
    """
    model = camera.info.model

    return model in {
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    }


def find_max_projector_brightness(camera: zivid.Camera) -> float:
    """Return the maximum supported projector brightness for the given camera model.

    Ensures the configured brightness does not exceed what the camera model allows.
    Values are based on hardware model specifications.

    Args:
        camera (zivid.Camera): The Zivid camera instance to query

    Returns:
        float: The maximum brightness level supported by the projector
    """
    if camera.info.model in (
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ):
        return 2.5
    if camera.info.model in (
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusL110,
    ):
        return 2.2
    if camera.info.model in (zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100):
        return 1.8
    return 1.0


def _find_marker(
    projected_marker_frame_2d: zivid.Frame2D,
    illuminated_scene_frame_2d: zivid.Frame2D,
    non_illuminated_scene_frame_2d: zivid.Frame2D,
    marker_resolution: Tuple[int, int],
    camera_info: zivid.CameraInfo,
) -> Tuple[int, int]:
    """Locate marker coordinates in image.

    Args:
        projected_marker_frame_2d: 2D frame of scene with projected marker
        illuminated_scene_frame_2d: 2D frame of scene illuminated by projector
        non_illuminated_scene_frame_2d: 2D frame of scene not illuminated by projector
        marker_resolution: (H,W) of marker image
        camera_info: Information about camera model, serial number etc

    Returns:
        Marker coordinates (x,y) in image

    """
    cropped_rows = 400

    normalized_image = _normalize(
        _cropped_gray_float_image(projected_marker_frame_2d.image_bgra_srgb().copy_data()[:, :, :3], cropped_rows),
        _cropped_gray_float_image(illuminated_scene_frame_2d.image_bgra_srgb().copy_data()[:, :, :3], cropped_rows),
        _cropped_gray_float_image(non_illuminated_scene_frame_2d.image_bgra_srgb().copy_data()[:, :, :3], cropped_rows),
    )

    blurred_marker = cv2.GaussianBlur(_create_marker(marker_resolution, (1,), (0,)), (5, 5), sigmaX=1.0, sigmaY=1.0)

    scale_factor = _projector_to_camera_scale_factor(camera_info)
    kernel = cv2.resize(blurred_marker, None, fx=scale_factor, fy=scale_factor)

    convolved_image = cv2.filter2D(normalized_image, -1, kernel)

    brightest_location = cv2.minMaxLoc(convolved_image)[3]

    return (brightest_location[0], brightest_location[1] + cropped_rows)


def _capture_with_capture_assistant(camera: zivid.Camera) -> zivid.Frame:
    """Capture with the Capture Assistant.

    Args:
        camera: Zivid camera

    Returns:
        Frame from capture

    """
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=timedelta(milliseconds=1200),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )
    settings: zivid.Settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)
    settings.processing.filters.reflection.removal.enabled = True
    settings.processing.filters.reflection.removal.mode = "global"
    settings.processing.filters.smoothing.gaussian.enabled = True
    settings.processing.filters.smoothing.gaussian.sigma = 1.5
    settings.sampling.pixel = "all"
    settings.color.sampling.pixel = "all"

    # We must limit Brightness to a *maximum* of 2.2, when using `all` mode.
    # This code can be removed by changing the Config.yml option 'Camera/Power/Limit'.
    for acquisition in settings.acquisitions:
        acquisition.brightness = min(acquisition.brightness, 2.2)

    return camera.capture_2d_3d(settings)


def _annotate(frame_2d: zivid.Frame2D, location: Tuple[int, int]) -> np.ndarray:
    """Annotate image with a red cross in location.

    Args:
        frame_2d: 2D frame containing image
        location: (x,y) coordinates to annotate

    Returns:
        Annotated BGRA image

    """
    image = frame_2d.image_bgra_srgb().copy_data()
    marker_color = (0, 0, 255, 255)
    marker_size = 10

    top_left_location = (location[0] - marker_size, location[1] - marker_size)
    bottom_right_location = (location[0] + marker_size, location[1] + marker_size)
    cv2.line(image, top_left_location, bottom_right_location, marker_color, 2)

    top_right_location = (location[0] - marker_size, location[1] + marker_size)
    bottom_left_location = (location[0] + marker_size, location[1] - marker_size)
    cv2.line(image, top_right_location, bottom_left_location, marker_color, 2)

    return image


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    with app.connect_camera() as camera:
        print("Retrieving the projector resolution that the camera supports")
        projector_resolution = zivid.projection.projector_resolution(camera)

        print(f"Creating a projector image with resolution: {projector_resolution}")
        background_color = (0, 0, 0, 255)
        projector_image = _create_background_image(projector_resolution, background_color)

        print("Drawing a green marker")
        marker_resolution = (41, 41)
        marker_color = (0, 255, 0, 255)
        marker = _create_marker(marker_resolution, marker_color, background_color)

        print("Copying the marker image to the projector image")
        _copy_to_center(marker, projector_image)

        projector_image_file = "ProjectorImage.png"
        print(f"Saving the projector image to file: {projector_image_file}")
        cv2.imwrite(projector_image_file, projector_image)

        print("Displaying the projector image")
        projected_image = zivid.projection.show_image_bgra(camera, projector_image)

        input("Press enter to continue ...")

        # Fine tune 2D settings until the "ProjectedMarker.png" image is well exposed if the projected marker well is not detected in ImageWithMarker.png.
        exposure_time = timedelta(microseconds=20000)
        aperture = 2.38
        gain = 1.0

        settings_2d_zero_brightness = zivid.Settings2D(
            acquisitions=[
                zivid.Settings2D.Acquisition(brightness=0.0, exposure_time=exposure_time, aperture=aperture, gain=gain)
            ],
            sampling=zivid.Settings2D.Sampling(_get_color_settings_for_camera(camera)),
        )

        settings_2d_max_brightness = zivid.Settings2D(
            acquisitions=[
                zivid.Settings2D.Acquisition(
                    brightness=find_max_projector_brightness(camera),
                    exposure_time=exposure_time,
                    aperture=aperture,
                    gain=gain,
                )
            ],
            sampling=zivid.Settings2D.Sampling(_get_color_settings_for_camera(camera)),
        )

        settings_2d_projection = zivid.Settings2D(
            acquisitions=[
                zivid.Settings2D.Acquisition(
                    brightness=find_max_projector_brightness(camera),
                    exposure_time=exposure_time,
                    aperture=aperture,
                    gain=gain,
                )
            ],
            sampling=zivid.Settings2D.Sampling(_get_color_settings_for_camera(camera)),
        )

        print("Capturing a 2D frame with the marker")
        projected_marker_frame_2d = projected_image.capture_2d(
            settings_2d_zero_brightness
            if not camera_supports_projection_brightness_boost(camera)
            else settings_2d_projection
        )
        projected_marker_frame_2d.image_rgba().save("ProjectedMarker.png")

        print("Capturing a 2D frame of the scene illuminated with the projector")
        illuminated_scene_frame_2d = camera.capture_2d(settings_2d_max_brightness)

        print("Capturing a 2D frame of the scene without projector illumination")
        non_illuminated_scene_frame_2d = camera.capture_2d(settings_2d_zero_brightness)

        print("Locating marker in the 2D image:")
        marker_location = _find_marker(
            projected_marker_frame_2d,
            illuminated_scene_frame_2d,
            non_illuminated_scene_frame_2d,
            marker_resolution,
            camera.info,
        )
        print(marker_location)

        print("Capturing a point cloud using Capture Assistant")

        frame = _capture_with_capture_assistant(camera)
        print("Looking up 3D coordinate based on the marker position in the 2D image:")
        points_xyz = frame.point_cloud().copy_data("xyz")

        points_xyz_height, points_xyz_width = points_xyz.shape[:2]
        row, col = marker_location[:2]
        if col < points_xyz_width and row < points_xyz_height and points_xyz[row, col] is not np.nan:
            print(points_xyz[row, col])

            print("Annotating the 2D image captured while projecting the marker")
            annotated_image = _annotate(projected_marker_frame_2d, marker_location)

            annotated_image_file = "ImageWithMarker.png"
            print(f"Saving the annotated 2D image to file: {annotated_image_file}")
            cv2.imwrite(annotated_image_file, annotated_image)

            print("Done")
        else:
            print("Unable to find 3D coordinate!")


if __name__ == "__main__":
    _main()
