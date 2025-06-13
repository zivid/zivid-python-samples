"""
Read intrinsic parameters from the Zivid camera (OpenCV model) or estimate them from the point cloud.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import zivid
import zivid.experimental.calibration


def _print_parameter_delta(label: str, fixed_value: float, estimated_value: float) -> None:
    delta = fixed_value - estimated_value
    if delta != 0:
        print(f"{label:>6}: {delta:6.2f} ({abs(100 * delta / fixed_value):6.2f}% )")


def _print_intrinsic_parameters_delta(
    fixed_intrinsics: zivid.CameraIntrinsics,
    estimated_intrinsics: zivid.CameraIntrinsics,
) -> None:
    _print_parameter_delta("CX", fixed_intrinsics.camera_matrix.cx, estimated_intrinsics.camera_matrix.cx)
    _print_parameter_delta("CY", fixed_intrinsics.camera_matrix.cy, estimated_intrinsics.camera_matrix.cy)
    _print_parameter_delta("FX", fixed_intrinsics.camera_matrix.fx, estimated_intrinsics.camera_matrix.fx)
    _print_parameter_delta("FY", fixed_intrinsics.camera_matrix.fy, estimated_intrinsics.camera_matrix.fy)

    _print_parameter_delta("K1", fixed_intrinsics.distortion.k1, estimated_intrinsics.distortion.k1)
    _print_parameter_delta("K2", fixed_intrinsics.distortion.k2, estimated_intrinsics.distortion.k2)
    _print_parameter_delta("K3", fixed_intrinsics.distortion.k3, estimated_intrinsics.distortion.k3)
    _print_parameter_delta("P1", fixed_intrinsics.distortion.p1, estimated_intrinsics.distortion.p1)
    _print_parameter_delta("P2", fixed_intrinsics.distortion.p2, estimated_intrinsics.distortion.p2)


def _subsampled_settings_for_camera(camera: zivid.Camera) -> zivid.Settings:
    settings_subsampled = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )
    model = camera.info.model
    if (
        model is zivid.CameraInfo.Model.zividTwo
        or model is zivid.CameraInfo.Model.zividTwoL100
        or model is zivid.CameraInfo.Model.zivid2PlusM130
        or model is zivid.CameraInfo.Model.zivid2PlusM60
        or model is zivid.CameraInfo.Model.zivid2PlusL110
    ):
        settings_subsampled.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample2x2
        settings_subsampled.color.sampling.pixel = zivid.Settings2D.Sampling.Pixel.blueSubsample2x2
    elif (
        model is zivid.CameraInfo.Model.zivid2PlusMR130
        or model is zivid.CameraInfo.Model.zivid2PlusMR60
        or model is zivid.CameraInfo.Model.zivid2PlusLR110
    ):
        settings_subsampled.sampling.pixel = zivid.Settings.Sampling.Pixel.by2x2
        settings_subsampled.color.sampling.pixel = zivid.Settings2D.Sampling.Pixel.by2x2
    else:
        raise ValueError(f"Unhandled enum value {model}")

    return settings_subsampled


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Getting camera intrinsics")
    intrinsics = zivid.experimental.calibration.intrinsics(camera)
    print(intrinsics)

    output_file = "Intrinsics.yml"
    print(f"Saving camera intrinsics to file: {output_file}")
    intrinsics.save(output_file)

    print("\nDifference between fixed intrinsics and estimated intrinsics for different apertures and temperatures:")

    for fnum in (5.66, 4.00, 2.83):
        settings = zivid.Settings(
            acquisitions=[zivid.Settings.Acquisition(aperture=fnum)],
            color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
        )
        frame = camera.capture_2d_3d(settings=settings)
        estimated_intrinsics = zivid.experimental.calibration.estimate_intrinsics(frame)
        temperature = frame.state.temperature.lens
        print(f"\nAperture: {fnum:.2f}, Lens Temperature: {temperature:.2f}°C")
        _print_intrinsic_parameters_delta(intrinsics, estimated_intrinsics)

    settings_subsampled = _subsampled_settings_for_camera(camera)
    fixed_intrinsics_for_subsampled_settings_path = "FixedIntrinsicsSubsampled2x2.yml"
    print(f"Saving camera intrinsics for subsampled capture to file: {fixed_intrinsics_for_subsampled_settings_path}")
    fixed_intrinsics_for_subsampled_settings = zivid.experimental.calibration.intrinsics(camera, settings_subsampled)
    fixed_intrinsics_for_subsampled_settings.save(fixed_intrinsics_for_subsampled_settings_path)

    frame = camera.capture_2d_3d(settings_subsampled)
    estimated_intrinsics_for_subsampled_settings = zivid.experimental.calibration.estimate_intrinsics(frame)
    estimated_intrinsics_for_subsampled_settings_path = "EstimatedIntrinsicsFromSubsampled2x2Capture.yml"
    print(
        f"Saving estimated camera intrinsics for subsampled capture to file: {estimated_intrinsics_for_subsampled_settings_path}"
    )
    estimated_intrinsics_for_subsampled_settings.save(estimated_intrinsics_for_subsampled_settings_path)
    print("\nDifference between fixed and estimated intrinsics for subsampled point cloud:")
    _print_intrinsic_parameters_delta(
        fixed_intrinsics_for_subsampled_settings,
        estimated_intrinsics_for_subsampled_settings,
    )

    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    print("Getting camera intrinsics for 2D settings")
    fixed_intrinsics_for_settings_2d = zivid.experimental.calibration.intrinsics(camera, settings_2d)
    print(fixed_intrinsics_for_settings_2d)
    fixed_intrinsics_for_settings_2d_path = "FixedIntrinsicsSettings2D.yml"
    print(f"Saving camera intrinsics for 2D settings to file: {fixed_intrinsics_for_settings_2d_path}")
    fixed_intrinsics_for_settings_2d.save(fixed_intrinsics_for_settings_2d_path)


if __name__ == "__main__":
    _main()
