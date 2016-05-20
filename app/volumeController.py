import alsaaudio
import time
import logging

class VolumeController(object):
    """docstring for VolumeController"""

    logger = logging.getLogger('VolumeController')

    def __init__(self):
        super(VolumeController, self).__init__()
        self.mixer = alsaaudio.Mixer("PCM")
        self.current_volume = self.get_volume()

    def get_volume(self):
        return self.mixer.getvolume()

    def set_volume(self, level):
        self.mixer.setvolume(level)
        self.current_volume = self.get_volume()
        value = self.current_volume[0]
        self.logger.info('set volume level to %i', value)
        return self.mixer.getvolume()

    def volume_up(self):
        current_volume = self.current_volume[0]
        if (current_volume < 95):
            volume = current_volume + 5
            self.set_volume(volume)
        else:
            self.set_volume(100)
        value = self.current_volume[0]
        self.logger.info('volume level increased to %i', value)

    def volume_down(self):
        current_volume = self.current_volume[0]
        if (current_volume > 5):
            volume = current_volume - 5
            self.set_volume(volume)
        else:
            self.set_volume(0)
        value = self.current_volume[0]
        self.logger.info('volume level decreased to %i', value)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    c = VolumeController()
    c.set_volume(50)
    time.sleep(2)
    c.volume_up()
    time.sleep(2)
    time.sleep(2)
    c.volume_down()
    time.sleep(2)
