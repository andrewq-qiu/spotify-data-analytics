"""Module containing classes and functions for creating
a GUI for interacting with Spotify Song Analytics.

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

from __future__ import annotations
import os
import sys
from typing import Optional
import requests
import pydub
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
import pygame.mixer
import get_playlist
import visualize_data
import analyze_song_graph
import song_graph


SCREEN_SIZE = (800, 600)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

GRAPH_CHART_LAYOUT = {'showlegend': True,
                      'margin': {'l': 0, 'r': 0, 't': 0, 'b': 50},
                      'autosize': True}

GRAPH_CHART_CONFIG = {'displayModeBar': False}

BAR_CHART_LAYOUT = {'showlegend': False,
                    'margin': {'l': 0, 'r': 0, 't': 50, 'b': 150},
                    'autosize': True}

BAR_CHART_CONFIG = {'displayModeBar': False}

PIE_CHART_LAYOUT = {'margin': {'t': 10, 'b': 50}}


class Page(qtw.QMainWindow):
    """A class representing a page in the GUI.
    """
    page_window: Optional[PageWindow]
    page_name: str

    def __init__(self, page_name: str) -> None:
        """Initialize the page."""

        qtw.QMainWindow.__init__(self)
        self.page_window = None
        self.page_name = page_name

    def connect_to_page_window(self, page_window: PageWindow) -> None:
        """Connect the page to a parent page window."""

        self.page_window = page_window

    def on_switched_to(self) -> None:
        """The function that is called when self.page_window
        switches to this page."""


class PageWindow(qtw.QMainWindow):
    """A PyQT window with the ability to handle multiple pages in the GUI
    and the switching between them.

    Instance Attributes:
        - stacked_widget: the widget responsible for displaying and switching between pages
        - pages: a dictionary mapping page names to Page instances
        - home: the home page of the
    """
    stacked_widget: qtw.QStackedWidget
    pages: dict[str, Page]
    home: Page

    def __init__(self, home: Page) -> None:
        """Initialize the page window."""
        qtw.QMainWindow.__init__(self)

        self.stacked_widget = qtw.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.pages = {}

        self.home = home
        self.add_page(home)

        self.go_to(home.page_name)

    def add_page(self, page: Page) -> None:
        """Add a page to the page window."""
        self.pages[page.page_name] = page
        self.stacked_widget.addWidget(page)
        page.connect_to_page_window(self)

    def del_page(self, page_name: str) -> None:
        """Remove a page from the page window."""
        self.stacked_widget.removeWidget(self.pages[page_name])
        del self.pages[page_name]

    def go_to(self, page_name: str) -> None:
        """Swap the page to a page in self.pages
        given the name of the page.

        If page_name does not refer to a page in self,
        then raise a ValueError.
        """

        if page_name in self.pages:
            page = self.pages[page_name]

            self.stacked_widget.setCurrentWidget(page)
            self.setWindowTitle(page.windowTitle())
            self.setFixedSize(page.size())

            page.on_switched_to()
        else:
            raise ValueError


class PlaylistEntryWidget(qtw.QWidget):
    """A class that handles the display of a form that allows
    users to select a playlist they want to load or input
    a link to a playlist they want to load themselves.

    Instance Attributes:
        - selection_type: the type of widget ('textbox' or 'dropdown')
                          selected at the moment
        - textbox: the widget for the textbox for entering a custom playlist
        - dropdown: the widget for selecting one of the preset playlists
        - go_button: the button for continuing with the playlist selection

    Representation Invariants:
        - self.selection_type in {'textbox', 'dropdown'}
    """

    selection_type: str
    textbox: qtw.QLineEdit
    dropdown: qtw.QComboBox
    go_button: qtw.QPushButton

    def __init__(self) -> None:
        """Initialize the widget."""
        qtw.QWidget.__init__(self)
        self.selection_type = 'textbox'
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface of the widget."""

        self.setLayout(qtw.QGridLayout())

        fields = qtw.QWidget()
        fields.setLayout(qtw.QVBoxLayout())

        text_box_label = NormalText('Playlist URL:')
        self.textbox = qtw.QLineEdit()
        self.textbox.textEdited.connect(self._on_textbox_edit)

        dropdown_label = NormalText('Choose a Playlist:')
        self.dropdown = qtw.QComboBox()
        self.dropdown.addItems(['None'] + list(get_playlist.DEFAULT_PLAYLISTS.keys()))
        self.dropdown.activated.connect(self._on_dropdown_select)

        fields.layout().addWidget(text_box_label)
        fields.layout().addWidget(self.textbox)
        fields.layout().addWidget(dropdown_label)
        fields.layout().addWidget(self.dropdown)

        self.go_button = qtw.QPushButton('GO')
        self.go_button.setFixedSize(75, 75)

        self.layout().addWidget(fields, 0, 0)
        self.layout().addWidget(self.go_button, 0, 1)

    def _on_dropdown_select(self) -> None:
        """A function that is called when an option
        in self.dropdown is selected."""

        text = self.dropdown.currentText()

        if text != 'None':
            # Then a playlist will selected
            self.selection_type = 'dropdown'
            self.textbox.clear()

    def _on_textbox_edit(self) -> None:
        """A function that is called when the
        text in self.textbox is edited."""

        self.selection_type = 'textbox'
        self.dropdown.setCurrentIndex(0)

    def freeze(self) -> None:
        """Freeze the widget and disable interaction
        with all buttons or forms.
        """

        self.go_button.setEnabled(False)
        self.dropdown.setEnabled(False)
        self.textbox.setEnabled(False)
        self.repaint()

    def unfreeze(self) -> None:
        """Unfreeze the widget and enable interaction
        with all buttons or forms."""

        self.go_button.setEnabled(True)
        self.dropdown.setEnabled(True)
        self.textbox.setEnabled(True)
        self.repaint()

    def get_current_selection(self) -> str:
        """If the dropdown is currently selected, return
        the text of the current option being selected.

        If the textbox is currently selected, return
        the text of the textbox."""

        if self.selection_type == 'textbox':
            return self.textbox.text()
        else:
            return self.dropdown.currentText()


