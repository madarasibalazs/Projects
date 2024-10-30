# My Flask app using the Spotify API

*Simple overview of purpose.*

I love listening to music, so I wanted to make a programming project that is connected to my passion, so I started making a simple version of Spotify.

## Description

My project is about making the most out of the Spotify API. Using my flask application, people can log in and use the functionalities that my app offers. These are very similar functionalities to the ones that Spotify has in its system, but this is not suprising as I am using their API along with the spotipy library.

### Dependencies

* All of the necessary libraries are in the requirements.txt file. After cloning the repository, to install the dependencies (see below):
* There is no OS requirement
* I use Pyton 3.9, but should work on older/newer python versions as well
* The official documentations can be found here:
  - Spotify API: https://developer.spotify.com/documentation/web-api
  - Spotipy: https://spotipy.readthedocs.io/en/2.24.0/

### Installing

* Simply cloning the whole repository and installing the necessary requirements should be enough to run my application. For cloning, use the following command:
```
git clone https://github.com/your-username/rock-paper-scissors.git
```
* After cloning, you have to install the dependencies:
```
pip install -r requirements.txt
```
* No modification is needed to the files, everything is structured.

## Getting Started

To run my application, first clone the repository and download the dependencies from the requiremets.txt file (see above).
**Before** starting my application, please make sure, that if you have a Spotify account you are logged **OUT** of it in the browser. If not, please continue reading. 

### Executing program

* After installing the necessary libraries, you have to run the "run.py" file (located in the root of my project) and click on the link that appears in the Run window (should be http://127.0.0.1:5000). You should see something like this:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 124-147-038
```
* Since you are not logged into any Spotify account at the moment, the app will redirect you to Spotify's official login page.
* **BEFORE** logging into the free account provided below, please make sure that the "Remember me" button above login button is **OFF**. This is important, because if you leave that option on, it will not clear the session properly (API constraints, I could not do anything about it) and can cause problems.
* Use the login information I provided, because the application I am making is in "Development Mode", therefore only those users can log into who I added to my app on the Spotify Developer Dashboard.
* The Spotify account I have provided below is a free one, which I have been not using, therefore the UI will be simple and some of the information will not appear, as the account has not been used. If you would like to use you own account, please open an issue where you write me your email and I will add you to the allowed users.

## The login data for the free account:
- email: madarasi.balazs04@gmail.com
- password: Testpassword123

## Functionalities

**The exact functionalities and where to find them:**
- **Database part**: "Check log-in times and other information" and "Look at statistics about my app's users" links on the homepage. In the first link, you can see what is stored in my database.
  - *Note:* I wanted to add more to my database part, but in the Spotify API documentation, in most endpoints it is said that "Spotify content may not be downloaded". Therefore, I could not extend my database.
- **Networking part**: The whole communication process with the Spotify API. Ensuring that the requests are correctly sent, getting the data and extracting the data that is presentable and useful.
- **Creating playlists**: Create a new playlist link on the homepage.
- **Editing playlists**: "See your playlists" links, where you can view all of your playlists and edit the ones that you "own" (made). This incluced adding and deleting tracks, editing the title, description and the public status of the playlist.
  - *Note:* When editing a playlist, it might take some time for the information to update in my application. I do not know exactly why, but e.g., if you update the description of the playlist it could take up to 2-3 minutes for the description to update. 
- **Getting another user's public playlists**: Users can search for playlists, look at the tracks in them and follow those playlists, which will be in their library along with their own playlists.
- **Get Spotify catalog information about albums, artists, playlists, tracks, shows or episodes**: "Search" link in the homepage.
- **Display a user’s profile information**: "View your profile" link. This displays general information about your profile. This is also the way to see your top items.
- **Get the top items (artists and tracks) of the user**: "View your profile" link and then "View your top items" link. This will display your top 10 tracks and artists.
- **Basic operations related to artists**: "Everything about artists" link, which allows you to search for an artist and the most probable search result will be displyed.
- **Follow artist**s: "Follow artists" link in the homepage. You can search for artists and then choose which one you would like to follow.
- **Unfollow artists**: "See who you are following" link in the homepage. Here you can see which artists are you already following and can choose to unfollow them.

## Help

* If there are any problems, please create an issue and I will check it out as soon as I can.
* There are some environment variables that I have used, such as the secret key and the client key for my application which I cannot upload for obvious privacy reasons.

## Authors

Me, Balazs Csaba Madarasi is the only author of this project.
If you want to contact me:
* E-mail: madarasi.balazs04@gmail.com

## License

This project is only for educational purposes. The application itself is in development mode.
