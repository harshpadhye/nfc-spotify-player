"""
App to play a specific playlist from my library.
To be integrated with NFC tags and iOS automation.

@author: Harsh Padhye
"""

import spotipy
from flask import Flask, request
import gunicorn
import os
import psycopg2
import util

app = Flask(__name__)


@app.route("/")
def main():

    # required scopes
    scope = "user-modify-playback-state playlist-read-private app-remote-control streaming"

    # authorize the client
    auth_manager = util.MySpotifyOAuth(
        scope=scope, username="harshpadhye", db_url=os.environ["DATABASE_URL"])

    client = spotipy.Spotify(auth_manager=auth_manager)

    # dictionary mapping playlist names to playlist uris (str:str)
    playlist_map = {}

    playlists = client.current_user_playlists()["items"]
    for pl in playlists:
        # maps the cleaned playlist name to the uri
        playlist_map[util.clean_string(pl["name"])] = pl["uri"]

    # grabs the desired album to play from the url query parameters
    to_play = util.clean_string(request.args.get("name", None))

    # shuffles and starts playback of selected playlist
    client.start_playback(
        device_id=os.environ["MY_IPHONE_ID"], context_uri=playlist_map[to_play])
    client.shuffle(state=True)

    # closes connection to the Postgres database
    auth_manager.terminate_connection()


if __name__ == "__main__":
    app.run()
