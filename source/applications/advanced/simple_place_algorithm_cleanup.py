import open3d as o3d
import numpy as np


def _crop_2d(bin: dict[str, int], xyz: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    return xyz[bin['row_min']:bin['row_max'], bin['col_min']:bin['col_max'], :]


def _find_placement_options(xyz_bin: np.ndarray, object_extent: np.ndarray) -> np.ndarray:
    min_values = np.flip(np.nanmin(xyz_bin[:,:,:2], axis=(0,1)))
    max_values = np.flip(np.nanmax(xyz_bin[:,:,:2], axis=(0,1)))
    bin_extent_mm = {
        'mm_x': max_values[0] - min_values[0],
        'mm_y': max_values[1] - min_values[1]
    }
    pixel_stride = [int(stride/2) for stride in list(xyz_bin.shape[0:2] / (np.asarray(list(bin_extent_mm.values())) / object_extent[:2]))]
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
    return placement_options


def _choose_placement_point(placement_options: np.ndarray) -> np.ndarray:
    max_min_z = np.nanmax(placement_options[:,:,2], axis=(0,1))
    placement = placement_options[placement_options[:,:,2] == max_min_z].squeeze()
    placement = placement if placement.shape[0] == 5 else placement[0,:].squeeze()
    return placement


def _main():
    pcd_path = "C:/Zivid/Temp/Fizyr/checkerboard_in_bin.pcd"
    pcd = o3d.io.read_point_cloud(pcd_path)
    xyz = np.asarray(pcd.points).reshape((1024, 1224, 3))
    rgb = np.asarray(pcd.colors).reshape((1024, 1224, 3))

    bin = {
        'row_min': 236, 
        'col_min': 229,
        'row_max': 840, 
        'col_max': 1166,
    }
    xyz_cropped = _crop_2d(bin, xyz, rgb)

    object_extent_mm = np.asarray([200, 300, 10])
    print(f"{object_extent_mm=}")
    placement_options = _find_placement_options(xyz_cropped, object_extent_mm)
    placement_point = _choose_placement_point(placement_options)
    print(f"Selected place point, translation: {placement_point[:3]}")


if __name__ == "__main__":
    _main()