class Heading(qtw.QLabel):
    """A text widget with large font meant for headings."""
    def __init__(self, text: str) -> None:
        """Initialize the text widget."""
        qtw.QLabel.__init__(self, text)


class SubHeading(qtw.QLabel):
    """A text widget with medium-large font meant for subheadings."""
    def __init__(self, text: str) -> None:
        """Initialize the text widget."""
        qtw.QLabel.__init__(self, text)


class NormalText(qtw.QLabel):
    """A text widget with medium-low font meant for normal text."""
    def __init__(self, text: str) -> None:
        """Initialize the text widget."""
        qtw.QLabel.__init__(self, text)


class SmallText(qtw.QLabel):
    """A text widget with small font."""
    def __init__(self, text: str) -> None:
        """Initialize the text widget."""
        qtw.QLabel.__init__(self, text)


class Container(qtw.QWidget):
    """A widget representing an empty container."""
    def __init__(self) -> None:
        """Initialize an empty container"""
        qtw.QWidget.__init__(self)


class HomePage(Page):
    """A page for the home page of the GUI.

    Instance Attributes:
        - playlist_entry: the widget for the form for playlist selection
        - extras_button: the button to move to the 'cool extras' page
    """
    playlist_entry: PlaylistEntryWidget
    extras_button: qtw.QPushButton

    def __init__(self, page_name: str) -> None:
        """Initialize the home page."""
        Page.__init__(self, page_name)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface of the home page."""
        self.setWindowTitle('Spotify Playlist Analytics - Andrew Qiu')

        self.setFixedSize(900, 280)
        container = Container()
        container.setFixedSize(900, 280)
        self.setCentralWidget(container)
        container.setLayout(qtw.QVBoxLayout())

        prompt = Heading('Spotify Playlist Analytics')
        prompt.setContentsMargins(20, 0, 0, 0)
        sub_prompt = SubHeading('Enter a link to a public Spotify playlist'
                                ' or choose a playlist from the dropdown.')
        sub_prompt.setContentsMargins(20, 0, 0, 0)

        self.playlist_entry = PlaylistEntryWidget()
        self.playlist_entry.go_button.clicked.connect(self._on_go_button_press)

        self.extras_button = qtw.QPushButton('COOL EXTRAS')
        self.extras_button.setFixedSize(90, 30)
        self.extras_button.clicked.connect(self._on_extras_button_press)

        container.layout().addWidget(prompt)
        container.layout().addWidget(sub_prompt)
        container.layout().addWidget(self.playlist_entry)
        container.layout().addWidget(self.extras_button)

    def _on_extras_button_press(self) -> None:
        """A function called when self.extras_button
        is pressed.

        If self.page_window is None or the 'cool_extras'
        page is not in self.page_window.pages, then
        raise a ValueError.

        Otherwise, move to the cool extras page.
        """
        if self.page_window is None or\
                'cool_extras' not in self.page_window.pages:
            raise ValueError
        else:
            self.page_window.go_to('cool_extras')

    def _on_go_button_press(self) -> None:
        """A function called when self.playlist_entry.go_button
        is pressed.

        If self.page_window is None or the 'playlist_page'
        page is not in self.page_window.pages, then
        raise a ValueError.

        Otherwise, move to the playlist entry page.
        """

        self.playlist_entry.freeze()

        if self.page_window is None or\
                'playlist_page' not in self.page_window.pages:
            raise ValueError
        else:
            if self.playlist_entry.selection_type == 'textbox':
                playlist_url = self.playlist_entry.get_current_selection()
            else:
                playlist_url = get_playlist.DEFAULT_PLAYLISTS[
                    self.playlist_entry.get_current_selection()]

            self.page_window.pages['playlist_page'].load_playlist_url(playlist_url)
            self.page_window.go_to('playlist_page')

    def on_switched_to(self) -> None:
        """A function called when the home page is
        switched to.

        Unfreeze the form on the home page."""
        self.playlist_entry.unfreeze()


class CoolExtrasPage(Page):
    """A page containing the cool extras portion.

    Instance Attributes:
        - web_view: the widget responsible for loading the cool extras HTML page
        - back_button: the button responsible for returning back to the home page
    """
    web_view: QWebEngineView
    back_button: qtw.QPushButton

    def __init__(self, page_name: str) -> None:
        """Initialize the page"""

        Page.__init__(self, page_name)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface for the page."""

        self.setWindowTitle('Spotify Playlist Analytics - Andrew Qiu')
        self.setFixedSize(1000, 800)

        container = Container()
        self.setCentralWidget(container)
        container.setLayout(qtw.QVBoxLayout())

        self.web_view = QWebEngineView()

        path = 'cool extras/extras.html'
        q_url = QUrl(ROOT_DIR.replace('\\', '/') + '/' + path)
        self.web_view.load(q_url)
        self.web_view.setFixedWidth(1000)

        self.back_button = qtw.QPushButton('Back ->')
        self.back_button.pressed.connect(self._on_back_button_press)

        container.layout().addWidget(self.web_view)
        container.layout().addWidget(self.back_button)

    def _on_back_button_press(self) -> None:
        """A function called when self.back_button is pressed.

        If self.page_window is None, raise a ValueError.
        Otherwise, return to the page 'home'.
        """

        if self.page_window is None:
            raise ValueError
        else:
            self.page_window.go_to('home')


