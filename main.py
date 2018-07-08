"""
    Automated Rental Property Analysis
    https://github.com/earlvanze/Paragon-MLS-API-Interface

    ~~~~~~~~~~~~~~
    Google OAuth Flask functionality from
    http://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example_with_refresh.html

"""

from __future__ import print_function
import os
import pathlib
import requests
from functions import *
from time import time
from requests_oauthlib import OAuth2Session
from apiclient.discovery import build
from httplib2 import Http
from flask import Flask, flash, render_template, redirect, url_for, session, request, jsonify
from oauth2client import client
from pprint import pformat


# This information is obtained upon registration of a new Google OAuth
# application at https://code.google.com/apis/console
client_id = "32857849252-ev5dnc6035d959cfdjngq6b3qiupr5mr.apps.googleusercontent.com"
client_secret = "_hyaZfOkNJIYxTl_HIz4S-rH"
redirect_uri = 'https://api-project-32857849252.appspot.com/callback'


# Uncomment for detailed oauthlib logs
#import logging
#import sys
#log = logging.getLogger('oauthlib')
#log.addHandler(logging.StreamHandler(sys.stdout))
#log.setLevel(logging.DEBUG)


# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://accounts.google.com/o/oauth2/token"
refresh_url = token_url # True for Google but not all providers.
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


# Flask App configuration
app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)


def append_to_gsheet(output_data=[], gsheet_id = args['gsheet_id'], range_name = RANGE_NAME):
    # Setup the Sheets API
    token = session['oauth_token']
    creds = client.AccessTokenCredentials(token['access_token'], headers['User-Agent'])
#    if not creds or creds.invalid:
#        flow = client.flow_from_clientsecrets('client_secret.json', scope)
#        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    body = {
        'values': output_data
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=gsheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    print('{0} rows updated.'.format(DictQuery(result).get('updates/updatedRows')))
    return result


#@app.route("/<string:gsheet_id>/<string:mls_number>/")
def parse_listing(gsheet_id, range_name, system_id, mls_id = None, mls_list = None):
    pathlib.Path(args['properties_folder']).mkdir(exist_ok=True)       # create temporary listings folder if nonexistent
    if not mls_id:
        mls_id = args['mls_id']
    if not system_id:
        system_id = args['system_id']
    mls_numbers = get_mls_numbers_and_cookies(mls_id, system_id, mls_list)
    get_properties(mls_numbers, system_id)
    output_data = parse_json()
    result = append_to_gsheet(output_data, gsheet_id, range_name)
    message = '{0} rows updated.'.format(DictQuery(result).get('updates/updatedRows'))
    return message
#    save_csv(output_data)
    empty_folder()


@app.route("/", methods=['GET', 'POST'])
def index():
    if 'oauth_token' in session:
        form = ReusableForm(request.form)
        print (form.errors)

        if request.method == 'POST':
            mls_list = request.form['mls_list']
            gsheet_id = request.form['gsheet_id']
            range_name = request.form['range_name']
            mls_id = request.form['mls_id']
            system_id = request.form['system_id']
#            print (mls_number, " ", gsheet_id)

            if form.validate():
                # Save the comment here.
                message = parse_listing(gsheet_id, range_name, system_id, mls_id, mls_list)
                return jsonify(data={'message': message})
            else:
                flash('Error: Some required fields are missing.')
                return jsonify(data=form.errors)

        return render_template('index.html', form=form)
    return redirect(url_for('login'))

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

    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri,
                           state=session['oauth_state'])
    token = google.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # We use the session as a simple DB for this example.
    session['oauth_token'] = token

    return redirect(url_for('index'))


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
    app.run(host='0.0.0.0', port=8080)
    StandaloneApplication(app, options).run()
    

if __name__ == '__main__':
	main()