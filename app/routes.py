
# Import necessary modules and functions
from flask import redirect, url_for, session, render_template, request, flash, get_flashed_messages
from app.auth import create_spotify_oauth
from app.models import *
import spotipy
from config import Config


def setup_routes(app):
    """
    Function which includes all the route handling function.
    :param app: Received from the __init__.py file. This initializes my flask application.
    :return: Returns nothing
    """
    app.config.from_object(Config)  # Load configuration settings from the Config object

    @app.route('/')
    def login():
        """
        Route handling functon for the login page. It clears the session so there is no information stored about the
        previous user.
        :return: Redirects the user to the Spotify authorization page
        """
        session.clear()
        auth_url = create_spotify_oauth().get_authorize_url()  # Get the Spotify authorization URL
        return redirect(auth_url)

    @app.route('/redirect')
    def redirect_page():
        """
        Route handling function for the redirect page after Spotify login. Exchange code for access token
        The check_cache=False part is needed, because it did not update the token information properly and the only
        solution I found was to ignore the cache
        :return: Redirect to the home page
        """
        code = request.args.get('code')  # Get the authorization code from the request
        token_info = create_spotify_oauth().get_access_token(code, check_cache=False)  # Exchange code for access token

        session['token_info'] = token_info  # Store the token info in the session

        user_info = display_current_user()  # Get current user info
        session['user_id'] = user_info['id']  # Store user ID in the session

        spotify = spotipy.Spotify(auth=token_info["access_token"])  # Create a Spotify client
        log_user_login(spotify)  # Log the user login --> needed for the database part and the statistics

        return redirect(url_for('home'))

    @app.route('/home')
    def home():
        """
        Route handling function for the home page.
        :return: Renders the homepage template if the user is logged in. Otherwise, it redirects to Spotify's login page
        """
        try:
            token_info = get_token()  # Get the current token info
            spotify = spotipy.Spotify(auth=token_info["access_token"])
        except Exception as e:
            flash(f"There was an error: {e}", category="error")  # Show the error to the user if any occurs.
            return redirect("/")  # Redirect to the login page if the user is not logged in
        return render_template('home.html')  # Render the home page template if the user is logged in

    @app.route('/user_logins')
    def user_logins():
        """
        Route handling function for displaying user logins.
        :return: Renders the HTML template which present the data in a table.
        """
        user_logins_ = get_user_logins()  # Get user login data
        return render_template("user_logins.html", user_logins=user_logins_)  # Render the user logins template

    @app.route('/user_stats')
    def user_stats():
        """
        Route handling function for displaying user statistics.
        :return: Renders the HTML template which present the calculated statistics.
        """
        stats = get_user_stats()  # Get user statistics
        return render_template("user_stats.html", **stats)  # Render the user statistics template

    @app.route('/search', methods=['GET', 'POST'])
    def search():
        """
        Route handling functon for searching in Spotify.
        :return: Renders the HTML template which present the search results.
        """
        if request.method == 'POST':
            query = request.form.get('query')  # Get search query from form
            search_type = request.form.get('type')  # Get search type from form
            results = search_spotify(query, search_type)  # Perform Spotify search
            return render_template('search_results.html', items=results,
                                   search_type=search_type)  # Render search results template
        return render_template('search.html')  # Render search form template if the method is GET

    @app.route('/current_user', methods=['GET'])
    def get_current_user():
        """
        Function to get the current user's general information and display it.
        :return: Renders the HTML template which present the information in an organized matter.
        """
        user_data = display_current_user()  # Get current user data
        return render_template('current_user.html', user_data=user_data)  # Render current user data template

    @app.route('/top_items', methods=['GET'])
    def top_items():
        """
        Function to get the user's top items, which includes the tracks and artists.
        :return: Renders the HTML template which present the tracks first then the artists in an organized matter.
        """
        items = get_top_items()  # Get top items for current user
        return render_template('user_top_items.html', items=items)  # Render top items template

    @app.route('/artists', methods=['GET', 'POST'])
    def get_artist():
        """
        Function which allows the user to retrieve more detailed and in-depth information about artists.
        :return: Renders the HTML template which present the information in an organized matter. This includes the
        artist's most listened tracks, the artist's albums and the relevant artists.
        """
        if request.method == 'POST':
            query = request.form.get('query')  # Get artist's name from the HTML form
            artist_details, artist_albums, artist_top_tracks, artist_related_artists = get_specific_artist(
                query)  # Get artist details

            # If there is information retrieved, render artist details template
            if artist_details:
                return render_template('artists_result.html',
                                       artist_details=artist_details,
                                       artist_albums=artist_albums,
                                       artist_top_tracks=artist_top_tracks,
                                       artist_related_artists=artist_related_artists)
            else:
                return render_template('artists.html')  # Render artist search form template if details are found
        else:
            return render_template('artists.html')  # Render artist search form template if the method is GET

    @app.route('/following', methods=['GET', 'POST'])
    def get_users_following():
        """
        Function to retrieve the artists that the current user is following. On the rendered template there is also the
        option to unfollow the artists, which is also handled by this function. This is achieved by the different methods
        :return: Renders the HTML template which present the followed artist in an organized matter.
        """
        if request.method == 'GET':
            followed = get_who_curr_user_follows()  # Get the artists that the user is following
            return render_template('following.html', followed=followed)  # Render following template
        elif request.method == 'POST':
            artist_id = request.form.get('artist_id')  # Get artist ID from form (hidden value)
            if artist_id:
                unfollow_artist(artist_id)  # Unfollow artist if the user clicks on the "Unfollow" button
            return redirect(url_for('get_users_following'))  # Redirect to the same function, which will result in
            # reloading the artists who the user is currently following
        else:
            return render_template('home.html')  # Render home page template (error prevention)

    @app.route('/follow', methods=['GET', 'POST'])
    def follow_artists():
        """
        Function which allows the user to search for artists and then choose which one to follow on Spotify.
        :return: Returns an error message if the user is already following the searched artist. Otherwise, it renders
        the page which shows the possible search results.
        """
        if request.method == 'POST':
            query = request.form.get('name')  # Get search query from form
            search_type = 'artist'  # Set the search type to 'artist'
            results = search_spotify(query, search_type)  # Search Spotify for the artist based on the query
            following_already = get_who_curr_user_follows()  # Get the list of artists the current user is already following
            following_already = [item['id'] for item in following_already]   # Extract the IDs of the followed artists

            # Check if the first result is already being followed
            if results[0]['id'] in following_already:
                # Display a message indicating the artist is already followed and suggest similar artists
                flash(f"You are already following the artists '{results[0]['name']}'. Here are some possibly "
                      f"similar artists.", "error")
                # Render the 'want_to_follow.html' template with the search results
                # If the user is already following the searched artist, the artist will not be displayed
                return render_template('want_to_follow.html', items=results, search_type=search_type)
            else:
                # Render the 'want_to_follow.html' template with the search results
                return render_template('want_to_follow.html', items=results, search_type=search_type)
        return render_template('follow.html')  # If the request method is GET, render the 'follow.html' template

    @app.route('/follow/<artist_id>', methods=['POST'])
    def follow_artist_action(artist_id):
        """
        Function which triggers the follow action when the user clicks on the "Follow" button.
        :param artist_id: The function receives the artist's ID from the HTML form as a hidden value
        :return: Redirects to the page which renders the artists that the user is currently following. Therefore, the
        user can instantly see, that the artis is in fact followed.
        """
        follow_artist(artist_id)  # Follow artist
        return redirect(url_for('get_users_following'))  # Redirect to currently following artists page

    @app.route('/playlist', methods=['GET', 'POST'])
    def display_playlists():
        """
        Function to display the current user's playlists. This includes the playlist that the user does not own, but
        follows. Of course, since the user is not the owner, the user is not able to edit these playlists but only view
        the tracks in the playlist beside the general information.
        :return: If there are any playlists, the function renders the HTML template to present the playlists and the
        options regarding these playlists.
        """
        playlists = get_playlists()  # Get user's playlists
        playlists = playlists['items']

        curr_user = display_current_user()['display_name']  # Get current user's display name
        # This is needed to distinguish if the user is the owner of the playlist or not.

        if playlists:
            return render_template('display_playlists.html', playlists=playlists, curr_user=curr_user)  # Render playlists template
        else:
            flash("Currently, you do not have any playlists.", category="error")  # Tells the user that the user
            # does not have any playlists yet and then refreshes the page after 4 seconds
            return render_template('home.html')  # Render home page template if there are no playlists.

    @app.route('/add_item_to_playlist', methods=['POST'])
    def add_item_to_playlist():
        """
        Function which allows the user to add songs to his/her playlist, if the user is the owner of the playlist.
        :return: If the user did not specify the name of the song, an error message will inform the user about this.
        Otherwise, it shows a confirmation message that the track was added, and it also updates the values of the
        playlist. This way the user can see that the song was in fact added and can also check the tracks in the playlist.
        """
        playlist_id = request.form.get('playlist_id')  # Get playlist ID from the HTML form as a hidden value
        song_name = request.form.get('song_name')  # Get song's name from the HTML form which the user gave

        # Necessary information to render the playlists after the addition of a song
        playlists = get_playlists()
        playlists = playlists['items']
        curr_user = display_current_user()['display_name']

        if not playlist_id or not song_name:
            flash("The song name is required in order to add it.", "error")  # Flash error message if required fields are missing
            return render_template('display_playlists.html', playlists=playlists, curr_user=curr_user)

        # Add song to playlist using the helper function
        result = add_to_playlist(playlist_id, song_name)

        if result:
            flash(f"Track '{song_name}' has been successfully added.", "success")  # Flash success message
        else:
            # Flash error message if there was an unexpected error
            flash(f"Failed to add the track '{song_name}' to the playlist.", "error")

        return redirect(url_for('display_playlists'))  # Redirect to playlists display

    @app.route('/remove_item_from_playlists', methods=['POST'])
    def remove_item_from_playlists():
        """
        Function which allows the user to remove songs from his/her playlist, if the user is the owner of the playlist.
        :return: If the user did not specify the name of the song, an error message will inform the user about this.
        Otherwise, it shows a confirmation message that the track was removed, and it also updates the values of the
        playlist. This way the user can see that the song was in fact removed and can also check the tracks in the playlist.
        """
        playlist_id = request.form.get('playlist_id')  # Get playlist ID from the HTML form as a hidden value
        song_name = request.form.get('song_name')  # Get song's name from the HTML form which the user gave

        # Necessary information to render the playlists after the addition of a song
        playlists = get_playlists()
        playlists = playlists['items']
        curr_user = display_current_user()['display_name']

        if not song_name or not playlist_id:
            flash("The song name is required in order to remove it.", "error")  # Flash error message if required fields are missing
            return render_template('display_playlists.html', playlists=playlists, curr_user=curr_user)

        # Remove song to playlist using the helper function
        result = remove_from_all_playlists(playlist_id, song_name)

        if result:
            flash(f"The song '{song_name}' has been successfully removed.", "success")  # Flash success message
        else:
            # Flash error message if there was an unexpected error
            flash(f"Failed to remove the song '{song_name}' from playlists."
                  f"The most probable cause is that the playlist does not contain the entered song. Check the spelling.", "error")

        return redirect(url_for('display_playlists'))  # Redirect to playlists display

    @app.route('/display_playlist_tracks/<playlist_id>')
    def display_playlist_tracks(playlist_id):
        """
        Function to display the tracks in each of the users playlist.
        :param playlist_id: The function gets the playlist's ID as a hidden value from the HTML form. This is needed so
        the helper function can recognize which playlist's tracks needs to be displayed.
        :return: Gives the user an error message if the playlist was not found. This is not a scenario that will likely
        happen, I just included it as a 'What-if' case. Otherwise, the function renders the tracks in the playlist.
        """
        playlists = get_playlists()  # Get the user's playlists
        playlists = playlists['items']

        # Get the selected playlist based on ID
        selected_playlist = None
        for playlist in playlists:
            if playlist['id'] == playlist_id:
                selected_playlist = playlist
                break

        if not selected_playlist:
            flash("Playlist not found", "error")  # Flash error message if playlist is not found
            return redirect(url_for('display_playlists'))  # Redirect to playlists display

        # Fetch tracks for the selected playlist
        tracks = get_playlist_tracks(playlist_id)

        # Render playlist tracks template
        return render_template('playlist_tracks.html', playlist=selected_playlist, tracks=tracks)

    @app.route('/create_playlist', methods=['GET', 'POST'])
    def create_playlist():
        """
        Function to create new playlists. THe name is required, the description is optional. The user also can decide if
        he/she wants to make the playlist public or not.
        :return: Success message if the playlist creation was successful and then renders the playlists page, so the user
        sees the newly created playlist and can add songs to it.
        """
        if request.method == 'POST':
            playlist_name = request.form['playlist_name']   # Get playlist name from the HTML form
            playlist_description = request.form['playlist_description']  # Get the optional playlist description from the HTML form
            is_public = request.form.get('is_public') == 'on'  # Get public/private status from the HTML form

            try:
                create_spot_playlist(playlist_name, playlist_description, is_public)  # Create new playlist
                flash('Playlist created successfully!', 'success')  # Flash success message
                return redirect(url_for('display_playlists'))  # Redirect to playlists display
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'danger')  # Flash error message in case of error

        return render_template('create_playlist.html')  # Render create playlist form template

    @app.route('/change_playlist_details/<playlist_id>', methods=['GET', 'POST'])
    def change_playlist_details(playlist_id):
        """
        Function to edit the playlist's general information, such as name and
        :param playlist_id: The function gets the playlist's ID from the HTML form as a hidden value.
        :return: Displays a success message if the update was successful and then renders the displays again to see the
        changes. Note that some of these changes might take some time to update in my application.
        """
        if request.method == 'POST':
            new_name = request.form.get('playlist_name')  # Get new playlist name from the HTML form --> use the old one if not updated
            new_description = request.form.get('playlist_description')   # Get new playlist description from form --> use the old one if not updated
            new_public = request.form.get('playlist_if_public')  # Get new public status of the playlist --> use the old status if not updated

            edit_playlist_details(playlist_id, new_name=new_name, new_description=new_description, new_public=new_public)  # Update playlist details

            flash("Playlist details updated successfully", "success")  # Flash success messages
            return redirect(url_for('display_playlists'))  # Redirect to playlists display

        # Check if there was a playlist selected, this is also for the "What-if" cases and unexpected error handling
        playlists = get_playlists()['items']
        selected_playlist = next((pl for pl in playlists if pl['id'] == playlist_id), None)

        if not selected_playlist:
            flash("Playlist not found", "error")  # Flash error message if playlist is not found
            return redirect(url_for('display_playlists'))  # Redirect to playlists display

        return render_template('edit_playlist.html', playlist=selected_playlist)  # Render edit playlist form templates

    @app.route('/display_searched_playlist_tracks/<playlist_id>')
    def display_searched_playlist_tracks(playlist_id):
        """
        Function to display the tracks of the playlists that the user searched for. The reason why this method is needed,
        is because there is slightly different information retrieved and a different method used when displaying the
        tracks of the user's playlists.
        :param playlist_id: The function receives the playlist's ID from the HTML form as a hidden value.
        :return: Renders the playlist's tracks. The same template is used for displaying the tracks of one of the user's
        playlist.
        """
        playlist = get_playlist(playlist_id)  # Get specific playlist
        tracks = get_playlist_tracks(playlist_id)  # Get tracks for the playlist

        return render_template('playlist_tracks.html', playlist=playlist, tracks=tracks)  # Render playlist tracks template

    @app.route('/follow_playlist/<playlist_id>', methods=['POST'])
    def follow_public_playlist(playlist_id):
        """
        Function to follow public playlists. This is needed, so when a user searches for a playlist, he/she can follow
        it automatically without having to go to another page.
        :param playlist_id: The function receives the playlist's ID from the HTML form as a hidden value.
        :return: Shows a success message for the user if the playlist was successfully followed and then renders the
        template of the users playlist, so the user can see that the playlist is in fact followed.
        """
        if request.method == 'POST':
            try:
                follow_playlist(playlist_id)  # Follow the playlist
                flash('Playlist successfully followed!', 'success')  # Flash success message
                return redirect(url_for('display_playlists'))  # Redirect to playlists display
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'danger')  # Flash error message
        return redirect(url_for('display_playlists'))  # Redirect to playlists display
