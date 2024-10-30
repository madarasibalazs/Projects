
# Import necessary modules and functions
from flask import Flask
from app.models import initialize_database
from app.routes import setup_routes

def create_app():
    """
    Create a Flask application instance
    :return: Return the configured Flask application instance
    """
    app = Flask(__name__, template_folder='templates')  # Create a new Flask application instance
    app.config.from_object('config.Config')  # Load configuration settings from the 'config.Config' object

    initialize_database()  # Initialize the database (if not exists)
    setup_routes(app)  # Set up application routes (e.g., define URL routes and associated view functions)

    return app  # Return the configured Flask application instance
