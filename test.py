import time
import sys
import gi
import os

from multiprocessing import Process


# Append the "gstelement" Path in current directory to the plugin search path
if "GST_PLUGIN_PATH" in os.environ:
    oldpath = os.environ["GST_PLUGIN_PATH"]
else:
    oldpath = ""
os.environ["GST_PLUGIN_PATH"] = oldpath + ":" + os.path.join(os.getcwd(),"gstelement")


gi.require_version("Tcam", "0.1")
gi.require_version("Gst", "1.0")

from gi.repository import Tcam, Gst


def start_gstreamer(trip_path):

    print("Starting gstreamer")
    Gst.init(sys.argv) # init gstreamer
    # Set this to a serial string for a specific camera
    camera = Gst.ElementFactory.make("tcambin")
    # in the READY state the camera will always be initialized
    camera.set_state(Gst.State.READY)


    # Set properties
    camera.set_tcam_property("GPOut", 0)
    camera.set_tcam_property("Strobe Enable", True)
    camera.set_tcam_property("Exposure Auto", False)
    camera.set_tcam_property("Exposure Time (us)", 10000)

    # cleanup, reset state

    camera.set_state(Gst.State.NULL)

    pipeline = Gst.parse_launch(
        "tcamsrc name=bin"
        " ! video/x-bayer,width=2048,height=2048,framerate=15/1"
        " ! imgproc"
        " ! queue leaky=2 max-size-buffers=16"
        " ! bayer2rgb"
        " ! queue"
        " ! videoconvert"
        " ! xvimagesink sync=false")
        # " ! queue"
        # " ! nvv4l2h265enc control-rate=1 bitrate=8000000 iframeinterval=10"
        # " ! video/x-h265, stream-format=(string)byte-stream"
        # " ! h265parse"
        # " ! queue"
        # " ! splitmuxsink name=fsink max-size-time=60000000000")
        # " ! tee name=t"
        # " ! bayer2rgb"
        # " ! videoconvert"
        # " ! queue"
        # " ! xvimagesink")
        # " t."
        # "! queue"
        # "! appsink name=asink")


    file_location = os.path.join(trip_path, 'video-%02d.mp4')

    fsink = pipeline.get_by_name("fsink")
    if fsink:
        fsink.set_property("location", file_location)


    clock = pipeline.get_pipeline_clock()



    result = pipeline.set_state(Gst.State.PLAYING)
    print(result)

    return pipeline

pipeline = start_gstreamer("files")

try:
    while True:
        time.sleep(1)
finally:
    pipeline.set_state(Gst.State.NULL)
