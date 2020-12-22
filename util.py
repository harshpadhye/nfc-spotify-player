"""
Utility functions
"""
import psycopg2
import spotipy
import json
import warnings
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError


def clean_string(phrase):
    """
    Helper function to remove special characters, capitalization, and spaces from a string
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
        self.psql.execute("UPDATE cache SET tokens=%s",
                          (json.dumps(token_info),))

        self.conn.commit()

    def get_access_token(self, code=None, as_dict=True, check_cache=True):
        """ Gets the access token for the app given the code

            Parameters:
                - code - the response code
                - as_dict - a boolean indicating if returning the access token
                            as a token_info dictionary, otherwise it will be returned
                            as a string.

        NOT EDITED FROM SPOTIPY DOCUMENTATION
        Rewritten to use overloaded methods
        """
        if as_dict:
            warnings.warn(
                "You're using 'as_dict = True'."
                "get_access_token will return the token string directly in future "
                "versions. Please adjust your code accordingly, or use "
                "get_cached_token instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if check_cache:
            token_info = self.get_cached_token()
            if token_info is not None:
                if super().is_token_expired(token_info):
                    token_info = self.refresh_access_token(
                        token_info["refresh_token"]
                    )
                return token_info if as_dict else token_info["access_token"]

        payload = {
            "redirect_uri": self.redirect_uri,
            "code": code or self.get_auth_response(),
            "grant_type": "authorization_code",
        }
        if self.scope:
            payload["scope"] = self.scope
        if self.state:
            payload["state"] = self.state

        headers = self._make_authorization_headers()

        response = self._session.post(
            self.OAUTH_TOKEN_URL,
            data=payload,
            headers=headers,
            verify=True,
            proxies=self.proxies,
            timeout=self.requests_timeout,
        )
        if response.status_code != 200:
            error_payload = response.json()
            raise SpotifyOauthError(
                'error: {0}, error_description: {1}'.format(
                    error_payload['error'], error_payload['error_description']),
                error=error_payload['error'],
                error_description=error_payload['error_description'])
        token_info = response.json()
        token_info = self._add_custom_values_to_token_info(token_info)
        self._save_token_info(token_info)
        return token_info if as_dict else token_info["access_token"]

    def terminate_connection(self):
        """
        Ends connection with Postgre database
        """
        self.psql.close()
        self.conn.close()
