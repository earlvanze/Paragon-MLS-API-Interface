# Paragon Real Estate Multiple Listing Service API Interface
### For Automated Four-Square Analysis of Rental Properties

This program takes in an ID from a Paragonrels.com URL and automatically populates the following
<a href="https://docs.google.com/spreadsheets/d/1QkDOfVxw0rtfB-XNEbWCAZEqY5njoIm8PDpvjpNCRrI">Google Spreadsheet</a>
in order to calculate Cash Flow and Cash-on-Cash Return for investment properties.


This spreadsheet was derived from the PDF available at
<a href="https://www.biggerpockets.com/renewsblog/easily-analyzing-rental-properties-four-square-method/">BiggerPockets.com</a>

## Prerequisites
From https://developers.google.com/sheets/api/quickstart/python

To run this program, you'll need:

Python 2.6 or greater.

The <a href="https://pypi.python.org/pypi/pip">pip</a> package management tool.

A Google account.

## Step 1: Turn on the Google Sheets API
Use <a href="https://console.developers.google.com/start/api?id=sheets.googleapis.com">this wizard</a> to create or
select a project in the Google Developers Console and automatically turn on the API.

Click Continue, then Go to credentials.

On the Add credentials to your project page, click the Cancel button.

At the top of the page, select the OAuth consent screen tab.

Select an Email address, enter a Product name if not already set, and click the Save button.

Select the Credentials tab, click the Create credentials button and select OAuth client ID.

Select the application type Other, enter the name "Google Sheets API Quickstart", and click the Create button.

Click OK to dismiss the resulting dialog.

Click the file_download (Download JSON) button to the right of the client ID.

Move this file to your working directory and rename it client_secret.json.


## Step 2: Install the Google Client Library and other non-standard python modules
Run the following command in Terminal to install the necessary libraries using pip:
```
pip install --upgrade pandas httplib2 google-api-python-client oauth2client
```
See the library's <a href="https://developers.google.com/api-client-library/python/start/installation">installation page</a> for the alternative installation options.

## Step 3: Make a copy of spreadsheet and update main.py
Make your own copy of the Google spreadsheet linked above and replace the SPREADSHEET_ID (line 18 of main.py)
with your own spreadsheet's ID (derived from the URL https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID})

## Step 4: Run the program
Run the sample using the following command:
```
python main.py [-id "{guid/id from URL of MLS listings from broker/agent}"] [-f "{temporary_folder_for_listings}"]
```
The sample will attempt to open a new window or tab in your default browser. If this fails, copy the URL from the console and manually open it in your browser.

If you are not already logged into your Google account, you will be prompted to log in.
If you are logged into multiple Google accounts, you will be asked to select one account to use for the authorization.

Click the Accept button.
The sample will proceed automatically, and you may close the window/tab.
