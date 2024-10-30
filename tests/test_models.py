import logging
from unittest.mock import MagicMock, patch

import pytest
from app import create_app
from app.models import *


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

# Fixture to setup a test database
@pytest.fixture
def setup_test_database():
    # Setup a test database
    test_db_path = os.path.join(os.path.dirname(__file__), 'test.db')  # Absolute path to your test database
    initialize_database(test_db_path)  # Initialize test database

    yield test_db_path  # Provide the test database path to tests

    # Teardown: Clean up the test database after tests
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


# Configure logging --> this is needed to make sure that the tests for CRUD operations are performed correctly
# The tests run really fast and I wanted to make sure that they actually test the function
logging.basicConfig(level=logging.DEBUG)


# Test case for insertion
def test_insert_user(setup_test_database):
    # Mock data for insertion
    new_user = {'user_id': 'test_user', 'sub_level': 'premium', 'display_name': 'Test User', 'followers': 100,
                'country': 'US'}

    # Insert new user into the test database
    conn = sqlite3.connect(setup_test_database)
    c = conn.cursor()

    try:
        logging.debug(f"Inserting user: {new_user['user_id']}")
        # Insertion
        c.execute(
            "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country) VALUES (?, ?, ?, ?, ?)",
            (new_user['user_id'], new_user['sub_level'], new_user['display_name'], new_user['followers'],
             new_user['country']))
        conn.commit()

        # Verification of insertion
        c.execute("SELECT * FROM user_logins WHERE user_id=?", (new_user['user_id'],))
        result = c.fetchone()

        assert result is not None
        assert result[1] == new_user['user_id']  # Check user_id
        logging.debug(f"User inserted successfully: {result}")

    finally:
        conn.close()

    logging.debug("Insert user test completed.")

# Test case for deletion
def test_delete_user(setup_test_database):
    # Mock data for insertion
    new_user = {'user_id': 'test_user', 'sub_level': 'premium', 'display_name': 'Test User', 'followers': 100,
                'country': 'US'}

    # Insert new user into the test database
    conn_insert = sqlite3.connect(setup_test_database)
    c_insert = conn_insert.cursor()

    # Delete user from the test database
    conn_delete = sqlite3.connect(setup_test_database)
    c_delete = conn_delete.cursor()

    try:
        # Insertion
        logging.debug(f"Inserting user: {new_user['user_id']}")
        c_insert.execute(
            "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country) VALUES (?, ?, ?, ?, ?)",
            (new_user['user_id'], new_user['sub_level'], new_user['display_name'], new_user['followers'],
             new_user['country']))
        conn_insert.commit()

        # Verification of insertion
        c_insert.execute("SELECT * FROM user_logins WHERE user_id=?", (new_user['user_id'],))
        result = c_insert.fetchone()

        assert result is not None
        assert result[1] == new_user['user_id']  # Check user_id
        logging.debug(f"User inserted successfully: {result}")

        # Deletion
        logging.debug(f"Deleting user: {new_user['user_id']}")
        c_delete.execute("DELETE FROM user_logins WHERE user_id=?", (new_user['user_id'],))
        conn_delete.commit()

        # Verification of deletion
        c_delete.execute("SELECT * FROM user_logins WHERE user_id=?", (new_user['user_id'],))
        result_after_delete = c_delete.fetchone()

        assert result_after_delete is None  # Make sure user no longer exists
        logging.debug("User deleted successfully.")

    finally:
        conn_insert.close()
        conn_delete.close()

    logging.debug("Delete user test completed.")

# This is basically the same as the test_insert_user() test but it is clearer to make a test for reading as well
def test_read_user(setup_test_database):
    # Mock data for insertion
    new_user = {'user_id': 'test_user', 'sub_level': 'premium', 'display_name': 'Test User', 'followers': 100,
                'country': 'US'}

    # Insert new user into the test database
    conn_insert = sqlite3.connect(setup_test_database)
    c_insert = conn_insert.cursor()

    try:
        # Insertion
        logging.debug(f"Inserting new user: {new_user['user_id']}")
        c_insert.execute(
            "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country) VALUES (?, ?, ?, ?, ?)",
            (new_user['user_id'], new_user['sub_level'], new_user['display_name'], new_user['followers'],
             new_user['country']))
        conn_insert.commit()

        # Reading the user
        conn_read = sqlite3.connect(setup_test_database)
        c_read = conn_read.cursor()

        logging.debug(f"Reading inserted user: {new_user['user_id']}")
        c_read.execute("SELECT * FROM user_logins WHERE user_id=?", (new_user['user_id'],))
        result = c_read.fetchone()
        logging.debug(f"Read user: {new_user['user_id']}")

        assert result is not None
        assert result[1] == new_user['user_id']  # Check user_id
        logging.debug(f"Reading finished.")

    finally:
        conn_insert.close()
        conn_read.close()

