#!/bin/sh

modprobe i2c-bcm2708
modprobe snd-soc-pcm512x
modprobe snd-soc-wm8804

# Get the spotify api key
key=/data/spotify_appkey.key
if [ ! -e "key" ]; then
  echo "creating spotify app key"
  echo $APP_KEY | base64 -d > /data/spotify_appkey.key
  echo "key created............"
else
    echo "Spotify Key already exists"
fi

# remove all old run logs
if [ -e "/data/runLog.nmea" ]; then
  echo "Removing old running logs..."
  rm /data/runLog.nmea
  rm /data/runUpload.gpx
fi

cp /data/spotify_appkey.key ./spotify_appkey.key
exec /usr/src/app/app/theRunner.py
#exec /usr/src/app/app/spotifyPlayer.py
echo "starting..."