class YearDistributionView(Container):
    """A widget containing a chart of the distribution of songs
    for a playlist by year.

    Instance Attributes:
        - pie_chart: the widget for displaying the pie chart of the distribution
    """

    pie_chart: QWebEngineView

    def __init__(self) -> None:
        """Initialize the widget."""
        Container.__init__(self)
        self._init_empty_ui()

    def _init_empty_ui(self) -> None:
        """Initialize an empty user interface for the widget."""

        self.setFixedSize(900, 300)
        self.setLayout(qtw.QVBoxLayout())

        title = SubHeading('Distribution of songs by year:')

        self.pie_chart = QWebEngineView()
        self.pie_chart.setFixedSize(900, 300)

        self.layout().addWidget(title)
        self.layout().addWidget(self.pie_chart)

    def fill_ui(self, pl_graph: song_graph.SongGraph) -> None:
        """Fill in the widget with the relevant chart
        given a song graph of a playlist, pl_graph.

        Preconditions:
            - pl_graph.are_attributes_generated()
            - pl_graph.parent_graph is not None
            - pl_graph.parent_graph.are_attributes_generated()
        """

        path = 'cache/year_distribution.html'

        visualize_data.visualize_attr_header_distr_pie(
            graph=pl_graph,
            attribute_header='year',
            output_to_html_path=path,
            layout=PIE_CHART_LAYOUT
        )

        q_url = QUrl(ROOT_DIR.replace('\\', '/') + '/' + path)

        self.pie_chart.load(q_url)
        self.update()