def test_modify_user(setup_test_database):
    # Mock data for insertion
    new_user = {'user_id': 'test_user', 'sub_level': 'premium', 'display_name': 'Test User', 'followers': 100,
                'country': 'US'}

    # Insert new user into the test database
    conn_insert = sqlite3.connect(setup_test_database)
    c_insert = conn_insert.cursor()

    try:
        # Insertion
        logging.debug(f"Inserting user: {new_user['user_id']}")
        c_insert.execute(
            "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country) VALUES (?, ?, ?, ?, ?)",
            (new_user['user_id'], new_user['sub_level'], new_user['display_name'], new_user['followers'],
             new_user['country']))
        conn_insert.commit()

        # Modifying user details
        conn_modify = sqlite3.connect(setup_test_database)
        c_modify = conn_modify.cursor()

        updated_display_name = 'Modified User'
        logging.debug(f"Updating inserted user: {new_user['user_id']}")

        c_modify.execute("UPDATE user_logins SET display_name=? WHERE user_id=?",
                         (updated_display_name, new_user['user_id']))
        conn_modify.commit()

        # Verification of modification
        logging.debug(f"Verifying the update about user: {new_user['user_id']}.")
        c_modify.execute("SELECT * FROM user_logins WHERE user_id=?", (new_user['user_id'],))
        result = c_modify.fetchone()

        assert result is not None
        assert updated_display_name in result  # Check updated display_name
        logging.debug(f"Verification finished.")

    finally:
        conn_insert.close()
        conn_modify.close()

def test_log_user_login_new_user(setup_test_database):
    # Mock Spotify instance with current_user method
    mock_spotify = MagicMock()
    mock_spotify.current_user.return_value = {
        'id': 'test_user', 'product': 'premium', 'display_name': 'Test User', 'followers': {'total': 100},
        'country': 'US'}

    logging.debug("Logging in new user with data: %s", mock_spotify.current_user.return_value)

    # Patch the sqlite3.connect method to use the test database
    with patch('sqlite3.connect', return_value=sqlite3.connect(setup_test_database)):
        # Log the user login
        log_user_login(mock_spotify)

    # Verify insertion
    conn = sqlite3.connect(setup_test_database)
    c = conn.cursor()
    c.execute("SELECT * FROM user_logins WHERE user_id=?", ('test_user',))
    result = c.fetchone()

    logging.debug("Inserted user data: %s", result)

    assert result is not None

    expected_values = {1: 'test_user', 3: 'premium', 4: 'Test User', 5: 100, 6: 'US'}

    for idx, expected in expected_values.items():
        assert result[idx] == expected, f"Expected {expected} at index {idx}, got {result[idx]}"

    conn.close()

def test_log_user_login_existing_user(setup_test_database):
    # Insert a user into the test database
    conn_insert = sqlite3.connect(setup_test_database)
    c_insert = conn_insert.cursor()
    c_insert.execute(
        "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country) VALUES (?, ?, ?, ?, ?)",
        ('test_user', 'free', 'Old User', 50, 'CA'))
    conn_insert.commit()
    conn_insert.close()

    logging.debug("Inserted existing user with initial data")

    # Mock Spotify instance with current_user method
    mock_spotify = MagicMock()
    mock_spotify.current_user.return_value = {
        'id': 'test_user', 'product': 'premium', 'display_name': 'Test User', 'followers': {'total': 100},
        'country': 'US'
    }

    logging.debug("Logging in existing user with updated data: %s", mock_spotify.current_user.return_value)

    # Patch the sqlite3.connect method to use the test database
    with patch('sqlite3.connect', return_value=sqlite3.connect(setup_test_database)):
        # Log the user login
        log_user_login(mock_spotify)

    # Verify update
    conn = sqlite3.connect(setup_test_database)
    c = conn.cursor()
    c.execute("SELECT * FROM user_logins WHERE user_id=?", ('test_user',))
    result = c.fetchone()

    logging.debug("Updated user data: %s", result)

    assert result is not None

    expected_values = {1: 'test_user', 3: 'premium', 4: 'Test User', 5: 100, 6: 'US'}

    for idx, expected in expected_values.items():
        assert result[idx] == expected, f"Expected {expected} at index {idx}, got {result[idx]}"

    conn.close()

