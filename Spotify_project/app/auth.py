
# Import necessary modules and functions
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import session, url_for, redirect
import os

def create_spotify_oauth():
    """
    Function to create a SpotifyOAuth object. Used for user authentication.
    :return: Returns the SpotifyOAuth object. IN that there are multiple things set, such as my application's client ID,
    client secret, redirect uri and scope (allows me to access different information and perform actions on the users
    behalf)
    """

    # Generate the redirect URI dynamically
    redirect_uri = url_for('redirect_page', _external=True)

    # Create and return a SpotifyOAuth object with the necessary credentials and scopes
    return SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),  # Spotify client ID from environment variable
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),  # Spotify client secret from environment variable
        redirect_uri=redirect_uri,  # Redirect URI for Spotify's OAuth flow
        scope='user-library-read playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private user-read-private user-read-email user-top-read user-follow-read user-follow-modify',   # Required scopes for accessing user's Spotify data
        cache_path=None  # No cache file path specified --> needed for session clearing
    )

def get_token():
    """
    Function to get the current user's access token
    :return: Returns the token information. It includes the access token, the token type, the refresh token and the time
    in which the token expires.
    """
    user_id = session.get('user_id')
    token_info = session.get('token_info', None)

    # If user ID or token info is not available, redirect to login page
    if not user_id or not token_info:
        redirect(url_for('login'))

    # Get the current time in seconds since the epoch
    now = int(time.time())

    # Check if the token is about to expire (less than 60 seconds remaining)
    is_expired = token_info['expires_at'] - now < 60

    # If the token is expired, refresh it
    if is_expired:
        spotify_oauth = create_spotify_oauth()  # Create a new SpotifyOAuth object
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])  # Refresh the access token using the refresh token
        session['token_info'] = token_info  # Update session with new token info

    return token_info