class DeviantAttributeView(Container):
    """A widget containing three charts, representing either the
    top three least or most deviant attribute headers of a playlist.

    Instance Attributes:
        - mode: the type of data displayed | 'most' for most deviant or
             'least' for least deviant attributes
        - num_attributes: the number of attributes to be displayed
        - charts: the list of widgets containing each distribution chart
                  for each of the deviant attributes

    Representation Invariants:
        - mode in {'most', 'least'}
    """

    mode: str
    num_attributes: int
    charts: list[QWebEngineView]

    def __init__(self, mode: str = 'most', num_attributes: int = 3) -> None:
        """Initialize the widget"""

        Container.__init__(self)
        self.mode = mode
        self.num_attributes = num_attributes
        self._init_empty_ui()

    def _init_empty_ui(self) -> None:
        """Initialize an empty user interface for the widget."""

        self.setFixedSize(900, 500)
        self.setLayout(qtw.QVBoxLayout())

        sub_container = Container()
        sub_container.setFixedSize(900, 500)
        sub_container.setLayout(qtw.QHBoxLayout())

        if self.mode == 'most':
            deviated_title = SubHeading('The top three most deviant attributes: (distributions)')
        else:
            deviated_title = SubHeading('The top three least deviant attributes: (distributions)')

        legend = qtw.QWidget()
        legend.setFixedSize(900, 30)
        legend.setProperty('state', 'legend')

        self.charts = []

        for _ in range(self.num_attributes):
            chart = QWebEngineView()
            chart.setFixedSize(300, 500)
            self.charts.append(chart)
            sub_container.layout().addWidget(chart)

        self.layout().addWidget(deviated_title)
        self.layout().addWidget(legend)
        self.layout().addWidget(sub_container)

    def fill_ui(self, pl_graph: song_graph.SongGraph) -> None:
        """Fill in the widget with the relevant charts
        given a playlist graph, pl_graph.

        Preconditions:
            - pl_graph.are_attributes_generated()
            - pl_graph.parent_graph is not None
            - pl_graph.parent_graph.are_attributes_generated()
        """

        if self.mode == 'most':
            top_attributes = analyze_song_graph.most_deviated_attr_headers(
                pl_graph, self.num_attributes, ignore={'year', 'popularity', 'explicit'})
        else:
            top_attributes = analyze_song_graph.least_deviated_attr_headers(
                pl_graph, self.num_attributes, ignore={'year', 'popularity', 'explicit'})

        for i in range(self.num_attributes):

            if self.mode == 'most':
                path = f'cache/most_deviated_{i}.html'
            else:
                path = f'cache/least_deviated_{i}.html'

            visualize_data.visualize_attr_header_distr_bar(
                pl_graph, top_attributes[i], path, BAR_CHART_LAYOUT, BAR_CHART_CONFIG)

            q_url = QUrl(ROOT_DIR.replace('\\', '/') + '/' + path)

            self.charts[i].load(q_url)

        self.update()


class CoverImage(qtw.QWidget):
    """A class representing a cover image for a
    song or a playlist.

    Instance Attributes:
        - image: the qtg.QImage object for the display of the cover image
        - size: the size of the image
        - image_view_label: the widget with which self.image is displayed on
    """

    image: qtg.QImage()
    size: tuple[int, int]
    image_view_label: qtw.QLabel

    def __init__(self, size: tuple[int, int]) -> None:
        """Initialize the widget."""

        qtw.QWidget.__init__(self)
        self.size = size
        self.setLayout(qtw.QHBoxLayout())
        self.setFixedSize(size[0], size[1])

        self.image_view_label = qtw.QLabel()
        self.image_view_label.setFixedSize(size[0], size[1])
        self.image = qtg.QImage()

        self.layout().addWidget(self.image_view_label)

    def load_from_url(self, image_url: str) -> None:
        """Fill in the widget with an image given an image_url."""

        data = requests.get(image_url).content

        self.image.loadFromData(data)
        self.image = self.image.scaled(self.size[0], self.size[1])
        self.image_view_label.setPixmap(qtg.QPixmap(self.image))

        self.update()


