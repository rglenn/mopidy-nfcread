from __future__ import absolute_import, unicode_literals

import logging
import os
import sys
import time
import inspect
import traceback

from mopidy import exceptions
import nfc

# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(
                              inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# use this if you want to include modules from a subfolder
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                                 inspect.getfile(inspect.currentframe()))[0],
                                                 "nfc")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

logger = logging.getLogger(__name__)
__logprefix__ = 'NFCread: '


class ReadTag():
    def __init__(self, devicepath, onread_callback):
        self.devicepath = devicepath
        self.onread_callback = onread_callback
        self._running = False

        try:
            self.clf = nfc.ContactlessFrontend(self.devicepath)
        except Exception:
            raise exceptions.FrontendError("Error on nfc reader init:\n" +
                                           traceback.format_exc())

    def run(self):
        try:
            self._running = True
            while self._running:
                tag = self.clf.connect(rdwr={'on-connect': self.__on_connect},
                                       terminate=self.status)
        except Exception:
            raise exceptions.FrontendError("Error in NFC connect():\n" +
                                           traceback.format_exc())
        finally:
            self.clf.close()
            logger.info(__logprefix__ + 'reader shut down')

    def stop(self):
        self._running = False

    def status(self):
        return not self._running

    def __on_connect(self, tag):
        if tag.ndef:
            record = tag.ndef.message[0]
            if record.type == "urn:nfc:wkt:T":
                ndef_text = nfc.ndef.TextRecord(record).text
                self.onread_callback(ndef_text)
            else:
                logger.info(__logprefix__ +
                            'NDEF data not of type "urn:nfc:wkt:T" (text)')
        else:
            logger.info(__logprefix__ + 'No NDEF data found')
        return True
