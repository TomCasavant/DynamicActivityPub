from flask import Blueprint, request, jsonify, Response
api_bp = Blueprint('api', __name__)
from models import User, Post, Group, db
from routes.activitypub.signature import signAndSend
from utils import get_or_create_user, get_user, get_or_create_group
from datetime import datetime
from constants import home_url, home_domain
from recipient import Recipient
from bs4 import BeautifulSoup
#api_bp = Blueprint('api', __name__)
from sqlalchemy import not_

@api_bp.route('/api/get_messages', methods=['GET'])
def get_messages():
    print("HERE")
    count = request.args.get('count', type=int, default=5)
    page = request.args.get('page', type=int, default=1)

    start = (page - 1) * count
    end = start + count

    posts = Post.query.order_by(Post.id.desc()).slice(start, end).all()
    result = [{'content': post.content, 'username': post.author_rel.username, 'id': post.id} for post in posts]

    return jsonify(result)

@api_bp.route('/api/get_recent_messages', methods=['GET'])
def get_recent_messages():
    last_id = request.args.get('last_id', type=int, default=0)

    posts = Post.query.join(User).filter(Post.id > last_id, not_(User.username.contains(home_domain))).order_by(Post.id.asc()).all()
    result = [{'id': post.id, 'content': BeautifulSoup(post.content, "html.parser").get_text(), 'username': post.author_rel.username} for post in posts]

    return jsonify(result)

@api_bp.route('/api/create_message', methods=['POST'])
def create_message():
    print("NEW MESSAGE")
    data = request.get_json()

    api_key = data.get('api_key')

    if api_key == 'temporary':
        print("API KEY")
        content = data.get('message')

        server = data.get('server')
        groups = data.get('groups')
        if not groups:
            groups = []
        for group in groups:
            print(f"Creating group {group}")
            get_or_create_group(group)

        ip_address = request.remote_addr
        username = data.get('username')
        if server:
            username += f"@{server}"
        if not username:
            username="null"
        else:
            user = get_or_create_user(username)
            #print(user)

        if content:
            create_post(content, username, groups)
            #for groupname in groups:
            #    group = get_or_create_group(groupname)
            #    create_post(content, username, group)
            # Create a new Post object
            #post = Post(content=content, author_id=user.id, created_at=datetime.utcnow())
            #db.session.add(post)
            #db.session.commit()
            return jsonify({'success': True, 'message': content})
        else:
            error = "Message content is missing"
    else:
        if api_key:
            error = "API Key is not valid"
        else:
            error = "API Key is Missing"

    return jsonify({'success': False, 'message': error})

