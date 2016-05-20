# Use base image for device arch with node installed
FROM resin/raspberrypi-python:2.7-20160506

RUN wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
RUN sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list

RUN apt-get update && apt-get install -yq \
   libasound2-dev libspotify-dev python-serial ppp && \
   apt-get clean && rm -rf /var/lib/apt/lists/*

# create src dir
RUN mkdir -p /usr/src/app/
COPY asound.conf /etc/asound.conf
# set as WORKDIR
WORKDIR /usr/src/app

# Copy requirements.txt first for better cache on later pushes
COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the resin.io build server
RUN pip install -r /requirements.txt

COPY entry.sh /usr/bin/entry.sh

# Copy all of files here for caching purposes
COPY . ./

ENV INITSYSTEM=off

# runs the start script on container start
CMD ["./app/start.sh"]
