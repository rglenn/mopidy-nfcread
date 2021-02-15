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
    def __init__(self, devicepath, onread_callback, onrelease_callback):
        self.devicepath = devicepath
        self.onread_callback = onread_callback
        self.onrelease_callback = onrelease_callback
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
                # poll for a tag. by default poll 5 times every 0.5 sec.
                # the terminate function should avoid that, but there
                # seems to be a catch after some time (or hardware issue?).
                tag = self.clf.connect(rdwr={
                                             'on-connect': self.__on_connect,
                                             'on-release': self.__on_release
                                            },
                                       terminate=self.status)
                # sleep for 0.5 seconds to avoid a direct reopen on serial
                # interfaces (e.g. on RasPi) leading to device blocking
                # timeouts...
                # (0.5s is just the same as nfcpy does by default...)
                # NOTE: absolute import necessary, hit exceptions
                # about not known functions when shutting down mopidy.
                time.sleep(0.5)
        except Exception:
            raise exceptions.FrontendError("Error in NFC connect():\n" +
                                           traceback.format_exc())
        finally:
            self.clf.close()
            logger.debug(__logprefix__ + 'reader shut down')

    def stop(self):
        self._running = False

    def status(self):
        return not self._running

    def __on_connect(self, tag):
        if tag.ndef:
            record = tag.ndef.records[0]
            if record.type == "urn:nfc:wkt:U":
                ndef_text = record.uri
                logger.info(__logprefix__ + 'tag found, uri is ' + ndef_text)
                self.onread_callback(ndef_text)
            else:
                logger.info(__logprefix__ +
                            'NDEF data not of type "urn:nfc:wkt:T" (text)')
        else:
            logger.info(__logprefix__ + 'No NDEF data found')
        # returning True lets connect() wait until the tag is no longer present
        # so we have a debounced state
        return True

    def __on_release(self, tag):
        logger.info(__logprefix__ + 'tag released, executing callback')
        self.onrelease_callback()
