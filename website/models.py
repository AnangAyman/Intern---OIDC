from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2TokenMixin,
    OAuth2AuthorizationCodeMixin
)
from datetime import datetime, timedelta
from sqlalchemy import Boolean, DateTime, String
from flask_migrate import Migrate

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)  # preferred_username
    email = db.Column(db.String(120), nullable=True)
    email_verified = db.Column(Boolean, default=False)  # Indicates if the email is verified
    phone_number = db.Column(db.String(20), nullable=True)
    mobile_number = db.Column(db.String(20), nullable=True)
    name = db.Column(String(120), nullable=True)  # Full name
    given_name = db.Column(String(40), nullable=True)  # First name
    family_name = db.Column(String(40), nullable=True)  # Last name
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __str__(self):
        return self.username

    def get_user_id(self):
        return self.id

    def get_claims(self):
        """
        Returns a dictionary of claims supported by this user.
        """
        return {
            "sub": str(self.id),  # Subject identifier for the user
            "name": self.name,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "preferred_username": self.username,
            "email": self.email,
            "email_verified": self.email_verified,
            "phone_number": self.phone_number,
            "mobile_number": self.mobile_number,
            "updated_at": int(self.updated_at.timestamp()) if self.updated_at else None,
        }

class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name='fk_oauth2code_user_id'))
    user = db.relationship('User')
    is_internal = db.Column(db.Integer, default=0)  # Indicates if the client is internal
    code_challenge_method = db.Column(db.String(48), nullable=True)


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name='fk_oauth2token_user_id'))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE',  name='fk_user_id'))
    user = db.relationship('User')
    revoked = db.Column(db.Boolean, default=False)  # New column

    def is_refresh_token_active(self):
        expires_at = datetime.utcfromtimestamp(self.issued_at) + timedelta(seconds=self.expires_in * 2)
        return not self.revoked and expires_at > datetime.utcnow()
