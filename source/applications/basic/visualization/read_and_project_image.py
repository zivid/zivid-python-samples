"""
Read a 2D image from file and project it using the camera projector.

The image for this sample can be found under the main instructions for Zivid samples.

"""

from datetime import timedelta
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import zivid
from zividsamples.paths import get_sample_data_path


def _resize_and_create_projector_image(image_to_resize: np.ndarray, final_resolution: Tuple) -> np.ndarray:
    """Resizes an image to a given resolution.

    Args:
        image_to_resize: openCV image that needs to be resized
        final_resolution: resolution after resizing

    Returns:
        An image with a resolution that matches the projector resolution

    """
    resized_image = cv2.resize(
        image_to_resize, (final_resolution[1], final_resolution[0]), interpolation=cv2.INTER_LINEAR
    )
    projector_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2BGRA)

    return projector_image


def get_projector_image_file_for_camera(camera: zivid.Camera) -> Path:
    """Provides the path to the projector image for a given camera.

    Args:
        camera: Zivid camera

    Returns:
        Path to the projector image

    Raises:
        RuntimeError: Invalid camera model

    """
    model = camera.info.model
    if model in [zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100]:
        return get_sample_data_path() / "ZividLogoZivid2ProjectorResolution.png"
    if model in [
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ]:
        return get_sample_data_path() / "ZividLogoZivid2PlusProjectorResolution.png"
    raise RuntimeError("Invalid camera model")


def make_settings_2d() -> zivid.Settings2D:
    """Creates 2D settings for a given camera.

    Args:

    Returns:
        2D settings

    """
    return zivid.Settings2D(
        acquisitions=[
            zivid.Settings2D.Acquisition(
                brightness=2.5,
                exposure_time=timedelta(microseconds=20000),
                aperture=2.83,
            )
        ],
        sampling=zivid.Settings2D.Sampling(color=zivid.Settings2D.Sampling.Color.grayscale),
    )


def camera_supports_projection_brightness_boost(camera: zivid.Camera) -> bool:
    """Checks if the provided model supports brightness boost.

    Args:
        camera: Zivid camera model

    Returns:
        True if it is a model that supports brightness boost, False otherwise

    """
    return camera.info.model in {
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusLR110,
        zivid.CameraInfo.Model.zivid2PlusMR60,
    }


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    image_file = get_sample_data_path() / "ZividLogo.png"
    print("Reading 2D image (of arbitrary resolution) from file: ")
    input_image = cv2.imread(str(image_file))
    if input_image is None:
        raise RuntimeError(f"File {image_file} not found or couldn't be read.")

    print(f"Input image size: {input_image.shape[:2]}")

    print("Retrieving the projector resolution that the camera supports")
    projector_resolution = zivid.projection.projector_resolution(camera)

    print(f"Resizing input image to fit projector resolution:{projector_resolution}")
    projector_image = _resize_and_create_projector_image(
        image_to_resize=input_image, final_resolution=projector_resolution
    )

    projector_image_file = "ProjectorImage.png"
    print(f"Saving the projector image to file: {projector_image_file}")
    cv2.imwrite(projector_image_file, projector_image)

    print("Displaying the projector image")
    with zivid.projection.show_image_bgra(camera, projector_image) as projected_image_handle:

        settings_2d = make_settings_2d()
        if not camera_supports_projection_brightness_boost(camera):
            settings_2d.acquisitions[0].brightness = 0.0
            settings_2d.sampling.color = zivid.Settings2D.Sampling.Color.rgb

        print("Capturing a 2D image with the projected image")
        frame_2d = projected_image_handle.capture_2d(settings_2d)

        captured_image_file = "CapturedImage.png"
        print(f"Saving the captured image: {captured_image_file}")
        frame_2d.image_bgra().save(captured_image_file)

        input("Press enter to stop projecting ...")

    projector_image_file_for_given_camera = get_projector_image_file_for_camera(camera)

    print(
        f"Reading 2D image (of resolution matching the Zivid camera projector resolution) from file: {projector_image_file_for_given_camera}"
    )
    projector_image_for_given_camera = zivid.Image.load(projector_image_file_for_given_camera, "bgra_srgb")

    with zivid.projection.show_image_bgra(
        camera, projector_image_for_given_camera.copy_data()
    ) as projected_image_handle:
        input("Press enter to stop projecting ...")


if __name__ == "__main__":
    _main()
