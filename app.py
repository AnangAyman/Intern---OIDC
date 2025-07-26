from website.app import create_app
from flask_migrate import Migrate
import os

app = create_app({
    'SECRET_KEY': 'secret', # Change secret key later
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': (
        f"mysql+mysqlconnector://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}"
    ),
})

from website.models import db  # Ensure db is imported after the app is created
migrate = Migrate(app, db)

@app.cli.command()
def initdb():
    db.create_all()
