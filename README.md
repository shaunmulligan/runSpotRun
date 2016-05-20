# GPS + Spotify + Resin.io

### What you need:
* Any Raspberry Pi
* pHat DAC hat [link]()
* FONA 3G board [link]()
* Adafruit Power-Boost 1000 Basic [link]()
* a 3G capable SIM card with data/credit
* Some push buttons
* A premium Spotify Account


#### Convert app key to base64
To get your spotify_appkey.key file on to your device we will use resin environment variables, but to do this we need to convert the `.key` file in to a base64 string. This can be done on OSX like so:
`base64 -i spotify_appkey.key `
Now take that output sting and add an Env Var on the resin.io Dashboard called `APP_KEY`

You will also need two other Env Vars, namely `SPOT_USER` and `SPOT_PASS` which are obviously your user login credentials for spotify.
