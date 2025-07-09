import sys
import os

# Activate the virtual environment
venv_path = '/var/www/vhosts/strategidigital.com/auth.domain/venv/bin/activate_this.py'
with open(venv_path) as file_:
    exec(file_.read(), dict(__file__=venv_path))

# Add project folder to system path
sys.path.insert(0, '/var/www/vhosts/strategidigital.com/auth.domain')

# Import the Flask app
from app import app as application