def test_get_user_logins(setup_test_database):
    # Insert mock user data into the test database
    mock_users = [
        ('user_1', 'premium', 'User One', 150, 'US', '2023-06-20 10:00:00'),
        ('user_2', 'free', 'User Two', 75, 'CA', '2023-06-21 15:30:00'),
        ('user_3', 'premium', 'User Three', 200, 'GB', '2023-06-22 08:45:00')
    ]

    conn_insert = sqlite3.connect(setup_test_database)
    c_insert = conn_insert.cursor()
    for user in mock_users:
        c_insert.execute(
            "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country, last_login_time) VALUES (?, ?, ?, ?, ?, ?)",
            user)
    conn_insert.commit()
    conn_insert.close()

    logging.debug("Inserted mock users")

    # Patch the sqlite3.connect method to use the test database
    with patch('sqlite3.connect', return_value=sqlite3.connect(setup_test_database)):
        # Fetch user login details
        user_logins = get_user_logins()

    logging.debug("Fetched user logins: %s", user_logins)

    # Expected results sorted by last_login_time descending --> added 2 hours to the times because I convert them to
    # the current time in our time zone
    expected_user_logins = [
        ('user_3', '2023-06-22 10:45:00', 'premium', 'User Three', 200, 'GB'),
        ('user_2', '2023-06-21 17:30:00', 'free', 'User Two', 75, 'CA'),
        ('user_1', '2023-06-20 12:00:00', 'premium', 'User One', 150, 'US')
    ]

    assert user_logins == expected_user_logins, f"Expected {expected_user_logins}, got {user_logins}"

def test_get_user_stats(setup_test_database):
    # Insert mock user data into the test database
    mock_users = [
        ('user_1', 'premium', 'User One', 150, 'US', '2024-05-12 10:00:00'),
        ('user_2', 'free', 'User Two', 75, 'CA', '2024-05-11 15:30:00'),
        ('user_3', 'premium', 'User Three', 200, 'GB', '2024-05-10 08:45:00'),
        ('user_4', 'premium', 'User Four', 120, 'US', '2024-06-22 10:00:00'),
        ('user_5', 'free', 'User Five', 50, 'CA', '2024-06-16 15:30:00'),
        ('user_6', 'premium', 'User Six', 90, 'GB', '2024-06-20 08:45:00')
    ]

    conn_insert = sqlite3.connect(setup_test_database)
    c_insert = conn_insert.cursor()
    for user in mock_users:
        c_insert.execute(
            "INSERT INTO user_logins (user_id, sub_level, display_name, followers, country, last_login_time) VALUES (?, ?, ?, ?, ?, ?)",
            user)
    conn_insert.commit()
    conn_insert.close()

    logging.debug("Inserted mock users for stats")

    # Patch the sqlite3.connect method to use the test database
    with patch('sqlite3.connect', return_value=sqlite3.connect(setup_test_database)):
        # Fetch user statistics
        user_stats = get_user_stats()

    logging.debug("Fetched user stats: %s", user_stats)

    # Expected results
    expected_stats = {
        "total_users": 6, "premium_users": 4, "premium_percentage": "66.667", "avg_followers": "114.167",
        "most_common_country": "US", "weekly_logins": 2, "monthly_logins": 3, "inactive_users_count": 3
    }

    for key, expected_value in expected_stats.items():
        assert user_stats[key] == expected_value, f"Expected {expected_value} for {key}, got {user_stats[key]}"

# Fixture for mocking Spotify API responses --> used to test if an empty list is returned for different search types
@pytest.fixture
def mock_spotify_empty():
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.search.return_value = {'artists': {'items': []}, 'tracks': {'items': []},
                                                 'albums': {'items': []},
                                                 'playlists': {'items': []}, 'shows': {'items': []},
                                                 'episodes': {'items': []}}
    return mock_spotify_instance

