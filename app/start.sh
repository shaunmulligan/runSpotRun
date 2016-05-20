#!/bin/sh

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
  rm runLog.nmea
  rm runUpload.gpx
fi

cp /data/spotify_appkey.key ./spotify_appkey.key
python ./app/theRunner.py
