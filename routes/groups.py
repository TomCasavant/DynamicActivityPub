from flask import Blueprint, make_response
groups_bp = Blueprint('groups', __name__)
#from models import User, Group, Post

#groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups/<group>')
def group(group):
    user = get_user("tom")
    public_key_pem = user.public_key
    response = make_response({
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
        ],
        "id": f"{home_url}/groups/{group}",
        "inbox": f"{home_url}/groups/{group}/inbox",
        "outbox": f"{home_url}/groups/{group}/outbox",
        "type": "Group",
        "name": f"Testing: {group}",
        "summary": f"This is a group from minetest",
        "preferredUsername": f"{group}",
        "publicKey": {
            "id": f"{home_url}/groups/{group}#main-key",
            "owner": f"{home_url}/groups/{group}",
            "publicKeyPem": public_key_pem
        },
        "attachment": [
            {
                "type": "PropertyValue",
                "name": "Bridge Manager",
                "value": "<a href=\"https://tomkahe.com/@tom\" target=\"_blank\" rel=\"nofollow noopener noreferrer m>"
            }
        ]
    })
    response.headers['Content-Type'] = 'application/activity+json'
    return response
