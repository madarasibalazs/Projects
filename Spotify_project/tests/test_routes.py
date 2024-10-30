
from unittest.mock import patch, call, MagicMock
import pytest
from flask import session, url_for
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

def test_login_redirects_to_spotify(client, mocker):
    # Mock the create_spotify_oauth function to return a predictable authorization URL
    mock_oauth = mocker.Mock()
    mock_oauth.get_authorize_url.return_value = 'https://accounts.spotify.com/authorize?...'
    mocker.patch('app.routes.create_spotify_oauth', return_value=mock_oauth)

    # Simulate a request to the login route
    response = client.get('/')

    # Check if session is cleared (empty)
    assert 'spotify_token' not in session
    assert len(session.items()) == 0

    # Check if the response is a redirect
    assert response.status_code == 302
    assert response.location.startswith('https://accounts.spotify.com/authorize')

def test_home_page(client):
    response = client.get('/home')
    assert response.status_code == 302
    assert "Set-Cookie" in response.headers.keys()
    assert b"You should be redirected automatically to the target URL" in response.data

@patch('app.routes.create_spotify_oauth')
@patch('app.routes.display_current_user')
@patch('app.routes.log_user_login')
def test_redirect_page(mock_log_user_login, mock_display_current_user, mock_create_spotify_oauth, client):
    # Mock the get_access_token method
    mock_oauth_instance = mock_create_spotify_oauth.return_value
    mock_oauth_instance.get_access_token.return_value = {
        'access_token': 'test_access_token','token_type': 'Bearer', 'expires_in': 3600, 'refresh_token': 'mock_refresh_token'}

    # Mock the display_current_user function
    mock_display_current_user.return_value = {'id': 'test_user_id', 'display_name': 'Test User'}

    # Simulate a request to the /redirect route with a code parameter
    response = client.get('/redirect?code=test_code')

    # Check if the response is a redirect to the home page
    assert response.status_code == 302
    assert b"Redirecting" in response.data
    assert b"/home" in response.data
    assert response.location == "/home"

    # Check if the token info is stored in the session
    with client.session_transaction() as sess:
        assert 'token_info' in sess
        assert len(sess['token_info']) == 3
        assert sess['token_info'] == {
            'access_token': 'test_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }

    # Check if the user ID is stored in the session
    with client.session_transaction() as sess:
        assert 'user_id' in sess
        assert sess['user_id'] == 'test_user_id'

    # Check that the get_access_token method was called with the correct parameters
    mock_oauth_instance.get_access_token.assert_called_once_with('test_code', check_cache=False)

    # Check that the display_current_user function was called
    mock_display_current_user.assert_called_once()

    # Check that the log_user_login function was called
    mock_log_user_login.assert_called_once()

@patch('app.routes.get_user_logins')
def test_user_logins(mock_get_user_logins, client):
    # Mock the get_user_logins function
    mock_get_user_logins.return_value = [
        (1, '2024-06-19 11:01:01', "free", 'user1', 2, "US"),
        (2, '2024-06-18 12:02:02', "premium", 'user2', 100, "UK"),
    ]

    # Simulate a request to the /user_logins route
    response = client.get('/user_logins')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered with the expected data
    user_logins = mock_get_user_logins.return_value
    for item in user_logins:
        for data in item:
            assert str(data).encode() in response.data

    # Verify that the get_user_logins function was called once
    mock_get_user_logins.assert_called_once()

@patch('app.routes.get_user_stats')
def test_user_stats(mock_get_user_stats, client):
    # Mock the get_user_stats function
    mock_get_user_stats.return_value = {
        'total_users': 1000, 'premium_users': 400, 'premium_percentage': 40, 'avg_followers': 150,
        'most_common_country': 'US', 'weekly_logins': 200, 'monthly_logins': 800, 'inactive_users_count': 50
    }

    # Simulate a request to the /user_stats route
    response = client.get('/user_stats')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered with the expected data
    stats = mock_get_user_stats.return_value
    for key, value in stats.items():
        assert str(value).encode() in response.data

    # Verify that the get_user_stats function was called once
    mock_get_user_stats.assert_called_once()

def test_search_get(client):
    # Simulate a GET request to /search
    response = client.get('/search')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Spotify Search' in response.data

def test_search_post(client, monkeypatch):
    # Mocking the search_spotify function to return test data
    def mock_search_spotify(query, search_type):
        if search_type == 'artist':
            return [
                {
                    'name': 'Example Artist', 'images': [{'url': 'https://example.com/artist_image.jpg'}],
                    'genres': ['Pop', 'Rock'], 'followers': {'total': 10000}, 'popularity': 80
                },
                {
                    'name': 'Related Artist 1', 'images': [{'url': 'https://example.com/related_artist_image.jpg'}],
                    'genres': ['Alternative'], 'followers': {'total': 5000}, 'popularity': 70
                },
                {
                    'name': 'Related Artist 2', 'images': [], 'genres': ['Pop'], 'followers': {'total': 8000},
                    'popularity': 75
                }
            ]
        elif search_type == 'album':
            return [
                {
                    'name': 'Album 1', 'artists': [{'name': 'Example Artist'}],
                    'images': [{'url': 'https://example.com/album_image.jpg'}],
                    'album_type': 'album', 'total_tracks': 12, 'release_date': '2023-01-01',
                }
            ]
        elif search_type == 'track':
            return [
                {
                    'name': 'Track A', 'artists': [{'name': 'Example Artist'}],
                    'album': {
                        'name': 'Album 1', 'release_date': '2023-01-01',
                        'images': [{'url': 'https://example.com/album_image.jpg'}]
                    },
                    'duration_ms': 240000, 'explicit': False, 'popularity': 70,
                }
            ]

        return []  # Return an empty list if search_type is unknown or not implemented

    monkeypatch.setattr('app.routes.search_spotify', mock_search_spotify)

    # Simulate a POST request to /search
    form_data = {'query': 'Example', 'type': 'artist'}
    response = client.post('/search', data=form_data)

    expected_items = [
        ('Example Artist', ['https://example.com/artist_image.jpg'], ['Pop', 'Rock'], '10000', '80'),
        ('Related Artist 1', ['https://example.com/related_artist_image.jpg'], ['Alternative'], '5000', '70'),
        ('Related Artist 2', [], ['Pop'], '8000', '75')
    ]

    for name, images, genres, followers, popularity in expected_items:
        assert name.encode() in response.data
        for image in images:
            assert image.encode() in response.data
        for genre in genres:
            assert genre.encode() in response.data
        assert str(followers).encode() in response.data
        assert str(popularity).encode() in response.data

    # Verify the "Back to Search" and "Back to Home" links are present
    assert b'<a href="/search">Back to Search</a>' in response.data
    assert b'<a href="/home">Back to Home</a>' in response.data

def test_get_current_user(client, mocker):
    # Mock data for display_current_user function
    mock_user_data = {
        'display_name': 'test_user', 'id': "TestID", 'email': 'test_user@example.com',
        'followers': 123, 'product': "premium", 'country': "US"
    }
    mocker.patch('app.routes.display_current_user', return_value=mock_user_data)

    # Simulate a GET request to /current_user
    response = client.get('/current_user')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Spotify User Info' in response.data

    # Check if user_data is passed to the template correctly
    stats = mock_user_data
    for value in stats.values():
        assert str(value).encode() in response.data

def test_get_current_user_top_items(client, mocker):
    # Mock data for display_current_user function
    tracks = [
        {'name': 'Track 1', 'album': 'Album 1', 'artists': 'Artist 1, Artist 2'},
        {'name': 'Track 2', 'album': 'Album 2', 'artists': 'Artist 3'},
        {'name': 'Track 3', 'album': 'Album 3', 'artists': 'Artist 4'}
    ]

    artists = [{'name': 'Artist A'}, {'name': 'Artist B'}, {'name': 'Artist C'}]

    # Construct the mock items object similar to what get_top_items() would return
    mock_items = {
        'tracks': tracks,
        'artists': artists
    }
    mocker.patch('app.routes.get_top_items', return_value=mock_items)

    # Simulate a GET request to /current_user
    response = client.get('/top_items')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Top Tracks' in response.data
    assert b'Top Artists' in response.data

    # Check if user_data is passed to the template correctly
    for track in tracks:
        for value in track.values():
            assert str(value).encode() in response.data

    for artist in artists:
        for value in artist.values():
            assert str(value).encode() in response.data

def test_artist_get(client):
    # Simulate a GET request to /search
    response = client.get('/artists')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Artist Search' in response.data

# Helper function for the test after it
def mock_get_specific_artist(artist_name):
    artist_details = {
        'name': artist_name, 'images': [{'url': 'https://example.com/artist_image.jpg'}],
        'genres': ['Pop', 'Rock'], 'followers': {'total': 10000}, 'popularity': 80,
        'external_urls': {'spotify': 'https://open.spotify.com/artist/artist_id'}
    }

    artist_top_tracks = {'tracks': [{'name': 'Track A'}, {'name': 'Track B'}]}

    artist_albums = {'items': [{'name': 'Album 1'}, {'name': 'Album 2'}]}

    artist_related_artists = {'artists': [{'name': 'Related Artist 1'}, {'name': 'Related Artist 2'}]}

    return artist_details, artist_albums, artist_top_tracks, artist_related_artists

def test_post_get_artist(client):
    artist_name = 'Example Artist'

    with patch('app.routes.get_specific_artist', side_effect=mock_get_specific_artist):
        # Simulate a POST request to '/artists' with form data
        response = client.post('/artists', data={'query': artist_name})

        # Check if the response status code is 200 (OK)
        assert response.status_code == 200

        # Check if the correct template is rendered
        assert b'Artist Details' in response.data

        # Check if the form template is not rendered when artist_details is returned
        assert b'Artist Search' not in response.data

        def assert_in_recursive(data, response_data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        assert_in_recursive(value, response_data)
                    else:
                        assert str(value) in response_data
            elif isinstance(data, list):
                for item in data:
                    assert_in_recursive(item, response_data)
            else:
                assert str(data) in response_data

        # Check if the data is passed to the template correctly
        info = mock_get_specific_artist(artist_name)
        for element in info:
            assert_in_recursive(element, response.data.decode())

        # Simulate when artist_details is not returned (empty result)
        # Mock get_specific_artist to return None for artist_details
        with patch('app.routes.get_specific_artist', return_value=(None, None, None, None)):
            response_empty = client.post('/artists', data={'query': 'Non-existent Artist'})

            # Check if the response status code is 200 (OK) when no artist_details is returned
            assert response_empty.status_code == 200

            # Check if the form template is rendered again when artist_details is not found
            assert b'Artist Search' in response_empty.data

def test_get_users_following(client, monkeypatch):
    # Mocking the get_who_curr_user_follows function to return test data
    def mock_get_who_curr_user_follows():
        return [
            {'id': '1', 'name': 'Artist 1', 'genres': ['Pop', 'Rock', 'Rap'], 'followers': {'total': 3542},
             'images': [{'url': 'https://example.com/artist1.jpg'}]},
            {'id': '2', 'name': 'Artist 2', 'genres': ['Retro', 'Rap'], 'followers': {'total': 12000},
             'images': [{'url': 'https://example.com/artist2.jpg'}]},
        ]

    monkeypatch.setattr('app.routes.get_who_curr_user_follows', mock_get_who_curr_user_follows)

    # Simulate a GET request to /following
    response = client.get('/following')
    assert response.status_code == 200

    data = mock_get_who_curr_user_follows()

    for item in data:
        assert item['name'].encode() in response.data
        for genre in item['genres']:
            assert genre.encode() in response.data
        assert str(item['followers']['total']).encode() in response.data
        for image in item['images']:
            assert image['url'].encode() in response.data

def test_post_unfollow_artist(client, monkeypatch):
    # Mocking the unfollow_artist function
    def mock_unfollow_artist(artist_id):
        assert artist_id == '1'  # We expect the artist_id to be '1' based on the test data

    monkeypatch.setattr('app.routes.unfollow_artist', mock_unfollow_artist)

    # Simulate a POST request to /following with form data
    form_data = {'artist_id': '1'}
    response = client.post('/following', data=form_data)

    # Check if the response status code is 302 (Redirect)
    assert response.status_code == 302

    # Check if the response headers contain the correct redirect location
    assert response.headers['Location'] == '/following'
    assert b'You should be redirected automatically to the target URL:' in response.data

    # Follow up with a GET request to ensure the artist was unfollowed
    def mock_get_who_curr_user_follows_after_unfollow():
        return [
            {'id': '2', 'name': 'Artist 2', 'genres': ['Retro', 'Rap'], 'followers': {'total': 12000},
             'images': [{'url': 'https://example.com/artist2.jpg'}]},
        ]

    monkeypatch.setattr('app.routes.get_who_curr_user_follows', mock_get_who_curr_user_follows_after_unfollow)
    response = client.get('/following')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    data = mock_get_who_curr_user_follows_after_unfollow()
    for item in data:
        assert item['name'].encode() in response.data
        for genre in item['genres']:
            assert genre.encode() in response.data
        assert str(item['followers']['total']).encode() in response.data
        for image in item['images']:
            assert image['url'].encode() in response.data

def test_follow_artist_get(client):
    # Simulate a GET request to /follow
    response = client.get('/follow')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Follow an artist' in response.data
    assert b'<a href="/home">Back to Home</a>' in response.data

def test_follow_artist_post(client, monkeypatch):
    # Mocking the search_spotify function to return test data
    def mock_search_spotify(query, search_type):
        return [
            {'id': '1', 'name': 'Artist 1', 'genres': ['Pop', 'Rock'], 'followers': {'total': 5000}, 'popularity': 80,
             'images': [{'url': 'https://example.com/artist1.jpg'}]},
            {'id': '2', 'name': 'Artist 2', 'genres': ['Rap'], 'followers': {'total': 3000}, 'popularity': 70,
             'images': [{'url': 'https://example.com/artist2.jpg'}]},
            {'id': '3', 'name': 'Artist 3', 'genres': ['Jazz'], 'followers': {'total': 2000}, 'popularity': 60,
             'images': [{'url': 'https://example.com/artist3.jpg'}]},
        ]

    monkeypatch.setattr('app.routes.search_spotify', mock_search_spotify)

    # Mocking the get_who_curr_user_follows function to return test data
    def mock_get_who_curr_user_follows():
        return [
            {'id': '1', 'name': 'Artist 1', 'genres': ['Pop', 'Rock'], 'followers': {'total': 5000},
             'images': [{'url': 'https://example.com/artist1.jpg'}]},
        ]

    monkeypatch.setattr('app.routes.get_who_curr_user_follows', mock_get_who_curr_user_follows)

    # Simulate a POST request to /follow with form data
    form_data = {'name': 'Artist 1'}
    response = client.post('/follow', data=form_data)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered and contains the flash message
    assert b"You are already following the artists &#39;Artist 1&#39" in response.data
    assert b" Here are some possibly similar artists." in response.data

    # Check if the search results are displayed in the response data
    results = mock_search_spotify('Artist 1', 'artist')
    for item in results[1:]:  # The first artist (the one that the user is already following) is not displayed
        assert item['name'].encode() in response.data
        for genre in item['genres']:
            assert genre.encode() in response.data
        assert str(item['followers']['total']).encode() in response.data
        assert str(item['popularity']).encode() in response.data
        for image in item['images']:
            assert image['url'].encode() in response.data

    # Simulate another POST request with a new artist that is not already followed
    form_data = {'name': 'Artist 2'}
    response = client.post('/follow', data=form_data)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the search results are displayed in the response data
    results = mock_search_spotify('Artist 2', 'artist')
    for item in results[1:]:
        assert item['name'].encode() in response.data
        for genre in item['genres']:
            assert genre.encode() in response.data
        assert str(item['followers']['total']).encode() in response.data
        assert str(item['popularity']).encode() in response.data
        for image in item['images']:
            assert image['url'].encode() in response.data

def test_follow_artist_action(client):
    artist_id = '1'

    # Mock the follow_artist function
    with patch('app.routes.follow_artist') as mock_follow_artist:
        # Simulate a POST request to /follow/<artist_id>
        response = client.post(f'/follow/{artist_id}')

        # Check if the follow_artist function was called with the correct artist_id
        mock_follow_artist.assert_called_once_with(artist_id)

        # Check if the response redirects to the get_users_following endpoint
        assert response.status_code == 302  # 302 is the HTTP status code for redirection
        assert response.location == '/following'
        assert b'You should be redirected automatically to the target URL:' in response.data

def mock_current_user_playlists():
    return {
        'items': [
            {
                'collaborative': False, 'description': 'This is a test playlist 1', 'id': 'playlist1_id',
                'images': [{'url': 'https://example.com/playlist1.jpg'}], 'name': 'My Playlist 1',
                'owner': {'display_name': 'Test User'}, 'public': True, 'tracks': {'total': 15},
            },
            {
                'collaborative': True, 'id': 'playlist2_id', 'images': [], 'name': 'My Playlist 2',
                'owner': {'display_name': 'Another User'}, 'public': False, 'tracks': {'total': 10},
            }
        ]
    }

def mock_get_token():
    return {
        "access_token": "mock_access_token", "expires_at": 3600, "token_type": "Bearer", "refresh_token": "mock_refresh_token"
    }

@patch('app.routes.get_playlists')
@patch('app.routes.display_current_user')  # Patch display_current_user to mock its behavior
def test_display_playlists_get(mock_display_current_user, mock_get_playlists, client):
    # Mock the return value of get_playlists
    mock_get_playlists.return_value = mock_current_user_playlists()

    # Mock the return value of display_current_user
    mock_display_current_user.return_value = {'display_name': 'Test User'}

    # Patch get_token to return mock token
    mock_token = mock_get_token()
    with patch('app.routes.get_token', lambda: mock_token):
        # Patch spotipy.Spotify to mock its behavior
        with patch('spotipy.Spotify') as mock_spotify:
            mock_spotify_instance = mock_spotify.return_value
            mock_spotify_instance.current_user_playlists.return_value = mock_current_user_playlists()

            # Simulate a GET request to /playlist
            response = client.get('/playlist')

    # Assert the status code of the response
    assert response.status_code == 200

    assert b'Your Playlists' in response.data
    assert b'My Playlist 1' in response.data
    assert b'This is a test playlist 1' in response.data
    assert b'Add song to playlist' in response.data
    assert b'Remove song from playlist' in response.data
    assert b'My Playlist 2' in response.data
    assert b'Edit the playlist' in response.data
    assert b'Remove song from playlist' in response.data
    assert b'Note: There might be some rendering issues' in response.data
    assert b'Important</strong>: When adding a new song' in response.data

@patch('app.routes.get_playlists')
@patch('app.routes.display_current_user')  # Patch display_current_user to mock its behavior
def test_display_playlists_no_playlists(mock_display_current_user, mock_get_playlists, client):
    # Mock the get_playlists function to return an empty list
    mock_get_playlists.return_value = {'items': []}

    # Mock the return value of display_current_user
    mock_display_current_user.return_value = {'display_name': 'Test User'}

    # Simulate a GET request to /playlist
    response = client.get('/playlist', follow_redirects=False)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Home' in response.data

    # Verify the flash message is present in the session
    assert b"Currently, you do not have any playlists." in response.data

    # Check additional things to make sure that the homepage is rendered
    assert b'To try out things, go to one of the following URLs:' in response.data
    assert response.data.count(b"<a") == 9

def mock_get_playlists():
    return {
        "items": [
            {
                "name": "My Playlist 1", "images": [{"url": "https://example.com/playlist1.jpg"}],
                "owner": {"display_name": "Test User"}, "collaborative": False, "public": True,
                "tracks": {"total": 15}, "id": "playlist1_id", "description": "This is a test playlist 1"
            }
        ]
    }

def mock_get_playlist_tracks(playlist_id):
    if playlist_id == 'playlist1_id':
        return [
            {'name': 'Song 1', 'artist': ['Artist 1', 'Artist 3'], 'album': 'Album 1', 'duration_ms': 180000},
            {'name': 'Song 2', 'artist': ['Artist 2', 'Artist 4'], 'album': 'Album 2', 'duration_ms': 240000}
        ]
    else:
        return []

def mock_display_current_user():
    return {"display_name": "Test User"}

def test_add_item_to_playlist_success(client, monkeypatch):
    # Mock get_playlists to return mock playlists
    monkeypatch.setattr('app.routes.get_playlists', mock_get_playlists)

    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Mock add_to_playlist to simulate successful addition
    with patch('app.routes.add_to_playlist') as mock_add_to_playlist:
        mock_add_to_playlist.return_value = True  # Simulate success

        # Simulate a POST request to /add_item_to_playlist
        response = client.post('/add_item_to_playlist', data={
            'playlist_id': 'playlist1_id',
            'song_name': 'Test Song'
        })

    # Check if the response redirects to display_playlists
    assert response.status_code == 302
    assert response.location == '/playlist'
    assert b'You should be redirected automatically to the target URL:' in response.data

    # Check if success message is flashed
    with client.session_transaction() as session:
        flash_messages = dict(session['_flashes'])
        assert flash_messages['success'] == "Track 'Test Song' has been successfully added."

def test_add_item_to_playlist_missing_song_name(client, monkeypatch):
    # Mock get_playlists to return mock playlists
    monkeypatch.setattr('app.routes.get_playlists', mock_get_playlists)

    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a POST request to /add_item_to_playlist without song_name
    response = client.post('/add_item_to_playlist', data={
        'playlist_id': 'playlist1_id',
        'song_name': ''
    }, follow_redirects=True)

    # Check if the response redirects back to display_playlists due to missing song name
    assert response.status_code == 200
    assert b"The song name is required in order to add it." in response.data
    assert b'<div class="alert alert-error">' in response.data
    assert b'Your Playlists' in response.data
    assert b'Your Playlists' in response.data

    # For loop to assert the correctly rendered information (can be used if more playlists are added)
    data = mock_get_playlists()
    for item in data["items"]:
        assert item["name"].encode() in response.data
        assert item["images"][0]["url"].encode() in response.data
        assert str(item["collaborative"]).encode() in response.data
        assert (b"Yes" if item['public'] else b"No") in response.data
        assert str(item["tracks"]["total"]).encode() in response.data
        assert item["id"].encode() in response.data
        assert item["description"].encode() in response.data

def test_remove_item_to_playlist_success(client, monkeypatch):
    # Mock get_playlists to return mock playlists
    monkeypatch.setattr('app.routes.get_playlists', mock_get_playlists)

    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Mock add_to_playlist to simulate successful addition
    with patch('app.routes.remove_from_all_playlists') as mock_remove_from_playlist:
        mock_remove_from_playlist.return_value = True  # Simulate success

        # Simulate a POST request to /add_item_to_playlist
        response = client.post('/remove_item_from_playlists', data={
            'playlist_id': 'playlist1_id',
            'song_name': 'Test Song'
        })

    # Check if the response redirects to display_playlists
    assert response.status_code == 302
    assert response.location == '/playlist'
    assert b'You should be redirected automatically to the target URL:' in response.data

    # Check if success message is flashed
    with client.session_transaction() as session:
        flash_messages = dict(session['_flashes'])
        assert flash_messages['success'] == "The song 'Test Song' has been successfully removed."

def test_remove_item_to_playlist_missing_song_name(client, monkeypatch):
    # Mock get_playlists to return mock playlists
    monkeypatch.setattr('app.routes.get_playlists', mock_get_playlists)

    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a POST request to /remove_item_from_playlists without song_name
    response = client.post('/remove_item_from_playlists', data={
        'playlist_id': 'playlist1_id',
        'song_name': ''
    }, follow_redirects=True)

    # Check if the response redirects back to display_playlists due to missing song name
    assert response.status_code == 200
    assert b"The song name is required in order to remove it." in response.data
    assert b'<div class="alert alert-error">' in response.data
    assert b'Your Playlists' in response.data

    # For loop to assert the correctly rendered information (can be used if more playlists are added)
    data = mock_get_playlists()
    for item in data["items"]:
        assert item["name"].encode() in response.data
        assert item["images"][0]["url"].encode() in response.data
        assert str(item["collaborative"]).encode() in response.data
        assert (b"Yes" if item['public'] else b"No") in response.data
        assert str(item["tracks"]["total"]).encode() in response.data
        assert item["id"].encode() in response.data
        assert item["description"].encode() in response.data

# Test when the playlist is found and tracks are displayed correctly
@patch('app.routes.get_playlist_tracks', side_effect=mock_get_playlist_tracks)
@patch('app.routes.get_playlists', side_effect=mock_get_playlists)
def test_display_playlist_tracks_success(mock_get_playlists, mock_get_playlist_tracks, client):
    playlist_id = 'playlist1_id'
    response = client.get(f'/display_playlist_tracks/{playlist_id}')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the playlist details are rendered correctly
    playlist_details = mock_get_playlists()['items'][0]
    assert playlist_details['name'].encode() in response.data
    if playlist_details['images']:
        assert playlist_details['images'][0]['url'].encode() in response.data
    assert str(playlist_details['collaborative']).encode() in response.data
    assert (b"Yes" if playlist_details['public'] else b"No") in response.data
    assert str(playlist_details['tracks']['total']).encode() in response.data
    if 'description' in playlist_details:
        assert playlist_details['description'].encode() in response.data

    # Check if the tracks are rendered correctly
    tracks = mock_get_playlist_tracks(playlist_id)
    for track in tracks:
        assert track['name'].encode() in response.data
        for artist in track['artist']:
            assert artist.encode() in response.data
        assert track['album'].encode() in response.data
        duration = f"{track['duration_ms'] // 60000} min {(track['duration_ms'] % 60000) // 1000} sec"
        assert duration.encode() in response.data

# Test when the playlist is not found and an error message is flashed
@patch('app.routes.get_playlist_tracks', side_effect=mock_get_playlist_tracks)
@patch('app.routes.get_playlists', side_effect=mock_get_playlists)
def test_display_playlist_tracks_not_found(mock_get_playlists, mock_get_playlist_tracks, client, monkeypatch):
    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    playlist_id = 'nonexistent_playlist_id'
    response = client.get(f'/display_playlist_tracks/{playlist_id}', follow_redirects=True)

    # Check if the response status code is 200 (OK) after redirect
    assert response.status_code == 200

    # Check if the correct template is rendered (display_playlists.html)
    assert b'Your Playlists' in response.data

    # Check if error message is flashed
    assert b"Playlist not found" in response.data

    # Ensure playlists are rendered correctly
    playlists = mock_get_playlists()
    for item in playlists['items']:
        assert item['name'].encode() in response.data
        if item['images']:
            assert item['images'][0]['url'].encode() in response.data
        assert str(item['collaborative']).encode() in response.data
        assert (b"Yes" if item['public'] else b"No") in response.data
        assert str(item['tracks']['total']).encode() in response.data
        if 'description' in item:
            assert item['description'].encode() in response.data

# Test when the playlist is created successfully
@patch('app.routes.create_spot_playlist', return_value=True)
@patch('app.routes.get_playlists', side_effect=mock_get_playlists)
def test_create_playlist_success(mock_get_playlists, mock_create_spot_playlist, client, monkeypatch):
    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a POST request to /create_playlist
    response = client.post('/create_playlist', data={
        'playlist_name': 'My Playlist 1',
        'playlist_description': 'This is a test playlist 1',
        'is_public': 'on'
    }, follow_redirects=True)

    # Check if the response status code is 200 (OK) after redirect
    assert response.status_code == 200

    # Check if the correct template is rendered (display_playlists.html)
    assert b'Your Playlists' in response.data

    # Check if success message is flashed
    assert b'Playlist created successfully!' in response.data

    # Ensure playlists are rendered correctly
    playlists = mock_get_playlists()
    for item in playlists['items']:
        assert item['name'].encode() in response.data
        if item['images']:
            assert item['images'][0]['url'].encode() in response.data
        assert str(item['collaborative']).encode() in response.data
        assert (b"Yes" if item['public'] else b"No") in response.data
        assert str(item['tracks']['total']).encode() in response.data
        if 'description' in item:
            assert item['description'].encode() in response.data

# Test when there is an error during playlist creation
@patch('app.routes.create_spot_playlist', side_effect=Exception('Test error'))
def test_create_playlist_error(mock_create_spot_playlist, client, monkeypatch):
    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a POST request to /create_playlist
    response = client.post('/create_playlist', data={
        'playlist_name': 'Test Playlist',
        'playlist_description': 'This is a test playlist',
        'is_public': 'on'
    }, follow_redirects=True)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered (create_playlist.html)
    assert b'Create a New Playlist' in response.data

    # Check if error message is flashed
    assert b'An error occurred: Test error' in response.data

    # Check if the correct template is rendered
    assert b'Create a New Playlist' in response.data

    # Check if the form fields are present
    assert b'<input type="text" name="playlist_name" placeholder="Playlist Name" required>' in response.data
    assert b'<textarea name="playlist_description" placeholder="Playlist Description" rows="4"></textarea>' in response.data
    assert b'<input type="checkbox" name="is_public">' in response.data
    assert b'<input type="submit" value="Create Playlist">' in response.data

    # Check if the navigation links are present
    assert b'<a href="' in response.data
    assert b'Back to Home' in response.data

def test_create_playlist_get(client):
    # Simulate a GET request to /create_playlist
    response = client.get('/create_playlist')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Create a New Playlist' in response.data

    # Check if the form fields are present
    assert b'<input type="text" name="playlist_name" placeholder="Playlist Name" required>' in response.data
    assert b'<textarea name="playlist_description" placeholder="Playlist Description" rows="4"></textarea>' in response.data
    assert b'<input type="checkbox" name="is_public">' in response.data
    assert b'<input type="submit" value="Create Playlist">' in response.data

    # Check if the navigation links are present
    assert b'<a href="' in response.data
    assert b'Back to Home' in response.data

# Test playlist not found
@patch('app.routes.get_playlists')
def test_change_playlist_details_not_found(mock_get_playlists, client, monkeypatch):
    mock_get_playlists.return_value = mock_get_playlists()

    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a GET request to /change_playlist_details/3 (non-existent playlist)
    response = client.get('/change_playlist_details/3', follow_redirects=True)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the correct template is rendered
    assert b'Your Playlist' in response.data

    # Check if error message is flashed
    assert b'Playlist not found' in response.data
    assert b'<div class="alert alert-error">' in response.data

# Test successful playlist update
@patch('app.routes.edit_playlist_details')
@patch('app.routes.get_playlists')
@patch('app.routes.create_spot_playlist', return_value=True)
def test_change_playlist_details_success(mock_create_spot_playlist, mock_get_playlists, mock_edit_playlist_details, client, monkeypatch):
    mock_get_playlists.return_value = mock_get_playlists()

    # Define the create_playlist_mocked function within the test scope
    def create_playlist_mocked(client, monkeypatch):
        # Mock display_current_user to return mock user data
        monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

        # Simulate a POST request to /create_playlist
        response_create = client.post('/create_playlist', data={
            'playlist_name': 'My Playlist 1',
            'playlist_description': 'This is a test playlist 1',
            'is_public': 'on'
        }, follow_redirects=True)

        # Check if the response status code is 200 (OK) after redirect
        assert response_create.status_code == 200
        # Check if the correct template is rendered (display_playlists.html)
        assert b'Your Playlists' in response_create.data
        # Check if success message is flashed
        assert b'Playlist created successfully!' in response_create.data

    # Call the helper function to create a playlist
    create_playlist_mocked(client, monkeypatch)

    # Simulate a POST request to /change_playlist_details/1
    response = client.post('/change_playlist_details/1', data={
        'playlist_name': 'Updated Playlist',
        'playlist_description': 'Updated description',
        'playlist_if_public': 'on'
    }, follow_redirects=True)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if success message is flashed
    assert b'Playlist details updated successfully' in response.data

    # Ensure the edit_playlist_details function was called with correct parameters
    mock_edit_playlist_details.assert_called_with('1', new_name='Updated Playlist', new_description='Updated description', new_public='on')

# Test when there is an error during playlist update
@patch('app.routes.edit_playlist_details', side_effect=Exception('Test error'))
@patch('app.routes.get_playlists')
def test_change_playlist_details_error(mock_get_playlists, mock_edit_playlist_details, client, monkeypatch):
    mock_get_playlists.return_value = mock_get_playlists()

    # Mock display_current_user to return mock user data
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a POST request to /change_playlist_details/playlist1_id
    with pytest.raises(Exception) as exception_info:
        client.post('/change_playlist_details/playlist1_id', data={
            'playlist_name': 'Updated Playlist',
            'playlist_description': 'Updated description',
            'playlist_if_public': 'on'
        }, follow_redirects=True)

    # Check if the exception message matches
    assert str(exception_info.value) == 'Test error'

# Test for display_searched_playlist_tracks function
@patch('app.routes.get_playlist', side_effect=lambda playlist_id: mock_get_playlists()['items'][0])
@patch('app.routes.get_playlist_tracks', side_effect=mock_get_playlist_tracks)
def test_display_searched_playlist_tracks(mock_get_playlist_tracks, mock_get_playlist, client):
    # Simulate a GET request to /display_searched_playlist_tracks/playlist1_id
    response = client.get('/display_searched_playlist_tracks/playlist1_id')

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    # Check if the rendered template contains expected data from mock_get_playlist and mock_get_playlist_tracks
    assert b'Tracks in Playlist: My Playlist 1' in response.data

    # Ensure the template 'playlist_tracks.html' is rendered
    assert b'Tracks' in response.data

    # Check if each track from mock_get_playlist_tracks is present in the response data
    for track_info in mock_get_playlist_tracks('playlist1_id'):
        assert track_info['name'].encode() in response.data
        for artist in track_info['artist']:
            assert artist.encode() in response.data
        assert track_info['album'].encode() in response.data
        assert str(track_info['duration_ms'] // 60000).encode() in response.data  # Check minutes
        assert str((track_info['duration_ms'] % 60000) // 1000).encode() in response.data  # Check seconds

    # Verify that get_playlist and get_playlist_tracks were called with the correct parameters
    mock_get_playlist.assert_called_once_with('playlist1_id')
    mock_get_playlist_tracks.assert_has_calls([call('playlist1_id'), call('playlist1_id')])

# Test for follow_public_playlist function
@patch('app.routes.follow_playlist')
def test_follow_public_playlist(mock_follow_playlist, client, monkeypatch):
    # Mock display_current_user to return mock user data
    mock_display_current_user = MagicMock(return_value={'display_name': 'Test User'})
    monkeypatch.setattr('app.routes.display_current_user', mock_display_current_user)

    # Simulate a POST request to /follow_playlist/playlist1_id
    playlist_id = 'playlist1_id'
    response = client.post(f'/follow_playlist/{playlist_id}')

    # Check if follow_playlist function was called with correct parameters
    mock_follow_playlist.assert_called_once_with(playlist_id)

    # Check if the response status code is 302 (redirect)
    assert response.status_code == 302

    # Check if it redirects to display_playlists route
    assert response.location == "/" + url_for('display_playlists', _external=True).split('/')[-1]

    # Check if success message is flashed
    with client.session_transaction() as session:
        flash_messages = session['_flashes']
        assert len(flash_messages) == 1
        assert flash_messages[0][1] == 'Playlist successfully followed!'
        assert flash_messages[0][0] == 'success'

    # Simulate an exception in follow_playlist function
    mock_follow_playlist.side_effect = Exception('Test error')
    response = client.post(f'/follow_playlist/{playlist_id}')

    # Check if follow_playlist function was called with correct parameters
    mock_follow_playlist.assert_called_with(playlist_id)

    # Check if the response status code is 302 (redirect)
    assert response.status_code == 302

    # Check if it redirects to display_playlists route
    assert response.location == "/" + url_for('display_playlists', _external=True).split('/')[-1]

    # Check if error message is flashed
    with client.session_transaction() as session:
        flash_messages = session['_flashes']
        assert len(flash_messages) == 2
        assert any('An error occurred' in message[1] for message in flash_messages)

    # Ensure follow_playlist was called twice (once successfully, once with error)
    assert mock_follow_playlist.call_count == 2
