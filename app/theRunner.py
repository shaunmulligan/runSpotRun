#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time, re, signal
import subprocess, uuid, logging

import humod
from humod.at_commands import Command
from serial.tools import list_ports
from spotifyPlayer import SpotifyPlayer
from nmeaConverter import Converter
# from volumeController import VolumeController
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
# GPIO 23, 24 & 25 set up as inputs, pulled up to avoid false detection.
# ports are wired to connect to GND on button press.
# So we'll be setting up falling edge detection for both
STOP_START_BTN = 25
SKIP_BTN = 24
MODE_BTN = 23
GPIO.setup(MODE_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STOP_START_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SKIP_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
filename = "/data/runLog.nmea"
username = os.environ['SPOT_USER']
password = os.environ['SPOT_PASS']
spotifyUri = 'spotify:user:fiat500c:playlist:54k50VZdvtnIPt4d8RBCmZ'
player = None

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

try:
    with Timeout(10):
        print('Creating Global Spotify object')
        player = SpotifyPlayer()
except Timeout.Timeout:
    print "Couldn't create spotify, Timed out!"
except Exception as e:
    print(e)
# audio = VolumeController()

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


    try:
        subprocess.Popen("route delete -net 0.0.0.0/0 ppp0")
        print 'Stopping Modem'
        modem.disconnect()
    except Exception as e:
        print 'Cant cleanup modem'

    print 'Stopping GPS'
    disableGps()
    print 'Cleaning up GPIO'
    GPIO.cleanup()
    print 'Stopping Prober'
    modem.prober.stop()
    print 'cleaning up...'

# signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def handleStartStopButton(channel):
    global logGps
    global filename
    global player
    # global audio
    if (GPIO.input(MODE_BTN) == GPIO.LOW):
        print 'Increase Volume'
        # audio.volume_up()
    else:
        if logGps:
            print "======== Stopping Tracking ========"
            logGps = False
            player.do_pause()
            nmeaFile = Converter()
            nmeaFile.convert(filename,"/data/runUpload.gpx")
        else:
            print "======== Starting a run ========"
            logGps = True

            # player.play_track_from_current_playlist(17)
            player.do_resume()


def handleSkipButton(channel):
    # global audio
    if (GPIO.input(MODE_BTN) == GPIO.LOW):
        print 'Decrease Volume'
        # audio.volume_down()
    else:
        print "skipping to next song"
        global player
        player.play_next_track()

GPIO.add_event_detect(STOP_START_BTN, GPIO.FALLING, callback=handleStartStopButton, bouncetime=300)

GPIO.add_event_detect(SKIP_BTN, GPIO.FALLING, callback=handleSkipButton, bouncetime=300)

def main():
    logging.basicConfig(level=logging.INFO)
    global spotifyUri
    global username
    global password
    global player
    # global audio
    humod.actions.PATTERN['location'] = re.compile(r'^\$GPGGA.*')
    humod.actions.PATTERN['signal'] = re.compile(r'^\+CSQ:.*')
    loc_action = (humod.actions.PATTERN['location'], handleNewLoc)
    rssi_action = (humod.actions.PATTERN['signal'], handleRssi)
    actions = [loc_action, rssi_action]

    # audio.set_volume(50)

    try:
        with Timeout(10):
            print('connecting...')
            modem.connect()
            print('connected.')
            # Start routing internet through modem
            subprocess.Popen("route add -net 0.0.0.0/0 ppp0")
    except Timeout.Timeout:
        print "Couldn't connect, Timed out!"
    except Exception as e:
        print(e)

    try:
        with Timeout(10):
            print('logging into spotify')
            player.do_login(username,password)
    except Timeout.Timeout:
        print "Couldn't login to spotify, Timed out!"
    except Exception as e:
        print(e)

    try:
        with Timeout(10):
            print('Start spotify playlist')
            player.playlist = player.get_playlist_from_uri(spotifyUri)
            player.play_track_from_current_playlist(3)
            player.do_pause()
    except Timeout.Timeout:
        print "Couldn't login to spotify, Timed out!"
    except Exception as e:
        print(e)

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

    try:
        print('starting event prober...')
        modem.prober.start(actions)
    except Exception as e:
        print(e)

    print('======== Ready to Run!!! ========')
    while True:
        time.sleep(5)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print 'Interrupted'
        sys.exit(0)
    finally:
        print("All cleaned up")
