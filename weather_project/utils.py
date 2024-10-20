import os
from PIL import Image, ImageTk
from tkinter import messagebox

class BackgroundManager:
    def __init__(self, image_label):
        self.image_label = image_label
        self.images_folder = "images"

        # Mapping weather IDs to background images
        self.weather_images = {
            # Thunderstorm
            200: "thunderstorm.jpg",

            # Drizzle
            300: "drizzle.jpg",

            # Rain
            500: "light_rain.jpg",
            501: "rain.jpg",
            502: "heavy_rain.jpg",

            # Snow
            600: "snowing.jpg",

            # Atmosphere
            701: "fog.jpg",
            711: "smoke.jpg",
            721: "haze.jpg",
            731: "sand.jpg",
            741: "fog.jpg",
            751: "sand.jpg",
            761: "dust.jpg",
            762: "volcanic_ash.jpg",
            771: "squalls.jpg",
            781: "tornado.jpg",

            # Clear
            800: "clear_sky.jpg",

            # Clouds
            801: "few_clouds.jpg",
            802: "scattered_clouds.jpg",
            803: "broken_clouds.jpg",
            804: "overcast_clouds.jpg",
        }

    def set_background_image(self, weather_id):
        """
        Sets the background image based on the weather ID.
        """
        if weather_id not in self.weather_images:
            weather_id = 'default'
        try:
            # Get the appropriate background image based on the weather ID
            image_filename = self.weather_images.get(weather_id, "default_weather.jpg")
            image_path = os.path.join(self.images_folder, image_filename)

            # Load and resize the image
            bg_image = Image.open(image_path)
            bg_image = bg_image.resize((900, 750), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(bg_image)

            # Update the background image label
            self.image_label.config(image=bg_photo)
            self.image_label.image = bg_photo  # Keep a reference to avoid garbage collection
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set background image: {e}")

def celsius_to_fahrenheit(celsius):
    """
    Converts Celsius temperature to Fahrenheit.
    """
    return (celsius * 9 / 5) + 32

def meters_per_sec_to_km_per_hour(mps):
    """
    Converts meters per seconds to kilometers per hour.
    """
    return mps * 3.6

def meters_per_sec_to_miles_per_hour(mps):
    """
    Converts meters per seconds to kilometers per hour.
    """
    return mps * 2.23694
