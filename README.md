# spotify-data-analytics

This is a project created over Spring 2021. This application allows users to analyze their Spotify playlists via their public Spotify playlist url through the Spotify API. The included GUI summarizes the key characteristics of the user's playlist and recommends the user new songs based on their playlist.

## Implementation notes
The main analytical and recommendation algorithms apply the Graph data structure. The graph constructed by the program represents the union of two subsets of the Spotify song library: a compiled .csv containing a few million cached songs, and the user's inputted songs through their playlist. 

The graph contains two main types of nodes: attribute nodes song nodes. Connections between song nodes are determined based on a weighted similarity score of song attributes. Connections between attributes and songs are determined using a percentile threshold whose values are determined by the distribution of attributes in the larger .csv dataset.

Recommendations of songs are developed by determining a playlist's characteristic song(s) and finding songs in the larger dataset with a large amount of unique paths connecting them.
