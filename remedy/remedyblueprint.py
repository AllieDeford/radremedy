"""
remedyblueprint.py

Contains the basic routes for the application and
helper methods employed by those routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, send_from_directory
from flask.ext.login import login_required, current_user
from werkzeug.contrib.cache import SimpleCache
from functools import wraps

from pagination import Pagination

from .remedy_utils import get_ip
from .email_utils import send_resource_error
from rad.models import Resource, Review, Category, db
from rad.forms import ContactForm, ReviewForm, UserSettingsForm
import rad.resourceservice
import rad.reviewservice
import rad.searchutils

import re
from jinja2 import evalcontextfilter, Markup, escape

import os 

PER_PAGE = 20

# Set up a basic in-memory cache
cache = SimpleCache()

def flash_errors(form):
    """
    Flashes errors for the provided form.

    Args:
        form: The form for which errors will be displayed.
    """
    for field, errors in form.errors.items():
        for error in errors:
            flash("%s field - %s" % (
                getattr(form, field).label.text,
                error
            ))


def get_paged_data(data, page, page_size=PER_PAGE):
    """
    Filters down a list of data to a specific page and returns
    the total count and the paged subset.  If there is no data
    provided, and a page other than the first is specified, the
    request will abort with 404 Not Found.

    Args:
        data: The data to filter down to a paged subset.
        page: The page number to use, starting with 1. If a value
            less than 1 is provided, the request will abort
            with 400 Bad Request.
        page_size: The page size to use, defaulted to PER_PAGE.

    Returns
        The total number of items in the list and the paged
        subset, in that order.
    """
    # Sanity check for page number
    if page < 1:
        abort(400)

    # Now make sure we're not paging too far
    if not data and page != 1:
        abort(404)

    start_index = (page-1)*page_size

    return len(data), data[start_index:start_index + page_size]


def url_for_other_page(page):
    """
    Generates a URL for the same page, with the only difference
    being that a new "page" query string value is updated
    with the provided page number.

    Args:
        page: The new page number to use.

    Returns:
        The URL for the current page with a new page number.
    """
    args = dict(request.view_args.items() + request.args.to_dict().items())
    args['page'] = page
    return url_for(request.endpoint, **args)


def latest_added(n):
    """
    Returns the latest n resources added to the database.
    Will use cached results with the default timeout.

    Args:
        n: The number of resources to return.

    Returns:
        A list of resources from the database.
    """
    # Try to get it from cache first
    added = cache.get('latest-added')

    if added is None:
        # Not in cache - load it up and store it
        added = rad.resourceservice.search(db, limit=n,
            search_params=dict(visible=True),
            order_by='date_created desc')
        cache.set('latest-added', added)

    return added


def latest_reviews(n):
    """
    Returns the latest n reviews added to the database.
    Will use cached results with the default timeout.

    Args:
        n: The number of reviews to return.

    Returns:
        A list of reviews from the database.
    """
    # Try to get it from cache first
    reviews = cache.get('latest-reviewed')

    if reviews is None:
        # Not in cache - load it up and store it
        # Get reviews that aren't superseded,
        # and ensure that only visible reviews are included
        reviews = db.session.query(Review). \
            join(Review.resource). \
            filter(Review.is_old_review == False). \
            filter(Review.visible == True). \
            filter(Resource.visible == True). \
            order_by(Review.date_created.desc())

        reviews = reviews.limit(n).all()
        cache.set('latest-reviewed', reviews)

    return reviews


def active_categories():
    """
    Returns all active categories in the database.

    Returns:
        A list of categories from the database.
    """
    return Category.query.filter(Category.visible == True).order_by(Category.name).all()


def resource_with_id(id):
    """
    Returns a resource from the database or aborts with a
    404 Not Found if it was not found.

    Args:
        id: The ID of the resource to retrieve.

    Returns:
        The specified resource.
    """
    result = rad.resourceservice.search(db, limit=1, search_params=dict(id=id))

    if result:
        return result[0]
    else:
        abort(404)


def resource_redirect(id):
    """
    Returns a redirection action to the specified resource.

    Args:
        id: The ID of the resource to redirect to.

    Returns:
        The redirection action.
    """
    return redirect(url_for('remedy.resource', resource_id=id))


def under_construction(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return render_template('under-construction.html')
    return decorated_function

remedy = Blueprint('remedy', __name__)


@remedy.context_processor
def context_override():
    """
    Overrides the behavior of url_for to include cache-busting
    timestamps for static files.
    
    Based on http://flask.pocoo.org/snippets/40/
    """
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    """
    Overrides the url_for behavior to include a
    timestamped "q" parameter to prevent caching of
    static resources.

    Based on http://flask.pocoo.org/snippets/40/

    Returns:
        The URL for the specified file at the indicated endpoint.
    """
    # Only do this for static files
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            # Get the full path to the file and look up the last-modified
            # time.
            file_path = os.path.join(remedy.root_path, 'static', filename)
            values['q'] = int(os.stat(file_path).st_mtime)

    return url_for(endpoint, **values)


@remedy.app_errorhandler(404)
def page_not_found(err):
    """
    Displays a 404 error page.

    Args:
        err: The encountered error.    

    Returns:
        A templated 404 page (via 404.html).
    """
    return render_template('404.html'), 404


@remedy.app_errorhandler(500)
def server_error(err):
    """
    Displays a 500 server error page.

    Args:
        err: The encountered error.

    Returns:
        A templated 500 page (via 500.html).
        This template is provided with the following variables:
            current_user: The currently-logged in user.        
            error_info: The encountered error.
    """
    return render_template('500.html', 
        current_user=current_user,
        error_info=err), 500

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@remedy.app_template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    """
    Splits the provided string into paragraph tags based on the
    line breaks within it and returns the escaped result.

    Args:
        eval_ctx: The context used for filter evaluation.
        value: The string to process.

    Returns:
        The processed, escaped string.
    """
    # We need to surround each split paragraph with a <p> tag,
    # because otherwise Jinja ignores the result. See the PR for #254.
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

@remedy.route('/favicon.ico')
def favicon():
    """
    Returns the favicon.

    Returns:
        The favicon at static/img/favicon.ico with
        the appropriate MIME type.
    """
    return send_from_directory(
        os.path.join(remedy.root_path, 'static', 'img'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon')


@remedy.route('/')
def index():
    """
    Displays the front page.

    Returns:
        A templated front page (via index.html).
        This template is provided with the following variables:
            recently_added: The most recently-added visible
                resources.
    """
    # Latest items should be a multiple of 3 because
    # we show at most 3 items in a row
    return render_template('index.html', 
        recently_added=latest_added(12))


@remedy.route('/resource/')
def redirect_home():
    return redirect(url_for('.index'))


@remedy.route('/resource/<resource_id>/')
def resource(resource_id):
    """
    Gets information about a single resource.

    Args:
        resource_id: The ID of the resource to show.

    Returns:
        A templated resource information page (via provider.html).
        This template is provided with the following variables:
            provider: The specific provider to display.
            reviews: The top-level reviews for this resource.
                Visible old reviews will be stored as an
                old_reviews_filtered field on each review.
    """
    # Get the resource and all visible top-level reviews
    resource = resource_with_id(resource_id)

    reviews = resource.reviews. \
        filter(Review.is_old_review==False). \
        filter(Review.visible == True). \
        all()

    # Ensure the filtered set of old reviews is
    # available on each review we're displaying
    for rev in reviews:
        # Filter down old to only the visible ones,
        # and add appropriate sorting
        rev.old_reviews_filtered = rev.old_reviews. \
            filter(Review.visible==True). \
            order_by(Review.date_created.desc()) \
            .all()

    return render_template('provider.html', 
        provider=resource,
        reviews=reviews)


@remedy.route('/find-provider/', defaults={'page': 1})
@remedy.route('/find-provider/page/<int:page>')
def resource_search(page):
    """
    Searches for resources that match the provided options
    and displays a page of search results.

    Args:
        search: The text to search on.
        id: The specific ID to filter on.
        addr: The text to display in the "Address" field.
            Not used for filtering.
        dist: The distance, in miles, to use for proximity-based searching.
        lat: The latitude to use for proximity-based searching.
        long: The longitude to use for proximity-based searching.
        page: The current page number. Defaults to 1.
        autofill: If set, will attempt to automatically fill the proximity-based
            search fields with the current user's default location, defaulting
            to a distance of 25. 

    Returns:
        A templated set of search results (via find-provider.html). This
        template is provided with the following variables:
            pagination: The paging information to use.
            providers: The page of providers to display.
            search_params: The dictionary of normalized searching options.
            categories: A list of all active categories.
    """

    # Start building out the search parameters.
    # At a minimum, we want to ensure that we only show visible resources.
    search_params = dict(visible=True)

    # If we're auto-filling, and the user is logged in, fill in their
    # location information
    try:
        if request.args.get('autofill', default=0, type=int) and \
            current_user.is_authenticated():
        
            rad.searchutils.add_string(search_params, 'addr', current_user.default_location)
            rad.searchutils.add_float(search_params, 'lat', current_user.default_latitude)
            rad.searchutils.add_float(search_params, 'long', current_user.default_longitude)
            search_params['dist'] = 25
    except Exception, e:
        pass

    # Search string
    rad.searchutils.add_string(search_params, 'search', request.args.get('search'))

    # ID - minimum value of 1
    rad.searchutils.add_int(search_params, 'id', request.args.get('id'), min_value=1)

    # Address string - just used for display
    rad.searchutils.add_string(search_params, 'addr', request.args.get('addr'))

    # Distance - minimum value of -1 (anywhere), maximum value of 500 (miles)
    rad.searchutils.add_float(search_params, 'dist', request.args.get('dist'), min_value=-1, max_value=500)

    # Latitude/longitude - no min/max values
    rad.searchutils.add_float(search_params, 'lat', request.args.get('lat'))
    rad.searchutils.add_float(search_params, 'long', request.args.get('long'))

    # Normalize our location-based searching params -
    # if dist/lat/long is missing, make sure address/lat/long is cleared
    # (but not dist, since we want to preserve "Anywhere" selections)
    if 'addr' not in search_params or \
        'dist' not in search_params or \
        search_params['dist'] <= 0 or \
        'lat' not in search_params or \
        'long' not in search_params:
        search_params.pop('addr', None)
        search_params.pop('lat', None)
        search_params.pop('long', None)

    # Issue #229 - If we don't have any distance specified,
    # default to 25 miles so that we'll have a default distance
    # in the event that they subsequently fill in an address
    if 'dist' not in search_params:
        search_params['dist'] = 25

    # Categories - this is a MultiDict so we need to use GetList
    rad.searchutils.add_int_set(search_params, 'categories', request.args.getlist('categories'))

    # All right - time to search!
    providers = rad.resourceservice.search(db, search_params=search_params)

    # Load up available categories
    categories = active_categories()

    # Set up our pagination and render out the template.
    count, paged_providers = get_paged_data(providers, page)
    pagination = Pagination(page, PER_PAGE, count)

    return render_template('find-provider.html',
        pagination=pagination,
        providers=paged_providers,
        search_params=search_params,
        categories=categories
    )


@remedy.route('/review/<resource_id>/', methods=['GET','POST'])
@login_required
def new_review(resource_id):
    """
    Allows users to submit a new review.

    Args:
        resource_id: The ID of the resource to review.

    Returns:
        When accessed via GET, a form for submitting reviews (via add-review.html).
        This template is provided with the following variables:
            provider: The specific provider being reviewd.
            has_existing_review: A boolean indicating if the
                current user has already left a review for
                this resource.
            form: A ReviewForm instance for submitting a
                new review.
        When accessed via POST, a redirection action to the associated resource
        after the review has been successfully submitted.
    """
    # Get the form - prefill the resource_id with what's
    # been provided via query string.
    form = ReviewForm(request.form)
    form.provider.data = resource_id

    # Get the associated resource
    resource = resource_with_id(resource_id)

    # See if we have other existing reviews left by this user
    existing_reviews = resource.reviews. \
        filter(Review.user_id == current_user.id). \
        all()

    if len(existing_reviews) > 0:
        has_existing_review = True
    else:
        has_existing_review = False

    # Only bother trying to handle the form if we have a submission
    if request.method == 'POST':
        # See if the form's valid
        if form.validate_on_submit():

            # Set up the new review
            new_r = Review(int(form.rating.data), 
                form.comments.data,
                resource, 
                user=current_user)

            # Set the IP
            new_r.ip = get_ip()

            # Add optional intake/staff ratings
            if int(form.intake_rating.data) > 0:
                new_r.intake_rating = int(form.intake_rating.data)
            else:
                new_r.intake_rating = None

            if int(form.staff_rating.data) > 0:
                new_r.staff_rating = int(form.staff_rating.data)
            else:
                new_r.staff_rating = None

            # Add the review and flush the DB to get the new review ID
            db.session.add(new_r)
            db.session.flush()

            # If we have other existing reviews, mark them as old
            if len(existing_reviews) > 0:
                for old_review in existing_reviews:
                    old_review.is_old_review = True
                    old_review.new_review_id = new_r.id

            db.session.commit()

            # Redirect the user to the resource
            flash('Review submitted!')

            return resource_redirect(new_r.resource_id)
        else:
            # Not valid - flash errors
            flash_errors(form)

    # We'll hit this if the form is invalid or we're
    # doing a simple GET.
    return render_template('add-review.html', 
        provider=resource,
        has_existing_review=has_existing_review,
        form=form)


@remedy.route('/delete-review/<review_id>', methods=['GET','POST'])
@login_required
def delete_review(review_id):
    """
    Handles the deletion of new reviews.

    Args:
        review_id: The ID of the review to delete.

    Returns:
        When accessed via GET, a form to confirm deletion (via find-provider.html). 
        This template is provided with the following variables:
            review: The review being deleted.
        When accessed via POST, a redirection action to the associated resource
        after the review has been deleted.
    """
    review = Review.query.filter(Review.id == review_id).first()

    # Make sure we got one
    if review is None:
        abort(404)

    # Make sure we're an admin or the person who actually submitted it
    if not current_user.admin and current_user.id != review.user_id:
        flash('You do not have permission to delete this review.')
        return resource_redirect(review.resource_id)

    if request.method == 'GET':
        # Return the view for deleting reviews
        return render_template('delete-review.html',
            review = review)
    else:
        rad.reviewservice.delete(db.session, review)
        flash('Review deleted.')
        return resource_redirect(review.resource_id)


@remedy.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Gets the settings for the current user.
    On a GET request it displays the user's information and a form for
        changing profile options.
    On a POST request, it submits the form, after checking for errors.

    Returns:
        The user's settings (via settings.html).
        This template is provided with the following variables:
            form: The WTForm to use for changing profile options.
    """
    # Prefill with existing user settings
    form = UserSettingsForm(request.form, current_user)

    if request.method == 'GET':
        return render_template('settings.html',
            form = form)
    else:
        if form.validate_on_submit():

            # Update the user's settings
            current_user.email = form.email.data
            current_user.display_name = form.display_name.data

            current_user.default_location = form.default_location.data
            current_user.default_latitude = form.default_latitude.data
            current_user.default_longitude = form.default_longitude.data

            db.session.commit()

            flash('Your profile has been updated!')

        else:
            # Flash any errors
            flash_errors(form)

        return render_template('settings.html',
            form = form)


