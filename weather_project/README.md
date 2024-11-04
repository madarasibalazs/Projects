# Weather Application

A user-friendly desktop application that provides real-time weather updates for cities around the world.

## Description

This weather application utilizes the OpenWeatherMap API to fetch current weather data such as temperature, humidity, wind speed, sunrise, sunset, and more. The app features an intuitive UI built with Python's Tkinter library and includes options for users to switch between Metric and Imperial units, toggle between light and dark mode, and change the language dynamically (English, Spanish, German). Users can also search for cities, view search history, and save/remove favorite cities for future reference.

I built this weather application using Tkinter to challenge myself with a more traditional desktop GUI approach, as I did not want to make a "traditional" weather application using JavaScript.

## Getting Started

### Dependencies

* Python 3.x
* The following Python libraries:
  * `requests`
  * `tkinter`
  * `PIL` (Pillow)
* Operating System: Works on Windows, macOS, and Linux.

### Installing

1. **Clone the Repository**:
   Clone the entire project repository to your local machine:
```
git clone https://github.com/madarasibalazs/Projects.git
```
 Then navigate to the folder:
```
cd Projects/weather_project
```

2. **Install Required Libraries**:
Navigate to the project directory and install the required dependencies using `pip`:
```
pip install -r requirements.txt
```

3. **API Key Setup**:
You will need an API key from [OpenWeatherMap](https://openweathermap.org/api). Create an account, generate an API key, and store it in a file named `api_key.txt` in the root directory of the project.

4. **City Data**:
The application uses city data from a smaller version of the GeoNames dataset. Ensure you place the `cities5000.txt` file in the correct location as described in the project folder structure.

### Executing Program

1. **Run the Application**:
Once you’ve completed the installation and API setup, run the program:
```
python main.py
```

2. **Using the App**:
* Search for a city by typing the name in the search bar.
* Toggle between Metric and Imperial units using the **Unit** button in the dropdown menu.
* Switch between light and dark mode in the dropdown menu.
* Select your preferred language from the language options (English, Spanish, German).
* Save cities to favorites and load weather data quickly by selecting them from the dropdown.
* Access search history and clear it when necessary.

## Additional features

* In the dropdown menu, the user can:
  * Switch between dark and light mode
  * Toggle the units between the metric and the imperial system
  * Change the language (English, German, Spanish)
* You can save cities to favourites and load the current weather quicker
* There is also a suggestion box to help you find your searched city faster
* A search history is also available to help you navigate quicker

## Help

If you encounter any issues, check the following common solutions:
1. **API Key Issues**:
Make sure your `api_key.txt` file is correctly configured and that your OpenWeatherMap API key is valid.
I would note, that it takes a couple of hours for OpenWeatherMap to generate and activate your API key. Make sure you wait for some time before trying out the project.

2. **Missing Dependencies**:
If you get errors related to missing libraries, ensure all dependencies are installed. (See more at the Dependencies part)

I want to also add, that I know the images should not be uploaded, but initially I planned it to be a local project and did not use the links of the images. This way it takes up more space in the Github repository, however it would take a lot of time to redo this part. 

If there are any problems, please create an issue and I will check it out as soon as I can.

## Authors

* Balazs Csaba Madarasi [@madarasibalazs](https://github.com/madarasibalazs)

## Acknowledgments

* [OpenWeatherMap API](https://openweathermap.org/api) for providing weather data.
* [GeoNames](http://www.geonames.org/) for city data.
* ReadMe template from [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
