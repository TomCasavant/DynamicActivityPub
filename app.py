from flask import Flask, render_template, request, jsonify, make_response, Response
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

from urllib.parse import urlparse
import base64
import hashlib
import datetime
import requests

import os
import json
from datetime import datetime
from models import db, User, Post, Group
from recipient import Recipient

from constants import home_url
from utils import get_user

#app = Flask(__name__)
#def create_app():
#    #app = Flask(__name__)
#    app.config['SECRET_KEY'] = 'none'
#    socketio = SocketIO(app)
#    message_list = []
#    api_key = 'temporary'
#    secret_password = os.getenv('SECRET_PASSWORD')
#    home_url = "https://activitypubtesting.duckdns.org"
#    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activitypub.db'

#    db = SQLAlchemy(app)
#    with app.app_context():
#        db.create_all()
#    return app

app = Flask(__name__)
app.config['SECRET_KEY'] = 'none'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activitypub.db'
db.init_app(app)
socketio = SocketIO(app)

def get_or_create_user(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        # Generate RSA key pair
        key = rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=2048
        )
        
        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption())

        public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PublicFormat.SubjectPublicKeyInfo
        )

        user = User(username=username, public_key=public_key.decode('utf-8'), encrypted_private_key=private_key)
        db.session.add(user)
        db.session.commit()

    return user

def get_user(username):
    return User.query.filter_by(username=username).first()
    
# Create the database tables
#db.create_all()
#with app.app_context():
#    db.create_all()

#@app.before_first_request
#def create_database():
#    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.route('/.well-known/webfinger')
def webfinger():
    #TODO: Update webfinger from config, add ability to select any user/verify user exists
    resource = request.args.get('resource')

    # acct:example@example.com
    # Parse the 'acct' URI to extract the username
    parts = resource.split(':')
    
    # Extract everything after 'acct:'
    username_with_domain = resource.split('acct:', 1)[1]

    # Remove the domain part
    username = username_with_domain.replace('@activitypubtesting.duckdns.org', '')
    user = get_user(username)
    if user:
        url = f"{home_url}/users/{username}"
    else:
        url = f"{home_url}/groups/{username}"
        
    response = make_response({
        "subject": resource,
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": url
            }
        ]
    })

    response.headers['Content-Type'] = 'application/jrd+json'
    return response

def post_message(content, source_user, recipient, sender_key):
    home_url = "your_home_url_here"

    sender_url = f"{home_url}/users/{source_user}"
    activity_id = f"{home_url}/users/{source_user}/posts/test"

    # Construct the message
    post_message = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": activity_id,
        "type": "Create",
        "to": [recipient.url],
        "actor": sender_url,
        "object": {
            "type": "Note",
            "content": content
        }
    }

    # Sign and send the message
    r = signAndSend(post_message, source_user, recipient, sender_key)

    # Log the request and response
    print("Request URL:", r.request.url)
    print("Request headers:", r.request.headers)
    print("Request body:", r.request.body)
    print("Response status code:", r.status_code)
    print("Response headers:", r.headers)
    print("Response body:", r.text)

    return Response(response=r.text, status=r.status_code, content_type=r.headers['content-type'])

if __name__ == '__main__':
    #create_app()
    #from models import User, Group, Post
    with app.app_context():
        db.create_all()
    from routes.users import users_bp
    from routes.groups import groups_bp
    from routes.api import api_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(api_bp)


    socketio.run(app, host='192.168.1.75', port=9999)