# Mocked function for get_token
def mock_get_token():
    return {
        "access_token": "mock_access_token", "expires_at": 3600, "token_type": "Bearer",
        "refresh_token": "mock_refresh_token"
    }

def test_search_artist_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('artist_name', 'artist')
            assert results == [], "Expected empty list for artist search"

def test_search_track_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('track_name', 'track')
            assert results == [], "Expected empty list for track search"

def test_search_album_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('album_name', 'album')
            assert results == [], "Expected empty list for album search"

def test_search_playlist_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('playlist_name', 'playlist')
            assert results == [], "Expected empty list for playlist search"

def test_search_show_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('show_name', 'show')
            assert results == [], "Expected empty list for show search"

def test_search_episode_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('episode_name', 'episode')
            assert results == [], "Expected empty list for episode search"

def test_invalid_search_type_empty(mock_spotify_empty):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_empty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify('invalid_query', 'invalid_type')
            assert results == [], "Expected empty list for invalid search type"

@pytest.fixture
def mock_spotify_nonempty():
    mock_spotify_instance = MagicMock()

    def mock_search(q, type, limit=10):
        mock_responses = {
            'artist': {
                'artists': {
                    'items': [
                        {
                            'followers': {'total': 85656875}, 'genres': ['detroit hip hop', 'hip hop', 'rap'],
                            'id': '7dGJo4pcD2V6oG8kP0tJRR', 'name': 'Eminem', 'popularity': 91,
                            'images': [{'height': 160,
                                        'url': 'https://i.scdn.co/image/ab6761610000f178a00b11c129b27a88fc72f36b',
                                        'width': 160}],
                        }]}
            },
            'track': {
                'tracks': {
                    'items': [
                        {"duration_ms": 227239, "explicit": True, "name": "Houdini", "popularity": 91},
                        {"duration_ms": 200000, "explicit": False, "name": "Houdini's Revenge", "popularity": 80},
                        {"duration_ms": 180000, "explicit": False, "name": "Another Track", "popularity": 85},
                        {"duration_ms": 240000, "explicit": True, "name": "Houdini", "popularity": 89},
                        {"duration_ms": 210000, "explicit": False, "name": "Track Houdini", "popularity": 88},
                        {"duration_ms": 190000, "explicit": True, "name": "Not Houdini", "popularity": 75},
                    ]
                }
            },
            'album': {
                'albums': {
                    'items': [
                        {'name': 'Sample Album', 'release_date': '2023-01-01', 'total_tracks': 12, 'popularity': 80},
                        {'name': 'Album Sample', 'release_date': '2023-02-01', 'total_tracks': 10, 'popularity': 85},
                        {'name': 'Another Album', 'release_date': '2023-03-01', 'total_tracks': 8, 'popularity': 70},
                        {'name': 'Sample Album', 'release_date': '2023-04-01', 'total_tracks': 15, 'popularity': 75},
                        {'name': 'Album Sample', 'release_date': '2023-05-01', 'total_tracks': 11, 'popularity': 82},
                    ]
                }
            },
            'playlist': {
                'playlists': {
                    'items': [
                        {'name': 'Sample Playlist', 'description': 'This is a sample playlist',
                         'tracks': {'total': 20}, 'owner': {'display_name': 'Sample Owner'},
                         }
                    ]
                }
            },
            'show': {
                'shows': {
                    'items': [
                        {'name': 'Example Show', 'publisher': 'Sample Publisher',
                         'description': 'This is a sample show', 'total_episodes': 50}
                    ]
                }
            },
            'episode': {
                'episodes': {
                    'items': [
                        {'name': 'Random Episode', 'description': 'This is a sample episode', 'duration_ms': 1800000,
                         'release_date': '2023-05-01',
                         }
                    ]
                }
            }
        }
        return mock_responses.get(type, {'items': []})  # Return empty list for unrecognized types

    mock_spotify_instance.search.side_effect = mock_search

    return mock_spotify_instance

