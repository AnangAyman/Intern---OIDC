from website.app import create_app
from flask_migrate import Migrate
#import pymysql

app = create_app({
    'SECRET_KEY': 'secret', # Change secret key later
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite', # Change uri to pymysql
})

from website.models import db  # Ensure db is imported after the app is created
migrate = Migrate(app, db)

@app.cli.command()
def initdb():
    db.create_all()
