"""
    Automated Rental Property Analysis
    https://github.com/earlvanze/Paragon-MLS-API-Interface

    ~~~~~~~~~~~~~~
    The Google OAuth Flask functionality is contributed by Bruno Rocha
    GitHub: https://github.com/rochacbruno
"""

from __future__ import print_function
import json
import pandas as pd
import time
import glob
import requests
import os, shutil
import pathlib
import argparse
import traceback
import datetime
from apiclient.discovery import build
from httplib2 import Http
from flask import Flask, flash, render_template, request, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from oauth2client import file, client, tools
from functions import *

# You should change these to match your own spreadsheet
GSHEET_ID = '1QkDOfVxw0rtfB-XNEbWCAZEqY5njoIm8PDpvjpNCRrI'
RANGE_NAME = 'Four-Square Analysis!A:AX'

# MLS_ID gets passed in by user but default is here if none passed in
MLS_ID = "6d70b762-36a4-4ac0-bedd-d0dae2920867"
SYSTEM_ID = "CRMLS"

# You generally don't need to change these
PROPERTIES_FOLDER = "listings"
# {0} is the SYSTEM_ID, {1} is the MLS number for a property,
# and {2} is a guid generated from http://{args.system_id}.paragonrels.com/CollabLink/public/CreateGuid
PARAGON_API_URL = "http://{0}.paragonrels.com/CollabLink/public/BlazeGetRequest?ApiAction=listing%2FGetListingDetails%2F" \
                  "&UrlData={1}%2F0%2F2%2Ffalse%2F{2}"

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/39.0.2171.95 Safari/537.36',
           'Cookie': 'psystemid={0};pagentid={1};pofficeid={2};'        # this gets updated in get_mls_numbers
}


# Flask App configuration
app = Flask(__name__)
app.config['GOOGLE_ID'] = "32857849252-evl55bpb1479bg2tofetg3jqbthurgkb.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "4b5JYPZUpbeFogmZ5w7GWZMl"
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': ['email', 'https://www.googleapis.com/auth/spreadsheets']
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    print (jsonify({"data": me.data}))
    return redirect(url_for('index'))


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')


#@app.route("/<string:gsheet_id>/<string:mls_number>/")
def parse_listing(gsheet_id, range_name, system_id, mls_id = None, mls_list = None):
    pathlib.Path(args.properties_folder).mkdir(exist_ok=True)       # create temporary listings folder if nonexistent
    if not mls_id:
        mls_id = args.mls_id
    if not system_id:
        system_id = args.system_id
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
    if 'google_token' in session:
        me = google.get('userinfo')
        print(jsonify({"data": me.data}))
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)