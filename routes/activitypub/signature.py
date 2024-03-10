from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

from utils import get_user
from datetime import datetime
import json
import base64
import hashlib
import requests

def create_digest(message):
    message_json = json.dumps(message)
    digest = base64.b64encode(hashlib.sha256(message_json.encode('utf-8')).digest())
    return digest


def signAndSend(message, source_username, recipient, sender_key):
    print(source_username)
    user = get_user(source_username)

    current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    digest = create_digest(message)
    #signature_text = b'(request-target): post %s\nhost: %s\ndate: %s' % (recipient.path.encode('utf-8'), recipient.host.encode('utf-8'), current_date.encode('utf-8'))
    #signature_text = b'(request-target): post %s\ndigest: SHA-256=%s\nhost: %s\ndate: %s' % (recipient.path.encode('
    signature_text = b'(request-target): post %s\ndigest: SHA-256=%s\nhost: %s\ndate: %s' % (recipient.path.encode('utf-8'), digest, recipient.host.encode('utf-8'), current_date.encode('utf-8'))

    private_key_text = user.encrypted_private_key

    private_key = serialization.load_pem_private_key(
        private_key_text,
        password=None,
        backend=crypto_default_backend()
    )
    raw_signature = private_key.sign(
        signature_text,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    #signature_header = 'keyId="%s",algorithm="rsa-sha256",headers="(request-target) digest host date",signature="%s"'>
    #signature_text = b'(request-target): post %s\nhost: %s\ndate: %s' % recipient_path.encode('utf-8'), recipient_host.encode('utf-8'), date.encode('utf-8')
    #signature_header = 'keyId="%s",algorithm="rsa-sha256",headers="(request-target) host date",signature="%s"' % (sender_key, base64.b64encode(raw_signature).decode('utf-8'))
    signature_header = 'keyId="%s",algorithm="rsa-sha256",headers="(request-target) digest host date",signature="%s"' % (sender_key, base64.b64encode(raw_signature).decode('utf-8'))

    headers = {
        'Date': current_date,
        'Content-Type': 'application/activity+json',
        'Host': recipient.host,
        'Digest': f"SHA-256={digest.decode('utf-8')}",
        'Signature': signature_header
    }
    print(raw_signature)
    verification_testing(f"http://192.168.1.75:9999/users/{source_username}", private_key, raw_signature, signature_text)

    r = requests.post(recipient.inbox, headers=headers, json=message)
    return r

def verification_testing(public_key_url, private_key, raw_signature, signature_text):
    # Load the public key JSON from the user's URL
    #public_key_url = 'http://192.168.1.75:9999/users/tom'
    public_key_response = requests.get(public_key_url)
    public_key_json = public_key_response.json()['publicKey']

    # Extract the public key from the JSON
    public_key_pem = public_key_json['publicKeyPem']

    # Load the public key
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode(),
        backend=crypto_default_backend()
    )
    try:
        public_key.verify(
            raw_signature,
            signature_text,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        print("Signature verification successful")
    except Exception as e:
        print(f"Signature verification failed: {e}")