# Parameterized test to cover different search types (testing also if it removed duplicates)
@pytest.mark.parametrize("search_type, query, expected_count",
                         [("track", "Houdini", 4),
                          ("track", "Album", 0),
                          ("album", "Sample", 2),
                          ("album", "Another", 1),
                          ("playlist", "Sample", 1),
                          ("show", "Example", 1),
                          ("episode", "Random", 1)])
def test_search_functions(mock_spotify_nonempty, search_type, query, expected_count):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_nonempty):
        with patch('app.models.get_token', side_effect=mock_get_token):
            results = search_spotify(query, search_type)
            print(results)
            assert len(
                results) == expected_count, f"Expected {expected_count} results for {search_type} search with query '{query}', but got {len(results)}"


mock_user_info = {
    "display_name": "Mock User", "id": "mock_user_id", "email": "mock_user@example.com", "followers": {"total": 1000},
    "product": "premium", "country": "US", "images": [{"url": "https://example.com/profile.jpg"}]
}

@pytest.fixture
def mock_get_token_():
    with patch('app.models.get_token') as mock_get_token_:
        mock_get_token.return_value = mock_get_token()
        yield mock_get_token

@pytest.fixture
def mock_spotify_current_user():
    mock_spotify_instance = MagicMock()

    # Mock current_user method
    def mock_current_user():
        return mock_user_info

    mock_spotify_instance.current_user.side_effect = mock_current_user
    return mock_spotify_instance

def test_display_current_user(mock_get_token_, mock_spotify_current_user):
    with patch('app.models.spotipy.Spotify', return_value=mock_spotify_current_user):
        user_data = display_current_user()

    expected_user_data = mock_user_info

    for key in expected_user_data:
        if key == "followers":
            assert user_data[key] == expected_user_data[key]["total"]
        else:
            assert user_data[key] == expected_user_data[
                key], f"Expected {key} to be {expected_user_data[key]}, but got {user_data[key]}"

@pytest.fixture
def mock_spotify_top_items():
    mock_spotify_instance = MagicMock()

    # Mocking current_user_top_tracks method
    mock_spotify_instance.current_user_top_tracks.return_value = {
        "items": [
            {"name": "Track 1", "album": {"name": "Album 1", "images": [{"url": "https://example.com/image1.jpg"}]},
             "artists": [{"name": "Artist 1"}]},
            {"name": "Track 2", "album": {"name": "Album 2", "images": [{"url": "https://example.com/image2.jpg"}]},
             "artists": [{"name": "Artist 2"}]}
        ]
    }

    # Mocking current_user_top_artists method
    mock_spotify_instance.current_user_top_artists.return_value = {
        "items": [
            {"name": "Artist 1", "images": [{"url": "https://example.com/artist1.jpg"}]},
            {"name": "Artist 2", "images": [{"url": "https://example.com/artist2.jpg"}]}
        ]
    }

    return mock_spotify_instance

def test_get_top_items(mock_get_token_, mock_spotify_top_items):
    with patch('app.models.get_token', return_value=mock_get_token()):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_top_items):
            top_items = get_top_items()

    assert len(top_items["tracks"]) == 2
    assert len(top_items["artists"]) == 2

    expected_tracks = [
        {"name": "Track 1", "album": "Album 1", "artists": "Artist 1", "image_url": "https://example.com/image1.jpg"},
        {"name": "Track 2", "album": "Album 2", "artists": "Artist 2", "image_url": "https://example.com/image2.jpg"},
    ]

    expected_artists = [
        {"name": "Artist 1", "image_url": "https://example.com/artist1.jpg"},
        {"name": "Artist 2", "image_url": "https://example.com/artist2.jpg"},
    ]

    # Assert tracks
    assert len(top_items["tracks"]) == len(expected_tracks)
    for i, expected_track in enumerate(expected_tracks):
        for key in expected_track:
            assert top_items["tracks"][i][key] == expected_track[key], \
                f"Expected track {i + 1}, {key} to be {expected_track[key]}, but got {top_items['tracks'][i][key]}"

    # Assert artists
    assert len(top_items["artists"]) == len(expected_artists)
    for i, expected_artist in enumerate(expected_artists):
        for key in expected_artist:
            assert top_items["artists"][i][key] == expected_artist[key], \
                f"Expected artist {i + 1}, {key} to be {expected_artist[key]}, but got {top_items['artists'][i][key]}"