def create_post(content, username, groups=[]):
    user = get_user(f"{username}")
    group_id = None
    group = None
    if groups:
        group = get_or_create_group(groups[0])
        group_id = group.id
    post = Post(content=content, author_id=user.id, created_at=datetime.utcnow(), group_id=group_id)
    db.session.add(post)
    db.session.commit()
    sender_url = f"{home_url}/users/{username}"
    sender_key = f"{home_url}/users/{username}#main-key"
    print(username)
    followers = user.followers
    for follower in followers:
        parts = follower.username.split('@')
        follower_username = parts[1] 
        follower_domain = parts[2]
        recipient = Recipient(follower_domain, follower_username)
        #print(recipient.url)
        #print(username)
        #print(domain)

        post_message = {
            "@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"],
            "id": f"{home_url}/users/{username}/posts/{post.id}", #TODO: This should be an activityID not post ID
            "type": "Create",
            "to": [f"{home_url}/users/{username}/followers/", "https://www.w3.org/ns/activitystreams#Public"],
            "actor": f"{home_url}/users/{username}",
            "object": {
                "@context": "https://www.w3.org/ns/activitystreams",
                "id": f"{home_url}/users/{username}/posts/{post.id}",
                "type": "Note",
                "content": content,
                "published": post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'), #post.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT'),
                "to": [f"{home_url}/users/{username}/followers/", "https://www.w3.org/ns/activitystreams#Public"]
            }
        }
        print(post_message)
        #signAndSend(post_message, username, recipient, sender_key)

    # User posts to group
    post_message = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": f"{home_url}/users/{username}/posts/{post.id}",
        "type": "Announce",
        "published": post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "cc": [f"{home_url}/groups/{groups[0]}/followers", f"{home_url}/users/{username}"],
        #"to": [f"{home_url}/groups/{groups[0]}"],  # Send to group's inbox
        "actor": f"{home_url}/groups/{groups[0]}",
        "object":"https://mastodon.social/users/TomsMusic/statuses/112106133817341563" #f"{home_url}/users/{username}/posts/{post.id}" #{
            #"@context": "https://www.w3.org/ns/activitystreams",
            #"id": f"{home_url}/users/{username}/posts/{post.id}",
            #"type": "Note",
            #"content": content,
            #"published": post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            #"to": [f"{home_url}/users/{username}/followers/", "https://www.w3.org/ns/activitystreams#Public"]
            #}
        }

    post_message = {
        "@context":"https://www.w3.org/ns/activitystreams",
        "id":f"{home_url}/users/{username}/posts/{post.id}/activity",
        "type":"Announce",
        "actor":f"{home_url}/groups/{groups[0]}",
        "published":datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "to":[
            "https://www.w3.org/ns/activitystreams#Public"
        ],
        "cc":[
            "https://activitypub.academy/users/eugunus_kronacut"
            #"https://tomkahe.com/users/tom/followers"
            #f"{home_url}/users/{username}",
            f"{home_url}/groups/{groups[0]}/followers"
        ],
        #"object":"https://activitypub.academy/@eugunus_kronacut/112107340"
        "object":f"{home_url}/users/{username}/posts/{post.id}"
    }
    # Loop through group followers
    print(group)
    print(f"FOLLOWERS: {group.followers}")
    sender_url = f"{home_url}/groups/{groups[0]}"
    sender_key = f"{home_url}/groups/{groups[0]}#main-key"
    for group_follower in group.followers:
        parts = group_follower.username.split('@')
        print(group_follower.username)
        group_follower_username = parts[1] 
        group_follower_domain = parts[2]
        group_recipient = Recipient(group_follower_domain, group_follower_username, type="USer")
        group_post_message = post_message
        #group_post_message = {
        #    "@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"],
        #    "id": f"{home_url}/users/{username}/posts/{post.id}",
        #    "type": "Announce",
        #    "to": [f"{home_url}/groups/{groups[0]}/followers/", "https://www.w3.org/ns/activitystreams#Public"],
        #    "actor": f"{home_url}/groups/{groups[0]}",
        #    "object": post_message
            #"object": {
            #    "id": f"{home_url}/posts/{post.id}",
            #    "type": "Note",
            #    "content": content,
            #    "published": post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            #    "to": [f"{home_url}/groups/{groups[0]}/followers/", "https://www.w3.org/ns/activitystreams#Public"]
            #}
        #}

        #group_post_message = {
         #   "@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"],
          #  "id": f"{home_url}/groups/{groups[0]}/posts/{post.id}", #TODO: This should be an activityID not post ID
          #  "type": "Announce",
          #  "to": [f"{home_url}/groups/{groups[0]}/followers/", "https://www.w3.org/ns/activitystreams#Public"],
          #  "actor": f"{home_url}/users/{username}",
          #  "object": f"{home_url}/posts/{post.id}"
            #"object": {
            #    "@context": "https://www.w3.org/ns/activitystreams",
            #    "id": f"{home_url}/groups/{group.name}/posts/{post.id}",
            #    "type": "Note",
            #    "content": content,
            #    "published": post.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            #    "to": [f"{home_url}/groups/{group.name}/followers/", "https://www.w3.org/ns/activitystreams#Public"]
            #}
       # }
        print(group_post_message)
        r = signAndSend(group_post_message, groups[0], group_recipient, sender_key, "group")
        print("Request URL:", r.request.url)
        print("Request headers:", r.request.headers)
        print("Request body:", r.request.body)
        print("Response status code:", r.status_code)
        print("Response headers:", r.headers)
        print("Response body:", r.text)


@api_bp.route('/api/follow_user', methods=['POST'])
def follow_user():
    data = request.get_json()
    server = data['server']
    username = data['username']
    source_user = data['source_user']

    sender_url = f"{home_url}/users/{source_user}"
    sender_key = f"{home_url}/users/{source_user}#main-key"

    print(f"FOllowing {username}")
    recipient = Recipient(server, username)

    activity_id = f"{home_url}/users/{source_user}/follows/test"

    # Now that the header is set up, we will construct the message
    follow_request_message = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": activity_id,
        "type": "Follow",
        "actor": sender_url,
        "object": recipient.url
    }
    r = signAndSend(follow_request_message, source_user, recipient, sender_key)

    # Log the request and response
    print("Request URL:", r.request.url)
    print("Request headers:", r.request.headers)
    print("Request body:", r.request.body)
    print("Response status code:", r.status_code)
    print("Response headers:", r.headers)
    print("Response body:", r.text)
    return Response(response=r.text, status=r.status_code, content_type=r.headers['content-type'])

@api_bp.route('/api/unfollow_user', methods=['POST'])
def unfollow_user():
    data = request.get_json()
    server = data['server']
    username = data['username']
    source_user = data['source_user']

    sender_url = f"{home_url}/users/{source_user}"
    sender_key = f"{home_url}/users/{source_user}#main-key"

    recipient = Recipient(server, username)

    activity_id = f"{home_url}/users/{source_user}/unfollows/test"

    # Now that the header is set up, we will construct the message
    unfollow_request_message = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": activity_id,
        "type": "Undo",
        "actor": sender_url,
        "object": {
            "type": "Follow",
            "actor": sender_url,
            "object": recipient.url
        }
    }
    r = signAndSend(unfollow_request_message, source_user, recipient, sender_key)

    # Log the request and response
    print("Request URL:", r.request.url)
    print("Request headers:", r.request.headers)
    print("Request body:", r.request.body)
    print("Response status code:", r.status_code)
    print("Response headers:", r.headers)
    print("Response body:", r.text)
    return Response(response=r.text, status=r.status_code, content_type=r.headers['content-type'])

@api_bp.route('/api/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    username = data.get('username')
    user = get_user(username)

    if user:
        # Update name if present in JSON
        if 'name' in data:
            user.name = data['name']

        # Update summary if present in JSON
        if 'summary' in data:
            user.summary = data['summary']

        # Update attachments if present in JSON
        if 'attachments' in data:
            user.attachments = data['attachments']

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404
