# -*- coding: utf-8 -*-

import json
import libpybee
import pandas as pd
import requests
import tqdm

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
    """Format track title to a suitable format for REST queries
    :param track_title: track title
    :return: formatted track title.
    """
    to_remove = ('[Extended Mix]', '[Original Mix]', '[Remix]', '[Extended Version]', '[', ']', '?', '(', ')')
    to_replace_by_space = (' × ', ', ')

    for sub_string in to_remove:
        track_title = track_title.replace(sub_string, '')
    for sub_string in to_replace_by_space:
        track_title = track_title.replace(sub_string, ' ')

    return track_title.strip().lower()


def remove_remixer(track_title: str, artist_list: list) -> list:
    """Remove remixer from artist list
    :param track_title: track title
    :param artist_list: artists list
    :return: the artists list without remixer.
    """
    return [artist for artist in artist_list if artist not in track_title]


def search(request_str: str) -> dict:
    """Search track in songstats.com database using their API
    :param request_str: character string including track title and artists involved
    :return: dictionary with track title (according to Songstats, for manual check) and Songstats ID.
    """
    response = requests.get(url="https://api.songstats.com/enterprise/v1/tracks/search",
                            headers={
                                "Accept-Encoding": "",
                                "Accept": "application/json",
                                "apikey": api_key
                            },
                            params={'q': request_str, 'limit': 1}).json()

    if not response['results']:
        return {'s_id': '', 's_title': ''}

    return {'s_id': response['results'][0]['songstats_track_id'], 's_title': response['results'][0]['title']}


'Main'

if __name__ == '__main__':
    MY_LIBRARY = libpybee.Library('../data/lib.xml')  # MusicBee Library File
    dj_global_playlist = MY_LIBRARY.playlists['6301']  # Playlist for Electronic Music

    # Keep 2024 releases and formatting
    tracks_2024_init = [{'title': format_title(track.title),
                         'artist_list': list(map(lambda x: x.lower(), track.artist_list)),
                         'label': list(map(lambda x: x.lower(), track.grouping)),
                         'genre': list(map(lambda x: x.lower(), track.genre))}
                        for track in dj_global_playlist.tracks if track.year == 2024]

    # Create the request string for the Songstats API
    tracks_2024_rq = [{'request': f'{", ".join(remove_remixer(track["title"], track["artist_list"]))} {track["title"]}',
                       'title': track['title'],
                       'artist_list': track['artist_list'],
                       'label': track['label'],
                       'genre': track['genre']} for track in tracks_2024_init]

    # Perform queries
    tracks_2024 = [{'title': track['title'],
                    'artist_list': track['artist_list'],
                    'label': track['label'],
                    'genre': track['genre'],
                    'request': track['request'],
                    'data': search(track['request'])} for track in tqdm.tqdm(tracks_2024_rq)]

    # Store results as JSON file
    with open('../data/selection_2024.json', 'w', encoding='utf-8') as selection_file:
        json.dump(tracks_2024, selection_file, ensure_ascii=False, indent=2, sort_keys=True)
