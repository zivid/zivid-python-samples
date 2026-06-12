"""
Capture point clouds, with color, from the Zivid camera, and visualize them in a loop.

"""

import threading
import time

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Creating default settings")
    settings = zivid.Settings(
        engine=zivid.Settings.Engine.phase,
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)

    print("Setting up visualization")
    visualizer_running = threading.Event()

    print("Visualizing point cloud")
    with zivid.visualization.Visualizer() as visualizer:
        visualizer.show(frame)
        visualizer.reset_to_fit()

        def _capture_thread() -> None:
            while visualizer_running.is_set():
                new_frame = camera.capture_2d_3d(settings)
                if visualizer_running.is_set():
                    visualizer.show(new_frame)
                time.sleep(0.01)

        capture_thread = threading.Thread(target=_capture_thread)

        print("Running visualizer. Blocking until window closes.")
        visualizer_running.set()
        capture_thread.start()
        visualizer.run()
        visualizer_running.clear()

        capture_thread.join()

    print("Visualizer closed")


if __name__ == "__main__":
    _main()
