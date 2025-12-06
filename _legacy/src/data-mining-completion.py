# -*- coding: utf-8 -*-

import ast
import itertools
import json
import os
import pandas as pd
import pyyoutube as pyt
import requests
import tqdm

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Pandas options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 275)

"""File Information
@file_name: data-mining-completion.py
@author: Dylan "dyl-m" Monfret
Script to complete and correct information retrieved with 'data-mining-prep.py'.
"""

with open('../tokens/songstats_key.txt', 'r', encoding='utf-8') as key_file:
    api_key = key_file.read()

with open('../data/selection_2024.json', 'r', encoding='utf-8') as j_file:
    selection_2024 = json.load(j_file)

with open('../data/data_2024.json', 'r', encoding='utf-8') as d_file:
    data_2024 = json.load(d_file)

with open('../data/ytb_2024.json', 'r', encoding='utf-8') as y_file:
    ytb_2024 = json.load(y_file)

playlist = 'PLOMUdQFdS-XNqUpFzE89aHgwn0wrBidyG'

'Functions'


def show_missing_s_id(track_list: list):
    """Print tracks with missing Songstats ID
    :param track_list: list of dictionaries with track information
    """
    for track in [track for track in track_list if not track['data']['s_id']]:
        print(track['request'])


def create_youtube_service():
    """Create a GCP service for YouTube API V3.
    Mostly inspired by this: https://learndataanalysis.org/google-py-file-source-code/
    :return service: a Google API service object build with 'googleapiclient.discovery.build'.
    """
    oauth_file = '../tokens/oauth.json'  # OAUTH 2.0 ID path
    scopes = ['https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/youtube.force-ssl']
    cred = None

    if os.path.exists('../tokens/credentials.json'):
        cred = Credentials.from_authorized_user_file('../tokens/credentials.json')  # Retrieve credentials

    if not cred or not cred.valid:  # Cred outdated or non-existant credentials
        if cred and cred.expired and cred.refresh_token:
            try:
                cred.refresh(Request())

            except RefreshError:
                print('Credentials can not be refreshed. New credentials needed.')
                flow = InstalledAppFlow.from_client_secrets_file(oauth_file, scopes)  # Create a Flow from 'oauth_file'
                cred = flow.run_local_server()  # Run authentication process

        else:
            # Create the authentification Flow from 'oauth_file' and then run authentication process
            flow = InstalledAppFlow.from_client_secrets_file(oauth_file, scopes)
            cred = flow.run_local_server()

        with open('../tokens/credentials.json', 'w') as cred_file:  # Save credentials as a JSON file
            # noinspection PyTypeChecker
            json.dump(ast.literal_eval(cred.to_json()), cred_file, ensure_ascii=False, indent=4)

    try:
        service = pyt.Client(client_id=cred.client_id, client_secret=cred.client_secret, access_token=cred.token)
        print('YouTube service created successfully.')
        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        raise error


def get_youtube_playlist_videos(service: pyt.Client, playlist_id: str) -> dict:
    """Get the videos in a YouTube playlist
    :param service: a Python YouTube Client
    :param playlist_id: a YouTube playlist ID
    :return: playlist items (videos) as a dictionary.
    """
    p_items = {}
    next_page_token = None

    while True:
        try:
            request = service.playlistItems.list(part=['snippet', 'contentDetails'],
                                                 playlist_id=playlist_id,
                                                 max_results=50,
                                                 pageToken=next_page_token)  # Request playlist's items

            # Keep necessary data
            p_items.update({item.contentDetails.videoId: item.snippet.title for item in request.items})

            next_page_token = request.nextPageToken

            if next_page_token is None:
                break

        except pyt.error.PyYouTubeException as error:
            raise error

    return p_items


def get_songstats_youtube_videos(songstats_id: str):
    if not songstats_id:
        return {}

    response = requests.get(url='https://api.songstats.com/enterprise/v1/tracks/stats',
                            headers={
                                'Accept-Encoding': '',
                                'Accept': 'application/json',
                                'apikey': api_key
                            },
                            params={'songstats_track_id': songstats_id,
                                    'with_videos': 'true',
                                    'source': 'youtube'}).json()

    yt_stats = [{'ytb_id': item['external_id'],
                 'views': item['view_count'],
                 'channel_name': item['youtube_channel_name']} for item in response['stats'][0]['data']['videos']]

    try:
        most_viewed = [vid for vid in yt_stats if ' - Topic' not in vid['channel_name']][0]

    except IndexError:
        most_viewed = {}

    yt_results = {
        'most_viewed': most_viewed,
        'all_sources': [vid['ytb_id'] for vid in yt_stats]
    }

    return yt_results


def show_most_viewed_missing():
    ytb_vid = [{'songstats_identifiers': track['songstats_identifiers'],
                'data': get_songstats_youtube_videos(track['songstats_identifiers']['s_id'])}
               for track in tqdm.tqdm(data_2024)]

    # Store results as JSON file
    with open('../data/ytb_2024.json', 'w', encoding='utf-8') as ytb_file:
        # noinspection PyTypeChecker
        json.dump(ytb_vid, ytb_file, ensure_ascii=False, indent=2, sort_keys=True)

    missing_video = [vid for vid in ytb_vid if not vid['data'].get('most_viewed')]

    for vid in missing_video:
        print(vid['songstats_identifiers']['s_id'], vid['songstats_identifiers']['s_title'])


def show_missing_source_from_youtube():
    my_service = create_youtube_service()
    videos_in_playlist = get_youtube_playlist_videos(my_service, playlist)
    sources_songstats = set(itertools.chain(*[item['data']['all_sources'] for item in ytb_2024]))
    missing_source = [(f'https://youtu.be/{v_id}', title) for v_id, title in videos_in_playlist.items() if
                      v_id not in sources_songstats]

    for item in missing_source:
        print(item)


def check_sources(threshold: int):
    validated = {'nl3bivek', 'bvrp6jlh', 'z90p25na', 'cxsruom1', '5fc29dga', 'mbjr7uin', 's0yn3m2g', 'iukgelph',
                 't2bi3g69', 'ghzbn7s1', 'nwqit015', 'a7z986yl', 'm0q9nujb', 'b4razlvm', 'mlwfg9v4', 'r3nlk0we'}

    source_list = {'spotify', 'apple_music', 'amazon', 'deezer', 'youtube', 'beatport', 'tidal', 'soundcloud'}

    for item in data_2024:
        response = requests.get(url='https://api.songstats.com/enterprise/v1/tracks/info',
                                headers={
                                    'Accept-Encoding': '',
                                    'Accept': 'application/json',
                                    'apikey': api_key
                                },
                                params={'songstats_track_id': item['songstats_identifiers']['s_id'],
                                        'with_videos': 'true',
                                        'source': 'youtube'}).json()

        found_source = set(track['source'] for track in response['track_info']['links'])
        check = all(e in found_source for e in source_list)

        if not check and len(found_source) < threshold and item['songstats_identifiers']['s_id'] not in validated:
            print(item['songstats_identifiers']['s_id'], item['songstats_identifiers']['s_title'])
            print(f'{found_source}\n')


'Main'

if __name__ == '__main__':
    print('Hello world!')
