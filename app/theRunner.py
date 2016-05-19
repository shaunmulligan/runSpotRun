# -*- coding: utf-8 -*-
import os, sys, time, re, signal
import subprocess, uuid

import humod
from humod.at_commands import Command
from serial.tools import list_ports
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
# GPIO 23, 24 & 17 set up as inputs, pulled up to avoid false detection.
# Both ports are wired to connect to GND on button press.
# So we'll be setting up falling edge detection for both
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

modemPorts = []

while True:
    print('searching for modem')
    portList = list_ports.grep("USB")
    for port, desc, hwid in sorted(portList):
        modemPorts.append(port)
    if len(modemPorts) > 0:
        print('modem detected')
        break
    time.sleep(10)

# Globals
atPort = modemPorts[2]
dataPort = modemPorts[3]
gpsUpdateRate = 5  # number of seconds between Loc updates
logGps = False # Boolean value to determine if we log GPS to file or not

filename = "/data/place-holder-name.nmea"

print "GPS data will be logged to: " + filename

modem = humod.Modem(atPort, dataPort)

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
    global logGps
    global filename
    if logGps:
        print(message)
        with open(filename, 'a') as f:
            f.write(message)


def handleRssi(modem, message):
    global logGps
    if logGps:
        print(message)


def cleanup(*args):
    print 'cleaning up...'
    modem.prober.stop()
    modem.disconnect()
    subprocess.Popen("route delete -net 0.0.0.0/0 ppp0")
    disableGps()
    GPIO.cleanup()           # clean up GPIO on normal exit
    os._exit

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def handleStartStopButton(channel):
    global logGps
    global filename
    if logGps:
        print "======== Stopping Tracking ========"
        logGps = False
    else:
        print "======== Starting a run ========"
        logGps = True
        uniqFileId = str(uuid.uuid4())
        filename = "/data/" + uniqFileId + ".nmea"

def handleSkipButton(channel):
    print "skipping to next song"

GPIO.add_event_detect(17, GPIO.FALLING, callback=handleStartStopButton, bouncetime=300)

GPIO.add_event_detect(23, GPIO.FALLING, callback=handleSkipButton, bouncetime=300)

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
            # Start routing internet through modem
            # subprocess.Popen("route add -net 0.0.0.0/0 ppp0")
    except Timeout.Timeout:
        print "Couldn't connect, Timed out!"

    try:
        with Timeout(40):
            print('apn: ', checkApn())
            enableAutoReporting()
            enableGps()
            print('gps conf: ', getGpsConf())
    except Timeout.Timeout:
        print "Couldn't connect, Timed out!"
    except Exception as e:
        print(e)

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
        # subprocess.Popen("route delete -net 0.0.0.0/0 ppp0")
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
        subprocess.Popen("route delete -net 0.0.0.0/0 ppp0")
        disableGps()
