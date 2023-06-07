import cv2
import open3d as o3d
import numpy as np

from sample_utils.display import display_rgb


def _depth_map(z: np.array) -> tuple[np.ndarray, str]:
    """Get depth map from xyz.

    Args:
        point_cloud: Zivid point cloud

    Returns:
        depth_map_color_map: Depth map (HxWx1 ndarray)

    """
    nanmin = np.nanmin(z)
    nanmax = np.nanmax(z)
    depth_map_uint8 = ((z - nanmin) / (nanmax - nanmin) * 255).astype(
        np.uint8
    )

    depth_map_color_map = cv2.applyColorMap(depth_map_uint8, cv2.COLORMAP_VIRIDIS)

    # Setting nans to black
    depth_map_color_map[np.isnan(z)[:, :]] = 0

    return (depth_map_color_map, f"{nanmin=}, {nanmax=}")


def _downsample(pcd: o3d.geometry.PointCloud) -> None:
    voxel_size = 0.05
    print(f"Downsample the point cloud with a voxel of {voxel_size}")
    # downsampled_pcd = pcd.voxel_down_sample(voxel_size=voxel_size)
    downsampled_pcd = pcd.farthest_point_down_sample(1000)
    print(f"{downsampled_pcd=}")
    print(np.asarray(downsampled_pcd.points).shape)
    # o3d.visualization.draw([downsampled_pcd])


