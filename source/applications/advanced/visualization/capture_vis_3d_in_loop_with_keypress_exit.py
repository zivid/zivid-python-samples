"""
Capture point clouds, with color, from the Zivid camera, and visualize them in a loop. Press 'q' to exit.

"""

import sys
import threading
import time

import zivid

if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty


def _get_key_non_blocking() -> str:
    if sys.platform == "win32":
        if msvcrt.kbhit():
            return msvcrt.getch().decode(errors="ignore")
        return ""
    readable = select.select([sys.stdin], [], [], 0)[0]
    if readable:
        return sys.stdin.read(1)
    return ""


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
    accept_end = threading.Event()
    accept_end.set()
    quit_requested = threading.Event()

    use_raw_terminal = sys.platform != "win32" and sys.stdin.isatty()
    if use_raw_terminal:
        old_terminal_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    try:
        print("Visualizing point cloud")
        with zivid.visualization.Visualizer() as visualizer:
            visualizer.show(frame)
            visualizer.reset_to_fit()

            def _capture_and_keypress_thread() -> None:
                print("Press 'q' in the terminal to quit")
                while not quit_requested.is_set():
                    if not visualizer_running.wait(timeout=0.01):
                        continue
                    key = _get_key_non_blocking()
                    if key == "q":
                        print("Closing application because user pressed 'q'")
                        quit_requested.set()
                        visualizer.close()
                    else:
                        accept_end.clear()
                        new_frame = camera.capture_2d_3d(settings)
                        if visualizer_running.is_set():
                            visualizer.show(new_frame)
                        accept_end.set()
                    time.sleep(0.01)

            capture_thread = threading.Thread(target=_capture_and_keypress_thread)
            capture_thread.start()

            print("Running visualizer. Blocking until window closes.")
            while True:
                visualizer_running.set()
                visualizer.run()
                visualizer_running.clear()

                if quit_requested.is_set():
                    break
                print("Visualizer window closed by user. It will be reopened if we're currently capturing.")
                if accept_end.is_set():
                    break

            capture_thread.join()

        print("Visualizer closed")
    finally:
        if use_raw_terminal:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_terminal_settings)


if __name__ == "__main__":
    _main()
