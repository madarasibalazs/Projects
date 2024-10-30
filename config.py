import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'ThisWillBeTheSecretCookieThingyThatIHaveToSet')
    SESSION_COOKIE_NAME = 'Spotify Cookie'
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
