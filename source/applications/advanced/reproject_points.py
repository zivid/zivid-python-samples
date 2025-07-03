"""
Illuminate checkerboard (Zivid Calibration Board) centers by getting the checkerboard feature points
and illuminating them with the projector.

The checkerboard feature points are first found through the API. These points are then used to get the
corresponding projector pixels. The projector pixel coordinates are then used to draw markers at the
correct locations before displaying the image using the projector.

"""

from datetime import timedelta
from typing import List, Tuple

import cv2
import numpy as np
import zivid
from zividsamples.settings_utils import get_matching_2d_preset_settings, update_exposure_based_on_relative_brightness


def _draw_filled_circles(
    image: np.ndarray, positions: List[List[float]], circle_size_in_pixels: int, circle_color: Tuple[int, ...]
) -> None:
    """Draw a circle for each position in positions in the image.

    Args:
        image: Image to draw circles in
        positions: List of 2D positions (X,Y) to draw a circle in
        circle_size_in_pixels: Radius of circles
        circle_color: Color of circles (RGB, RGBA, BGR, BGRA etc.)

    """
    for position in positions:
        if np.nan not in position:
            point = (round(position[0]), round(position[1]))
            cv2.circle(image, point, circle_size_in_pixels, circle_color, -1)


def _get_2d_capture_settings(camera: zivid.Camera) -> zivid.Settings2D:
    """Get 2D capture settings based on the camera model.

    Args:
        camera: Zivid camera

    Returns:
        2D capture settings

    """

    def _get_sampling_color_for_model(model: zivid.CameraInfo.Model) -> zivid.Settings2D.Sampling.Color:
        """Get the sampling color based on the camera model.

        Args:
            model: Zivid camera model

        Raises:
            ValueError: If the camera model is not supported

        Returns:
            Sampling color for the camera model
        """
        if model in [
            zivid.CameraInfo.Model.zividTwo,
            zivid.CameraInfo.Model.zividTwoL100,
            zivid.CameraInfo.Model.zivid2PlusM130,
            zivid.CameraInfo.Model.zivid2PlusM60,
            zivid.CameraInfo.Model.zivid2PlusL110,
        ]:
            sampling_color = zivid.Settings2D.Sampling.Color.rgb
        elif model in [
            zivid.CameraInfo.Model.zivid2PlusMR130,
            zivid.CameraInfo.Model.zivid2PlusMR60,
            zivid.CameraInfo.Model.zivid2PlusLR110,
        ]:
            sampling_color = zivid.Settings2D.Sampling.Color.grayscale
        else:
            raise ValueError(f"Unsupported camera model '{model}'")
        return sampling_color

    sampling_color = _get_sampling_color_for_model(camera.info.model)
    try:
        return get_matching_2d_preset_settings(camera, sampling_color, zivid.Settings2D.Sampling.Pixel.all)
    except RuntimeError:
        settings_2d = zivid.Settings2D(
            acquisitions=[
                zivid.Settings2D.Acquisition(brightness=0.0, exposure_time=timedelta(microseconds=20000), aperture=2.83)
            ],
            sampling=zivid.Settings2D.Sampling(color=sampling_color, pixel=zivid.Settings2D.Sampling.Pixel.all),
        )

        return settings_2d


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Capturing and detecting feature points of the Zivid checkerboard")
    detection_result = zivid.calibration.detect_calibration_board(camera)
    if not detection_result.valid():
        raise RuntimeError(f"Calibration board not detected! {detection_result.status_description()}")

    feature_points = detection_result.feature_points()

    print("Getting projector pixels (2D) corresponding to points (3D)")
    projector_pixels = zivid.projection.pixels_from_3d_points(camera, feature_points)

    print("Retrieving the projector resolution that the camera supports")
    projector_resolution = zivid.projection.projector_resolution(camera)

    print(f"Creating a blank projector image with resolution: {projector_resolution}")
    background_color = (0, 0, 0, 255)
    projector_image = np.full(
        (projector_resolution[0], projector_resolution[1], len(background_color)), background_color, dtype=np.uint8
    )

    print("Drawing circles on the projector image for each grid point")
    circle_color = (0, 255, 0, 255)
    _draw_filled_circles(projector_image, projector_pixels, 2, circle_color)

    projector_image_file = "ProjectorImage.png"
    print(f"Saving the projector image to file: {projector_image_file}")
    cv2.imwrite(projector_image_file, projector_image)

    settings_2d = update_exposure_based_on_relative_brightness(camera, _get_2d_capture_settings(camera))

    print("Displaying the projector image")
    with zivid.projection.show_image_bgra(camera, projector_image) as projected_image:
        print("Capturing a 2D image with the projected image")
        frame_2d = projected_image.capture_2d(settings_2d)

        captured_image_file = "CapturedImage.png"
        print(f"Saving the captured image: {captured_image_file}")
        frame_2d.image_bgra_srgb().save(captured_image_file)

        input("Press enter to stop projecting ...")

    print("Done")


if __name__ == "__main__":
    _main()
