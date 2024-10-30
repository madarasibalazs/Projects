
# Import necessary modules and functions
import sqlite3
from datetime import datetime, timezone, timedelta
import spotipy
from app.auth import get_token
import os

def initialize_database(db_path=None):
    """
    Function to initialize the SQLite database if not exists. This is the database part of the assignment.
    :return: Returns True
    """
    if db_path is None:
        # Default path for production --> had to use full path to work without errors, should work on every computer
        db_path = '\\'.join(os.path.dirname(__file__).split('\\')[0:-1]) + "\\instance\\spotify.db"

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)  # Connecting to SQLite database
    c = conn.cursor()

    # Creating user_logins table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_logins (
            id INTEGER PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            last_login_time TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'utc')),
            sub_level TEXT NOT NULL,
            display_name TEXT NOT NULL,
            followers INTEGER NOT NULL,
            country TEXT NOT NULL
        )
    ''')
    conn.commit()  # Committing the transaction
    conn.close()  # Closing the database connection
    return True

def log_user_login(spotify):
    """
    Function to log user login details into the SQLite database
    :param spotify: the spotify instance
    :return: True
    """

    # Fetching current user data from Spotify API
    conn = sqlite3.connect('instance/spotify.db')
    c = conn.cursor()
    user_data = spotify.current_user()
    user_id = user_data['id']
    sub_level = user_data['product']
    display_name = user_data['display_name']
    followers = int(user_data['followers']['total'])
    country = user_data['country']

    # Checking if the user already exists in the database
    c.execute("SELECT COUNT(*) FROM user_logins WHERE user_id=?", (user_id,))
    existing_user = c.fetchone()[0]

    # Getting current UTC time as last login time
    last_login_time_utc = datetime.utcnow().replace(tzinfo=timezone.utc).replace(microsecond=0)

    # Inserting or updating user login details based on existences
    if existing_user == 0:
        c.execute(
            "INSERT INTO user_logins (user_id, last_login_time, sub_level, display_name, followers, country) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, last_login_time_utc, sub_level, display_name, followers, country))
    else:
        c.execute(
            "UPDATE user_logins SET last_login_time=?, sub_level=?, display_name=?, followers=?, country=? WHERE user_id=?",
            (last_login_time_utc, sub_level, display_name, followers, country, user_id))
    conn.commit()
    conn.close()
    return True

def get_user_logins():
    """
    Function to fetch user login details from the SQLite database
    :return: Returns the login details that was collected from the database
    """
    conn = sqlite3.connect('instance/spotify.db')
    c = conn.cursor()

    # Fetching user login details sorted by last login time descending
    c.execute("SELECT user_id, strftime('%Y-%m-%d %H:%M:%S', last_login_time, 'localtime') AS local_time, sub_level, display_name, followers, country FROM user_logins ORDER BY last_login_time DESC")
    user_logins = c.fetchall()
    conn.close()
    return user_logins

def get_user_stats():
    """
    Function to retrieve various statistics from the user_logins table
    :return: Returns the calculated statistics
    """
    conn = sqlite3.connect('instance/spotify.db')
    c = conn.cursor()

    # Fetching count of users per subscription level
    c.execute("SELECT sub_level, COUNT(*) FROM user_logins GROUP BY sub_level")
    sub_level_counts = c.fetchall()
    total_users = sum(count for _, count in sub_level_counts)
    premium_users = sum(count for sub_level, count in sub_level_counts if sub_level == "premium")
    premium_percentage = (premium_users / total_users)*100 if total_users > 0 else 0

    # Calculating average number of followers
    c.execute("SELECT AVG(followers) FROM user_logins")
    avg_followers = c.fetchone()[0]

    # Finding the most common country among users
    c.execute("SELECT country, COUNT(*) FROM user_logins GROUP BY country ORDER BY COUNT(*) DESC LIMIT 1")
    most_common_country = c.fetchone()[0]

    # Fetching weekly logins
    c.execute("SELECT strftime('%Y-%W', last_login_time, 'localtime') AS login_week, COUNT(*) FROM user_logins GROUP BY login_week ORDER BY login_week DESC")
    weekly_logins = c.fetchall()

    # Fetching monthly logins
    c.execute("SELECT strftime('%Y-%m', last_login_time, 'localtime') AS login_month, COUNT(*) FROM user_logins GROUP BY login_month ORDER BY login_month DESC")
    monthly_logins = c.fetchall()

    # Calculating count of inactive users (not logged in within the last 10 days)
    days_threshold = 10
    threshold_date = datetime.utcnow().date() - timedelta(days=days_threshold)
    c.execute("SELECT COUNT(*) FROM user_logins WHERE last_login_time < ?", (threshold_date,))
    inactive_users_count = c.fetchone()[0]

    conn.close()

    # Returning the calculated statistics and formatting them
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "premium_percentage": f"{premium_percentage:.3f}",
        "avg_followers": f"{avg_followers:.3f}",
        "most_common_country": most_common_country,
        "weekly_logins": weekly_logins[0][1],
        "monthly_logins": monthly_logins[0][1],
        "inactive_users_count": inactive_users_count
    }

def search_spotify(query, search_type):
    """
    Function to perform different search queries in spotify. This allows the user to search for artists, tracks, albums,
    playlists, shows and episodes and see general information about these.
    :param query: The user specifies it and the function receives it from the HTML form. This is for example the name of
    the artist or song.
    :param search_type: The chosen search type, which has to be set for relevant search results.
    :return: Returns the results of the search.
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    # Performing search based on search type (artist, track, album, playlist, show, episode)
    if search_type == 'artist':
        results = spotify.search(q=query, type='artist', limit=10)
        items = results['artists']['items']
    elif search_type == 'track':
        results = spotify.search(q=query, type='track', limit=50)
        items = results['tracks']['items']

        # Filtering tracks based on query and sorting them by popularity
        filtered_items = [item for item in items if query.lower() in item['name'].lower() or
                          item['name'].lower().startswith(query.lower())]
        filtered_items.sort(key=lambda x: x["popularity"], reverse=True)

        # Removing possible duplicates
        seen_names = set()
        unique_items = []
        for item in filtered_items:
            if item['name'] not in seen_names:
                unique_items.append(item)
                seen_names.add(item['name'])
                if len(unique_items) == 10:
                    break
        items = unique_items[:11]
    elif search_type == 'album':
        results = spotify.search(q=query, type='album')
        items = results['albums']['items']

        # Filtering albums based on query
        filtered = [item for item in items if query.lower() in item['name'].lower() or
                    item['name'].lower().startswith(query.lower())]

        # Removing possible duplicates until there are 10 items
        seen_albums = set()
        unique_albums = []
        for item in filtered:
            if item['name'] not in seen_albums:
                unique_albums.append(item)
                seen_albums.add(item['name'])
                if len(unique_albums) == 10:
                    break
        items = unique_albums[:11]
    elif search_type == 'playlist':
        results = spotify.search(q=query, type='playlist')
        items = results['playlists']['items']
    elif search_type == 'show':
        results = spotify.search(q=query, type='show')
        items = results['shows']['items']
    elif search_type == 'episode':
        results = spotify.search(q=query, type='episode')
        items = results['episodes']['items']
    else:
        items = []  # Default case where no valid search type is provided
    return items  # Returning the search results

def display_current_user():
    """
    Function to get the current user's data and display it
    :return: Returns the extracted information about the user
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    user_info = spotify.current_user()  # Fetching current user information from Spotify

    user_data = {
        "display_name": user_info["display_name"],
        "id": user_info["id"],
        "email": user_info["email"],
        "followers": user_info["followers"]["total"],
        "product": user_info["product"],
        "country": user_info["country"],
        "images": user_info["images"]
    }

    return user_data  # Returning current user's data

def get_top_items():
    """
    Function to get the current user's top items, which are the top tracks and top artists
    :return: Returns information about the top tracks and artists
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    top_tracks = spotify.current_user_top_tracks(limit=10)  # Fetching the top 10 tracks for current user
    top_artists = spotify.current_user_top_artists(limit=10)  # Fetching the top 10 artists for current user

    # Extracting relevant information from top tracks and top artists
    tracks_info = [
        {
            "name": track["name"],
            "album": track["album"]["name"],
            "artists": ", ".join(artist["name"] for artist in track["artists"]),
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
        }
        for track in top_tracks["items"]
    ]

    artists_info = [
        {
            "name": artist["name"],
            "image_url": artist["images"][0]["url"] if artist["images"] else None
        }
        for artist in top_artists["items"]
    ]

    # Returning the information about the top tracks and artists
    return {
        "tracks": tracks_info,
        "artists": artists_info
    }

def get_specific_artist(artist_name):
    """
    Function to search up more information about an artists
    :param artist_name: The name of the artists that the user is looking for. The function receives it from the HTML form
    :return: Returns the relevant information, which are the search results
    """
    artist = search_spotify(artist_name, 'artist')  # Searching for the artist

    if artist:
        token_info = get_token()
        spotify = spotipy.Spotify(auth=token_info["access_token"])

        first_result = artist[0]  # Assuming first search result is the desired artist
        artist_id = first_result['id']

        # Fetching detailed information about the artist, their albums, top tracks, and related artists
        artist_details = spotify.artist(artist_id)
        artist_albums = spotify.artist_albums(artist_id)
        artist_top_tracks = spotify.artist_top_tracks(artist_id)
        artist_related_artists = spotify.artist_related_artists(artist_id)
        return artist_details, artist_albums, artist_top_tracks, artist_related_artists
    else:
        return None, None, None, None

def get_who_curr_user_follows():
    """
    Function to get the artists that the current user is following
    :return: Returns the list of artists that the user is following
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    followed_artists = []
    limit = 50
    after = None

    # Fetching artists that the current user follows, handling pagination
    while True:
        if after:
            results = spotify.current_user_followed_artists(limit=limit, after=after)
        else:
            results = spotify.current_user_followed_artists(limit=limit)

        artists = results['artists']['items']
        followed_artists.extend(artists)

        if len(artists) < limit:
            break

        after = artists[-1]['id']
    return followed_artists

def unfollow_artist(artist_id):
    """
    Function which makes it possible to unfollow artists
    :param artist_id: The function gets the artist's ID from the HTML form, which is needed for unfollowing
    :return: Returns the artist's ID for confirmation
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    artist_id_list = [artist_id]  # Converting the id to a list, so it is passed properly to the function
    spotify.user_unfollow_artists(artist_id_list)  # Unfollowing the specified artist

    return artist_id  # Returning the unfollowed artist's ID

def follow_artist(artist_id):
    """
    Function which makes it possible to follow artists that the user is currently not following
    :param artist_id: The function gets the artist's ID from the HTML form, which is needed for following
    :return: Returns the artist's ID for confirmation
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    artist_id_list = [artist_id]
    spotify.user_follow_artists(artist_id_list)  # Following the specified artist
    return artist_id  # Returning the followed artist's ID

def get_playlists():
    """
    Function to get the current user's playlists
    :return: Returns the list of the user's playlists
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    playlists = spotify.current_user_playlists()  # Fetching current user's playlists

    return playlists  # Returning the list of playlists

def get_playlist(playlist_id):
    """
    Function to get a specific playlist. This is needed, so the user can follow playlists, which they searched and are
    not in their library. For actually following a playlist there is a different function defined.
    :param playlist_id: The function gets the ID of the playlist from the HTML form, when it renders the page so the
    function knows which playlist the user wants to follow
    :return: Return the playlist
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])
    playlist = spotify.playlist(playlist_id=playlist_id)   # Fetching details of a specific playlist
    return playlist

def add_to_playlist(playlist_id, song_name):
    """
    Functon to add a track to a playlist in the user's library.
    :param playlist_id:
    :param song_name: The function receives the song's name from the HTML form. The user enters this value. The first
    search result is added to the playlist, as it is the most likely to be the song the user was looking for.
    :return: Returns True if the song was added to the playlist and False otherwise
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    # Search for the song to get its ID
    results = spotify.search(q=song_name, type='track', limit=1)
    if results['tracks']['items']:
        song_id = results['tracks']['items'][0]['id']
        spotify.playlist_add_items(playlist_id, [song_id])  # Adding the song to the specified playlist
        return True
    return False  # Returning False if song not found or cannot be added

def remove_from_all_playlists(playlist_id, song_name):
    """
    Function to remove all instances of a song from the specified playlist
    :param playlist_id: The function gets the ID of the playlist from the HTML form
    :param song_name: The function receives the song's name from the HTML form. The user enters this value.
    :return: Returns True if the song was deleted from the playlist and False otherwise
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    # Function to fetch all tracks from the playlist, handling pagination
    def fetch_all_tracks(playlist_id):
        tracks = []
        results = spotify.playlist_items(playlist_id)
        while results:
            tracks.extend(results['items'])
            if results['next']:
                results = spotify.next(results)
            else:
                results = None
        return tracks

    all_tracks = fetch_all_tracks(playlist_id)  # Fetching all tracks from the playlist, calling the function defined above

    # Removing all occurrences of the specified song from the playlist
    for item in all_tracks:
        if 'track' in item and item['track']:
            track = item['track']
            if song_name.lower() in track['name'].lower():
                song_id = track['id']
                spotify.playlist_remove_all_occurrences_of_items(playlist_id, [song_id])
                return True
    return False  # Returning False if song not found in the playlist

def get_playlist_tracks(playlist_id):
    """
    Function to retrieve every track in a particular playlist.
    :param playlist_id: The function gets the playlist's ID from the HTML form, so it gets the tracks of the correct
    playlist
    :return: Returns the tracks information.
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    # Function to fetch all tracks from the playlist, handling pagination
    def fetch_all_tracks(playlist_id):
        tracks = []
        results = spotify.playlist_items(playlist_id)
        while results:
            tracks.extend(results['items'])
            if results['next']:
                results = spotify.next(results)
            else:
                results = None
        return tracks

    all_tracks = fetch_all_tracks(playlist_id)  # Fetching all tracks from the playlist, calling the function defined above

    print(all_tracks)
    # Extract relevant track information
    tracks_info = []
    for item in all_tracks:
        if 'track' in item and item['track']:
            track = item['track']
            tracks_info.append({
                'id': track['id'],
                'name': track['name'],
                'artist':  [artist['name'] for artist in track['artists']],
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'preview_url': track['preview_url'] if 'preview_url' in track else None,
            })

    return tracks_info

def create_spot_playlist(playlist_name, playlist_description, is_public):
    """
    Function to create a new playlist.
    :param playlist_name: The name of the playlist given by the user in the HTML form
    :param playlist_description: The description of the playlist given by the user in the HTML form
    :param is_public: The parameter which sets if the playlist should be public or private
    :return: Returns the newly created playlist
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    user_id = spotify.current_user()["id"]  # Getting the ID of the current user
    playlist = spotify.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=is_public,
        description=playlist_description
    )

    return playlist  # Return the newly created playlist

def edit_playlist_details(playlist_id, new_name=None, new_description=None, new_public=None):
    """
    Function to edits the details of an existing playlist.
    :param playlist_id: The ID of the playlist
    :param new_name: The edited name of the playlist, given by the user in the HTML form
    :param new_description: The edited description of the playlist, given by the user in the HTML form
    :param new_public: The edited public/private status of the playlist, given by the user in the HTML form
    :return: Returns the updated playlist
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    # Updating playlist details with provided name, description, and public status
    new_playlist = spotify.playlist_change_details(playlist_id, name=new_name, description=new_description, public=new_public)

    return new_playlist  # Return the edited playlist

def follow_playlist(playlist_id):
    """
    Function to follow a playlist that the user searched for. This function makes it possible to follow other users
    public playlists
    :param playlist_id: The function receives the ID of the playlist from the HTML
    :return: Returns True
    """
    token_info = get_token()
    spotify = spotipy.Spotify(auth=token_info["access_token"])

    spotify.current_user_follow_playlist(playlist_id)  # Follow the artist with the received ID
    return True
