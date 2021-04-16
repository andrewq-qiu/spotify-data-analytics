"""Module for interacting with the Spotify API to
retrieve playlist and song information.

This module relies on the environmental variables
SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET for authorization
to access the Spotify API.

MIT License

Copyright (c) 2021 Andrew Qiu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any, Union, Optional
import time
import base64
import os
import json
import requests
import song_graph
from song_graph import Song
import get_dataset_data


DEFAULT_PLAYLISTS = {
    'My Playlist': 'https://open.spotify.com/playlist/37i9dQZF1E37NlLG'
                   '3OEVtr?si=wGLNP1faSz--_52wf87H_A',
    "Kevin's Playlist": 'https://open.spotify.com/playlist/2lBR4CNNTu'
                        'a6ElWknxgJWi?si=cc415d7969fe4788&nd=1',
    'Spotify Rap Jazz and Chill': 'https://open.spotify.com/playlist/6QrU3'
                                  'UUxANjjstAKuGlSsK?si=-EPeSOLYQFi6eWzPFP3nYA',
    'Spotify Jazz in the Background': 'https://open.spotify.com/playlist/37i9dQZF1'
                                      'DWV7EzJMK2FUI?si=nC7MSsBlTqqOas9sX_XZlw',
    'Hot Hits Canada': 'https://open.spotify.com/playlist/37i9dQZ'
                       'F1DWXT8uSSn6PRy?si=GB2-0gBrT0GYnVrFKWSeLA',
    'Rap 2021 | Hip Hop & Rap Hits 2021': 'https://open.spotify.com/playlist/5x4vTYH7dI'
                                          'Z2A4tviBajlk?si=PZoAJa49QAiE8KA-JVbYDA'
}


class ApiInteractError(Exception):
    """Raised when there was an issue interacting with the
    Spotify API. This may be the result of invalid parameters,
    invalid authentication, or any issue relating to the Spotify API."""


class SpotifyTokenManager:
    """A class that handles Spotify API tokens
    and regenerates them when needed.

    Instance Attributes:
        - last_request_time: the last time since the token was refreshed
                             expressed as seconds after epoch in UTC
        - expiry_time: the amount of seconds until the token expires
                       since the last_request_time
    """
    last_request_time: float
    expiry_time: int

    # Private Instance Attributes:
    #   - _token: the current unexpired token

    _token: Optional[str]

    def __init__(self) -> None:
        """Initialize a spotify token manager."""

        self.last_request_time = 0.0
        self.expiry_time = 0
        self._token = None

    def _refresh_token(self) -> None:
        """Interact with the Spotify API to generate
        a new token. Raise an ApiInteractError if
        this interaction is unsuccessful.
        """

        url = 'https://accounts.spotify.com/api/token'
        id_secret = os.environ.get(
            'SPOTIFY_CLIENT_ID') + ':' + os.environ.get('SPOTIFY_CLIENT_SECRET')

        headers = {
            'Authorization': f'Basic {base64.b64encode(id_secret.encode()).decode()}'
        }

        body = {'grant_type': 'client_credentials'}

        r = requests.post(url, headers=headers, data=body)

        if r.status_code != 200:
            raise ApiInteractError

        data = json.loads(r.text)

        self._token = data['access_token']
        self.last_request_time = time.time()
        self.expiry_time = int(data['expires_in'])

    def get_token(self) -> None:
        """Return an unexpired Spotify API Token."""

        # Time since last call in seconds
        now = time.time()
        time_since_last_call = now - self.last_request_time

        # Add a second buffer to token expiry
        if time_since_last_call > self.expiry_time - 5:
            # Then the token has expired or is close
            # enough to expiring.
            self._refresh_token()
            return self._token
        else:
            return self._token


def _spotify_get_playlist_items(token_manager: SpotifyTokenManager, playlist_id: str) -> dict:
    """Interact with the Spotify API and return a dictionary
    containing the items of a playlist given a playlist id.

    Raise an ApiInteractError if this interaction was unsuccessful.
    """

    url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'

    headers = {
        'Authorization': f'Bearer {token_manager.get_token()}'
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise ApiInteractError

    return json.loads(r.text)


def _spotify_get_audio_features(token_manager: SpotifyTokenManager, track_ids: list[str]) -> list:
    """Interact with the Spotify API and return a list containing
    the audio features for each track in track_ids.

    Raise an ApiInteractError if this interaction was unsuccessful.
    """

    url = 'https://api.spotify.com/v1/audio-features'

    headers = {
        'Authorization': f'Bearer {token_manager.get_token()}'
    }

    params = {
        'ids': ','.join(track_ids)
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise ApiInteractError

    return json.loads(r.text)['audio_features']


def _spotify_get_playlist_info(token_manager: SpotifyTokenManager, playlist_id: str) -> dict:
    """Interact with the Spotify API and return a dictionary
    containing information about a playlist given a playlist_id.

    Raise an ApiInteractError if this interaction was unsuccessful.
    """

    url = 'https://api.spotify.com/v1/playlists/' + playlist_id

    headers = {
        'Authorization': f'Bearer {token_manager.get_token()}'
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise ApiInteractError

    return json.loads(r.text)


def _spotify_get_several_songs_info(
        token_manager: SpotifyTokenManager, track_ids: list[str]) -> dict:
    """Interact with the Spotify API and return a list containing
    the song information for each track in track_ids.

    Raise an ApiInteractError if this interaction was unsuccessful.
    """

    url = 'https://api.spotify.com/v1/tracks/'

    headers = {
        'Authorization': f'Bearer {token_manager.get_token()}'
    }

    params = {
        'ids': ','.join(track_ids)
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise ApiInteractError

    return json.loads(r.text)


def get_playlist_info_from_url(
        token_manager: SpotifyTokenManager, playlist_url: str) -> dict[str, str]:
    """Return a dictionary containing the name, cover_url, and author
    of a playlist given a playlist_url using the Spotify API.

    Raise an ApiInteractError if the API interaction was unsuccessful.
    """

    playlist_id = get_id_from_playlist_url(playlist_url)

    data = _spotify_get_playlist_info(token_manager, playlist_id)

    to_return = {
        'name': data['name'],
        'cover_url': data['images'][0]['url'],
        'author': data['owner']['display_name']
    }

    return to_return


def get_song_covers_and_samples(
        token_manager: SpotifyTokenManager, songs: list[Song]) -> list[tuple[str, str]]:
    """Return a list of tuples for each song in songs.
    Each tuple contains the cover url and preview url of the song.

    Raise an ApiInteractError if the API interaction was unsuccessful.
    """

    track_ids = [song.spotify_id for song in songs]

    data = _spotify_get_several_songs_info(token_manager, track_ids)

    to_return = []

    for track in data['tracks']:
        to_return.append((track['album']['images'][0]['url'], track['preview_url']))

    return to_return


def get_id_from_playlist_url(url: str) -> str:
    """Return the playlist id of a Spotify playlist given
    a Spotify playlist url.

    Raise a ValueError if no such id can be found.

    >>> get_id_from_playlist_url('https://open.spotify.com/playlist/37i9dQZF1DWXT8uSSn6PRy?si=UutGRn1YR3CGl1Tw8WhHpQ')
    '37i9dQZF1DWXT8uSSn6PRy'
    """

    start = url.find('playlist/') + len('playlist/')
    end = url.find('?')

    to_return = url[start: end]

    if to_return == '':
        raise ValueError
    else:
        return to_return


def spotify_features_to_song_attr(
        audio_features: dict[str, Any], track_info: dict) -> dict[str, Union[float, int]]:
    """Return a dictionary of attributes compatible with the
    Song class from a dictionary of audio features and track (song)
    information from the Spotify API.

    Ensure that the attributes of the returned dict have the correct typing according
    to song_graph.INT_HEADERS, and song_graph.FLOAT_HEADERS.

    Preconditions:
        - 'explicit' in song_graph.INT_HEADERS
        - 'year' in song_graph.INT_HEADERS
        - 'popularity' in song_graph.INT_HEADERS
    """

    to_return = {}

    for feature in audio_features:
        if feature in song_graph.FLOAT_HEADERS:
            to_return[feature] = float(audio_features[feature])
        elif feature in song_graph.INT_HEADERS:
            to_return[feature] = int(audio_features[feature])

    # Add Explicit, Year, and Popularity attributes from track_info
    to_return['explicit'] = int(track_info['explicit'])
    # All songs on spotify have a four digit year which occurs in the first
    # four characters of the release_date string
    to_return['year'] = int(track_info['album']['release_date'][:4])
    to_return['popularity'] = int(track_info['popularity'])

    return to_return


def get_songs_from_playlist_url(
        token_manager: SpotifyTokenManager, playlist_url: str) -> list[Song]:
    """Return a list of Song instances corresponding to the songs
    contained in a Spotify playlist url.

    Raise an ApiInteractError if there any issues with the
    interaction with the Spotify API.
    """

    playlist_id = get_id_from_playlist_url(playlist_url)

    data = _spotify_get_playlist_items(token_manager, playlist_id)

    track_ids = [itm['track']['id'] for itm in data['items']]
    features = _spotify_get_audio_features(token_manager, track_ids)

    songs = []
    i = 0

    for item in data['items']:
        name = item['track']['name']
        artists = [artist['name'] for artist in item['track']['artists']]
        spotify_id = item['track']['id']

        attributes = spotify_features_to_song_attr(features[i], item['track'])
        songs.append(Song(name, spotify_id, artists, attributes))

        i += 1

    return songs


def create_song_graph_from_songs(songs: list[Song],
                                 parent_graph: song_graph.SongGraph = None,
                                 year_separation: int = 10) -> song_graph.SongGraph:
    """Create and return a song graph from a list of songs.

    (Optional) Add a parent graph from a larger dataset to the new song graph.

    (Optional) year_separation defines the way year attribute vertices are to be
    created. I.e. the intervals in year attribute vertices. For example,
    a year_separation of 10 will create year attribute vertices
    for each decade spanned by the playlist.

    Preconditions:
        - parent_graph is None or parent_graph.are_attributes_created()
        # parent_graph is not None implies parent_graph.are_attributes_created()
    """

    graph = song_graph.SongGraph(parent_graph)

    for song in songs:
        graph.add_song(song)

    if parent_graph is None:
        graph.generate_attribute_vertices(year_separation)
    else:
        graph.generate_attribute_vertices(use_parent=True, year_separation=year_separation)

    return graph


def get_ds_and_pl_graphs_from_url(
        token_manager: SpotifyTokenManager, playlist_url: str, year_separation: int = 10) ->\
        tuple[song_graph.SongGraph, song_graph.SongGraph]:
    """From a Spotify playlist URL, load relevant songs
    from the Spotify dataset in the decades of songs spanned by the playlist.
    Store these songs in a song graph.

    Create a song graph containing the songs of the playlist
    with the larger dataset song graph as its parent graph.

    year_separation defines the way year attribute vertices are to be
    created. I.e. the intervals in year attribute vertices. For example,
    a year_separation of 10 will create year attribute vertices
    for each decade spanned by the playlist.

    Return a tuple containing (dataset_graph, playlist_graph).
    """

    songs = get_songs_from_playlist_url(token_manager, playlist_url)

    decades_spanned = set()
    for song in songs:
        # The decade of the song represented by the first year of the decade
        decade = (song.attributes['year'] // 10) * 10
        decades_spanned.add(decade)

    dataset_graph = get_dataset_data.get_song_graph_from_decades(decades_spanned, year_separation)
    playlist_graph = create_song_graph_from_songs(songs,
                                                  parent_graph=dataset_graph,
                                                  year_separation=year_separation)

    return dataset_graph, playlist_graph


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['typing', 'time', 'requests', 'base64', 'os',
                          'json', 'song_graph', 'get_dataset_data'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E1136']
    })
