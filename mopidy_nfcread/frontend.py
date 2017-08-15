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
        self.tagReader = ReadTag(self.devicepath, self.ndef_read_callback)
        self.tagReaderThread = None

    def ndef_read_callback(self, data):
        self.core.tracklist.clear()
        self.core.tracklist.add(None, None, data, None)
        self.core.playback.play()

    def on_start(self):
        try:
            self.tagReaderThreaded = Thread(target=self.tagReader.start)
            self.tagReader.daemon = True
            self.tagReaderThreaded.start()
            logger.info(__logprefix__ + ' started reader thread')
        except Exception:
            traceback.print_exc()

    def on_stop(self):
        logger.warning(__logprefix__ + 'stopping extension')
        self.tagReader.stop()