@remedy.route('/about/')
def about():
    return render_template('about.html')

@remedy.route('/get-involved/')
def get_involved():
    return render_template('get-involved.html')

@remedy.route('/how-to-use/')
@under_construction
def how_to_use():
    pass 

@remedy.route('/contact/')
def contact():
    return render_template('contact.html') 

@remedy.route('/projects/')
def projects():
    return render_template('projects.html')

@remedy.route('/donate/')
def donate():
    return render_template('donate.html') 

@remedy.route('/about-the-beta/')
def about_the_beta():
    return render_template('about-the-beta.html') 

@remedy.route('/disclaimer/')
def disclaimer():
    return render_template('disclaimer.html') 

@remedy.route('/user-agreement/')
def user_agreement():
    return render_template('user-agreement.html') 

@remedy.route('/privacy-policy/')
def privacy_policy():
    return render_template('privacy-policy.html') 

@remedy.route('/terms-of-service/')
def terms_of_service():
    return render_template('terms-of-service.html') 

@remedy.route('/submit-error/<resource_id>/', methods=['GET', 'POST'])
@login_required
def submit_error(resource_id) :
    """
    Gets error submission form for a given resource.
    On a GET request it displays the form. 
    On a POST request, it submits the form, after checking for errors. 

    Args:
        resource_id: The ID of the resource to report an error on.

    Returns:
        A form for reporting errors (via error.html).
        This template is provided with the following variables:
            resource: The specific resource to report an error on.
            form: the WTForm to use
    """
    form = ContactForm()
    resource = resource_with_id(resource_id)
 
    if request.method == 'POST':
        if form.validate() == False:
            flash('Message field is required.')
            return render_template('error.html', resource=resource, form=form)
        else:
            send_resource_error(resource, form.message.data)
            return render_template('error-submitted.html')

    elif request.method == 'GET':
        return render_template('error.html', resource=resource, form=form)


