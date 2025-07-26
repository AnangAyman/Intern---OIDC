import os
import urllib.parse
from website.app import create_app
from flask_migrate import Migrate

# --- Safely Encode Credentials from Environment ---
encoded_user = urllib.parse.quote_plus(os.environ.get('DB_USER', ''))
encoded_password = urllib.parse.quote_plus(os.environ.get('DB_PASSWORD', ''))
db_host = os.environ.get('DB_HOST', '')
db_name = os.environ.get('DB_NAME', '') # This will be 'grapeweb_new_oidc'

app = create_app({
    'SECRET_KEY': 'your_secret_key_here',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    # --- THIS IS THE PART TO CHANGE ---
    'SQLALCHEMY_DATABASE_URI': (
        f"mysql+mysqlconnector://{encoded_user}:{encoded_password}@{db_host}/{db_name}"
    ),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
})

from website.models import db
migrate = Migrate(app, db)

# --- THIS IS THE NEW CODE TO ADD ---
# This block ensures that tables are created automatically.
with app.app_context():
    db.create_all()
# --- END OF NEW CODE ---

@app.cli.command()
def initdb():
    """Initializes the database."""
    db.create_all()