from os import walk
from os import path
from os import sep
from pygame.mixer import Sound
import logging

SOUND_DIR = path.abspath(
    path.join(
        path.dirname(__file__),
        '..',
        'assets',
        'sound'))


class SoundBank:
    """Prefetches and holds sounds. A soundbank will be configured with a base
    sound path, where the files are stored. The sounds files can be accessed
    with a key which is constructed from the path relative to the sound path.

        Args:
            sound_path (string): The base path of the sound files for this bank.
    """
    logger = logging.getLogger('sound.SoundBank')

    def __init__(self, sound_path=SOUND_DIR):
        self.sound_path = sound_path
        self.sounds = {}
        self.__prefetch_soundfiles()

    def __prefetch_soundfiles(self):
        self.logger.debug('Prefetch sound files from %s', self.sound_path)
        for root, dirs, sfiles in walk(self.sound_path):
            for sound_file in sfiles:
                self.__add_sound(root, sound_file)

    def __add_sound(self, root, sound_file):
        filename = path.join(root, sound_file)
        key = path.join(root.lstrip(self.sound_path), sound_file)
        key = key.replace(sep, '.').lstrip('.')
        self.logger.debug('Add sound %s', key)
        self.sounds[key] = Sound(filename)

    def get(self, key):
        """Get a Sound from the bank.

            Args:
                key (string): A Key in form 'package.sound.wav'

            Rerturns:
                A pygame.mixer.Sound object or None if the key does not exists.
        """
        return self.sounds.get(key)