@pytest.fixture
def mock_spotify_artist_data():
    # Mock data for artist details
    artist_details = {
        'name': 'Sample Artist', 'followers': {'total': 1000000}, 'genres': ['pop', 'rock'], 'popularity': 80,
        'images': [{'url': 'https://example.com/artist.jpg', 'height': 200, 'width': 200}]
    }

    # Mock data for artist albums
    artist_albums = {
        'items': [
            {'name': 'Album 1', 'release_date': '2023-01-01', 'total_tracks': 12},
            {'name': 'Album 2', 'release_date': '2023-05-15', 'total_tracks': 10}
        ]
    }

    # Mock data for artist top tracks
    artist_top_tracks = {
        'tracks': [
            {'name': 'Track 1', 'duration_ms': 240000, 'explicit': False},
            {'name': 'Track 2', 'duration_ms': 210000, 'explicit': True}
        ]
    }

    # Mock data for related artists
    artist_related_artists = {
        'artists': [
            {'name': 'Related Artist 1', 'followers': {'total': 123123}, 'genres': ['jazz', 'rock'],
             'popularity': 70, 'images': [{'url': 'https://example.com/rel_artist1.jpg', 'height': 100, 'width': 100}]},
            {'name': 'Related Artist 2',
             'followers': {'total': 345123}, 'genres': ['rap', 'pop'], 'popularity': 60,
             'images': [{'url': 'https://example.com/rel_artist2.jpg', 'height': 150, 'width': 150}]}
        ]
    }

    return artist_details, artist_albums, artist_top_tracks, artist_related_artists

def test_get_specific_artist(mock_spotify_artist_data, mock_get_token_fix):
    artist_name = 'Sample Artist'  # Artist name to search for

    # Mocking search_spotify function to return mock artist data
    mock_search_spotify = MagicMock(return_value=[{
        'id': 'sample_artist_id',
        'name': 'Sample Artist',
        'popularity': 80,
        'genres': ['pop', 'rock'],
        'images': [{'url': 'https://example.com/artist.jpg', 'height': 200, 'width': 200}]
    }])

    mock_spotify_instance = MagicMock()
    mock_spotify_instance.artist.return_value = mock_spotify_artist_data[0]
    mock_spotify_instance.artist_albums.return_value = mock_spotify_artist_data[1]
    mock_spotify_instance.artist_top_tracks.return_value = mock_spotify_artist_data[2]
    mock_spotify_instance.artist_related_artists.return_value = mock_spotify_artist_data[3]

    with patch('app.models.search_spotify', mock_search_spotify):
        with patch('app.models.get_token', mock_get_token_fix):
            with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
                artist_details, artist_albums, artist_top_tracks, artist_related_artists = get_specific_artist(
                    artist_name)

    expected_data = {
        'artist_details': mock_spotify_artist_data[0],
        'artist_albums': mock_spotify_artist_data[1],
        'artist_top_tracks': mock_spotify_artist_data[2],
        'artist_related_artists': mock_spotify_artist_data[3]
    }

    # Iterate over each key and assert the corresponding data
    for key, expected_value in expected_data.items():
        if key == 'artist_albums' and artist_albums:
            assert len(artist_albums['items']) == len(expected_value['items'])
            for idx, item in enumerate(expected_value['items']):
                assert artist_albums['items'][idx]['name'] == item['name']
                assert artist_albums['items'][idx]['release_date'] == item['release_date']
                assert artist_albums['items'][idx]['total_tracks'] == item['total_tracks']
        elif key == 'artist_details' and artist_details:
            assert artist_details == expected_value
        elif key == 'artist_top_tracks' and artist_top_tracks:
            assert len(artist_top_tracks['tracks']) == len(expected_value['tracks'])
            for idx, track in enumerate(expected_value['tracks']):
                assert artist_top_tracks['tracks'][idx]['name'] == track['name']
                assert artist_top_tracks['tracks'][idx]['duration_ms'] == track['duration_ms']
                assert artist_top_tracks['tracks'][idx]['explicit'] == track['explicit']
        elif key == 'artist_related_artists' and artist_related_artists:
            assert len(artist_related_artists['artists']) == len(expected_value['artists'])
            for idx, related_artist in enumerate(expected_value['artists']):
                assert artist_related_artists['artists'][idx]['name'] == related_artist['name']
                assert artist_related_artists['artists'][idx]['followers']['total'] == related_artist['followers'][
                    'total']
                assert artist_related_artists['artists'][idx]['popularity'] == related_artist['popularity']
        else:
            raise AssertionError(f"Unexpected key found in expected_data: {key}")

