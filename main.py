"""
    Automated Rental Property Analysis
    https://github.com/earlvanze/Paragon-MLS-API-Interface

    ~~~~~~~~~~~~~~
    Google OAuth Flask functionality from
    http://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example_with_refresh.html

"""

from __future__ import print_function
import os
import requests
import json
from functions import *
from time import time
from requests_oauthlib import OAuth2Session
from flask import Flask, flash, render_template, redirect, url_for, session, request, jsonify, send_file
from pprint import pformat

args['dev_mode'] = False

# This information is obtained upon registration of a new Google OAuth
# application at https://code.google.com/apis/console
if args['dev_mode']:
    redirect_uri = 'https://localhost:8080/callback'						# for testing on local computer or Google App Engine
else:
    #redirect_uri = 'https://api-project-32857849252.appspot.com/callback'	# for live deployment in Google App Engine
    redirect_uri = 'https://rentals.earlyrewirement.com/callback'				# for live deployment with subdomain in Google App Engine

client_secret_filename = "client_secret.json"
with open(client_secret_filename, 'r') as file:
    json_repr = file.read()
    data = json.loads(json_repr)
    client_id = DictQuery(data).get("web/client_id")
    client_secret = DictQuery(data).get("web/client_secret")


# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://accounts.google.com/o/oauth2/token"
refresh_url = token_url # True for Google but not all providers.
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


# Flask App configuration
app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)


#@app.route("/<string:gsheet_id>/<string:mls_number>/")
#parse_form(gsheet_id, range_name, system_id, mls_id = None, mls_list = None)


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route("/app", methods=['GET', 'POST'])
def analyze():
    if 'oauth_token' in session:
        automatic_refresh()
        form = ReusableForm(request.form)
        print (form.errors)

        if request.method == 'POST':
            mls_list = request.form['mls_list']
            gsheet_id = request.form['gsheet_id']
            range_name = request.form['range_name']
            mls_id = request.form['mls_id']
            system_id = request.form['system_id']

            if form.validate():
                message = parse_form(gsheet_id, range_name, system_id, mls_id, mls_list)
                flash(message)
                return jsonify(data={'message': message})
            else:
                flash('Error: Some required fields are missing.')
                flash(form.errors)
                return jsonify(data={'message': form.errors})
        # GET request
        return render_template('analyze.html', form=form)
    return redirect(url_for('login'))


@ app.route('/download_all')
def download_all():
    return send_file('{}/listings.zip'.format(args['properties_folder']),
                     mimetype='zip',
                     attachment_filename='listings.zip',
                 as_attachment=True)


@app.route("/login")
def login():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Google)
    using an URL with a few key OAuth parameters.
    """

    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = google.authorization_url(authorization_base_url,
        access_type="offline",      # offline for refresh token
        include_granted_scopes='true', # Enable incremental authorization. Recommended as a best practice.
        prompt="consent")    # force to always make user click authorize

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.
@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    try:
        google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri,
                               state=session['oauth_state'])
        token = google.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=request.url)

        # We use the session as a simple DB for this example.
        session['oauth_token'] = token
        return redirect(url_for('analyze'))

    except KeyError:
        return redirect(url_for('analyze'))


@app.route("/menu", methods=["GET"])
def menu():
    """"""
    return """
    <head>
        <title>Menu</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">
    </head>
    <body>
    <h1>Congratulations, you have obtained an OAuth 2 token!</h1>
    <h2>What would you like to do next?</h2>
    <ul>
        <li><a href="/"> Go to Home Page</a></li>
        <li><a href="/profile"> Get account profile</a></li>
        <li><a href="/automatic_refresh"> Implicitly refresh the token</a></li>
        <li><a href="/manual_refresh"> Explicitly refresh the token</a></li>
        <li><a href="/validate"> Validate the token</a></li>
        <li><a href="/logout"> Log Out</a></li>
    </ul>

    <pre>
    %s
    </pre>
    </body>
    """ % pformat(session['oauth_token'], indent=4)


@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    google = OAuth2Session(client_id, token=session['oauth_token'])
    return jsonify(google.get('https://www.googleapis.com/oauth2/v1/userinfo').json())


@app.route("/automatic_refresh", methods=["GET"])
def automatic_refresh():
    """Refreshing an OAuth 2 token using a refresh token.
    """
    token = session['oauth_token']

    # We force an expiration by setting expired at in the past.
    # This will trigger an automatic refresh next time we interact with
    # Googles API.
    token['expires_at'] = time() - 10

    extra = {
        'client_id': client_id,
        'client_secret': client_secret,
    }

    def token_updater(token):
        session['oauth_token'] = token

    google = OAuth2Session(client_id,
                           token=token,
                           auto_refresh_kwargs=extra,
                           auto_refresh_url=refresh_url,
                           token_updater=token_updater)

    # Trigger the automatic refresh
    jsonify(google.get('https://www.googleapis.com/oauth2/v1/userinfo').json())
    return jsonify(session['oauth_token'])


@app.route("/manual_refresh", methods=["GET"])
def manual_refresh():
    """Refreshing an OAuth 2 token using a refresh token.
    """
    token = session['oauth_token']

    extra = {
        'client_id': client_id,
        'client_secret': client_secret,
    }

    google = OAuth2Session(client_id, token=token)
    session['oauth_token'] = google.refresh_token(refresh_url, **extra)
    return jsonify(session['oauth_token'])


@app.route("/validate", methods=["GET"])
def validate():
    """Validate a token with the OAuth provider Google.
    """
    token = session['oauth_token']

    # Defined at https://developers.google.com/accounts/docs/OAuth2LoginV1#validatingtoken
    validate_url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?'
                    'access_token=%s' % token['access_token'])

    # No OAuth2Session is needed, just a plain GET request
    return jsonify(requests.get(validate_url).json())


@app.route('/logout')
def logout():
    session.pop('oauth_token', None)
    session.pop('oauth_state', None)
    return redirect(url_for('login'))


def main():
    # This allows us to use a plain HTTP callback
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
    options = {
        'bind': '%s:%s' % ('127.0.0.1', '8080'),
        'workers': number_of_workers(),
    }
    app.run(host='0.0.0.0', port=8080, ssl_context='adhoc')
    StandaloneApplication(app, options).run()
    

if __name__ == '__main__':
    main()
