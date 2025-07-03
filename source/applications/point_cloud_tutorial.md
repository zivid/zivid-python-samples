# Point Cloud Tutorial

Note\! This tutorial has been generated for use on Github. For original
tutorial see:
[point\_cloud\_tutorial](https://support.zivid.com/latest/academy/applications/point-cloud-tutorial.html)



---

*Contents:*
[**Introduction**](#Introduction) |
[**Frame**](#Frame) |
[**Point**](#Point-Cloud) |
[**Downsample**](#Downsample) |
[**Voxel**](#Voxel-downsample) |
[**Normals**](#Normals) |
[**Visualize**](#Visualize) |
[**Conclusion**](#Conclusion) |
[**Version**](#Version-History)

---



## Introduction

This tutorial describes how to use Zivid SDK to work with [Point
Cloud](https://support.zivid.com/latest//reference-articles/point-cloud-structure-and-output-formats.html)
data.

-----

Tip:

> If you prefer watching a video, our webinar [Getting your point cloud
> ready for your
> application](https://www.zivid.com/webinars-page?wchannelid=ffpqbqc7sg&wmediaid=h66zph71vo)
> covers the Point Cloud Tutorial.

**Prerequisites**

  - Install [Zivid
    Software](https://support.zivid.com/latest//getting-started/software-installation.html).
  - For Python: install
    [zivid-python](https://github.com/zivid/zivid-python#installation)

## Frame

The `zivid.Frame` contains the point cloud and color image (stored on
compute device memory) and the capture and camera information. Capture
^^^^^^^

When you capture with Zivid, you get a frame in return. The point cloud
is stored in the frame, and the frame is stored in the GPU memory. The
capture can contain color or not, depending of the method that you call.
For more information see this `table with different capture
modes<capture-mode-table>`.

### Capture with color

If you want to capture a point cloud with color, you can use the
`Zivid::Camera::capture2D3D()` method.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L22-L23))

``` sourceCode python
frame = camera.capture_2d_3d(settings)
```

### Capture without color

If you want to capture a point cloud without color, you can use the
`Zivid::Camera::capture3D()` method.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L122))

``` sourceCode python
frame_3d = camera.capture_3d(settings)
```

Check
[capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_tutorial.md)
for detailed instructions on how to capture.

#### Load

The frame can also be loaded from a ZDF file.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py#L14-L17))

``` sourceCode python
data_file = get_sample_data_path() / "Zivid3D.zdf"
print(f"Reading point cloud from file: {data_file}")
frame = zivid.Frame(data_file)
```

## Point Cloud

#### Get handle from Frame

You can now get a handle to the point cloud data on the GPU.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py#L20))

``` sourceCode python
point_cloud = frame.point_cloud()
```

Point cloud contains XYZ, RGB, and SNR, laid out on a 2D grid.

For more info check out [Point Cloud
Structure](https://support.zivid.com/latest//reference-articles/point-cloud-structure-and-output-formats.html).

The function `zivid.frame.point_cloud()` does not perform any copying
from GPU memory.

-----

Note:

`zivid.camera.capture_2d_3d()` and `zivid.camera.capture_3d()` methods
return at some moment in time after the camera completes capturing raw
images. The handle from `zivid.frame.point_cloud()` is available
instantly. However, the actual point cloud data becomes available only
after the processing on the GPU is finished. Any calls to data-copy
functions (section below) will block and wait for processing to finish
before proceeding with the requested copy operation.

For detailed explanation, see [Point Cloud Capture
Process](https://support.zivid.com/latest/academy/camera/point-cloud-capture-process.html).

-----

#### Unorganized point cloud

It is possible to convert the organized point cloud to an unorganized
point cloud. While doing so, all NaN values are removed, and the point
cloud is flattened to a 1D array.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/multi_camera/stitch_by_transformation.py#L109))

``` sourceCode python
unorganized_point_cloud = frame.point_cloud().to_unorganized_point_cloud()
```

### Combining multiple unorganized point clouds

The unorganized point cloud can be extended with additional unorganized
point clouds.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/multi_camera/stitch_by_transformation_from_zdf.py#L76))

``` sourceCode python
stitched_point_cloud.extend(current_point_cloud.transform(transformation_matrix))
```

#### Copy from GPU to CPU memory

You can now selectively copy data based on what is required. This is the
complete list of output data formats and how to copy them from the GPU.
Most of these APIs also applies to the unorganized point cloud.

| Return type                                                                                                                           | Copy functions                    | Data per pixel | Total data |
| ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | -------------- | ---------- |
| `numpy.ndarray([height,width,3], dtype=float32)`                                                                                      | `PointCloud.copy_data("xyz")`     | 12 bytes       | 28 MB      |
| `numpy.ndarray([height,width,3], dtype=float32)`                                                                                      | `PointCloud.copy_data("xyzw")`    | 16 bytes       | 37 MB      |
| `numpy.ndarray([height,width], dtype=float32)`                                                                                        | `PointCloud.copy_data("z")`       | 4 bytes        | 9 MB       |
| `numpy.ndarray([height,width,4], dtype=uint8)`                                                                                        | `PointCloud.copy_data("rgba")`    | 4 bytes        | 9 MB       |
| `numpy.ndarray([height,width,4], dtype=uint8)`                                                                                        | `PointCloud.copy_data("bgra")`    | 4 bytes        | 9 MB       |
| `numpy.ndarray([height,width,4], dtype=uint8)`                                                                                        | `PointCloud.copy_data("srgb")`    | 4 bytes        | 9 MB       |
| `numpy.ndarray([height,width], dtype=float32)`                                                                                        | `PointCloud.copy_data("snr")`     | 4 bytes        | 9 MB       |
| `numpy.ndarray([height,width], dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('r', 'u1'), ('g', 'u1'), ('b', 'u1'), ('a', 'u1')])` | `PointCloud.copy_data("xyzrgba")` | 16 bytes       | 37 MB      |

Here is an example of how to copy data.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py#L21-L22))

``` sourceCode python
xyz = point_cloud.copy_data("xyz")
rgba = point_cloud.copy_data("rgba_srgb")
```

### Memory allocation options

In terms of memory allocation, there are two ways to copy data:

  - The Zivid SDK can allocate a memory buffer and copy data to it.
  - A user can pass a pointer to a pre-allocated memory buffer, and the
    Zivid SDK will copy the data to the pre-allocated memory buffer.

-----

You may want to
[transform](https://support.zivid.com/latest//academy/applications/transform.html)
the point cloud to change its origin from the camera to the robot base
frame or, e.g., [scale the point cloud by transforming it from mm to
m](https://support.zivid.com/latest//academy/applications/transform/transform-millimeters-to-meters.html).

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/hand_eye_calibration/utilize_hand_eye_calibration.py#L120))

``` sourceCode python
point_cloud.transform(base_to_camera_transform)
```

Transformation can be done in-place:

  - `Zivid::PointCloud::transform()`
  - `Zivid::UnorganizedPointCloud::transform()`

or by creating a new instance:

  - `Zivid::PointCloud::transformed()`
  - `Zivid::UnorganizedPointCloud::transformed()`

The following example shows how create a new instance of
`Zivid::UnorganizedPointCloud` with a transformation applied to it. Note
that in this sample is is not necessary to create a new instance, as the
untransformed point cloud is not used after the transformation.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/multi_camera/stitch_by_transformation.py#L111))

``` sourceCode python
transformed_unorganized_point_cloud = unorganized_point_cloud.transformed(transformation_matrix)
```

Even the in-place API returns the transformed point cloud, so you can
use it directly, as in the example below.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/multi_camera/stitch_by_transformation_from_zdf.py#L76))

``` sourceCode python
stitched_point_cloud.extend(current_point_cloud.transform(transformation_matrix))
```

## Downsample

Sometimes you might not need a point cloud with as `high spatial
resolution (High spatial resolution means more detail and less distance
between points)` as given from the camera. You may then
[downsample](https://support.zivid.com/latest//academy/applications/downsampling.html)
the point cloud.

-----

Note:

> [Sampling
> (3D)](https://support.zivid.com/latest/reference-articles/settings/sampling.html)
> describes a hardware-based sub-/downsample method that reduces the
> resolution of the point cloud during capture while also reducing the
> acquisition and capture time.

-----

-----

Note:

`Zivid::UnorganizedPointCloud` does not support downsampling, but it
does support voxel downsampling, see `voxel_downsample`.

-----

Downsampling can be done in-place, which modifies the current point
cloud.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/downsample.py#L63))

``` sourceCode python
point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)
```

It is also possible to get the downsampled point cloud as a new point
cloud instance, which does not alter the existing point cloud.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/downsample.py#L57))

``` sourceCode python
downsampled_point_cloud = point_cloud.downsampled(zivid.PointCloud.Downsampling.by2x2)
```

Zivid SDK supports the following downsampling rates: `by2x2`, `by3x3`,
and `by4x4`, with the possibility to perform downsampling multiple
times.

## Voxel downsample

`Zivid::UnorganizedPointCloud` supports voxel downsampling. The API
takes two arguments:

1.  `voxelSize` - the size of the voxel in millimeters.
2.  `minPointsPerVoxel` - the minimum number of points per voxel to keep
    it.

Voxel downsampling subdivides 3D space into a grid of cubic voxels with
a given size. If a given voxel contains a number of points at or above
the given limit, all those source points are replaced with a single
point with the following properties:

  - Position (XYZ) is an SNR-weighted average of the source points'
    positions, i.e. a high-confidence source point will have a greater
    influence on the resulting position than a low-confidence one.
  - Color (RGBA) is the average of the source points' colors.
  - Signal-to-noise ratio (SNR) is sqrt(sum(SNR^2)) of the source
    points' SNR values, i.e. the SNR of a new point will increase with
    both the number and the confidence of the source points that were
    used to compute its position.

Using minPointsPerVoxel \> 1 is particularly useful for removing noise
and artifacts from unorganized point clouds that are a combination of
point clouds captured from different angles. This is because a given
artifact is most likely only present in one of the captures, and
minPointsPerVoxel can be used to only fill voxels that both captures
"agree" on.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/multi_camera/stitch_by_transformation.py#L115))

``` sourceCode python
final_point_cloud = stitched_point_cloud.voxel_downsampled(0.5, 1)
```

## Normals

Some applications require computing
[normals](https://support.zivid.com/latest//academy/applications/normals.html)
from the point cloud.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/advanced/capture_hdr_print_normals.py#L48-L49))

``` sourceCode python
print("Computing normals and copying them to CPU memory")
normals = point_cloud.copy_data("normals")
```

The Normals API computes the normal at each point in the point cloud and
copies normals from the GPU memory to the CPU memory. The result is a
matrix of normal vectors, one for each point in the input point cloud.
The size of normals is equal to the size of the input point cloud.

## Visualize

Having the frame allows you to visualize the point cloud.

No source available for {language\_name}You can visualize the point
cloud from the point cloud object as well.

No source available for {language\_name}For more information, check out
[Visualization
Tutorial](https://support.zivid.com/latest/academy/applications/visualization-tutorial.html),
where we cover point cloud, color image, depth map, and normals
visualization, with implementations using third party libraries.

## Conclusion

This tutorial shows how to use the Zivid SDK to extract the point cloud,
manipulate it, transform it, and visualize it.

## Version History

| SDK    | Changes                                                                                                                                                           |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.16.0 | Added support for `Zivid::UnorganizedPointCloud`. `transformed` is added as a function to `Zivid::PointCloud` (also available in `Zivid::UnorganizedPointCloud`). |
| 2.11.0 | Added support for SRGB color space.                                                                                                                               |
| 2.10.0 | [:orphan:](https://support.zivid.com/latest/academy/camera/monochrome-capture.html) introduces a faster alternative to `downsample_point_cloud_tutorial`.         |
