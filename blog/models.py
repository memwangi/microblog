from blog import db
from datetime import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from blog import login
from hashlib import md5


# Followers association table
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer,db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer,db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    """Password Hash is for password encryption
    The backref argument defines the name of a field that will be added to the objects of the "many" class that points back at the "one" object. This will add a post.author expression that will return the user given a post. """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=dt.utcnow)


    followed = db.relationship('User', 
        secondary=followers,
        primaryjoin=(followers.c.follower_id ==id),
        secondaryjoin=(followers.c.followed_id == id),
        backref = db.backref('followers',lazy='dynamic'),lazy='dynamic'    
    )


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
    
    def follow(self,user):
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self,user):
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self,user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    
    def followed_posts(self):
        """In the index page of the application I'm going to show blog posts written by all the people that are followed by the logged in user, so I need to come up with a database query that returns these posts."""

        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id) # Most recent first

        # We need to use a union operator to also show the Posts by the logged in user
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    

class Post(db.Model):
    """A single post has the user who posted it as the foreignKey. 
    ALso note that user.id is the reference to the value id in the user table,in the database"""
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=dt.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


@login.user_loader
def load_user(id):
    """ Because Flask-Login knows nothing about databases, it needs the application's help in loading a user. For that reason, the extension expects that the application will configure a user loader function, that can be called to load a user given the ID."""
    return User.query.get(int(id))

