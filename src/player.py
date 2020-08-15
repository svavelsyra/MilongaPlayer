import ctypes
import logging
import os
import time
import vlc

# Windows sleep behaviour constants
ES_CONTINOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

class Player():
    """
    Interface towards vlc-player.
    
    Some enhancements to some methods are done.
    """
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
        """Toggle pause status."""
        self.paused = not self.paused
        self.set_pause(self.paused)

    def set_pause(self, wanted_status):
        """Set pause status to wanted status."""
        self.paused = wanted_status
        self.log.info(f'Setting paused: {wanted_status}')
        self.vlc.set_pause(wanted_status)
        
    def play(self, track=None):
        """
        Play selected track if suplied otherwise
        tell vlc to just play whats loaded currently.
        """
        if track:
            if not os.path.exists(track):
                self.log.warning(f'Could not find track: {track}')
                return
            self.current_track = track
            self.set_mrl(track)
        self.vlc.play()
        start_time = time.monotonic() 
        while not self.is_playing():
            if time.monotonic() - start_time > 5:
                self.log.warning(
                    'Timeout recived in waiting for playback to start')
                return

    def stop(self):
        """Stop playing."""
        self.playing = False
        self.pause = False
        self.vlc.stop()

    def enable_sleep(self):
        """Enable sleep on windows"""
        if os.name == 'nt':
            self.log.info('Enabling sleep')
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINOUS)

    def disable_sleep(self):
        """Disable sleep on windows."""
        if os.name == 'nt':
            self.log.info('Disabling sleep')
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINOUS|ES_SYSTEM_REQUIRED)
