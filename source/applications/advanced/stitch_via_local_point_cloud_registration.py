"""
Stitch two point clouds using a transformation estimated by Local Point Cloud Registration and apply Voxel Downsample.

Dataset: https://support.zivid.com/en/latest/api-reference/samples/sample-data.html

Extract the content into :
    • Windows:   %ProgramData%\\Zivid\\StitchingPointClouds\\
    • Linux:     /usr/share/Zivid/data/StitchingPointClouds/

    StitchingPointClouds/
        └── BlueObject/

The folder must contain two ZDF files used for this sample.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import zivid
from zivid.experimental.toolbox.point_cloud_registration import (
    LocalPointCloudRegistrationParameters,
    local_point_cloud_registration,
)
from zividsamples.display import display_pointcloud
from zividsamples.paths import get_sample_data_path


def _main() -> None:
    zivid.Application()

    # Ensure the dataset is extracted to the correct location depending on the operating system:
    #   • Windows:   %ProgramData%\\Zivid\\StitchingPointClouds\\
    #   • Linux:     /usr/share/Zivid/data/StitchingPointClouds/
    # The folder must contain:
    #   StitchingPointClouds/
    #     └── BlueObject/
    print("Reading point clouds from files")
    directory = get_sample_data_path() / "StitchingPointClouds" / "BlueObject"

    if not directory.exists() or not directory.exists():
        raise FileNotFoundError(
            f"Missing dataset folders.\n"
            f"Make sure 'StitchingPointClouds/BlueObject' exist at {get_sample_data_path()}.\n\n"
            f"You can download the dataset (StitchingPointClouds.zip) from:\n"
            f"https://support.zivid.com/en/latest/api-reference/samples/sample-data.html"
        )

    frame_1 = zivid.Frame(directory / "BlueObject.zdf")
    frame_2 = zivid.Frame(directory / "BlueObjectSlightlyMoved.zdf")

    print("Converting organized point clouds to unorganized point clouds and voxel downsampling")
    unorganized_point_cloud_1 = frame_1.point_cloud().to_unorganized_point_cloud()
    unorganized_point_cloud_2 = frame_2.point_cloud().to_unorganized_point_cloud()

    print("Displaying point clouds before stitching")
    unorganized_not_stitched_point_cloud = zivid.UnorganizedPointCloud()
    unorganized_not_stitched_point_cloud.extend(unorganized_point_cloud_1)
    unorganized_not_stitched_point_cloud.extend(unorganized_point_cloud_2)
    display_pointcloud(
        xyz=unorganized_not_stitched_point_cloud.copy_data("xyz"),
        rgb=unorganized_not_stitched_point_cloud.copy_data("rgba")[:, 0:3],
    )

    print("Estimating transformation between point clouds")
    unorganized_point_cloud_1_lpcr = unorganized_point_cloud_1.voxel_downsampled(voxel_size=1.0, min_points_per_voxel=3)
    unorganized_point_cloud_2_lpcr = unorganized_point_cloud_2.voxel_downsampled(voxel_size=1.0, min_points_per_voxel=3)
    registration_params = LocalPointCloudRegistrationParameters()
    local_point_cloud_registration_result = local_point_cloud_registration(
        target=unorganized_point_cloud_1_lpcr, source=unorganized_point_cloud_2_lpcr, parameters=registration_params
    )
    assert local_point_cloud_registration_result.converged(), "Registration did not converge..."
    point_cloud_1_to_point_cloud_2_transform = local_point_cloud_registration_result.transform()

    print("Displaying point clouds after stitching")
    final_point_cloud = zivid.UnorganizedPointCloud()
    final_point_cloud.extend(unorganized_point_cloud_1)
    unorganized_point_cloud_2_transformed = unorganized_point_cloud_2.transformed(
        point_cloud_1_to_point_cloud_2_transform.to_matrix()
    )
    final_point_cloud.extend(unorganized_point_cloud_2_transformed)
    display_pointcloud(
        xyz=final_point_cloud.copy_data("xyz"),
        rgb=final_point_cloud.copy_data("rgba")[:, 0:3],
    )

    print("Voxel-downsampling the stitched point cloud")
    final_point_cloud = final_point_cloud.voxel_downsampled(voxel_size=2.0, min_points_per_voxel=1)
    display_pointcloud(
        xyz=final_point_cloud.copy_data("xyz"),
        rgb=final_point_cloud.copy_data("rgba")[:, 0:3],
    )


if __name__ == "__main__":
    _main()
