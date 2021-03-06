"""
models.py

Defines the database models.

"""
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.event import listens_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
import bcrypt

db = SQLAlchemy()


resourcecategory = db.Table(
    'resourcecategory',
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
    )


class Resource(db.Model):
    """
    A resource used to recommend health care
    providers to L.G.B.T.Q.I.A people.
    """
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Unicode(250), nullable=False)
    organization = db.Column(db.Unicode(500))
    description = db.Column(db.UnicodeText)
    visible = db.Column(db.Boolean, nullable=False, default=True)

    address = db.Column(db.Unicode(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location = db.Column(db.Unicode(500))

    email = db.Column(db.Unicode(250))
    phone = db.Column(db.Unicode(50))
    fax = db.Column(db.Unicode(50))
    url = db.Column(db.Unicode(500))
    hours = db.Column(db.UnicodeText)

    source = db.Column(db.UnicodeText)
    npi = db.Column(db.Unicode(10))
    notes = db.Column(db.UnicodeText)

    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_verified = db.Column(db.Date)

    categories = db.relationship('Category', secondary=resourcecategory,
        backref=db.backref('resources', lazy='dynamic'))    
    category_text = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


class Category(db.Model):
    """
    A category to which one or more resources can belong.
    """
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Unicode(100), nullable=False, unique=True)
    description = db.Column(db.UnicodeText)
    keywords = db.Column(db.UnicodeText)

    visible = db.Column(db.Boolean, nullable=False, default=True)

    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __unicode__(self):
        return self.name


class User(UserMixin, db.Model):
    """
    A RAD user.
    """
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.Unicode(50), nullable=False, unique=True)
    password = db.Column(db.Unicode(128), nullable=False, server_default="")
    email = db.Column(db.Unicode(250), nullable=False)

    admin = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    default_location = db.Column(db.Unicode(500))
    default_latitude = db.Column(db.Float)
    default_longitude = db.Column(db.Float)

    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    """
    The name to display with a user's reviews.
    """
    display_name = db.Column(db.Unicode(100), nullable=False, server_default='')
    
    """
    Indicates if a user has confirmed their account by clicking
    the link in the provided email. The confirmation code
    will be stored in email_code.
    """
    email_activated = db.Column(db.Boolean, nullable=False, default=False, server_default='1')
    
    """
    The date/time the user requested a password reset. The code
    to reset the password will be stored in email_code.
    """
    reset_pass_date = db.Column(db.DateTime, nullable=True)
    
    """
    The code used for email registration and password resets.
    This will be a string representation of a UUID, in lowercase
    and without brackets.
    """
    email_code = db.Column(db.Unicode(36), nullable=True)

    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email

        if password is not None:
            self.password = bcrypt.hashpw(password, bcrypt.gensalt())

    def verify_password(self, password):
        return bcrypt.hashpw(password, self.password) == self.password

    def __unicode__(self):
        return self.username


class Review(db.Model):
    """
    A review of a resource by a user.
    """
    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.UnicodeText, nullable=False)

    rating = db.Column(db.Integer)
    intake_rating = db.Column(db.Integer)
    staff_rating = db.Column(db.Integer)
    composite_rating = db.Column(db.Float)

    visible = db.Column(db.Boolean, nullable=False, default=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip = db.Column(db.Unicode(45))

    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    resource = db.relationship('Resource',
                               backref=db.backref('reviews',
                                                  lazy='dynamic'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User',
                           backref=db.backref('reviews',
                                              lazy='dynamic'))

    is_old_review = db.Column(db.Boolean, nullable=False, default=False, server_default='0')

    new_review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=True)

    # We want to passively delete here because we'll be manually updating
    # foreign key references in the review service.
    old_reviews = db.relationship('Review',
                                  backref=db.backref("new_review", remote_side=id),
                                  lazy="dynamic",
                                  passive_deletes=True)

    def __init__(self, rating=None, text=None, resource=None, user=None):
        self.text = text
        self.rating = rating
        self.resource = resource
        self.user = user

    def __unicode__(self):
        return self.text


class LoginHistory(db.Model):
    """
    A recorded login attempt (successful or otherwise) for a user.
    """
    id = db.Column(db.Integer, primary_key=True)

    login_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip = db.Column(db.Unicode(45), nullable=False)
    username = db.Column(db.Unicode(50), nullable=False)
    successful = db.Column(db.Boolean, nullable=False)
    
    failure_reason = db.Column(db.Unicode(20))

@listens_for(Resource, 'before_insert')
@listens_for(Resource, 'before_update')
def normalize_resource(mapper, connect, target):
    """
    Normalizes a resource before it is saved to the database.
    This ensures that the resource's categories are properly
    denormalized in the category_text and that the resource's
    URL starts with some sort of http:// or https:// prefix
    if it has been provided.

    Args:
        mapper: The mapper that is the target of the event.
        connection: The database connection being used.
        target: The resource being persisted to the database.
    """
    # If we have categories, denormalize the category text
    # so that we can use it in text-based searching
    if target.categories:
        target.category_text = ', '.join(c.name + ' ' + (c.keywords or '') for c in target.categories)
    else:
        target.category_text = ''

    # If we have a URL and it doesn't start with http://
    # or https://, append http:// to the beginning
    if target.url and \
        not target.url.isspace() and \
        not target.url.lower().strip().startswith(('http://', 'https://')):
        target.url = 'http://' + target.url.strip()

@listens_for(Review, 'before_insert')
@listens_for(Review, 'before_update')
def normalize_review(mapper, connect, target):
    """
    Normalizes a review before it is saved to the database.
    This ensures that the composite rating is properly
    calculated.

    Args:
        mapper: The mapper that is the target of the event.
        connection: The database connection being used.
        target: The resource being persisted to the database.
    """
    composite_rating = 0.0
    ratings_count = 0.0

    if target.rating is not None and target.rating > 0:
        composite_rating += target.rating
        ratings_count += 1.0

    if target.staff_rating is not None and target.staff_rating > 0:
        composite_rating += target.staff_rating
        ratings_count += 1.0

    if target.intake_rating is not None and target.intake_rating > 0:
        composite_rating += target.intake_rating
        ratings_count += 1.0

    # Create an average based on the number of submitted ratings
    # and store that in composite_rating
    if ratings_count > 0.0:
        target.composite_rating = composite_rating / ratings_count
    else:
        target.composite_rating = None
