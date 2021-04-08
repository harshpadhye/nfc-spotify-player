# nfc-spotify-player
Spotify applet to play a select playlist from my library, using the OAuth2 authorization codeflow.
The applet is wrapped in the Flask framework and hosted on Heroku. All cache stored in Postgres databases.

## Purpose
This application is a workaround for iOS Shortcuts' lack of integration with Spotify. Triggering an NFC tag
with my smartphone sends an appropriate request URL to the webpage hosted on Heroku, which then calls the Spotify
API to select the intended playlist to shuffle.
