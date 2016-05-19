#!/bin/sh

# Get the spotify api key
key=/data/spotify_appkey.key
if [ ! -e "key" ]; then
  echo "creating spotify app key"
  echo $APP_KEY | base64 -d > /data/spotify_appkey.key
else
    echo "Spotify Key already exists"
fi

python ./app/theRunner.py
