from flask import Blueprint, request, Response, make_response, jsonify
users_bp = Blueprint('users', __name__)
from models import Group, User, Post, db
from utils import get_user, convert_actor_url
from constants import home_url
from datetime import datetime
#users_bp = Blueprint('users', __name__)

@users_bp.route('/users/<username>')
def user(username):
    user = get_user(username)
    if user:
        created_at = user.created_at
        summary = user.summary
        name = user.name
        attachments = user.attachments
        
        public_key_pem = user.public_key
        response = make_response({
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
            ],
            "id": f"{home_url}/users/{username}",
            "inbox": f"{home_url}/users/{username}/inbox",
            "outbox": f"{home_url}/users/{username}/outbox",
            "type": "Person",
            "name": f"{user.name}",
            "summary": f"{summary}",
            "preferredUsername": f"{username}",
            "publicKey": {
                "id": f"{home_url}/users/{username}#main-key",
                "owner": f"{home_url}/users/{username}",
                "publicKeyPem": public_key_pem
            },
            "manuallyApprovesFollowers":False,
            "attachment": attachments 
        })
        response.headers['Content-Type'] = 'application/activity+json'
    else:
        return Response("", status=404)
    return response


@users_bp.route('/users/<username>/posts/<int:post_id>')
def get_post(username, post_id):
    post = Post.query.get_or_404(post_id)

    activity = {
        '@context': [
            "https://www.w3.org/ns/activitystreams",
            {
                "ostatus": "http://ostatus.org#",
                "atomUri": "ostatus:atomUri",
                "inReplyToAtomUri": "ostatus:inReplyToAtomUri",
                "conversation": "ostatus:conversation",
                "sensitive": "as:sensitive",
                "toot": "http://joinmastodon.org/ns#",
                "votersCount": "toot:votersCount"
            }
        ],
        'type': 'Note',
        'id': f'{home_url}/users/{username}/posts/{post.id}',
        'to': ['https://www.w3.org/ns/activitystreams#Public'],
        'inReplyTo': None,
        'published': post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'url': f'{home_url}/users/{username}/posts/{post.id}',
        'attributedTo': f'{home_url}/users/{username}',
        'summary': None,
        'sensitive': False,
        'content': post.content,
        'contentMap': {
            'en': post.content
        },
        'attachment': [],
        'tag': [],
        'replies': {
            'id': f'{home_url}/users/{username}/posts/{post.id}/replies',
            'type': 'Collection',
            'first': {
                'type': 'CollectionPage',
                'next': f'{home_url}/users/{username}/posts/{post.id}/replies?only_other_accounts=true&page=true',
                'partOf': f'{home_url}/users/{username}/posts/{post.id}/replies',
                'items': []
            }
        }
    }

    return jsonify(activity)

#@users_bp.route('/users/<username>/posts/<int:post_id>')
#def get_post(username, post_id):
#    post = Post.query.get_or_404(post_id)
#    return jsonify({
#        'type': 'Note',
#        'id': f'{home_url}/users/{username}/posts/{post.id}',
#         "@context": [
#                "https://www.w3.org/ns/activitystreams"
#        ],
#        "to":[
#            "https://www.w3.org/ns/activitystreams#Public"
#        ],
#        'inReplyTo': None,
#        'attachment': [],
#        'sensitive': False,
#        'tag': [],
#        'content': post.content,
#        'author_id': post.author_id,
#        'published': post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
#        'url': f'{home_url}/users/{username}/posts/{post.id}',
#        'attributedTo':f'{home_url}/users/{username}'
#    })

@users_bp.route('/users/<username>/outbox')
def get_posts(username):
    post = Post.query.get_or_404(1)
    return jsonify([
        {
            'id': post.id,
            'content': post.content,
            'author_id': post.author_id,
            'created_at': post.created_at
        }
    ])

# Assuming you have a function to create an ActivityStreams object
def create_accept_activity(follower_url, followed_url):
    accept_activity = {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'type': 'Accept',
        'actor': followed_url,
        'object': follower_url
    }
    return accept_activity


@users_bp.route('/users/<username>/inbox', methods=['POST'])
def user_inbox(username):
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

        post = Post(content=content, author_id=user.id, created_at=datetime.utcnow())
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

        followed = User.query.filter_by(username=convert_actor_url(followed_url)).first()
        print(follower, followed)
        # Check if both users exist in the database
        if follower and followed:
            # Add the follower to the followed user's followers
            followed.followers.append(follower)
            db.session.commit()
            print(follower)
            print(followed)
            print(followed.followers)

            # Return a 202 Accepted response
            accept_activity = create_accept_activity(follower_url, followed_url)
            response = jsonify(accept_activity)
            response.status_code = 202
            return response

    # Check if the request is an Undo activity
    elif data.get('type') == 'Undo' and data.get('object', {}).get('type') == 'Follow':
        print(data)
        follower_url = data.get('actor')
        followed_url = data.get('object').get('object')

        # Retrieve the follower and followed users from the database
        follower = User.query.filter_by(username=convert_actor_url(follower_url)).first()
        followed = User.query.filter_by(username=convert_actor_url(followed_url)).first()

        # Check if both users exist in the database
        if follower and followed:
            # Remove the follower from the followed user's followers
            print(followed)
            print(followed.followers)
            print(follower)
            if follower in followed.followers:
                followed.followers.remove(follower)
                db.session.commit()

            # Return a 202 Accepted response
            return Response("", status=202)

    return Response("", status=202)

#users_bp = Blueprint('users', __name__)
