from flask import Blueprint, make_response
from flask import Blueprint, request, Response, make_response, jsonify
from utils import get_group, convert_actor_url
from constants import home_url, home_domain
from models import Group, User, db, Post
#from recipient import Recipient
from recipient import Recipient
import requests
from routes.activitypub.signature import signAndSend

groups_bp = Blueprint('groups', __name__)
#from models import User, Group, Post

#groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups/<group_name>')
def group(group_name):
    group = get_group(group_name)
    public_key_pem = group.public_key
    response = make_response({
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
        ],
        "id": f"{home_url}/groups/{group_name}",
        "inbox": f"{home_url}/groups/{group_name}/inbox",
        "outbox": f"{home_url}/groups/{group_name}/outbox",
        "manuallyApprovesFollowers":False,
        "type": "Group",
        "name": f"Testing: {group_name}",
        "summary": f"This is a group from minetest",
        "preferredUsername": f"{group_name}",
        "publicKey": {
            "id": f"{home_url}/groups/{group_name}#main-key",
            "owner": f"{home_url}/groups/{group_name}",
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

#@groups_bp.route('/groups/<groupname>/follow', methods=['POST'])
def follow_group(groupname):
    data = request.get_json()
    follower_url = data.get('actor')
    follower_username = convert_actor_url(follower_url)
    follower = User.query.filter_by(username=follower_username).first()
    if not follower:
        follower = User(username=follower_username)
        db.session.add(follower)
        db.session.commit()

    group = Group.query.filter_by(name=groupname).first()
    if not group:
        group = Group(name=groupname)
        db.session.add(group)
        db.session.commit()

    group.followers.append(follower)
    db.session.commit()

    return Response("", status=202)


#@groups_bp.route('/groups/<groupname>/unfollow', methods=['POST'])
def unfollow_group(groupname):
    data = request.get_json()
    follower_url = data.get('actor')
    follower_username = convert_actor_url(follower_url)
    follower = User.query.filter_by(username=follower_username).first()

    group = Group.query.filter_by(name=groupname).first()
    if follower and group:
        if follower in group.followers:
            group.followers.remove(follower)
            db.session.commit()

    return Response("", status=202)

def create_accept_activity(follower_url, followed_url):
    accept_activity = {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'id': f"{home_url}/activities/1",
        'type': 'Accept',
        'actor': followed_url,
        'object': {
            'id': follower_url,
            'type': 'Follow',
            'actor': follower_url,
            'object': followed_url
        }
    }
    return accept_activity

def send_activity_to_inbox(actor_url, activity):
    # Retrieve the JSON-LD representation of the actor
    actor_response = requests.get(actor_url, headers={"Accept": "application/activity+json"})
    actor_data = actor_response.json()

    # Look up the inbox property in the actor's JSON-LD representation
    inbox_url = actor_data.get("inbox")
    if not inbox_url:
        print("No inbox found for actor")
        return

    # Make an HTTP POST request to the inbox URL
    response = requests.post(inbox_url, json=activity)
    if response.status_code == 200:
        print("Activity sent successfully")
    else:
        print(f"Failed to send activity. Status code: {response.status_code}")


@groups_bp.route('/groups/<groupname>/inbox', methods=['POST'])
def group_inbox(groupname):
    data = request.get_json()
    print(data)

    # Check if the request is a Create activity
    if data.get('type') == 'Create':
        # Extract the status content
        content = data.get('object', {}).get('content')
        actor_url = data.get('actor')
        print(actor_url)
        # Find or create the user
        actor_username = convert_actor_url(actor_url)
        user = User.query.filter_by(username=actor_username).first()
        if not user:
            user = User(username=actor_username)
            db.session.add(user)
            db.session.commit()

        group = Group.query.filter_by(name=groupname).first()
        if not group:
            group = Group(name=groupname)
            db.session.add(group)
            db.session.commit()

        post = Post(content=content, author_id=user.id, group_id=group.id, created_at=datetime.utcnow())
        db.session.add(post)
        db.session.commit()

        # Return a 202 Accepted response
        return Response("", status=202)

        # Check if the request is a Follow activity
    elif data.get('type') == 'Follow':
        print("Getting followers:")
        follower_url = data.get('actor')
        followed_url = data.get('object')
        print(follower_url)
        print(followed_url)
        # Retrieve the follower and followed users from the database
        follower = User.query.filter_by(username=convert_actor_url(follower_url)).first()
        if not follower:
            follower = User(username=convert_actor_url(follower_url))
            db.session.add(follower)
            db.session.commit()

        followed = Group.query.filter_by(name=convert_actor_url(followed_url)).first()
        print(f"Converted {convert_actor_url(followed_url)}")
        print(f"{followed_url}")
        print("THESE AR ETHE FOLLOWERS")
        print(follower, followed)

        #if not followed_group:
        #    followed_group = Group(name=convert_actor_url(followed_url))
        #    db.session.add(followed_group)
        #    db.session.commit()
        # Check if both users exist in the database
        print(f"FOllwoer: {follower} {followed}")
        if follower and followed:
            print("Got follower and followed")
            # Add the follower to the followed user's followers
            followed.followers.append(follower)
            db.session.commit()
            print(f"Successfully added {follower} to {followed}")
            print(follower)
            print(followed)
            print(followed.followers)

            accept_activity = create_accept_activity(follower_url, followed_url)
            sender_url = f"{home_url}/groups/{groupname}"
            sender_key = f"{home_url}/groups/{groupname}#main-key"
            parts = follower.username.split('@')
            print(follower.username)
            group_follower_username = parts[1]
            group_follower_domain = parts[2]
            group_recipient = Recipient(group_follower_domain, group_follower_username, type="USer")

            signAndSend(accept_activity, groupname, group_recipient, sender_key, "group")
            #send_activity_to_inbox(follower_url, accept_activity)
            response = jsonify(accept_activity)
            response.status_code = 200
            print(accept_activity)
            return response
    # Check if the request is an Undo activity
    elif data.get('type') == 'Undo' and data.get('object', {}).get('type') == 'Follow':
        print(data)
        follower_url = data.get('actor')
        followed_url = data.get('object').get('object')

        # Retrieve the follower and followed users from the database
        follower = User.query.filter_by(username=convert_actor_url(follower_url)).first()
        followed = Group.query.filter_by(name=convert_actor_url(followed_url)).first()

        # Check if both users exist in the database
        if follower and followed:
            # Remove the follower from the followed user's followers
            print(followed)
            print(followed.followers)
            print(follower)
            if follower in followed.followers:
                followed.followers.remove(follower)
                db.session.commit()


    return Response("", status=202)

@groups_bp.route('/groups/<group_name>/posts/<int:post_id>')
def get_group_post(group_name, post_id):
    group = Group.query.filter_by(name=group_name).first_or_404()
    post = Post.query.filter_by(id=post_id, group_id=group.id).first_or_404()
    return jsonify({
        'id': post.id,
        'content': post.content,
        'author_id': post.author_id,
        'created_at': post.created_at
    })
