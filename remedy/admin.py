"""
admin.py

Contains functionality for providing administrative interfaces
to items in the system.
"""
from admin_views import *

import os
import os.path as op

from flask.ext.admin import Admin
from flask.ext.admin.menu import MenuLink

from remedy.rad.models import db

admin = Admin(name='RAD Remedy Admin',
    index_view=homeview.AdminHomeView())
admin.add_view(resourceview.ResourceView(db.session,
    category='Resource',
    name='All',
    endpoint='resourceview',))
admin.add_view(resourceview.ResourceRequiringGeocodingView(db.session,
    category='Resource',
    name='Needing Geocoding', 
    endpoint='geocode-resourceview'))
admin.add_view(resourceview.ResourceRequiringCategoriesView(db.session,
    category='Resource',
    name='Needing Categorization', 
    endpoint='category-resourceview'))
admin.add_view(resourceview.ResourceRequiringNpiView(db.session,
    category='Resource',
    name='Needing NPI', 
    endpoint='npi-resourceview'))

# Calculate our path for imports, create it if it doesn't exist
resource_path = op.join(op.dirname(__file__), 'imports', 'resources')

if not op.exists(resource_path):
    os.makedirs(resource_path)

admin.add_view(resourceimportview.ResourceImportFilesView(resource_path,
    None,
    category='Resource',
    name='CSV Import'))
admin.add_view(resourceimportview.ResourceImportView(db.session, resource_path))

admin.add_view(resourceview.ResourceCategoryAssignView(db.session))

admin.add_view(userview.UserView(db.session, 
    category='User',
    name='Users',
    endpoint='userview'))
admin.add_view(loginhistoryview.LoginHistoryView(db.session, 
    category='User',
    name='Login History',
    endpoint='loginhistoryview'))

admin.add_view(categoryview.CategoryView(db.session, endpoint='categoryview'))
admin.add_view(categoryview.CategoryMergeView(db.session))
admin.add_view(reviewview.ReviewView(db.session, endpoint='reviewview'))

# Add a link back to the main site
admin.add_link(MenuLink(name="Main Site", url='/'))
