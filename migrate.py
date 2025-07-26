# migrate.py (MySQL-to-MySQL Version)

import os
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
import sys
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")

# Define OLD and NEW database names
OLD_DB_NAME = "grapeweb_oidc"
NEW_DB_NAME = "grapeweb_new_oidc" # This will be the DB used by the app

if not all([DB_USER, DB_PASSWORD, DB_HOST]):
    print("FATAL: DB_USER, DB_PASSWORD, or DB_HOST environment variables are not set.")
    sys.exit(1)

# --- Database Connection URLs ---
OLD_DB_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{OLD_DB_NAME}"
NEW_DB_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{NEW_DB_NAME}"

print("Connecting to MySQL databases...")
try:
    old_engine = create_engine(OLD_DB_URL)
    new_engine = create_engine(NEW_DB_URL)
    old_engine.connect()
    new_engine.connect()
    print("Database connections successful.")
except Exception as e:
    print(f"\nFATAL: Could not connect to MySQL. Check credentials in .env file and network access.")
    print(f"Error details: {e}")
    sys.exit(1)

# --- Define Table Structures ---
metadata = MetaData()

# Define the OLD 'account' table structure based on your `DESCRIBE` output
old_account_table = Table('account', metadata,
    Column('id', Integer, primary_key=True),
    Column('login', String(255), primary_key=True), # This is the username
    Column('name', String(255)),
    Column('given_name', String(255)),
    Column('family_name', String(255)),
    Column('email', String(255)),
    Column('email_verified', Boolean),
    Column('phone_number', String(255)),
    Column('mobile_number', String(255)),
)

# Define the NEW 'user' table that your application needs
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

def migrate_data():
    print("\nStarting migration process...")
    try:
        OldSession = sessionmaker(bind=old_engine)
        old_session = OldSession()

        NewSession = sessionmaker(bind=new_engine)
        new_session = NewSession()

        # The new table will be called 'user' as defined by your app's model
        print(f"Creating table '{new_user_table.name}' in database '{NEW_DB_NAME}' if it doesn't exist...")
        metadata.create_all(new_engine, tables=[new_user_table])

        print(f"Fetching users from '{OLD_DB_NAME}.account'...")
        old_users = old_session.query(old_account_table).all()
        print(f"Found {len(old_users)} users to migrate.")

        migrated_count = 0
        for user in old_users:
            if not user.email:
                print(f"Skipping user with login '{user.login}' because they have no email address.")
                continue

            new_user_data = {
                'id': user.id,
                'username': user.login, # Mapping 'login' to 'username'
                'email': user.email,
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