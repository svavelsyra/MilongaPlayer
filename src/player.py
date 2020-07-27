import ctypes
import logging
import os
import vlc

# Windows sleep behaviour constants
ES_CONTINOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

class Player():
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.Player')
        self.vlc = vlc.MediaPlayer(*args, **kwargs)
        self.playing = False
        self.paused = False
        self.current_track = None
        self.t = None

    def __getattr__(self, item):
        return getattr(self.vlc, item)

    def __enter__(self):
        self.disable_sleep()
        return self

    def __exit__(self, *args):
        self.enable_sleep()
        self.vlc.stop()        

    def pause(self):
        self.paused = not self.paused
        self.set_pause(self.paused)

    def set_pause(self, wanted_status):
        self.paused = wanted_status
        self.vlc.set_pause(wanted_status)
        
    def play(self, track=None):
        if track:
            self.set_mrl(track)
        self.vlc.play()
        while not self.is_playing():
            pass

    def stop(self):
        self.playing = False
        self.pause = False
        self.vlc.stop()

    def enable_sleep(self):
        if os.name == 'nt':
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINOUS)

    def disable_sleep(self):
        if os.name == 'nt':
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINOUS|ES_SYSTEM_REQUIRED)
