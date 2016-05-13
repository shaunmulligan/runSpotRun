# -*- coding: utf-8 -*-
import os, sys, time, re
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


def enableAutoReporting():
    autoCmd = Command(modem, '+AUTOCSQ')
    return autoCmd.set("1,0")


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
    print(settingStr)
    if getGpsConf()[0]:
        print('GPS is already running')
        gpsConf.set("0,2")
        time.sleep(0.2)
        gpsNmeaCmd.set(settingStr)
        time.sleep(0.2)
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


def main():
    humod.actions.PATTERN['location'] = re.compile(r'^\$GPGGA.*')
    humod.actions.PATTERN['signal'] = re.compile(r'^\+CSQ:.*')
    print(humod.actions.PATTERN.keys())
    loc_action = (humod.actions.PATTERN['location'], handleNewLoc)
    rssi_action = (humod.actions.PATTERN['signal'], handleRssi)
    actions = [loc_action, rssi_action]

    try:
        print('connecting...')
        modem.connect()
        print('connected.')
    except Exception as e:
        print(e)

    print('apn: ', checkApn())
    enableAutoReporting()
    enableGps()
    print('gps conf: ', getGpsConf())
    print('starting event prober...')
    modem.prober.start(actions)

    while True:
        time.sleep(5)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        modem.prober.stop()
        disableGps()
        print 'Interrupted'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