@pytest.fixture
def mock_spotify_followed_artists():
    # Mock data for followed artists
    mock_followed_artists = [
        {'id': 'artist1_id', 'name': 'Artist 1'}, {'id': 'artist2_id', 'name': 'Artist 2'},
        {'id': 'artist3_id', 'name': 'Artist 3'}, {'id': 'artist4_id', 'name': 'Artist 4'},
        {'id': 'artist5_id', 'name': 'Artist 5'}, {'id': 'artist6_id', 'name': 'Artist 6'}
    ]
    return mock_followed_artists

@pytest.fixture
def mock_get_token_fix():
    return MagicMock(return_value={
        "access_token": "mock_access_token", "expires_at": 3600, "token_type": "Bearer",
        "refresh_token": "mock_refresh_token"
    })

def test_get_who_curr_user_follows(mock_spotify_followed_artists, mock_get_token_fix):
    # Mocking spotipy.Spotify class
    mock_spotify_instance = MagicMock()

    # Mock the single call to current_user_followed_artists to return all artists
    mock_spotify_instance.current_user_followed_artists.return_value = {
        'artists': {'items': mock_spotify_followed_artists}
    }

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            followed_artists = get_who_curr_user_follows()

    # Assert the length and contents of followed_artists
    assert len(followed_artists) == len(mock_spotify_followed_artists)
    for expected_artist, actual_artist in zip(mock_spotify_followed_artists, followed_artists):
        assert expected_artist['id'] == actual_artist['id']
        assert expected_artist['name'] == actual_artist['name']

def test_unfollow_artist(mock_get_token_fix):
    artist_id = 'artist123'  # Example artist ID to unfollow

    # Mocking spotipy.Spotify class
    mock_spotify_instance = MagicMock()

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            result = unfollow_artist(artist_id)

    # Assert that the function returns the artist_id after unfollowing
    assert result == artist_id

    # Assert that user_unfollow_artists method was called once with the correct arguments
    mock_spotify_instance.user_unfollow_artists.assert_called_once_with([artist_id])

# Test function for follow_artist
def test_follow_artist(mock_get_token_fix):
    artist_id = 'artist123'  # Example artist ID to follow

    # Mocking spotipy.Spotify class
    mock_spotify_instance = MagicMock()

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            result = follow_artist(artist_id)

    # Assert that the function returns the artist_id after following
    assert result == artist_id

    # Assert that user_follow_artists method was called once with the correct arguments
    mock_spotify_instance.user_follow_artists.assert_called_once_with([artist_id])

def test_get_playlists(mock_get_token_fix):
    # Example mock playlists data
    mock_playlists_data = {
        'items': [
            {'id': 'playlist1_id', 'name': 'Playlist 1'},
            {'id': 'playlist2_id', 'name': 'Playlist 2'},
            {'id': 'playlist3_id', 'name': 'Playlist 3'}
        ]
    }

    # Mocking spotipy.Spotify class
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.current_user_playlists.return_value = mock_playlists_data

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            playlists = get_playlists()

    # Assert the returned playlists match the mock data
    assert playlists == mock_playlists_data

    # Assert that current_user_playlists method was called once
    mock_spotify_instance.current_user_playlists.assert_called_once()

def test_get_playlist(mock_get_token_fix):
    # Example playlist_id to fetch
    playlist_id = 'playlist123'

    # Example mock playlist data
    mock_playlist_data = {
        'id': playlist_id,
        'name': 'Test Playlist',
        'description': 'This is a mock playlist for testing purposes',
        'tracks': {
            'items': [
                {'track': {'id': 'track1_id', 'name': 'Track 1'}},
                {'track': {'id': 'track2_id', 'name': 'Track 2'}}
            ]
        }
    }

    # Mocking spotipy.Spotify class
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.playlist.return_value = mock_playlist_data

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            playlist = get_playlist(playlist_id)

    # Assert the returned playlist matches the mock data
    assert playlist == mock_playlist_data

    # Assert that playlist method was called once with the correct playlist_id
    mock_spotify_instance.playlist.assert_called_once_with(playlist_id=playlist_id)