def _crop_2d(bin: dict[str, int], xyz: np.ndarray, rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xyz_cropped = xyz[bin['row_min']:bin['row_max'], bin['col_min']:bin['col_max'], :]
    rgb_cropped = rgb[bin['row_min']:bin['row_max'], bin['col_min']:bin['col_max'], :]
    return (xyz_cropped, rgb_cropped)


def _find_placement_options(xyz_bin: np.ndarray, object_extent: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    min_values = np.flip(np.nanmin(xyz_bin[:,:,:2], axis=(0,1)))
    max_values = np.flip(np.nanmax(xyz_bin[:,:,:2], axis=(0,1)))
    detected_bin = {
        'row_min': min_values[1], 
        'col_min': min_values[0],
        'row_max': max_values[1], 
        'col_max': max_values[0],
        'bin_width': max_values[1] - min_values[1],
        'bin_height': max_values[0] - min_values[0],
    }
    print(detected_bin)
    bin_extent_mm = {
        'mm_x': detected_bin['col_max'] - detected_bin['col_min'],
        'mm_y': detected_bin['row_max'] - detected_bin['row_min']
    }
    print(bin_extent_mm)
    print(f"mm per pixels in x = {detected_bin['bin_width']/xyz_bin.shape[1]}")
    print(f"mm per pixels in y = {detected_bin['bin_height']/xyz_bin.shape[0]}")
    spatial_resolution = xyz_bin.shape[1]/detected_bin['bin_width']
    pixel_stride = [int(stride/2) for stride in list(xyz_bin.shape[0:2] / (np.asarray(list(bin_extent_mm.values())) / object_extent[:2]))]
    print(f"{pixel_stride=}")
    rows = list(range(pixel_stride[0], xyz_bin.shape[0] - pixel_stride[0], pixel_stride[0]))
    cols = list(range(pixel_stride[1], xyz_bin.shape[1] - pixel_stride[1], pixel_stride[1]))
    placement_options = np.zeros((len(rows)+1, len(cols)+1, 5))
    placement_options[:, :, :] = np.asarray([1,2,3,4,5])
    for placement_row, pixel_row in enumerate(rows):
        for placement_col, pixel_col in enumerate(cols):
            placement_options[placement_row, placement_col, :2] = np.nanmean(xyz_bin[pixel_row-pixel_stride[0]:pixel_row+pixel_stride[0], pixel_col-pixel_stride[1]:pixel_col+pixel_stride[1], :2], axis=(0,1))
            placement_options[placement_row, placement_col, 2] = np.nanmin(xyz_bin[pixel_row-pixel_stride[0]:pixel_row+pixel_stride[0], pixel_col-pixel_stride[1]:pixel_col+pixel_stride[1], 2], axis=(0,1))
            placement_options[placement_row, placement_col, 3:] = [pixel_row, pixel_col]
    # Add options to place aligned with the right and bottom edge
    for placement_row, pixel_row in enumerate(rows):
        placement_options[placement_row, -1, :2] = np.nanmean(xyz_bin[pixel_row-pixel_stride[0]:pixel_row+pixel_stride[0], -2*pixel_stride[1]:, :2], axis=(0,1))
        placement_options[placement_row, -1, 2] = np.nanmin(xyz_bin[pixel_row-pixel_stride[0]:pixel_row+pixel_stride[0], -2*pixel_stride[1]:, 2], axis=(0,1))
        placement_options[placement_row, -1, 3:] = [pixel_row, xyz_bin.shape[1] - pixel_stride[1]]
    for placement_col, pixel_col in enumerate(cols):
        placement_options[-1, placement_col, :2] = np.nanmean(xyz_bin[-2*pixel_stride[0]:, pixel_col-pixel_stride[1]:pixel_col+pixel_stride[1], :2], axis=(0,1))
        placement_options[-1, placement_col, 2] = np.nanmin(xyz_bin[-2*pixel_stride[0]:, pixel_col-pixel_stride[1]:pixel_col+pixel_stride[1], 2], axis=(0,1))
        placement_options[-1, placement_col, 3:] = [xyz_bin.shape[0] - pixel_stride[0], pixel_col]
    placement_options[-1, -1, :2] = np.nanmean(xyz_bin[-2*pixel_stride[0]:, -2*pixel_stride[1]:, :2], axis=(0,1))
    placement_options[-1, -1, 2] = np.nanmin(xyz_bin[-2*pixel_stride[0]:, -2*pixel_stride[1]:, 2], axis=(0,1))
    placement_options[-1, -1, 3:] = [xyz_bin.shape[0] - 2*pixel_stride[0], xyz_bin.shape[1] - pixel_stride[1]]
    return (placement_options, object_extent*spatial_resolution)


def _choose_placement_point(placement_options: np.ndarray) -> np.ndarray:
    max_min_z = np.nanmax(placement_options[:,:,2], axis=(0,1))
    print("Possible min-z values:")
    print(placement_options[:,:,2])
    placement = placement_options[placement_options[:,:,2] == max_min_z].squeeze()
    placement = placement if placement.shape[0] == 5 else placement[0,:].squeeze()
    return placement


def _main():
    pcd_path = "C:/Zivid/Temp/Fizyr/checkerboard_in_bin.pcd"
    pcd = o3d.io.read_point_cloud(pcd_path)
    # pcd.transform([[1/1000, 0, 0, 0], [0, 1/1000, 0, 0], [0, 0, 1/1000, 0], [0, 0, 0, 1]])
    print(f"{pcd=}")
    # o3d.visualization.draw([pcd])
    xyz = np.asarray(pcd.points).reshape((1024, 1224, 3))
    print(f"{xyz.shape=}")
    rgb = np.asarray(pcd.colors).reshape((1024, 1224, 3))
    print(f"{rgb.shape=}")
    # display_rgb(rgb)

    bin = {
        'row_min': 236, 
        'col_min': 229,
        'row_max': 840, 
        'col_max': 1166,
    }
    xyz_cropped, rgb_cropped = _crop_2d(bin, xyz, rgb)
    # rgb_cropped = rgb
    # xyz_cropped = xyz
    print(f"{rgb_cropped.shape=}, type:{rgb_cropped.dtype}")
    display_rgb(rgb_cropped)
    depth_map, meta = _depth_map(xyz_cropped[:,:,2])
    display_rgb(depth_map, f"z, {meta}")

    checkerboard = {
        'row_min': 377, 
        'col_min': 503,
        'row_max': 779, 
        'col_max': 922,
    }
    object_points, object_rgb = _crop_2d(checkerboard, xyz, rgb)
    print(f"{object_points.shape=}")
    bounding_box = o3d.geometry.AxisAlignedBoundingBox.create_from_points(o3d.utility.Vector3dVector(object_points.reshape((-1, 3))))
    print(f"{bounding_box=}")
    # object_extent = bounding_box.get_extent()
    object_extent_mm = np.asarray([200, 300, 10])
    print(f"{object_extent_mm=}")
    placement_options, object_extent_pixels = _find_placement_options(xyz_cropped, object_extent_mm)
    annotated_image = rgb_cropped.copy()
    # annotated_image = depth_map.copy()
    for row in range(placement_options.shape[0]):
    # for row in range(0, placement_options.shape[0], 2):
        for col in range(placement_options.shape[1]):
        # for col in range(0, placement_options.shape[1], 2):
            placement_as_int = placement_options[row, col, 3:].astype(dtype=np.int32)
            pt1 = np.flip(placement_as_int - (np.asarray(object_extent_pixels[:2])/2).astype(np)).astype(dtype=np.int32)
            pt2 = np.flip(placement_as_int + (np.asarray(object_extent_pixels[:2])/2).astype(np)).astype(dtype=np.int32)
            color = tuple(np.random.rand(3).tolist())
            print(f"{placement_as_int=}, {color=}")
            annotated_image = cv2.putText(
                annotated_image, 
                f"{placement_options[row, col, 2]:.1f}", 
                org=np.flip(placement_as_int),
                fontFace=cv2.FONT_HERSHEY_PLAIN,
                fontScale=1,
                color=color
            )
            annotated_image = cv2.rectangle(annotated_image, pt1=pt1, pt2=pt2, color=color, thickness=1)
            annotated_image = cv2.circle(annotated_image, center=np.flip(placement_as_int), radius=5, color=color, thickness=cv2.FILLED)
    placement_point = _choose_placement_point(placement_options)
    # place_point_image = cv2.circle(annotated_image, center=np.flip(placement_point), radius=10, color=[255, 255, 0], thickness=cv2.FILLED)
    display_rgb(annotated_image, title="All possible place points")
    place_point_image = rgb_cropped.copy()
    print(f"{placement_point=}")
    placement_point_pixel = placement_point[3:].astype(np.int32)
    place_point_image = cv2.circle(place_point_image, center=np.flip(placement_point_pixel), radius=10, color=[255, 255, 0], thickness=cv2.FILLED)
    pt1 = np.flip(placement_point_pixel - (np.asarray(object_extent_pixels[:2])/2)).astype(dtype=np.int32)
    pt2 = np.flip(placement_point_pixel + (np.asarray(object_extent_pixels[:2])/2)).astype(dtype=np.int32)
    annotated_image = cv2.rectangle(place_point_image, pt1=pt1, pt2=pt2, color=[255, 255, 0], thickness=1)
    display_rgb(place_point_image, title=f"Selected place point: Translation: {placement_point[:3]}")

    # # xyz_box_mask = 
    # for index, axis in enumerate(['x', 'y', 'z']):
    #     depth_map, meta = _depth_map(xyz[:,:,index])
    #     display_rgb(depth_map, f"{axis=}, {meta}")

    # _downsample(pcd)
    
    print("done")


if __name__ == "__main__":
    _main()
