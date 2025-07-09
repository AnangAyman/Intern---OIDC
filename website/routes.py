import time
from flask import Blueprint, request, session
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from .models import db, User, OAuth2Client
from .oauth2 import authorization, require_oauth, generate_user_info


bp = Blueprint('home', __name__)


def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None

# User signup / login
@bp.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')  # <-- ADD THIS LINE to get the email

        # Check if email is provided
        if not email:
            return "Email is required.", 400

        user = User.query.filter_by(username=username).first()
        if not user:
            # Pass the email when creating the new user
            user = User(username=username, email=email) # <-- UPDATE THIS LINE
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        return redirect('/')

    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []
    return render_template('home.html', user=user, clients=clients)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


# Create new clients
@bp.route('/create_client', methods=('GET', 'POST'))
def create_client():
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        return render_template('create_client.html')
    form = request.form
    client_id = gen_salt(24)
    client = OAuth2Client(client_id=client_id, user_id=user.id)
    # Mixin doesn't set the issue_at date
    client.client_id_issued_at = int(time.time())

    client.is_internal = 1 if "is_internal" in form else 0

    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"],
        "is_internal": client.is_internal
    }
    client.set_client_metadata(client_metadata)

    if client.token_endpoint_auth_method == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.commit()
    return redirect('/')

# Ask user to grant the permissions
@bp.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    if request.method == 'GET':
        try:
            grant = authorization.get_consent_grant(end_user=user)
            client = grant.client
            scope = client.get_allowed_scope(grant.request.scope)

            # If client is internal, immediately grant authorization
            if client.is_internal == 1:
                return authorization.create_authorization_response(grant_user=user)
            
        except OAuth2Error as error:
            return jsonify(dict(error.get_body()))
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


# Create the tokens
@bp.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()

@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')

# Example API
@bp.route('/oauth/userinfo')
@require_oauth('profile')
def api_me():

    user = current_token.user  # Get the user associated with the current token
    return jsonify({
            "id": user.id,
            "name": f"{user.given_name} {user.family_name}",  # Combine first and last names
            "given_name": user.given_name,
            "family_name": user.family_name,
            "preferred_username": user.username,
            "email": user.email,
            "email_verified": user.email_verified,
            "phone_number": user.phone_number,
            "mobile_number": user.mobile_number,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        })
    # return jsonify(
    #     generate_user_info(current_token.user, current_token.scope))

@bp.route('/oauth/email')
@require_oauth(['profile', 'email'])
def email_me():

    user = current_token.user  # Get the user associated with the current token
    return jsonify({
            "email": user.email,
            "email_verified": user.email_verified,
        })