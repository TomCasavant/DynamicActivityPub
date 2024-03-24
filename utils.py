from models import User, db, Group
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from urllib.parse import urlparse
from constants import home_domain

def convert_actor_url(actor_url):
    parsed_url = urlparse(actor_url)
    domain = parsed_url.netloc
    parts = parsed_url.path.split('/')
    username = parts[-1]
    return f"@{username}@{domain}"

def create_rsa_key_pair():
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

    return public_key.decode('utf-8'), private_key

def get_user(username):
    username = f"@{username}@{home_domain}"
    return User.query.filter_by(username=username).first()

#def get_or_create_user(username):
def get_or_create_user(username):
    username = f"@{username}@{home_domain}"
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        public_key, private_key = create_rsa_key_pair()
        user = User(username=username, public_key=public_key, encrypted_private_key=private_key, name=username)
        db.session.add(user)
        db.session.commit()

    return user

def get_or_create_group(name):
    name = f"@{name}@{home_domain}"
    group = Group.query.filter_by(name=name).first()

    if group is None:
        print("group doesn't exist")
        public_key, private_key = create_rsa_key_pair()
        group = Group(name=name, public_key=public_key, encrypted_private_key=private_key)
        db.session.add(group)
        db.session.commit()

    return group

def get_group(groupname):
    groupname = f"@{groupname}@{home_domain}"
    return Group.query.filter_by(name=groupname).first()