def test_add_to_playlist(mock_get_token_fix):
    # Example playlist_id and song_name
    playlist_id = 'playlist123'
    song_name = 'Example Song'

    # Mock Spotify search results for the song
    mock_song_id = 'track123'
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.search.return_value = {
        'tracks': {
            'items': [{'id': mock_song_id}]
        }
    }

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            result = add_to_playlist(playlist_id, song_name)

    # Assert that the function returns True indicating successful addition
    assert result is True

    # Assert that search method was called once with correct parameters
    mock_spotify_instance.search.assert_called_once_with(q=song_name, type='track', limit=1)

    # Assert that playlist_add_items method was called once with correct parameters
    mock_spotify_instance.playlist_add_items.assert_called_once_with(playlist_id, [mock_song_id])

def test_add_to_playlist_song_not_found(mock_get_token_fix):
    playlist_id = 'playlist123'
    song_name = 'Non-existent Song'

    # Mock Spotify search results for the song (empty items list)
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.search.return_value = {
        'tracks': {
            'items': []
        }
    }

    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            result = add_to_playlist(playlist_id, song_name)

    # Assert that the function returns False indicating song not found
    assert result is False

    # Assert that search method was called once with correct parameters
    mock_spotify_instance.search.assert_called_once_with(q=song_name, type='track', limit=1)

    # Assert that playlist_add_items method was not called
    mock_spotify_instance.playlist_add_items.assert_not_called()

def test_create_spot_playlist(mock_get_token_fix):
    # Mock input parameters
    playlist_name = 'Test Playlist'
    playlist_description = 'This is a test playlist'
    is_public = True

    # Mock Spotify instance and its methods
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.current_user.return_value = {'id': 'user123'}
    mock_spotify_instance.user_playlist_create.return_value = {
        'id': 'playlist123', 'name': playlist_name, 'description': playlist_description, 'public': is_public
    }

    # Mocking spotipy.Spotify class
    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            playlist = create_spot_playlist(playlist_name, playlist_description, is_public)

    # Assert the result of create_spot_playlist function
    assert playlist['name'] == playlist_name
    assert playlist['description'] == playlist_description
    assert playlist['public'] == is_public

    # Assert that user_playlist_create method was called once with the correct arguments
    mock_spotify_instance.user_playlist_create.assert_called_once_with(
        user='user123', name=playlist_name, public=is_public, description=playlist_description)

def test_edit_playlist_details(mock_get_token_fix):
    # Mock input parameters
    playlist_id = 'playlist123'
    new_name = 'New Playlist Name'
    new_description = 'Updated playlist description'
    new_public = True

    # Mock Spotify instance and its methods
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.playlist_change_details.return_value = {
        'id': playlist_id,
        'name': new_name,
        'description': new_description,
        'public': new_public
    }

    # Mocking spotipy.Spotify class
    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            updated_playlist = edit_playlist_details(playlist_id, new_name=new_name, new_description=new_description,
                                                     new_public=new_public)

    # Assert the result of edit_playlist_details function
    assert updated_playlist['id'] == playlist_id
    assert updated_playlist['name'] == new_name
    assert updated_playlist['description'] == new_description
    assert updated_playlist['public'] == new_public

    # Assert that playlist_change_details method was called once with the correct arguments
    mock_spotify_instance.playlist_change_details.assert_called_once_with(
        playlist_id, name=new_name, description=new_description, public=new_public)

def test_follow_playlist(mock_get_token_fix):
    # Mock input parameters
    playlist_id = 'playlist123'

    # Mock Spotify instance and its methods
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.current_user_follow_playlist.return_value = None

    # Mocking spotipy.Spotify class
    with patch('app.models.get_token', mock_get_token_fix):
        with patch('app.models.spotipy.Spotify', return_value=mock_spotify_instance):
            result = follow_playlist(playlist_id)

    # Assert the result of follow_playlist function
    assert result is True

    # Assert that current_user_follow_playlist method was called once with the correct arguments
    mock_spotify_instance.current_user_follow_playlist.assert_called_once_with(playlist_id)
