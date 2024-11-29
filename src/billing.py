# -*- coding: utf-8 -*-

import requests

"""File Information
@file_name: billing.py
@author: Dylan "dyl-m" Monfret
Script to track Songstats billing
"""

if __name__ == "__main__":
    with open('../token/songstats_key.txt', 'r', encoding='utf-8') as key_file:
        api_key = key_file.read()

    response = requests.get("https://api.songstats.com/enterprise/v1/status",
                            headers={"Accept-Encoding": "", "Accept": "application/json", "apikey": api_key})

    print(response.json())
