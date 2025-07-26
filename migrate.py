# migrate.py (Final Version - Allows Duplicate/Null Emails)

import os
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
import sys
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

# --- Configuration ---
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
OLD_DB_NAME = "grapeweb_oidc"
NEW_DB_NAME = "grapeweb_new_oidc"

if not all([DB_USER, DB_PASSWORD, DB_HOST]):
    print("FATAL: DB_USER, DB_PASSWORD, or DB_HOST environment variables are not set.")
    sys.exit(1)

# --- Safely Encode Credentials ---
encoded_user = urllib.parse.quote_plus(DB_USER)
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

# --- Database Connection URLs ---
OLD_DB_URL = f"mysql+mysqlconnector://{encoded_user}:{encoded_password}@{DB_HOST}/{OLD_DB_NAME}"
NEW_DB_URL = f"mysql+mysqlconnector://{encoded_user}:{encoded_password}@{DB_HOST}/{NEW_DB_NAME}"

print("Connecting to MySQL databases...")
try:
    old_engine = create_engine(OLD_DB_URL)
    new_engine = create_engine(NEW_DB_URL)
    old_engine.connect()
    new_engine.connect()
    print("Database connections successful.")
except Exception as e:
    print(f"\nFATAL: Could not connect to MySQL. Check credentials and network access.")
    sys.exit(1)

# --- Define Table Structures ---
metadata = MetaData()
old_account_table = Table('account', metadata,
    Column('id', Integer, primary_key=True),
    Column('login', String(255), primary_key=True),
    Column('name', String(255)),
    Column('given_name', String(255)),
    Column('family_name', String(255)),
    Column('email', String(255)),
    Column('email_verified', Boolean),
    Column('phone_number', String(255)),
    Column('mobile_number', String(255)),
)
# Define the NEW 'user' table with the updated, less strict email column
new_user_table = Table('user', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(40), unique=True, nullable=False),
    # --- THIS IS THE KEY SCHEMA CHANGE ---
    Column('email', String(120), nullable=True, unique=False), # Email is now optional and not unique
    Column('email_verified', Boolean, default=False, nullable=True),
    Column('phone_number', String(20), nullable=True),
    Column('mobile_number', String(20), nullable=True),
    Column('name', String(200), nullable=True),
    Column('given_name', String(100), nullable=True),
    Column('family_name', String(100), nullable=True),
    Column('updated_at', DateTime, nullable=True),
)

def migrate_data():
    print("\nStarting migration process...")
    try:
        OldSession = sessionmaker(bind=old_engine)
        old_session = OldSession()
        NewSession = sessionmaker(bind=new_engine)
        new_session = NewSession()

        # We will drop the old table first to ensure a clean slate
        print(f"Dropping table '{new_user_table.name}' in '{NEW_DB_NAME}' if it exists, for a clean migration...")
        new_user_table.drop(new_engine, checkfirst=True)

        print(f"Creating new, updated table '{new_user_table.name}' in database '{NEW_DB_NAME}'...")
        metadata.create_all(new_engine, tables=[new_user_table])

        print(f"Fetching users from '{OLD_DB_NAME}.account'...")
        old_users = old_session.query(old_account_table).all()
        print(f"Found {len(old_users)} users to migrate.")

        migrated_count = 0
        for user in old_users:
            new_user_data = {
                'id': user.id,
                'username': user.login,
                'email': user.email, # Email can be null now
                'email_verified': user.email_verified if user.email_verified is not None else False,
                'name': user.name,
                'given_name': user.given_name,
                'family_name': user.family_name,
                'phone_number': user.phone_number,
                'mobile_number': user.mobile_number,
            }
            stmt = new_user_table.insert().values(new_user_data)
            new_session.execute(stmt)
            migrated_count += 1

        if migrated_count > 0:
            print(f"Committing {migrated_count} new users to the database...")
            new_session.commit()

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ An error occurred during migration: {e}")
    finally:
        if 'old_session' in locals() and old_session.is_active: old_session.close()
        if 'new_session' in locals() and new_session.is_active: new_session.close()
        print("Database connections closed.")

if __name__ == "__main__":
    migrate_data()