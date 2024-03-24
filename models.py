#from app import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

#follower_association_table = Table('follower_association', db.Model.metadata,
#    Column('follower_id', Integer, ForeignKey('user.id')),
#    Column('followed_id', Integer, ForeignKey('user.id'))
#)

follower_association_table = Table('follower_association', db.Model.metadata,
    Column('follower_id', Integer, ForeignKey('user.id')),
    Column('followed_id', Integer, ForeignKey('user.id')),
    Column('group_id', Integer, ForeignKey('group.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Profile
    username = db.Column(db.String(50), unique=True, nullable=False)
    summary = db.Column(db.String(100), nullable=False, default="")
    name = db.Column(db.String(50), nullable=False, default="")
    attachments = db.Column(JSON, nullable=False, default=[])

    public_key = db.Column(db.String(500), nullable=True)
    encrypted_private_key = db.Column(db.LargeBinary, nullable=True)
    is_local = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    followers = relationship(
        "User", secondary=follower_association_table,
        primaryjoin=id==follower_association_table.c.followed_id,
        secondaryjoin=id==follower_association_table.c.follower_id,
        backref="following"
    )

    def __repr__(self):
        return f'<User {self.username} (Local: {self.is_local})>'

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    public_key = db.Column(db.String(500), nullable=False)
    encrypted_private_key = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Define relationship with User for followers
    #followers = relationship(
    #    "User", secondary=follower_association_table,
    #    primaryjoin=id==follower_association_table.c.followed_id,
    #    secondaryjoin=id==follower_association_table.c.follower_id,
    #    backref="following_groups"
    #)

    followers = relationship(
        "User", secondary=follower_association_table,
        primaryjoin=id==follower_association_table.c.group_id,
        secondaryjoin=follower_association_table.c.follower_id==User.id,
        backref="following_groups"
    )

    # Define relationship with Post
    posts = db.relationship('Post', backref='group', lazy=True)

    def __repr__(self):
        return f'<Group {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)  # Nullable because a post can be for an individual user
    author_rel = db.relationship('User', backref='posts')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.author_id}: {self.content}>'

