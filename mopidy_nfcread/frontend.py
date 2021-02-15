from __future__ import absolute_import, unicode_literals

from threading import Thread
import traceback
import logging
import pykka

from mopidy import core
from .readnfctag import ReadTag

logger = logging.getLogger(__name__)
__logprefix__ = 'NFCread: '


class NFCread(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(NFCread, self).__init__()
        self.core = core
        self.devicepath = str(config['nfcread']['devicepath'])
        self.tagReader = ReadTag(self.devicepath,
                                 self.ndef_read_callback,
                                 self.release_callback)
        self.tagReaderThread = None

    def ndef_read_callback(self, data):
        self.core.tracklist.clear()
        logger.info(__logprefix__ + ' got uri = ' + data + ', starting playback')
        self.core.tracklist.add(uris=[data])
        logger.info(__logprefix__ + ' added to tracklist')
        self.core.playback.play()

    # TODO: the action should be configurable
    def release_callback(self):
        logger.info(__logprefix__ + ' card released, stopping playback')
        self.core.playback.stop()
        self.core.tracklist.clear()

    def on_start(self):
        try:
            self.tagReaderThreaded = Thread(target=self.tagReader.run)
            self.tagReader.daemon = True
            self.tagReaderThreaded.start()
            logger.info(__logprefix__ + ' started reader thread')
        except Exception:
            traceback.print_exc()

    def on_stop(self):
        logger.info(__logprefix__ + 'stopping extension')
        self.tagReader.stop()