class PlayListViewTitle(qtw.QWidget):
    """A widget for displaying the name and artist
    of a playlist.

    Instance Attributes:
        - title: the widget displaying the title of the playlist
        - subtitle: the widget displaying the artists of the playlist
        - cover_image: the widget displaying the cover image of the playlist
    """

    title: Heading
    subtitle: SubHeading
    cover_image: CoverImage

    def __init__(self) -> None:
        """Initialize the widget."""
        qtw.QWidget.__init__(self)
        self._init_empty_ui()

    def _init_empty_ui(self) -> None:
        """Initialize an empty user interface for the widget."""
        self.setLayout(qtw.QGridLayout())

        sub_container = qtw.QWidget()
        sub_container.setLayout(qtw.QVBoxLayout())

        self.title = Heading('My Playlist Name...')
        self.subtitle = SubHeading('By Author...')
        self.cover_image = CoverImage((70, 70))

        sub_container.layout().addWidget(self.title)
        sub_container.layout().addWidget(self.subtitle)

        self.layout().addWidget(self.cover_image, 0, 0)
        self.layout().addWidget(sub_container, 0, 1)

    def fill_ui(self, token_manager: get_playlist.SpotifyTokenManager,
                playlist_url: str) -> None:
        """Fill the title and subtitle of the widget given
        a playlist_url and token_manager."""

        playlist_info = get_playlist.get_playlist_info_from_url(
            token_manager, playlist_url)

        self.title.setText(playlist_info['name'])
        self.subtitle.setText(f'By {playlist_info["author"]}')

        self.cover_image.load_from_url(playlist_info['cover_url'])
        self.update()


class Mixer:
    """A class that handles the playback of sounds using
    the pygame.mixer module.

    Instance Attributes:
        - current_song_url: the url of the song that is currently playing or is paused
    """

    current_song_url: Optional[str]

    # Private Instance Attributes:
    #   - _downloaded_songs: a dictionary mapping the url of a song to
    #                        an index associated to a cached mp3 file.
    # Private Representation Invariants:
    #   - all(os.path.isfile('cache/cached_song_{self._downloaded_songs[url]}.mp3')\
    #         for url in self._downloaded_songs)

    _downloaded_songs: dict[str, int]

    def __init__(self) -> None:
        """Initialize the mixer."""
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        self._downloaded_songs = {}
        self.current_song_url = None

    def download_song(self, song_url: str) -> Optional[int]:
        """Download a song as an mp3 file given a song_url.
        Convert the mp3 file to a .wav file for pygame support.
        In success, return the index of the new song in the cache.
        Otherwise, return None.

        Preconditions:
            - song_url points to an mp3 file
        """
        data = requests.get(song_url)

        if data.status_code != 200:
            # A status code of 200 is sent when an mp3
            # is at the link.
            return None

        new_index = len(self._downloaded_songs)

        with open(f'cache/cached_song_{new_index}.mp3', 'wb') as f:
            f.write(data.content)

        sound = pydub.AudioSegment.from_mp3(f'cache/cached_song_{new_index}.mp3')
        sound.export(f'cache/cached_song_{new_index}.wav', format='wav')

        # Remove old file
        os.remove(f'cache/cached_song_{new_index}.mp3')

        self._downloaded_songs[song_url] = new_index

        return new_index

    def play_from_url(self, url: str) -> None:
        """Play a sound given a url to an mp3 file of that sound.
        If the sound has not already been downloaded, download
        the song and convert it to a .wav format.

        Play the cached .wav file.

        If no mp3 file is successfully retrieved, raise a ValueError.
        """

        if url not in self._downloaded_songs:
            index = self.download_song(url)
        else:
            index = self._downloaded_songs[url]

        if index is None:
            raise ValueError

        pygame.mixer.music.load(f'cache/cached_song_{index}.wav')
        self.current_song_url = url
        self.play()

    def pause(self) -> None:
        """Pause the playback of any sounds.

        If no sounds are being played, raise a ValueError."""
        if self.current_song_url is None:
            raise ValueError

        pygame.mixer.music.pause()

    def play(self) -> None:
        """Resume the playback of any sounds.

        If no sounds are currently being played or are
        currently paused, then raise a ValueError.
        """
        if self.current_song_url is None:
            raise ValueError

        # Repeat the song indefinitely.
        pygame.mixer.music.play(loops=-1)

    def clear_all_songs(self) -> None:
        """Pause any sounds currently being played and
        clear the cache of any sounds that have been downloaded."""

        if self.current_song_url is not None:
            self.pause()

        pygame.mixer.music.unload()

        for url in self._downloaded_songs:
            index = self._downloaded_songs[url]

            if os.path.exists(f'cache/cached_song_{index}.mp3'):
                os.remove(f'cache/cached_song_{index}.mp3')

        self.current_song_url = None
        self._downloaded_songs = {}


