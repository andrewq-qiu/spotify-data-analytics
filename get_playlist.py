"""Module for retrieving a public playlist from
Spotify and the attributes of their songs."""

from dotenv import load_dotenv
from typing import Any, Union
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import song_graph
from song_graph import Song
import get_dataset_data

load_dotenv('token.env')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())


def get_id_from_playlist_url(url: str) -> str:
    """

    Preconditions:
        - the url is in the following format: TODO

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


def convert_spotify_attributes_to_song_attributes(
        audio_features: dict[str, Any], track_info: dict) -> dict[str, Union[float, int]]:
    """Return a dictionary of attributes compatible with the
    Song class from a dictionary of audio features and track (song)
    information from the Spotify API.

    Ensure that the attributes of the returned dict have the correct typing according
    to song_graph.HEADERS, song_graph.INT_HEADERS, and song_graph.FLOAT_HEADERS.

    Preconditions:
        - 'explicit' in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS)
        - 'year' in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS)
        - 'popularity' in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS)
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


def get_songs_from_playlist_url(url: str) -> list[Song]:
    """Return a list of Song instances corresponding to the songs
    contained in a Spotify playlist url.
    """
    playlist_id = get_id_from_playlist_url(url)

    data = sp.playlist_items(playlist_id)

    track_ids = [item['track']['id'] for item in data['items']]
    features = sp.audio_features(track_ids)

    songs = []
    i = 0

    for item in data['items']:
        name = item['track']['name']
        artists = [artist['name'] for artist in item['track']['artists']]
        spotify_id = item['track']['id']

        attributes = convert_spotify_attributes_to_song_attributes(features[i], item['track'])
        songs.append(Song(name, spotify_id, artists, attributes))

        i += 1

    return songs


def create_song_graph_from_songs(songs: list[Song],
                                 parent_graph: song_graph.SongGraph = None) -> song_graph.SongGraph:
    """Create and return a song graph from a list of songs.

    (Optional) Add a parent graph from a larger dataset to the new song graph.

    Preconditions:
        - parent_graph is None or parent_graph.are_attributes_created()
            # parent_graph is not None implies parent_graph.are_attributes_created()
    """

    graph = song_graph.SongGraph(parent_graph)

    for song in songs:
        graph.add_song(song)

    if parent_graph is None:
        graph.generate_attribute_vertices()
    else:
        graph.generate_attribute_vertices(use_parent=True)

    return graph


def create_dataset_and_playlist_graphs_from_url(url: str) -> tuple[song_graph.SongGraph, song_graph.SongGraph]:
    """From a Spotify playlist URL, load relevant songs
    from the Spotify dataset in the decades of songs spanned by the playlist.
    Store these songs in a song graph.

    Create a song graph containing the songs of the playlist
    with the larger dataset song graph as its parent graph.

    Return a tuple containing (dataset_graph, playlist_graph).
    """

    songs = get_songs_from_playlist_url(url)

    decades_spanned = set()
    for song in songs:
        # The decade of the song represented by the first year of the decade
        decade = (song.attributes['year'] // 10) * 10
        decades_spanned.add(decade)

    dataset_graph = get_dataset_data.get_song_graph_from_decades(decades_spanned)
    playlist_graph = create_song_graph_from_songs(songs, parent_graph=dataset_graph)

    return dataset_graph, playlist_graph


if __name__ == '__main__':
    import analyze_song_graph
    import visualize_graph

    my_url = 'https://open.spotify.com/playlist/2lBR4CNNTua6ElWknxgJWi?si=cc415d7969fe4788&nd=1'
    ds_graph, pl_graph = create_dataset_and_playlist_graphs_from_url(my_url)

    # for v in ds_graph.get_attribute_vertices():
    #     print(v.item, len(v.neighbours))

    print(analyze_song_graph.get_most_significant_attributes(pl_graph))
    graph_nx = analyze_song_graph.create_clustered_networkx_song_graph(pl_graph, 0.8)

    visualize_graph.visualize_graph(graph_nx)
