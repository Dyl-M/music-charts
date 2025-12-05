# -*- coding: utf-8 -*-

import collections
import json
import requests
import tqdm

"""File Information
@file_name: data-mining-sstats.py
@author: Dylan "dyl-m" Monfret
Script to get all necessary information from Songstats API
"""

with open('../tokens/songstats_key.txt', 'r', encoding='utf-8') as key_file:
    api_key = key_file.read()

with open('../data/selection_2024.json', 'r', encoding='utf-8') as selection_file:
    # noinspection PyTypeChecker
    selection_2024 = json.load(selection_file)

'Functions'


def get_stats(songstats_id: str) -> dict:
    """Get data from Songstats API
    :param songstats_id: Songstats ID
    :return: a dictionary with Songstats data by platform.
    """
    if not songstats_id:
        return {}

    source_list = ('spotify', 'apple_music', 'amazon', 'deezer', 'tiktok', 'youtube', 'tracklist', 'beatport',
                   'tidal', 'soundcloud')

    response = requests.get(url='https://api.songstats.com/enterprise/v1/tracks/stats',
                            headers={
                                'Accept-Encoding': '',
                                'Accept': 'application/json',
                                'apikey': api_key
                            },
                            params={'songstats_track_id': songstats_id,
                                    'source': ",".join(source_list)}).json()
    try:
        stats_list_dict = [{f'{stats_list["source"].replace("tracklist", "1001tracklists")}_{key}': value
                            for key, value in stats_list['data'].items()}
                           for stats_list in response['stats']]

        flatten_dict = dict(collections.ChainMap(*stats_list_dict))
        flatten_dict.update(get_peaks(songstats_id))

        return flatten_dict

    except KeyError:
        return {}


def get_peaks(songstats_id: str) -> dict:
    """Get peak popularity for a track on Deezer, Spotify and Tidal
    :param songstats_id: Songstats ID
    :return: a dictionary with peak popularity by platform.
    """

    def max_calc(pop_list: list) -> int:
        try:
            return max(pop_list)

        except ValueError:
            return 0

    if not songstats_id:
        return {}

    source_list = ('spotify', 'deezer', 'tidal')

    response = requests.get(url="https://api.songstats.com/enterprise/v1//tracks/historic_stats",
                            headers={
                                'Accept-Encoding': '',
                                'Accept': 'application/json',
                                'apikey': api_key
                            },
                            params={'songstats_track_id': songstats_id,
                                    'start_date': '2024-01-01',
                                    'source': ",".join(source_list)}).json()

    stats = {f'{history["source"]}_popularity_peak': max_calc([track['popularity_current']
                                                               for track in history['data']['history']])
             for history in response['stats']}

    return stats


'Main'

if __name__ == '__main__':
    data_2024 = [{'title': track['title'],
                  'artist_list': track['artist_list'],
                  'label': track['label'],
                  'genre': track['genre'],
                  'request': track['request'],
                  'songstats_identifiers': track['data'],
                  'data': get_stats(track['data']['s_id'])} for track in tqdm.tqdm(selection_2024)]

    # Store results as JSON file
    with open('../data/data_2024.json', 'w', encoding='utf-8') as data_file:
        # noinspection PyTypeChecker
        json.dump(data_2024, data_file, ensure_ascii=False, indent=2, sort_keys=True)
