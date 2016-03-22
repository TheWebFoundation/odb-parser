import requests
from requests.adapters import HTTPAdapter


def get_json(uri, params):
    """
    Returns a JSON document given an API's URI
    :param uri:
    :param params:
    :return json_response:
    """
    s = requests.Session()
    s.mount(uri, HTTPAdapter(max_retries=10))
    response = requests.get(uri, params=params)
    return response.json()
