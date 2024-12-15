# -*- coding: utf-8 -*-

import ast
import json
import os
import pandas as pd
import pyyoutube as pyt

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

with open('../data/selection_2024.json', 'r', encoding='utf-8') as j_file:
    selection_2024 = json.load(j_file)

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

    if not cred or not cred.valid:  # Cover outdated or non-existant credentials
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


'Main'

if __name__ == '__main__':
    show_missing_s_id(selection_2024)
    # my_service = create_youtube_service()
