# -*- coding: utf-8 -*-

import json
import libpybee
import pandas as pd
import requests

# Pandas options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 275)

"""File Information
@file_name: data-mining.py
@author: Dylan "dyl-m" Monfret
Script for exploring and harvesting data from the MusicBee library and Songstats API
"""

with open('../token/songstats_key.txt', 'r', encoding='utf-8') as key_file:
    api_key = key_file.read()

'Functions'


def format_title(track_title: str) -> str:
    """
    :param track_title:
    :return:
    """
    to_remove = ('[Extended Mix]', '[Original Mix]', '[Remix]', '[Extended Version]', '[', ']', '?', '.', '(', ')')
    to_replace_by_space = (' × ', ', ')

    for sub_string in to_remove:
        track_title = track_title.replace(sub_string, '')
    for sub_string in to_replace_by_space:
        track_title = track_title.replace(sub_string, ' ')

    return track_title.strip().lower()


def remove_remixer(track_title: str, artist_list: list) -> list:
    """
    :param track_title:
    :param artist_list:
    :return:
    """
    return [artist for artist in artist_list if artist not in track_title]


def search(request_str: str) -> dict:
    """
    :param request_str:
    :return:
    """
    response = requests.get(url="https://api.songstats.com/enterprise/v1/tracks/search",
                            headers={
                                "Accept-Encoding": "",
                                "Accept": "application/json",
                                "apikey": api_key
                            },
                            params={'q': request_str, 'limit': 1})

    return response.json()


'Main'

MY_LIBRARY = libpybee.Library('../../../../Music/MusicBee/iTunes Music Library.xml')
dj_global_playlist = MY_LIBRARY.playlists['6543']

tracks_2024_init = [{'title': format_title(track.title),
                     'artist_list': list(map(lambda x: x.lower(), track.artist_list)),
                     'genre': list(map(lambda x: x.lower(), track.genre))}
                    for track in dj_global_playlist.tracks if track.year == 2024]

tracks_2024_rq = [{'title': track['title'], 'artist_list': track['artist_list'], 'genre': track['genre'],
                   'request': f'{", ".join(remove_remixer(track["title"], track["artist_list"]))} {track["title"]}'}
                  for track in tracks_2024_init]

tracks_2024 = [{'title': track['title'],
                'artist_list': track['artist_list'],
                'genre': track['genre'],
                'request': track['request'],
                'data': search(track['request'])} for track in tracks_2024_rq]

with open('../data/selection_2024.json', 'w', encoding='utf-8') as selection_file:
    json.dump(tracks_2024, selection_file, ensure_ascii=False, indent=4)
