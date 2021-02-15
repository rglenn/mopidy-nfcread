import time
import threading

from readnfctag import ReadTag


def readcallback(data):
    print('data read: ' + data)

def releasecallback():
    print('released:')

reader = ReadTag('tty:AMA0:pn532', readcallback, releasecallback)
reader.run()

while True:
    print('waiting')
    time.sleep(3)
