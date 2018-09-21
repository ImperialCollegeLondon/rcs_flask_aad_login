# rcs-flask-aad-login
Python package to allow Flask web applications to single sign-on through IC's Azure Active Directory

Provides a package that wraps the necessary extensions and attribute labels to add single sign on 
through the Imperial College Microsoft Azure Active Directory to a Flask application.

## Example
A simple example Flask app (which of course won't work until you've set up your AAD app):

```python
from flask import Flask
from flask_login import login_required
import rcs_flask_aad_login

app = Flask(__name__)
app.config.update({
    # Standard Flask SECRET_KEY.  Must be set or example will fail.
    # python -c 'import os; print(os.urandom(24).encode("hex"))'
    'SECRET_KEY': 'notsecret',
    # Insert your own app's metadata url here.
    'SAML_METADATA_URL': 'https://login.microsoftonline.com/2b897507-ee8c-4575-830b-4f8267c3d307/federationmetadata/2007-06/federationmetadata.xml?appid=a301bd20-6119-40ea-a6e1-4d82f14b5d0e',
})

rcs_flask_aad_login.init_app(app)

@app.route('/')
def index():
    return 'Public info'
    
def priv():
    return """\
secrets<br>
username: %s<br>
username w domain: %s<br>
givenname: %s<br>
surname: %s<br>
displayname: %s<br>
emailaddress: %s""" % (current_user.username, current_user.username_domain,
    current_user.givenname, current_user.surname, current_user.displayname,
    current_user.emailaddress)

if __name__ == '__main__':
    app.run(ssl_context='adhoc', port=5000, debug=True)
```
To run this in the flask development server you would need to run it as
`python app.py`, rather than
using the `FLASK_APP flask run` method, otherwise the SSL context doesn't load.  AAD
requires https for the Reply-URL.

With this app the `/` route is unprotected but the `/priv` route is only
available to logged in users.  If someone tries to access `/priv` who is not
signed on, the app will redirect them to the login URL, which redirects them to
the AAD single sign on.  After authentication they are redirected back to the
page they were trying to access.  If they have a valid SSO session with AAD this
process is seamless.

## Installation
```python
pip install git+git://github.com/ImperialCollegeLondon/rcs_flask_aad_login
```

## Setup
```python
from flask import Flask
from flask_login import login_required
import rcs_flask_aad_login

app = Flask(__name__)
app.config.update({
  'SAML_METADATA_URL': 'https://login.microsoftonline.com/2b897507-ee8c-4575-830b-4f8267c3d307/federationmetadata/2007-06/federationmetadata.xml?appid=a301bd20-6119-40ea-a6e1-4d82f14b5d0e',
  'SECRET_KEY': '',
  
rcs_flask_aad_login.init_app(app)
```
The `SAML_METADATA_URL` parameter is what MS Azure calls the App Federation Metadata URL.
For our app it's found in the MS Azure setup pages at:
`Home->imperial college london->Enterprise applications->All applications->RCS Self-Service Portal DEV->Single sign-on`
under '4. SAML Signing Certificate'.  On the same page you must fill in
'Indentifier (Entity ID)' to `https://<yourappsbaseurl>/saml/metadata/`,
and 'Reply URL (Assertion Consumer Service URL)' to `https://<yourappsbaseurl>/saml/acs/`.
The latter in particular must be a `https` URL.  Save the page and run `Test SAML Settings`
if desired.

Annoyingly there's another page which must be updated.  It is at
`Home->Imperial College London - App registrations->RCS Self-Service Portal DEV->Settings->Properties`.
Set the Home Page URL to the base URL of your app.  This is checked when your
app initiates the sign-on.  If it's wrong you'll get errors like
`Application with identifier 'http://localhost:8080/saml/metadata/' was not found in the directory...`,
where `localhost:8080` is the page of your app you're initiating the SSO from.

Now decorate routes with `@login_required`.  When a user accesses the route
they will be redirected through to the AAD single sign on and then
redirected back to the page they were requesting.  You can provide a login
link by using the URL `url_for('login')` provides, and a logout link
from `url_for('logout')`.  The logout link will log the user out of the 
Flask-login session, but not out of the AAD SSO session, which will
expire according to whatever settings it and the user have set. If
the user attempts to log in while their SSO session is valid, they will
be signed in and returned to the desired page fairly seamlessly.

## Accessing user data
When a user authenticates a Flask-login `User` object is created and
populated with data from the IC AAD entry.  The current parameters are

* `username` - this is the bare college username.
* `username_domain` - this is the college username with '@ic.ac.uk' appended.
* `givenname` - the forename(s).
* `surname` - the surname.
* `displayname` - the college entry for the full name, usually 'Surname, Forename(s)'.
* `emailaddress` - email address

The `current_user` variable (`from flask_login import current_user`) holds the
logged in `User` object or `None`.  Access the parameters as normal: e.g.
`current_user.username`.

## Behind the scenes
The package uses the [Flask-login](https://flask-login.readthedocs.io/en/latest/) and
[Flask-SAML](https://flask-saml.readthedocs.io/en/latest/) packages.  Flask-login
provides a session based login system; decorate private routes in the app with
`@login_required`. When an unauthorised user accesses such a route we send them to
the Flask-SAML provided login route (`url_for('login'`), setting a parameter so
that after the SSO sign on they will be redirected back to the page they were
trying to access.