class PlayPauseButton(qtw.QPushButton):
    """A widget handling the playing and pausing of sample
    songs in the SongPreview widget.

    Instance Attributes:
        - song_url: the url of the song played/paused when the button is clicked
        - paused: whether or not the song is paused
        - mixer: the mixer controlling the playback of all sounds
        - connected_buttons: a set of PlayPauseButton instances which interact with self such that
                             when self is playing, all buttons in the set are paused.
                             When any button in the set is playing, self is paused.

    Representation Invariants:
        - self.paused or all(other.paused for other in self.connected_buttons)
    """

    song_url: Optional[str]
    paused: bool
    mixer: Mixer
    connected_buttons: set[PlayPauseButton]

    def __init__(self, mixer: Mixer) -> None:
        """Initialize the widget using a mixer."""
        qtw.QPushButton.__init__(self)
        self.song_url = None
        self.paused = True
        self.setProperty('state', 'paused')

        self.mixer = mixer
        self.connected_buttons = set()

        self.clicked.connect(self.toggle_play)

    def set_song_url(self, song_url: str) -> None:
        """Set the url of the song that is to be played."""
        self.song_url = song_url

    def connect_button(self, button: PlayPauseButton) -> None:
        """Connect two PlayPauseButton instances together such that
        when one button is set to play, all other connected buttons are
        set to pause.

        Raise a ValueError if button and self are the same.
        """
        if button is self:
            raise ValueError

        self.connected_buttons.add(button)
        button.connected_buttons.add(self)

    def _pause_connected_buttons(self) -> None:
        """Pause all PlayPauseButton instances connected to self."""
        for button in self.connected_buttons:
            if not button.paused:
                button.toggle_play()

    def toggle_play(self) -> None:
        """Toggle the playback of song associated to self
        and pause any connected PlayPauseButton instances if
        applicable.
        """
        assert self.song_url is not None
        self.paused = not self.paused

        if self.paused:
            self.setProperty('state', 'paused')

            self.mixer.pause()
        else:
            self.setProperty('state', 'play')
            self._pause_connected_buttons()

            self.mixer.play_from_url(self.song_url)

        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class SongPreview(qtw.QWidget):
    """A widget for previewing songs to a user.
    This widget includes displaying a cover image, the title,
    the artist(s), and the ability to play a short 30s sample
    of the song if available through the Spotify API.

    Instance Attributes:
        - play_button: the button responsible for a user being able to play or pause
                       the playback of a sample of a song
        - mixer: the mixer controlling the playback of all sounds
        - cover: the widget displaying the cover image of the song
        - title: the widget displaying the title of the song
        - subtitle: the widget displaying the artist(s) of the song
    """

    play_button: PlayPauseButton
    mixer: Mixer
    cover: CoverImage
    title: Heading
    subtitle: SubHeading

    def __init__(self, mixer: Mixer) -> None:
        """Initialize the widget."""

        qtw.QWidget.__init__(self)
        self.mixer = mixer
        self._init_empty_ui()

    def _init_empty_ui(self) -> None:
        """Initialize an empty user interface for the widget."""

        self.setFixedSize(300, 350)
        self.setLayout(qtw.QVBoxLayout())

        self.cover = CoverImage((200, 200))
        self.title = NormalText('Song Name')
        self.subtitle = SmallText('By Artist')

        play_button_container = Container()
        play_button_container.setFixedWidth(200)
        play_button_container.setLayout(qtw.QHBoxLayout())

        self.play_button = PlayPauseButton(self.mixer)
        self.play_button.setFixedSize(40, 40)
        play_button_container.layout().addStretch()
        play_button_container.layout().addWidget(self.play_button)
        play_button_container.layout().addStretch()

        self.layout().addWidget(self.cover)
        self.layout().addWidget(self.title)
        self.layout().addWidget(self.subtitle)
        self.layout().addWidget(play_button_container)
        self.layout().addStretch()

    def fill_ui(self, song: song_graph.Song,
                preview_url: Optional[str], cover_url: str) -> None:
        """Fill the user interface with song information given a
        Song instance, preview_url, and cover_url to the song."""

        self.cover.load_from_url(cover_url)

        self.title.setText(song.name)
        self.subtitle.setText(f'By {", ".join(song.artists)}')

        if preview_url is None or self.mixer.download_song(preview_url) is None:
            self.play_button.setVisible(False)
        else:
            self.play_button.set_song_url(preview_url)
            self.play_button.setVisible(True)

        self.update()

    def connect_to_other_song_preview(self, other: SongPreview) -> None:
        """Connect self to another instance of SongPreview such that
        when sounds are being played in one instance, all connected instances
        are automatically paused."""

        self.play_button.connect_button(other.play_button)


