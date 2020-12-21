"""
Utility functions
"""
import psycopg2
import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth


def clean_string(phrase):
    """
    Helper function to remove special characters, capitilzation, and spaces from a string
    """
    ret = [char for char in phrase if char.isalnum()]
    return "".join(ret).lower()


class MySpotifyOAuth(SpotifyOAuth):
    """
    Customized authorization manager to read and write
    cached authorization tokens from Postgres database.
    """

    def __init__(self, scope, username, db_url):
        super(MySpotifyOAuth, self).__init__(scope=scope, username=username)

        # connects to the postgres db
        self.db_url = db_url
        self.conn = psycopg2.connect(db_url)
        self.psql = self.conn.cursor()

    def get_cached_token(self):
        """
        Retrieves cached token info from Postgres Database
        """
        
        # fetch the token info string from the first row of the cache table
        self.psql.execute("SELECT * FROM cache;")
        token_info_string = self.psql.fetchone()[0]
        token_info = json.loads(token_info_string)

        # if scopes don't match, then bail
        if "scope" not in token_info or not self._is_scope_subset(
                self.scope, token_info["scope"]):
            return None

        # refresh token if needed
        if self.is_token_expired(token_info):
            token_info = self.refresh_access_token(token_info["refresh_token"])

        return token_info

    def _save_token_info(self, token_info):
        """
        Updates Postgres table with the updated token info
        """

        # rewrites the first row with the new token info string
        self.psql.execute("UPDATE cache SET tokens=%s", (json.dumps(token_info),))
        self.conn.commit()

    def terminate_connection(self):
        """
        Ends connection with Postgre database
        """
        self.psql.close()
        self.conn.close()