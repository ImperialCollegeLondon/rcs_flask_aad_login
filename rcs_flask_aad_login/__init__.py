from __future__ import absolute_import
from flask import url_for, session, current_app, request, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import flask_saml
import datetime

name = "rcs_flask_aad_login"

# Configuration:
# in app.config
#   you MUST have a good SECRET_KEY (as usual)
#   set SAML_METADATA_URL to the metadata URL your SSO provides.
#     MS Azure calls this App Federation Metadata URL

# In the SSO you want the Reply-URL to be /saml/acs, must be https.
#   the App-ID-URL is /saml/metadata.
#   

# A word on sessions.  The Flask-Login package is supposed to provide a
# session that by default, lasts only as long as the browsing session.  So if
# a user closes their browser the session goes away.  THIS DOES NOT APPEAR TO
# BE THE CASE, with Chrome when an option like "Continue where I left off"
# is set.  The session persists forever!
# The downside to this is that if the user logs in there is potentially
# nothing to check their continued legitimacy -- they never get further than
# the Flask-Login session authenticating them so never get to the SSO.
#
# The SSO session is hovering in the background.  If the user logs out of the
# Flask-Login session (or is timed out) then they are redirected to the SSO
# login.  This might well (depending on its settings and the settings of the
# user) log them in without further interaction -- no password.  This is the
# point of SSO after all!  This redirection / login / redirection back
# to the original page is very quick.
#
# We want to defer as much as possible to the SSO provider, so we want
# to create Flask-Login sessions that last as little time as possible.
# Therefore we have to, er, set the session cookie to be permanent and
# then define permanent as, say, 1 day.


class User(UserMixin):
    '''Our user object'''

    def __init__(self, session):
        saml = session['saml']
        self.id = saml['subject']
        attribs = saml['attributes']
        self.username_domain = attribs[u'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name'][0]
        self.username = self.username_domain
        m = self.username.find('@ic.ac.uk')
        if m > 0:
            self.username = self.username[:m]
        self.givenname = attribs.get(u'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname', (None,))[0]
        self.surname = attribs.get(u'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname', (None,))[0]
        self.displayname = attribs.get(u'http://schemas.microsoft.com/identity/claims/displayname', (None,))[0]
        self.emailaddress = attribs.get(u'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress', (None,))[0]
        self.department = attribs.get(u'department', (None,))[0]
        self.status = attribs.get(u'status', (None,))[0]
        self.users_group = attribs.get(u'users_group', (None,))[0]

def init_app(app):
    '''Call this once the flask app is created'''

    # Workaround for Chrome not expiring browser sessions
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
    
    with app.app_context():
        login_manager = LoginManager(app)
        saml = flask_saml.FlaskSAML(app)

    @app.login_manager.user_loader
    def load_user(user_id):
        '''Takes unicode ID and returns a User object.
        We're just going to load data from the SAML session if
        it's there.  Otherwise, return None'''
        if 'saml' in session:
            if 'subject' in session['saml'] and user_id == session['saml']['subject']:
                return User(session)
        return None

    @flask_saml.saml_authenticated.connect_via(app)
    def on_saml_authenticated(sender, subject, attributes, auth):
        login_user(load_user(subject))
        # Permanent now defined to be 1 day.  Workaround for Chrome.
        session.permanent = True

    @flask_saml.saml_log_out.connect_via(app)
    def on_saml_logout(sender):
        logout_user()

    def handle_unauthed():
        return redirect(url_for('login', next=request.url))
        
    login_manager.unauthorized_handler(handle_unauthed)

    @app.before_first_request
    def before_first():
        login_manager.login_view = url_for('login')
        
