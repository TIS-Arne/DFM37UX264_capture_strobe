import gi

from PIL import Image, ImageDraw, ImageFont
import Jetson.GPIO as GPIO
import os
import threadsched


gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GLib, GObject, GstBase, GstVideo

Gst.init(None)


VIDEOCAPS = Gst.Caps(Gst.Structure("video/x-bayer",
                                   width=Gst.IntRange(range(1, GLib.MAXINT)),
                                   height=Gst.IntRange(range(1, GLib.MAXINT)),
                                   framerate=Gst.FractionRange(Gst.Fraction(1,1), Gst.Fraction(GLib.MAXINT, 1))
                                   ))



class ImgProc(GstBase.BaseTransform):
    __gstmetadata__ = ("ImgProc", "Filter", "Process image data", "Arne Caspari")

    __gsttemplates__ = (
        Gst.PadTemplate.new("src",
            Gst.PadDirection.SRC,
            Gst.PadPresence.ALWAYS,
            VIDEOCAPS ),
        Gst.PadTemplate.new("sink",
            Gst.PadDirection.SINK,
            Gst.PadPresence.ALWAYS,
            VIDEOCAPS ))

    def __init__(self):
        GstBase.BaseTransform.__init__(self)
        self.set_in_place(True)

        self.videoinfo = GstVideo.VideoInfo()

        self.last_gpio_ts = 0
        self.last_buf_ts = 0

        GPIO.setmode(GPIO.BOARD)
        channel = 16
        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
        GPIO.add_event_detect(channel, GPIO.FALLING, callback=self.gpio_event)


    def __del__(self):
        GPIO.cleanup()


    def gpio_event(self, channel):
        policy, prio = threadsched.get_curschedparam()
        if policy != threadsched.SCHED_RR:
            ret = threadsched.set_curschedparam(threadsched.SCHED_RR, 10)
            if ret == 0:
                print("gpio: moved to RT scheduler")

        clock = self.get_clock()
        # The clock will only be present after the stream got started,
        # but GPIO events will come all the time
        if (clock):
            ts = clock.get_time()
            dt = ts - self.last_gpio_ts
            self.last_gpio_ts = ts
            print("gpio:", Gst.TIME_ARGS(ts), "dt:", Gst.TIME_ARGS(dt))


    def do_transform_ip(self, buf: Gst.Buffer) -> Gst.FlowReturn:
        policy, prio = threadsched.get_curschedparam()
        if policy != threadsched.SCHED_RR:
            ret = threadsched.set_curschedparam(threadsched.SCHED_RR, 10)
            if ret == 0:
                print("gstreamer: moved to RT scheduler")

        ts = self.base_time + buf.pts
        dt = ts - self.last_buf_ts
        self.last_buf_ts = ts
        print("buf :", Gst.TIME_ARGS(ts), "dt:", Gst.TIME_ARGS(dt))

        return Gst.FlowReturn.OK


    def do_set_caps(self, icaps: Gst.Caps, ocaps: Gst.Caps) -> bool:
        self.videoinfo.from_caps(icaps)
        return True

GObject.type_register(ImgProc)
__gstelementfactory__ = ("imgproc", Gst.Rank.NONE, ImgProc)
