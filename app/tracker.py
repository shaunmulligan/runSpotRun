# -*- coding: utf-8 -*-
import os, sys, time
import humod
from humod.at_commands import Command
modem = humod.Modem('/dev/ttyUSB2', '/dev/ttyUSB3')

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



def enableGps():
    gpsConf = Command(modem, '+CGPS')
    gpsNmeaCmd = Command(modem, '+CGPSINFOCFG')
    if getGpsConf()[0]:
        print('GPS is already running')
        gpsConf.set("0,2")
        time.sleep(0.2)
        gpsNmeaCmd.set("5,1")
        time.sleep(0.2)
        gpsConf.set("1,2")
    else:
        gpsNmeaCmd.set("5,1")
        time.sleep(0.2)
        gpsConf.set("1,2")
        print('GPS enabled')

def disableGps():
    gpsConf = Command(modem, '+CGPS')
    gpsConf.set("0,2")
    time.sleep(0.2)

def getGpsConf():
    gpsConf = Command(modem, '+CGPS')
    return gpsConf.get()[0].encode('UTF8').split(',',1)


def main():
    print('connecting...')
    modem.connect()
    print('connected.')

    enableGps()

    # Define a new sms handling function.
    def new_sms(modem, message):
        print('New message arrived: %r' % message)
    # Assign the function to the pattern.
    sms_action = (humod.actions.PATTERN['new sms'], new_sms)
    # Create actions list with patterns-action pairs.
    print(humod.actions.PATTERN)
    actions = [sms_action]
    # Enable NMI.
    modem.enable_nmi(True)
    # Start the Prober.
    modem.prober.start(actions)


    while True:
        time.sleep(5)

    modem.disconnect()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        modem.disconnect()
        disableGps()
        print('modem disconnected')
        print 'Interrupted'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
