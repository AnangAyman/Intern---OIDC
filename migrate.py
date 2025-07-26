# migrate.py (Secure Version)

import os
import sqlite3
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
import sys
from dotenv import load_dotenv

# Load environment variables from a .env file
# This allows you to keep credentials out of the code.
load_dotenv()

# --- Configuration ---
# This script now reads all credentials securely from environment variables.
# We will create a .env file on the server to provide these values.
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
OLD_SQLITE_FILE = "db.sqlite" # You can also make this an environment variable if you wish

# Check if all required environment variables are set
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    print("FATAL: One or more database environment variables (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) are not set.")
    sys.exit(1)

# --- This part is a template, no changes needed below ---
NEW_DB_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

print("Connecting to the new MySQL database...")
try:
    new_engine = create_engine(NEW_DB_URL)
    new_engine.connect()
    print("MySQL connection successful.")
except Exception as e:
    print(f"\nFATAL: Could not connect to MySQL. Please check your credentials in the .env file and network access.")
    print(f"Error details: {e}")
    sys.exit(1)

metadata = MetaData()
new_user_table = Table('user', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(40), unique=True, nullable=False),
    Column('email', String(120), unique=True, nullable=False),
    Column('email_verified', Boolean, default=False, nullable=False),
    Column('phone_number', String(20), nullable=True),
    Column('mobile_number', String(20), nullable=True),
    Column('name', String(200), nullable=True),
    Column('given_name', String(100), nullable=True),
    Column('family_name', String(100), nullable=True),
    Column('updated_at', DateTime, nullable=True),
)

def migrate_from_sqlite():
    print("\nStarting migration process...")
    try:
        print(f"Connecting to old SQLite database file: {OLD_SQLITE_FILE}")
        sqlite_conn = sqlite3.connect(OLD_SQLITE_FILE)
        sqlite_cursor = sqlite_conn.cursor()
        print("SQLite connection successful.")
    except Exception as e:
        print(f"\nFATAL: Could not open SQLite file '{OLD_SQLITE_FILE}'. Make sure it's in the same directory.")
        print(f"Error details: {e}")
        sys.exit(1)

    try:
        NewSession = sessionmaker(bind=new_engine)
        new_session = NewSession()
        print(f"Creating table 'user' in MySQL database '{DB_NAME}' if it doesn't exist...")
        metadata.create_all(new_engine, tables=[new_user_table])
        print("Fetching users from SQLite...")
        sqlite_cursor.execute("SELECT id, username, email FROM user")
        old_users = sqlite_cursor.fetchall()
        print(f"Found {len(old_users)} users to migrate.")

        migrated_count = 0
        for user_row in old_users:
            new_user_data = {'id': user_row[0], 'username': user_row[1], 'email': user_row[2], 'email_verified': False}
            stmt = new_user_table.insert().values(new_user_data)
            new_session.execute(stmt)
            migrated_count += 1

        if migrated_count > 0:
            print(f"Committing {migrated_count} new users to the MySQL database...")
            new_session.commit()

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ An error occurred during migration: {e}")
    finally:
        if 'sqlite_conn' in locals(): sqlite_conn.close()
        if 'new_session' in locals() and new_session.is_active: new_session.close()
        print("Database connections closed.")

if __name__ == "__main__":
    migrate_from_sqlite()