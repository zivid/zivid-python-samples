"""
This example shows how to capture a Zivid point cloud and save it to a .PLY
file format.
"""

import datetime
import zivid

def _main():
    app = zivid.Application()
    
    FilenamePLY = "Zivid3D.ply"
    
    print("Connecting to the camera")
    camera = app.connect_camera()
    
    print("Configuring the camera settings")
    with camera.update_settings() as updater:
        updater.settings.exposure_time = datetime.timedelta(microseconds=10000)
        updater.settings.iris = 21        
        updater.settings.filters.reflection.enabled = True
    
    print("Capturing a frame")
    with camera.capture() as frame:
        print("Saving the frame to ", FilenamePLY)
        frame.save(FilenamePLY)
        
if __name__ == "__main__":
    _main()
