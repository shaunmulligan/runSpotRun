# -*- coding: utf-8 -*-
import os, sys, time, re, signal
import traceback
import logging
import humod
from humod.at_commands import Command
from serial.tools import list_ports

modemPorts = []

while len(modemPorts) == 0:
    print('searching for modem')
    portList = list_ports.grep("USB")
    for port, desc, hwid in sorted(portList):
        modemPorts.append(port)


# Globals
atPort = modemPorts[2]
dataPort = modemPorts[3]
gpsUpdateRate = 5  # number of seconds between Loc updates

modem = humod.Modem(atPort, dataPort)
print('modem detected')

class Timeout():
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()

def enableAutoReporting():
    autoCmd = Command(modem, '+AUTOCSQ')
    autoCmd.set("1,0")
    print('GPS auto reporting enabled')


def checkApn():
    apnCmd = Command(modem, '+CGSOCKCONT')
    return apnCmd.get()[0]


def syncModemTime():
    #xtraGps = Command(modem, '+CGPSXE')
    #xtraSetup = Command(modem, '+CGPSXD')
    setServerCmd = Command(modem, '+CHTPSERV')
    setServerCmd.set('\"ADD\", "www.google.com", 80, 1')
    timeSync = Command(modem, '+CHTPUPDATE')
    timeSync.run()


def getTime():
    timeCmd = Command(modem, '+CCLK')
    return timeCmd.get()


def getGpsConf():
    gpsConf = Command(modem, '+CGPS')
    return gpsConf.get()[0].encode('UTF8').split(',', 1)


def enableGps():
    gpsConf = Command(modem, '+CGPS')
    gpsNmeaCmd = Command(modem, '+CGPSINFOCFG')
    settingStr = "%s,1" % str(gpsUpdateRate)

    if getGpsConf()[0]:
        print('GPS is already running')
        gpsConf.set("0,2")
        time.sleep(1)
        gpsNmeaCmd.set(settingStr)
        time.sleep(1)
        gpsConf.set("1,2")
    else:
        gpsNmeaCmd.set(settingStr)
        time.sleep(0.2)
        gpsConf.set("1,2")
        print('GPS enabled')


def disableGps():
    gpsConf = Command(modem, '+CGPS')
    gpsConf.set("0,2")
    time.sleep(0.2)
    print('GPS disabled')


def handleNewLoc(modem, message):
    print(message)


def handleRssi(modem, message):
    print(message)


def cleanup(*args):
    print 'cleaning up...'
    modem.prober.stop()
    modem.disconnect()
    disableGps()
    os._exit

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    humod.actions.PATTERN['location'] = re.compile(r'^\$GPGGA.*')
    humod.actions.PATTERN['signal'] = re.compile(r'^\+CSQ:.*')
    loc_action = (humod.actions.PATTERN['location'], handleNewLoc)
    rssi_action = (humod.actions.PATTERN['signal'], handleRssi)
    actions = [loc_action, rssi_action]

    try:
        with Timeout(10):
            print('connecting...')
            modem.connect()
            print('connected.')
    except Timeout.Timeout:
        print "Couldn't connect, Timed out!"

    try:
        print('apn: ', checkApn())
        enableAutoReporting()
        enableGps()
        print('gps conf: ', getGpsConf())
    except Exception as e:
        logging.error(traceback.format_exc())

    print('starting event prober...')
    modem.prober.start(actions)

    while True:
        time.sleep(5)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        modem.prober.stop()
        modem.disconnect()
        disableGps()
        print 'Interrupted'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    finally:
        print("cleaning up")
        modem.prober.stop()
        modem.disconnect()
        disableGps()
