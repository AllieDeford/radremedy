"""
forms.py

Contains general-purpose forms, such as those for contacting
the RAD team about resource corrections, reviewing resources,
and changing user settings.
"""

from flask.ext.login import current_user
from flask_wtf import Form

from wtforms import StringField, TextField, TextAreaField, SubmitField, ValidationError, \
    HiddenField, SelectField, RadioField, DecimalField, IntegerField, SelectMultipleField, widgets
from wtforms.widgets import HiddenInput
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, Email, Optional, NumberRange, URL
from wtforms.fields.html5 import URLField, TelField

from .models import Resource, User

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

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
    street_address = StringField('Street Address', 
        description="Formatting: Street # Street Suite # (ex. 5555 N. Main St #2)", 
        validators=[
        Optional()])
    city = StringField('City', 
        validators=[Optional()])
    state = SelectField('State', choices=[('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'), ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'), ('FL', 'Florida'), ('GA', 'Georgia'), 
                ('HI', 'Hawaii'), ('ID', 'Idaho'), ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'), 
                ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'), ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), 
                ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'), ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'), 
                ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'), ('VA', 'Virgina'), ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'), ('WY', 'Wyoming')])
    zipcode = StringField('Zip Code', 
        validators=[
        Optional(), 
        Length(5,5)])
    country = StringField('Country', 
        validators=[
        Optional()])
    phone_number = TelField('Phone Number', 
        validators=[
        Optional()])
    fax_number = TelField('Fax Number', 
        validators=[
        Optional()])
    email = StringField('Email', validators=[
        Optional(), 
        Email(), 
        Length(1, 70)
    ])
    website = URLField('Website', validators=[
        Optional(), 
        URL()
    ])
    office_hours = TextAreaField('Office Hours', 
        description="Specific Formatting: Days: Mon, Tues, Wed, Thurs, Fri, Sat, Sun; Hours: 9 am - 4:30 pm; Extra Specifics: (Walk-ins) (Long Formatting Example: Mon, Tues, Wed - 9 am - 4:30 pm (By Appointment Only); Thurs-Sat - 10:30 am - 7 pm (Appointments and Walk-ins); Sun - Closed)", 
        validators=[Optional()])

    catagories = MultiCheckboxField('Catagories', choices=[
        ("Medical Services", "Medical Services (Specify below if possible)"), 
        ("Primary Care", "Primary Care"),
        ("Masculinizing Hormones", "Masculinizing Hormones"),
        ("Feminizing Hormones", "Feminizing Hormones"),
        ("Puberty Blockers", "Puberty Blockers"),
        ("Endocrinology", "Endocrinology"),
        ("Internal Medicine", "Internal Medicine"),
        ("Pediatrics", "Pediatrics"),
        ("Obstetrics and Gynecology", "Obstetrics and Gynecology"),
        ("Reproductive Health", "Reproductive Health"),
        ("Transition-Related Surgery", "Transition-Related Surgery (Specify below if possible)"),
        ("HIV/STI Services", "HIV/STI Services"),
        ("Vision", "Vision"),
        ("Dental", "Dental"),
        ("Mental Health Services", "Mental Health Services (Specify below if possible)"),
        ("Individual Therapy", "Individual Therapy"),
        ("Group Therapy", "Group Therapy"),
        ("Family Therapy", "Family Therapy"),
        ("Child Therapy", "Child Therapy"),
        ("Adolescent Therapy", "Adolescent Therapy"),
        ("Psychiatry", "Psychiatry"),
        ("Addiction and Recovery", "Addiction and Recovery"),
        ("Support Groups", "Support Groups"),
        ("Social Groups", "Social Groups"),
        ("Social Services", "Social Services (Specify below if possible)"),
        ("Advocacy Organization", "Advocacy Organization"),
        ("Housing Services", "Housing Services"),
        ("Legal Services", "Legal Services"),
        ("Transition-Related Legal Services", "Transition-Related Legal Services"),
        ("Spiritual Resource", "Spiritual Resource"),
        ("Electrolysis/Hair Removal", "Electrolysis/Hair Removal"),
        ("Sexual Assault/Intimate Partner Violence Services", "Sexual Assault/Intimate Partner Violence Services"),
        ("Complementary and Alternative Medicine", "Complementary and Alternative Medicine"),
        ("Acupuncture/Acupressure", "Acupuncture/Acupressure"),
        ("Yoga", "Yoga"),
        ("Massage", "Massage"),
        ("Voice Training", "Voice Training")
        ], 
        validators=[Optional()])
    other = TextAreaField('Other', 
        description="We will eventually be expanding the database to have more information and it would be helpful to have all known information about this provider available. Please list anything that is provided that did not fit into the above questions, such as sliding scale, insurance accepted, other languages spoken, etc. *Formatting: Please separate information with a semi-colon (;) (ex. Sliding Fee; Spanish; Provider does not require a note from a therapist for HRT; Not accepting new patients)*", 
        validators=[
        Optional(), 
        Length(1, 2000)
    ])

    
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

    submit = SubmitField("Submit")



