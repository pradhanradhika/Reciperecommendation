from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

class Config:
    print(os.getenv('GOOGLE_API_KEY'))  # Should output the value from the .env file if loaded correctly

    #SECRET_KEY = os.getenv('SECRET_KEY')  # Load Flask secret key
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Load Google API key
    # Add other configuration variables as needed
