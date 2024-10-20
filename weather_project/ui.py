import tkinter as tk
from tkinter import messagebox
from utils import BackgroundManager, celsius_to_fahrenheit, meters_per_sec_to_km_per_hour, meters_per_sec_to_miles_per_hour
from weather import WeatherFetcher
from helpers import load_country_codes, load_city_data, load_language
import requests
from PIL import Image, ImageTk
from io import BytesIO

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather App")
        self.root.geometry("900x750")

        self.current_language = "en"  # Default to English
        self.translations = load_language(self.current_language)

        self.search_history = []  # To store the last few searched cities

        self.bg_image_label = tk.Label(root)
        self.bg_image_label.place(relwidth=1, relheight=1)

        # Load country codes and city data
        self.country_codes = load_country_codes('countries.csv')
        self.city_data = load_city_data('cities5000.txt')  # Load city data from TXT

        # Initialize background manager and weather fetcher
        self.bg_manager = BackgroundManager(self.bg_image_label)
        api_key = open("api_key.txt", "r").read().strip()
        self.weather_fetcher = WeatherFetcher(api_key, self.country_codes)

        # Track the current temperature unit (Metric units by default)
        self.current_unit = "Metric"
        self.weather_data = None  # Track weather data, so we can update the display when unit changes

        self.create_widgets()
        self.bg_manager.set_background_image("default")  # Set a default background image on start

        self.favorites = []
        self.load_favorites_from_file()

        # Initializing the theme as Light mode
        self.is_dark_mode = False

        # Call after creating widgets to ensure language support
        self.apply_translations()

    def create_widgets(self):
        # Create a dropdown menu in the top-left corner
        self.create_menu()

        self.favorites_frame = tk.Frame(self.root, bg="#ffffff")
        self.favorites_frame.place(relx=0.15, rely=0.525, relwidth=0.25, relheight=0.2)

        # Initialize with a default value for the OptionMenu
        self.favorites_var = tk.StringVar(self.favorites_frame)
        self.favorites_var.set("Select a favorite city")  # Default value

        # Create OptionMenu with initial value
        self.favorites_menu = tk.OptionMenu(self.favorites_frame, self.favorites_var, "Select a favorite city")
        self.favorites_menu.config(font=("Helvetica", 12))  # Increase font size
        self.favorites_menu.place(relx=0.025, rely=0.05, relwidth=0.95, relheight=0.25)

        # Add a button to load the selected favorite city's weather
        self.load_favorite_button = tk.Button(self.favorites_frame, text="Load Favorite", font=("Helvetica", 12),
                                              command=self.load_favorite_city)
        self.load_favorite_button.place(relx=0.025, rely=0.35, relwidth=0.95, relheight=0.25)

        self.remove_favorite_button = tk.Button(self.favorites_frame, text="Remove from Favorites", font=("Helvetica", 12),
                                                command=self.remove_from_favorites)
        self.remove_favorite_button.place(relx=0.025, rely=0.65, relwidth=0.95, relheight=0.25)

        # Create an empty list for favorites
        self.favorites = []

        # Frame for search history (right below search input)
        self.history_frame = tk.Frame(self.root, bg="#ffffff")
        self.history_frame.place_forget()

        self.history_label = tk.Label(self.history_frame, text="Search History:", font=("Helvetica", 12, "bold"),
                                      bg="#ffffff")
        self.history_label.pack(side=tk.TOP, padx=5, pady=5, anchor='w')

        self.history_listbox = tk.Listbox(self.history_frame, height=5, bg="lightyellow", borderwidth=2, relief="solid",
                                          font=("Helvetica", 12))
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)

        self.clear_history_button = tk.Button(self.history_frame, text="Clear History", font=("Helvetica", 12),
                                              command=self.clear_search_history)
        self.clear_history_button.pack(side=tk.BOTTOM, pady=5, padx=5)

        # Frame for the search bar and buttons (left side)
        self.top_left_frame = tk.Frame(self.root, bg="#ffffff")
        self.top_left_frame.place(relx=0.1, rely=0.02, relwidth=0.35, relheight=0.2, anchor="nw")

        self.city_var = tk.StringVar()
        self.city_var.trace("w", self.on_city_input_change)

        self.city_label = tk.Label(self.top_left_frame, text="City:", font=("Helvetica", 12, "bold"), bg="#ffffff")
        self.city_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')

        self.city_entry = tk.Entry(self.top_left_frame, textvariable=self.city_var, font=("Helvetica", 12), width=25)
        self.city_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        self.search_button = tk.Button(self.top_left_frame, text="Search", font=("Helvetica", 12),
                                       command=self.fetch_weather_command)
        self.search_button.grid(row=1, column=0, padx=5, pady=0, columnspan=2, sticky='ew')

        self.clear_button = tk.Button(self.top_left_frame, text="Clear Searchbar", font=("Helvetica", 12),
                                      command=self.clear_searchbar)
        self.clear_button.grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky='ew')

        self.favorite_button = tk.Button(self.top_left_frame, text="Save to Favorites", font=("Helvetica", 12),
                                         command=self.save_to_favorites)
        self.favorite_button.grid(row=3, column=0, padx=5, pady=5, columnspan=2, sticky='ew')

        # Configure row and column weights to center the buttons
        self.top_left_frame.grid_columnconfigure(0, weight=1)
        self.top_left_frame.grid_columnconfigure(1, weight=1)
        self.top_left_frame.grid_rowconfigure(1, weight=1)

        # Frame for the suggested cities (right side)
        self.top_right_frame = tk.Frame(self.root, bg="#ffffff")

        self.suggestion_label = tk.Label(self.top_right_frame, text="Suggested cities:",
                                         font=("Helvetica", 12, "bold"), bg="#ffffff")
        self.suggestion_label.pack(side=tk.TOP, padx=5, pady=5, anchor='w')

        # Autocomplete suggestions listbox
        self.suggestion_listbox = tk.Listbox(self.top_right_frame, height=5, bg="lightyellow", borderwidth=2,
                                             relief="solid", font=("Helvetica", 12))
        self.suggestion_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.suggestion_listbox.bind("<<ListboxSelect>>", self.on_suggestion_select)

        # Exit button
        self.exit_button = tk.Button(self.root, text="Exit", font=("Helvetica", 12), command=self.root.quit)
        self.exit_button.place(relx=0.99, rely=0.99, relwidth=0.1, relheight=0.05, anchor="se")

        # Weather information frame
        self.weather_frame = tk.Frame(self.root, padx=10, pady=0, bg="#f0f0f0", bd=2, relief="sunken")
        self.weather_frame.place_forget()  # Hide the weather frame initially

        self.weather_icon_label = tk.Label(self.weather_frame, bg="#C4A484")  # Add this for the weather icon
        self.weather_icon_label.place(relx=0.835, rely=0, relwidth=0.2, relheight=0.15, anchor="nw")  # Position the icon next to weather

        self.labels_text = [
            self.translations['weather'],
            self.translations['feels_like'],
            self.translations['min_temp'],
            self.translations['max_temp'],
            self.translations['humidity'],
            self.translations['wind_speed'],
            self.translations['rain_volume'],
            self.translations['country'],
            self.translations['sunrise'],
            self.translations['sunset']
        ]

        self.labels = self.create_weather_labels(self.weather_frame, self.labels_text)

        # Initially hide all labels and the weather frame
        self.hide_labels()

    def create_menu(self):
        # Create a main menu bar
        self.menu_bar = tk.Menu(self.root)

        # Create the 'Options' dropdown
        options_menu = tk.Menu(self.menu_bar, tearoff=0)

        # Add "Dark Mode" toggle
        options_menu.add_command(label="Toggle Dark Mode", command=self.toggle_theme)

        # Add "Language Select" submenu
        language_menu = tk.Menu(options_menu, tearoff=0)
        language_menu.add_command(label="English", command=lambda: self.change_language("English"))
        language_menu.add_command(label="Spanish", command=lambda: self.change_language("Spanish"))
        language_menu.add_command(label="German", command=lambda: self.change_language("German"))
        options_menu.add_cascade(label="Select Language", menu=language_menu)

        # Add "Unit" toggle
        options_menu.add_command(label="Toggle Unit", command=self.toggle_unit)

        # Add the 'Options' menu to the menu bar
        self.menu_bar.add_cascade(label="Options", menu=options_menu)

        # Attach the menu bar to the root window
        self.root.config(menu=self.menu_bar)

    def toggle_theme(self):
        if self.is_dark_mode:
            # Switch to Light Mode
            self.root.configure(bg="white")
            self.weather_frame.config(bg="#f0f0f0")
            self.favorites_frame.config(bg="#ffffff")
            self.history_frame.config(bg="#ffffff")
            self.top_left_frame.config(bg="#ffffff")
            self.top_right_frame.config(bg="#ffffff")

            # Change button and label styles to Light Mode
            self.search_button.config(bg="white", fg="black")
            self.clear_button.config(bg="white", fg="black")
            self.favorite_button.config(bg="white", fg="black")
            self.load_favorite_button.config(bg="white", fg="black")
            self.remove_favorite_button.config(bg="white", fg="black")
            self.exit_button.config(bg="white", fg="black")
            self.clear_history_button.config(bg="white", fg="black")
            self.favorites_menu.config(bg="white", fg="black")

            # Change the labels and their backgrounds to Dark Mode
            self.city_label.config(bg="#ffffff", fg="black")
            self.history_label.config(bg="#ffffff", fg="black")
            self.suggestion_label.config(bg="#ffffff", fg="black")
            self.city_entry.config(bg="#ffffff", fg="black")

            # Change the list-boxes to Light Mode
            self.history_listbox.config(bg="lightyellow")
            self.suggestion_listbox.config(bg="lightyellow")

            # Change label text to black for Light Mode
            for label in self.labels:
                label.config(bg="#f0f0f0", fg="black")

            self.is_dark_mode = False
        else:
            # Switch to Dark Mode
            self.root.configure(bg="black")
            self.weather_frame.config(bg="#333333")
            self.favorites_frame.config(bg="#444444")
            self.history_frame.config(bg="#444444")
            self.top_left_frame.config(bg="#444444")
            self.top_right_frame.config(bg="#444444")

            # Change button and label styles to Dark Mode
            self.search_button.config(bg="gray", fg="white")
            self.clear_button.config(bg="gray", fg="white")
            self.favorite_button.config(bg="gray", fg="white")
            self.load_favorite_button.config(bg="gray", fg="white")
            self.remove_favorite_button.config(bg="gray", fg="white")
            self.exit_button.config(bg="gray", fg="white")
            self.clear_history_button.config(bg="gray", fg="white")
            self.favorites_menu.config(bg="gray", fg="white")

            # Change the labels and their backgrounds to Dark Mode
            self.city_label.config(bg="#444444", fg="white")
            self.history_label.config(bg="#444444", fg="white")
            self.suggestion_label.config(bg="#444444", fg="white")
            self.city_entry.config(bg="gray", fg="white")

            # Change the list-boxes to Dark Mode
            self.history_listbox.config(bg="gray")
            self.suggestion_listbox.config(bg="gray")

            # Change label text to white for Dark Mode
            for label in self.labels:
                label.config(bg="#333333", fg="white")

            self.is_dark_mode = True

    def clear_search_history(self):
        self.search_history.clear()
        self.history_listbox.delete(0, tk.END)

    def update_menu_labels(self):
        # Clear the existing menu
        self.menu_bar.delete(0, 'end')

        # Create a new 'Options' menu
        options_menu = tk.Menu(self.menu_bar, tearoff=0)

        # Add "Dark Mode" toggle with translated text
        options_menu.add_command(label=self.translations.get("toggle_dark_mode", "Toggle Dark Mode"),
                                 command=self.toggle_theme)

        # Add "Language Select" submenu with translated text
        language_menu = tk.Menu(options_menu, tearoff=0)
        language_menu.add_command(label=self.translations.get("language_english", "English"),
                                  command=lambda: self.change_language("English"))
        language_menu.add_command(label=self.translations.get("language_spanish", "Spanish"),
                                  command=lambda: self.change_language("Spanish"))
        language_menu.add_command(label=self.translations.get("language_german", "German"),
                                  command=lambda: self.change_language("German"))
        options_menu.add_cascade(label=self.translations.get("select_language", "Select Language"), menu=language_menu)

        # Add "Unit" toggle with translated text
        options_menu.add_command(label=self.translations.get("toggle_unit", "Toggle Unit"), command=self.toggle_unit)

        # Add the 'Options' menu back to the menu bar
        self.menu_bar.add_cascade(label=self.translations.get("options", "Options"), menu=options_menu)

        # Attach the updated menu bar to the root window
        self.root.config(menu=self.menu_bar)

    def change_language(self, selected_language):
        language_mapping = {
            "English": "en",
            "Spanish": "es",
            "German": "de"
        }

        # Get the language code from the selected language
        language_code = language_mapping.get(selected_language, "en")

        # Switch to the selected language (this should update the translations)
        self.switch_language(language_code)

        # Update the menu labels
        self.update_menu_labels()

        # After switching the language, update the labels if weather data is available
        if self.weather_data:
            self.update_labels()  # Reuse the stored weather data to update labels in the new language

    def apply_translations(self):
        """
        Apply the translations to all text-based widgets in the application.
        """
        # General UI translations
        self.city_label.config(text=self.translations['city_label'])
        self.search_button.config(text=self.translations['search_button'])
        self.clear_button.config(text=self.translations['clear_button'])
        self.favorite_button.config(text=self.translations['save_favorite_button'])
        self.exit_button.config(text=self.translations['exit_button'])
        self.suggestion_label.config(text=self.translations['suggested_cities'])
        self.load_favorite_button.config(text=self.translations['load_favorite_button'])
        self.remove_favorite_button.config(text=self.translations['remove_favorite_button'])
        self.clear_history_button.config(text=self.translations['clear_history_button'])
        self.history_label.config(text=self.translations['search_history'])

        # Weather frame translations
        weather_labels_translations = [
            self.translations['weather'], self.translations['feels_like'],
            self.translations['min_temp'], self.translations['max_temp'],
            self.translations['humidity'], self.translations['wind_speed'],
            self.translations['rain_volume'], self.translations['country'],
            self.translations['sunrise'], self.translations['sunset']
        ]

        # Apply translations to each weather label
        for label, translated_text in zip(self.labels, weather_labels_translations):
            label.config(text=translated_text)

    def switch_language(self, language_code):
        """
        Switches the language of the app.
        """
        self.current_language = language_code
        self.translations = load_language(language_code)
        self.apply_translations()

    def save_to_favorites(self):
        city = self.city_var.get().strip()
        if city:
            if city not in self.favorites:  # Check if city is already in favorites
                self.favorites.append(city)
                self.update_favorites_menu()  # Update the favorites list in the UI
                self.save_favorites_to_file()  # Save favorites to file

                # Use translations for success message
                messagebox.showinfo(self.translations['success'],
                                    self.translations['city_added'].format(city=city))
            else:
                # Use translations for warning message
                messagebox.showwarning(self.translations['warning'],
                                       self.translations['city_already_in_favorites'].format(city=city))
        else:
            # Use translations for error message
            messagebox.showerror(self.translations['error'],
                                 self.translations['no_city_to_add'])

    def update_favorites_menu(self):
        # Safely destroy the old OptionMenu widget if it exists
        if hasattr(self, 'favorites_menu'):
            self.favorites_menu.destroy()

        # Create a new OptionMenu with the updated favorites list
        if self.favorites:
            # If there are favorites, set the first favorite city as the default value
            self.favorites_var.set(self.favorites[0])
            # Create the OptionMenu with the updated list of favorites
            self.favorites_menu = tk.OptionMenu(self.favorites_frame, self.favorites_var, *self.favorites)
        else:
            # If there are no favorites, show a default "Select a favorite city" option
            self.favorites_var.set("Select a favorite city")
            self.favorites_menu = tk.OptionMenu(self.favorites_frame, self.favorites_var, "Select a favorite city")

        # Place the new OptionMenu widget back onto the GUI
        self.favorites_menu.config(font=("Helvetica", 12))  # Increase font size
        self.favorites_menu.place(relx=0.025, rely=0.05, relwidth=0.95, relheight=0.25)

    def toggle_unit(self):
        """
        Toggle between Celsius and Fahrenheit, and update the displayed temperature accordingly.
        """
        if self.current_unit == "Metric":
            self.current_unit = "Imperial"
        else:
            self.current_unit = "Metric"

        # If weather data is already loaded, update the labels with the converted values
        if self.weather_data:
            self.update_labels(self.weather_data)

    def create_weather_labels(self, parent_frame, labels_text):
        """
        Creates and returns a list of label widgets for displaying weather information.
        """
        labels = []
        for text in labels_text:
            label = tk.Label(parent_frame, text=text, font=("Helvetica", 12), bg="#f0f0f0")
            labels.append(label)
        return labels

    def on_city_input_change(self, *args):
        """
        Filters city names based on user input and displays suggestions.
        """
        if len(self.city_var.get().strip()) > 0:  # show the weather frame if the user starts typing
            self.top_right_frame.place(relx=0.55, rely=0.02, relwidth=0.35, relheight=0.2, anchor="nw")
        else:
            self.top_right_frame.place_forget()  # Hide the weather frame initially
        input_text = self.city_var.get().strip().lower()
        self.suggestion_listbox.delete(0, tk.END)

        if input_text:
            # Filter cities that start with the input text
            matching_cities = [
                                  f"{city}, {country_code}"
                                  for city, country_code in self.city_data
                                  if city.lower().startswith(input_text)
                              ][:5]  # Limit to top 5 matches

            for city in matching_cities:
                self.suggestion_listbox.insert(tk.END, city)

            if matching_cities:
                self.suggestion_listbox.lift()  # Show the listbox if there are matches
        else:
            self.suggestion_listbox.lower()  # Hide the listbox if input is empty

    def on_suggestion_select(self, event):
        """
        Handles the selection of a city from the suggestion list.
        """
        selected_city = self.suggestion_listbox.get(self.suggestion_listbox.curselection())
        city_name = selected_city.split(",")[0]  # Extract the city name
        self.city_var.set(city_name)  # Set the city name in the entry field
        self.suggestion_listbox.lower()  # Hide the listbox after selection

    def update_weather_icon(self, icon_code):
        """
        Updates the weather icon based on the OpenWeatherMap icon code.
        """
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        response = requests.get(icon_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize((50, 50), Image.Resampling.LANCZOS)  # Resize icon to fit nicely in the frame
        self.weather_icon = ImageTk.PhotoImage(img)
        self.weather_icon_label.config(image=self.weather_icon)

    def add_to_search_history(self, city):
        if len(self.search_history) > 0:
            self.history_frame.place(relx=0.1, rely=0.25, relwidth=0.35, relheight=0.25, anchor="nw")

        if city in self.search_history:
            self.search_history.remove(city)  # Remove it so we can re-add it at the top
        self.search_history.insert(0, city)  # Add city to the top of the list

        # Keep the search history to a max of 5 items
        if len(self.search_history) > 5:
            self.search_history.pop()

        # Update the listbox with the new history
        self.history_listbox.delete(0, tk.END)
        for city in self.search_history:
            self.history_listbox.insert(tk.END, city)

    def on_history_select(self, event):
        try:
            selected_city = self.history_listbox.get(self.history_listbox.curselection())
            self.city_var.set(selected_city)  # Set the selected city in the entry field
            self.fetch_weather_command()  # Fetch the weather for the selected city
        except tk.TclError:
            pass  # Handle the case where the selection is cleared

    def fetch_weather_command(self):
        """
        Handles the fetch weather button click.
        """
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning(self.translations['warning'],
                                   self.translations['input_error'])
            return

        try:
            # Fetch weather data from the API
            self.weather_data = self.weather_fetcher.fetch_weather(city)  # Save weather data to self.weather_data

            # Update search history
            self.add_to_search_history(city)

            # Map the weather condition ID to set the appropriate background
            weather_id = self.weather_data["weather_id"]
            weather_id_mapping = {
                200: range(200, 233),
                300: range(300, 322),
                500: (500, 520, 521),
                501: (501, 511, 531),
                502: (502, 503, 504, 522),
                600: range(600, 623)
            }

            for mapped_id, condition_ids in weather_id_mapping.items():
                if weather_id in condition_ids:
                    weather_id = mapped_id
                    break

            # Update the background and labels with the fetched data
            self.bg_manager.set_background_image(weather_id)
            self.update_labels(self.weather_data)
            self.update_weather_icon(self.weather_data["icon"])

            # Show the weather frame and labels
            self.show_labels()
            self.weather_frame.place(relx=0.725, rely=0.25, relwidth=0.42, relheight=0.46, anchor="n")
            self.history_frame.place(relx=0.1, rely=0.25, relwidth=0.35, relheight=0.25, anchor="nw")

        except RuntimeError as e:
            messagebox.showerror("Error", str(e))

    def update_labels(self, data=None):
        """
        Updates the label texts with the fetched weather data, handling unit conversion and maintaining translations.
        If 'data' is provided, use it; otherwise, use the last stored weather data.
        """
        # If new data is provided, store it for future use
        if data:
            self.last_weather_data = data
        elif not self.last_weather_data:
            # No data available to display, return without updating
            return

        # Use the stored weather data if no new data is provided
        data = self.last_weather_data

        # Handle unit conversion
        if self.current_unit == "Imperial":
            temperature = celsius_to_fahrenheit(data['temperature_celsius'])
            feels_like = celsius_to_fahrenheit(data['feels_like_celsius'])
            temp_min = celsius_to_fahrenheit(data['temp_min_celsius'])
            temp_max = celsius_to_fahrenheit(data['temp_max_celsius'])
            temp_unit = "°F"
            wind_speed = meters_per_sec_to_miles_per_hour(data["wind_speed"])
            wind_speed_unit = "mph"
        else:
            temperature = data['temperature_celsius']
            feels_like = data['feels_like_celsius']
            temp_min = data['temp_min_celsius']
            temp_max = data['temp_max_celsius']
            temp_unit = "°C"
            wind_speed = meters_per_sec_to_km_per_hour(data["wind_speed"])
            wind_speed_unit = "km/h"

        # Construct the translated label texts with weather data
        label_texts = {
            'weather': f"{self.translations['weather']}: {data['weather']}",
            'temperature': f"{self.translations['temperature']}: {temperature:.1f} {temp_unit}",
            'feels_like': f"{self.translations['feels_like']}: {feels_like:.1f} {temp_unit}",
            'min_temp': f"{self.translations['min_temp']}: {temp_min:.1f} {temp_unit}",
            'max_temp': f"{self.translations['max_temp']}: {temp_max:.1f} {temp_unit}",
            'humidity': f"{self.translations['humidity']}: {data['humidity']}%",
            'wind_speed': f"{self.translations['wind_speed']}: {wind_speed:.1f} {wind_speed_unit}",
            'rain_volume': f"{self.translations['rain_volume']}: {data['rain_volume']} mm" if data[
                                                                                                  "rain_volume"] != "N/A" else f"{self.translations['rain_volume']}: No data",
            'country': f"{self.translations['country']}: {data['country']}",
            'sunrise': f"{self.translations['sunrise']}: {data['sunrise_time']}",
            'sunset': f"{self.translations['sunset']}: {data['sunset_time']}"
        }

        # Ensure labels_text holds the correct translation keys
        expected_label_keys = ['weather', 'temperature', 'feels_like', 'min_temp', 'max_temp', 'humidity', 'wind_speed',
                               'rain_volume', 'country', 'sunrise', 'sunset']
        self.labels_text = [self.translations[key] for key in expected_label_keys]

        # Update the actual labels with translated text and corresponding weather data
        for label, label_key in zip(self.labels, expected_label_keys):
            label.config(text=label_texts.get(label_key, label_key))

        # Ensure the labels are visible
        self.show_labels()

    def show_labels(self):
        """
        Displays the labels in the weather frame.
        """
        for idx, label in enumerate(self.labels):
            label.grid(row=idx, column=0, sticky='w', padx=10, pady=5)

    def hide_labels(self):
        """
        Hides the labels in the weather frame.
        """
        for label in self.labels:
            label.grid_forget()

    def clear_searchbar(self):
        """
        Clears the search bar and hides weather labels.
        """
        self.city_entry.delete(0, tk.END)
        self.bg_manager.set_background_image("default")
        self.hide_labels()
        self.suggestion_listbox.lower()  # Hide suggestions when cleared

        # Hide the weather frame
        self.weather_frame.place_forget()
        self.top_right_frame.place_forget()

    def load_favorites_from_file(self):
        try:
            with open("favorites.txt", "r") as f:
                self.favorites = [line.strip() for line in f.readlines()]
            # Update the favorites menu with the loaded cities
            self.update_favorites_menu()
        except FileNotFoundError:
            # If no file exists, just keep an empty favorites list
            self.favorites = []
            self.update_favorites_menu()  # Update the menu to show the default option

    def save_favorites_to_file(self):
        with open("favorites.txt", "w") as f:
            for city in self.favorites:
                f.write(city + "\n")

    def load_favorite_city(self):
        selected_city = self.favorites_var.get()
        if selected_city and selected_city != "Select a favorite city":
            self.city_var.set(selected_city)  # Set the selected city in the search bar
            self.fetch_weather_command()  # Fetch weather for the selected city
            self.history_frame.place(relx=0.1, rely=0.25, relwidth=0.35, relheight=0.25, anchor="nw")
        else:
            messagebox.showwarning(self.translations['warning'],
                                   self.translations['not_valid_in_favorites'])

    def remove_from_favorites(self):
        selected_city = self.favorites_var.get()
        if selected_city in self.favorites:
            self.favorites.remove(selected_city)
            self.update_favorites_menu()  # Update the drop-down
            self.save_favorites_to_file()  # Save the updated list to the file
            messagebox.showinfo(self.translations['success'],
                                self.translations['removed_from_favorites'].format(city=selected_city))
        else:
            messagebox.showwarning(self.translations['warning'],
                                   self.translations['no_selected_or_nothing_to_remove'])
