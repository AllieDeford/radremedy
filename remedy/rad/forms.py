"""
forms.py

Contains general-purpose forms, such as those for contacting
the RAD team about resource corrections, reviewing resources,
and changing user settings.
"""

from flask.ext.login import current_user
from flask_wtf import Form

from wtforms import StringField, TextField, TextAreaField, SubmitField, ValidationError, \
    HiddenField, SelectField, RadioField, DecimalField, IntegerField
from wtforms.widgets import HiddenInput
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, Email, Optional, NumberRange

from .models import Resource, User

class ContactForm(Form):
    """
    A form for submitting a correction to a resource.

    Fields on the form:
        message
    """
    message = TextAreaField("Message", validators=[
        DataRequired("A message is required.")
    ])

    submit = SubmitField("Send")


class ReviewForm(Form):
    """
    A form for submitting resource reviews.

    Fields on the form:
        rating
        intake_rating
        staff_rating
        comments
        provider (Hidden)
    """
    rating = RadioField('Provider Experience', choices=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], validators=[
        DataRequired()
    ])

    intake_rating = RadioField('Intake Experience', default='0', choices=[
        ('0', 'N/A'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], validators=[
        DataRequired()
    ])

    staff_rating = RadioField('Staff Experience', default='0', choices=[
        ('0', 'N/A'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], validators=[
        DataRequired()
    ])

    # this is the text field with more details
    comments = TextAreaField('Comments', validators=[
        DataRequired(), 
        Length(1, 2000)
    ])

    # the Resource been reviewed, this field is hidden
    # because we set in the templates, the user
    # doesn't actually have to select this
    provider = HiddenField(validators=[
        DataRequired()
    ])

    submit = SubmitField('Submit Review')

    def validate_provider(self, field):
        """
        Validates that the provider exists in the database.
        """
        if Resource.query.get(field.data) is None:
            raise ValidationError('No provider found.')


class UserSettingsForm(Form):
    """
    A form for submitting resource reviews.

    Fields on the form:
        email
        display_name
        default_location
        default_latitude (Hidden)
        default_longitude (Hidden)
    """
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(), 
        Length(1, 70)
    ])

    display_name = StringField('Displayed Name', validators=[
        DataRequired(), 
        Length(2, 100)
    ])

    default_location = StringField('Default Location', validators=[
        Optional(), 
        Length(0, 500)
    ])
    
    default_latitude = DecimalField(widget=HiddenInput(), validators=[
        Optional()
    ])
    
    default_longitude = DecimalField(widget=HiddenInput(), validators=[
        Optional()
    ])

    submit = SubmitField('Save')

    def validate_email(self, field):
        """
        Validates that the provided email is unique.
        """
        existing_user = User.query. \
            filter(User.email == field.data). \
            filter(User.id != current_user.id). \
            first()

        if existing_user:
            raise ValidationError('A user already exists in the database with that email.')

class NewProviderForm(Form):
    provider_name = StringField('Provider Name', validators=[DataRequired()])
    organization_name = StringField('Organization Name', validators=[Optional()])
    description = TextAreaField('Description', 
        description="This is a brief description of an organization, such as a mission statement or similar. If this is not obvious when you are trying to fill in the blanks, do not worry about it and leave it blank.", 
        validators=[
        Optional(), 
        Length(1, 2000)
    ])
    npi = IntegerField('NPI Number', 
        description="Write a better description of NPI number", 
        validators=[
        Optional(), 
        NumberRange(1000000000, 9999999999)])