class RecommendedSongsView(qtw.QWidget):
    """A widget for displaying the recommended songs
    to a user given their playlist.

    Instance Attributes:
        - mixer: the Mixer instance responsible for handling the playback
                 of songs.
        - song_previews: a list containing SongPreview instances
                         for displaying individual previews for each of
                         the recommended songs
    """

    mixer: Mixer
    song_previews: list[SongPreview]

    def __init__(self) -> None:
        """Initialize the widget."""
        qtw.QWidget.__init__(self)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface for
        the widget."""
        self.mixer = Mixer()

        container = Container()
        container.setLayout(qtw.QHBoxLayout())
        container.setFixedSize(900, 350)

        self.setLayout(qtw.QVBoxLayout())
        self.setFixedSize(900, 400)

        title = SubHeading('Recommended Songs:')
        self.layout().addWidget(title)

        self.song_previews = []

        for i in range(3):
            self.song_previews.append(SongPreview(self.mixer))
            container.layout().addWidget(self.song_previews[i])

        self.song_previews[0].connect_to_other_song_preview(self.song_previews[1])
        self.song_previews[0].connect_to_other_song_preview(self.song_previews[2])
        self.song_previews[1].connect_to_other_song_preview(self.song_previews[2])

        self.layout().addWidget(container)

    def fill_ui(self, token_manager: get_playlist.SpotifyTokenManager,
                pl_graph: song_graph.SongGraph) -> None:
        """Fill the user interface of the widget given
        a token_manager to interact with the Spotify API, and
        a playlist stored in a playlist graph (pl_graph).
        """
        clusters = analyze_song_graph.find_clusters(pl_graph)

        recommended_songs_so_far = set()

        for i in range(3):
            recommended_song, _ = analyze_song_graph.recommended_song_for_playlist(
                pl_graph, clusters, ignore=recommended_songs_so_far)

            recommended_songs_so_far.add(recommended_song)

        recommended_songs = list(recommended_songs_so_far)

        urls = get_playlist.get_song_covers_and_samples(
            token_manager, recommended_songs)

        for i in range(3):
            cover_url = urls[i][0]
            preview_url = urls[i][1]

            self.song_previews[i].fill_ui(
                recommended_songs[i], preview_url, cover_url)

        self.update()

    def on_close(self) -> None:
        """A function that is to be called when the page containing
        the widget is closed or when the widget is no longer visible.

        Pause any songs currently being played and clear all songs
        from the cache in self.mixer.
        """

        for song_preview in self.song_previews:
            if not song_preview.play_button.paused:
                song_preview.play_button.toggle_play()

        self.mixer.clear_all_songs()


class PlaylistView(qtw.QScrollArea):
    """A widget for displaying the analytics of a playlist
    to a user.

    Instance Attributes:
        - title_view: a widget for displaying the title, cover image, and
                      artist(s) of the playlist
        - graph_view: a widget for displaying the clustered graph representation
                      of the playlist
        - most_deviant_view: a widget for displaying the charts of the top three most
                             deviant attributes of the playlist
        - least_deviant_view: a widget for displaying the charts of the top three least
                              deviant attributes of the playlist
        - recommended_songs_view: a widget for previewing three recommended songs based on the
                                  songs in the playlist
    """

    title_view: PlayListViewTitle
    graph_view: QWebEngineView
    most_deviant_view: DeviantAttributeView
    least_deviant_view: DeviantAttributeView
    year_distribution_view: YearDistributionView
    recommended_songs_view: RecommendedSongsView

    def __init__(self) -> None:
        """Initialize the widget."""
        qtw.QScrollArea.__init__(self)

        self._init_empty_ui()

    def _init_empty_ui(self) -> None:
        """Initialize an empty user interface."""
        container = Container()
        container.setLayout(qtw.QVBoxLayout())
        container.setFixedWidth(1000)
        container.setMinimumHeight(800)

        self.title_view = PlayListViewTitle()
        message = SmallText('Double click on items in the legend to isolate them.'
                            '\nThe songs are colored by the attribute selected, '
                            'where blue represents low and yellow represents high.'
                            'Red is somewhere in-between.'
                            '\nThe green nodes are the characteristic attribute vertices'
                            ' for each cluster.')
        message.setStyleSheet('margin-left: 15px;')

        self.graph_view = QWebEngineView()
        self.graph_view.setFixedSize(900, 800)

        self.most_deviant_view = DeviantAttributeView('most')
        self.least_deviant_view = DeviantAttributeView('least')

        self.year_distribution_view = YearDistributionView()

        self.recommended_songs_view = RecommendedSongsView()

        container.layout().addWidget(self.title_view)
        container.layout().addWidget(message)
        container.layout().addWidget(self.graph_view)
        container.layout().addWidget(self.most_deviant_view)
        container.layout().addWidget(self.least_deviant_view)
        container.layout().addWidget(self.year_distribution_view)
        container.layout().addWidget(self.recommended_songs_view)

        self.setWidget(container)

    def fill_ui(self, token_manager: get_playlist.SpotifyTokenManager,
                playlist_url: str, pl_graph: song_graph.SongGraph) -> None:
        """Fill the user interface given a token_manager to access
        the Spotify API along with a playlist_url, and a pl_graph containing
        the songs of the playlist."""

        path = 'cache/clustered_graph.html'

        clustered_graph = analyze_song_graph.create_clustered_nx_song_graph(
            pl_graph, ignore={'year', 'popularity', 'explicit'}
        )

        visualize_data.visualize_graph_with_attributes(
            pl_graph, clustered_graph, path, GRAPH_CHART_LAYOUT, GRAPH_CHART_CONFIG)
        q_url = QUrl(ROOT_DIR.replace('\\', '/') + '/' + path)

        self.title_view.fill_ui(token_manager, playlist_url)
        self.graph_view.load(q_url)
        self.most_deviant_view.fill_ui(pl_graph)
        self.least_deviant_view.fill_ui(pl_graph)
        self.year_distribution_view.fill_ui(pl_graph)
        self.recommended_songs_view.fill_ui(token_manager, pl_graph)

        self.update()


class PlaylistPage(Page):
    """A page containing the analytics and recommended songs
    for some playlist.

    Instance Attributes:
        - token_manager: the Spotify API token manager for handling API access
        - playlist_view: the widget responsible for showing the analytics of the playlist
        - back_button: a button to return back to the home page
    """
    token_manager: get_playlist.SpotifyTokenManager
    playlist_view: PlaylistView
    back_button: qtw.QPushButton

    def __init__(self, page_name: str) -> None:
        """Initialize the page."""

        Page.__init__(self, page_name)
        self.token_manager = get_playlist.SpotifyTokenManager()
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface for the page."""

        self.setWindowTitle('Spotify Playlist Analytics - Andrew Qiu')
        self.setFixedSize(1000, 800)

        container = Container()
        self.setCentralWidget(container)
        container.setLayout(qtw.QVBoxLayout())

        self.playlist_view = PlaylistView()

        self.back_button = qtw.QPushButton('<- Back')
        self.back_button.pressed.connect(self._on_back_button_press)

        container.layout().addWidget(self.playlist_view)
        container.layout().addWidget(self.back_button)

    def load_playlist_url(self, playlist_url: str) -> None:
        """Fill in the user interface of the page given a playlist_url."""

        _, pl_graph = get_playlist.get_ds_and_pl_graphs_from_url(
            self.token_manager, playlist_url, print_progress=True)

        print('Creating charts...')

        self.playlist_view.fill_ui(self.token_manager, playlist_url, pl_graph)

    def _on_back_button_press(self) -> None:
        """A function called when self.back_button is pressed.

        If self.page_window is None, then raise a ValueError.
        Otherwise, return to the page 'home'.
        """

        if self.page_window is None:
            raise ValueError
        else:
            self.page_window.go_to('home')
            self.playlist_view.recommended_songs_view.on_close()


def show_gui() -> None:
    """Display the interactive GUI of the
    Spotify Playlist Analytics project."""

    app = qtw.QApplication(sys.argv)

    w = PageWindow(HomePage('home'))
    w.add_page(PlaylistPage('playlist_page'))
    w.add_page(CoolExtrasPage('cool_extras'))

    stylesheet = open('gui.css', 'r').read()
    w.setStyleSheet(stylesheet)

    w.show()
    app.exec_()


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['__future__', 'os', 'typing', 'requests', 'PyQt5.QtWidgets',
                          'PyQt5.QtGui', 'PyQt5.QtCore', 'PyQt5.QtWebEngineWidgets',
                          'pygame.mixer', 'get_playlist', 'visualize_data', 'analyze_song_graph',
                          'song_graph', 'sys'],
        'allowed-io': ['show_gui', 'download_song', 'load_playlist_url'],
        'max-line-length': 100,
        'disable': ['E1136', 'E0611']
    })
