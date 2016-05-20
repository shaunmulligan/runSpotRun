#!/usr/bin/env python

"""
This is an example of a simple command line client for Spotify using pyspotify.

You can run this file directly::

    python shell.py

Then run the ``help`` command on the ``spotify>`` prompt to view all available
commands.
"""

from __future__ import unicode_literals

import logging
import threading
import time

import spotify


class SpotifyPlayer:

    logger = logging.getLogger('SpotifyPlayer')

    def __init__(self):

        self.logged_in = threading.Event()
        self.logged_out = threading.Event()
        self.logged_out.set()
        self.config = spotify.Config()
        self.config.cache_location = '/data'
        # self.config.application_key = '/data/spotify_appkey.key'

        self.session = spotify.Session(config=self.config)
        self.session.on(spotify.SessionEvent.CONNECTION_STATE_UPDATED,self.on_connection_state_changed)
        self.session.on(spotify.SessionEvent.END_OF_TRACK, self.on_end_of_track)

        try:
            self.audio_driver = spotify.AlsaSink(self.session)
        except ImportError:
            self.logger.warning(
                'No audio sink found; audio playback unavailable.')
        # Default playlist
        self.playlist = None
        self.playlist_index = 0

        self.event_loop = spotify.EventLoop(self.session)
        self.event_loop.start()


    def on_connection_state_changed(self, session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            self.logged_in.set()
            self.logged_out.clear()
        elif session.connection.state is spotify.ConnectionState.LOGGED_OUT:
            self.logged_in.clear()
            self.logged_out.set()

    def on_end_of_track(self, session):
        self.logger.info('track ended')
        self.playlist_index += 1
        self.logger.info('playing song %i of playlist.', self.playlist_index)
        self.play_track_from_current_playlist(self.playlist_index)
        #self.session.player.play(False)

    def do_login(self, username, password):
        self.session.login(username, password, remember_me=True)
        self.logged_in.wait()

    def do_logout(self, line):
        "logout"
        self.session.logout()
        self.logged_out.wait()

    def do_whoami(self, line):
        "whoami"
        if self.logged_in.is_set():
            self.logger.info(
                'I am %s aka %s. You can find me at %s',
                self.session.user.canonical_name,
                self.session.user.display_name,
                self.session.user.link)
        else:
            self.logger.info(
                'I am not logged in, but I may be %s',
                self.session.remembered_user)

    def do_play_uri(self, line):
        "play <spotify track uri>"
        if not self.logged_in.is_set():
            self.logger.warning('You must be logged in to play')
            return
        try:
            track = self.session.get_track(line)
            track.load()
        except (ValueError, spotify.Error) as e:
            self.logger.warning(e)
            return
        self.logger.info('Loading track into player')
        self.session.player.load(track)
        self.logger.info('Playing "%s" by %s',track.name, track.artists[0].name)
        self.session.player.play()

    def do_pause(self):
        self.logger.info('Pausing track')
        self.session.player.play(False)

    def do_resume(self):
        self.logger.info('Resuming track')
        self.session.player.play()

    def do_stop(self):
        self.logger.info('Stopping track')
        self.session.player.play(False)
        self.session.player.unload()

    def do_seek(self, seconds):
        "seek <seconds>"
        if not self.logged_in.is_set():
            self.logger.warning('You must be logged in to seek')
            return
        if self.session.player.state is spotify.PlayerState.UNLOADED:
            self.logger.warning('A track must be loaded before seeking')
            return
        self.session.player.seek(int(seconds) * 1000)

    def do_search(self, query):
        "search <query>"
        if not self.logged_in.is_set():
            self.logger.warning('You must be logged in to search')
            return
        try:
            result = self.session.search(query)
            result.load()
        except spotify.Error as e:
            self.logger.warning(e)
            return
        self.logger.info(
            '%d tracks, %d albums, %d artists, and %d playlists found.',
            result.track_total, result.album_total,
            result.artist_total, result.playlist_total)
        self.logger.info('Top tracks:')
        for track in result.tracks:
            self.logger.info(
                '[%s] %s - %s', track.link, track.artists[0].name, track.name)

    def get_playlist_from_uri(self, uri):
        "get a playlist <spotify playlist uri>"
        if not self.logged_in.is_set():
            self.logger.warning('You must be logged in to play')
            return
        try:
            playlist = self.session.get_playlist(uri)
            playlist.load()
        except (ValueError, spotify.Error) as e:
            self.logger.warning(e)
            return
        self.logger.info('Loading playlist ')
        return playlist

    def play_track_from_current_playlist(self, index):
        current_playlist = self.playlist.tracks
        self.logger.info('current playlist has %i songs',len(current_playlist))
        self.logger.info('requested song index is: %i',index)
        if (index > len(current_playlist)):
            self.logger.info('index to large, returning to start of playlist')
            self.playlist_index = 0
        else:
            self.playlist_index = index

        trackUri = current_playlist[self.playlist_index].link.uri
        self.logger.info('playing track %i of playlist.', self.playlist_index)
        self.do_play_uri(trackUri)

    def play_next_track(self):
        current_index = self.playlist_index
        self.logger.info('skipping to next track')
        self.play_track_from_current_playlist(current_index+1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    player = SpotifyPlayer()
    player.do_login('your_user_name','your_password')
    player.playlist = player.get_playlist_from_uri('spotify:user:fiat500c:playlist:54k50VZdvtnIPt4d8RBCmZ')
    player.play_track_from_current_playlist(6)
    time.sleep(10)
    player.play_next_track()
    time.sleep(10000)
