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
@file_name: data-mining-completion.py
@author: Dylan "dyl-m" Monfret
Script to complete and correct information retrieved with 'data-mining.py'.
"""

with open('../data/selection_2024.json', 'r', encoding='utf-8') as j_file:
    selection_2024 = json.load(j_file)

'Functions'


def show_missing_s_id(track_list: list):
    """Print tracks with missing Songstats ID
    :param track_list: list of dictionaries with track information
    """
    for track in [track for track in selection_2024 if not track['data']['s_id']]:
        print(track['request'])


'Main'

if __name__ == '__main__':
    show_missing_s_id(selection_2024)
