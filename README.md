# Paragon Real Estate Multiple Listing Service API Interface
### For Automated Four-Square Analysis of Rental Properties

This program takes in an ID from a Paragonrels.com or fnimls.com URL and automatically populates your own copy of this
<a href="https://docs.google.com/spreadsheets/d/1S-Vqsw_JyrCo6_zziWM_llZNl8AU92MeLZx9Xp5lMyw/copy"><b>Google Spreadsheet</b></a>
in order to calculate Cash Flow and Cash-on-Cash Return for investment properties. No coding experience necessary.

Row 2 of the spreadsheet has formulas that automatically populate with calculations for each new row.
I recommend leaving these formulas in place.


This spreadsheet was derived from the PDF available at
<a href="https://www.biggerpockets.com/renewsblog/easily-analyzing-rental-properties-four-square-method/">BiggerPockets.com</a>

You can try out a live demo of the program at <a href="https://api-project-32857849252.appspot.com/">
<b>https://api-project-32857849252.appspot.com/</b></a>. Go to the Google Sheet and click File > Make a Copy if it doesn't ask you to copy automatically.
Make your own copy of the Google spreadsheet linked above and copy your own Google Sheet's ID
(derived from the URL https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}) to the Google Sheet ID box on the form. The only required fields are the Google Sheet ID in the field at the bottom, and the MLS number(s) pasted in the big text box.

I've tested this with crmls, hudson, gamls, and triangle regions/system IDs I found on Twitter.
Other *.paragonrels.com regions may or may not work out of the box. Change the System ID accordingly.

You should have an agent send you a listing from your region's MLS in order to get the GUID ("MLS ID") from the URL,
which is used to pull the listings in that ID.

Alternatively, if you know your local MLS System ID, you can pass that in along with a text file
containing a list of MLS numbers you're interested in analyzing.
The System ID is usually the subdomain of *.paragonrels.com or *.fnimls.com but this may be different for your region.
Given only the System ID and the MLS number, the Paragon API can return the listing's information.

However, each MLS system is slightly different in the formatting of their listings
(and sometimes, listings within the same MLS system are different from each other)
and thus, the json result from the get_properties() function is formatted differently and parses slightly differently.
 If you encounter errors in parsing the json even though the json files are properly created in the "listings" folder,
  you may need to adjust the parse_json() code inside the nested try-except blocks to fit your listings'
  general format so it can be parsed properly.


## Prerequisites for running the app on your desktop
From https://developers.google.com/sheets/api/quickstart/python

To run this program, you'll need:

Python 2.6 or greater.

This was developed and tested using Python 3.6.4 on macOS High Sierra
but it should work in any other Python environment as long as the necessary Python modules are installed.
If Python complains that one of the modules is missing, just install that module and let me know that this
documentation is missing a package.

I did not test this in a fresh Python environment or virtualenv isolated from any existing modules.


The <a href="https://pypi.python.org/pypi/pip">pip</a> package management tool.


A Google account.

Clone this repository using git in Terminal (Mac or Linux) by typing:
```
git clone https://github.com/earlvanze/Paragon-MLS-API-Interface paragon && cd paragon
```
Windows users need to install git or GitHub Desktop or simply download the repository as a zip and unzip the package.

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
Make your own copy of the Google spreadsheet linked above and replace GSHEET_ID
with your own Google Sheet's ID (derived from the URL https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID})

You can also pass this in as a command-line argument to override the default global variable one time

If you renamed the specific sheet 'Four-Square Analysis!A:AX' inside the Google Sheets file or modified the number of columns,
replace RANGE_NAME with the new name along with the new range of columns.

Note that if you modify the number of columns, you may also want to modify the columns list in save_csv() to match.
Or not, since the save_csv() function does not affect the append_to_gsheet() function.

What is important is that if you want to save a csv of the listings, the number of columns in the output_data list
returned by get_properties() and passed in to save_csv() MUST match the number of items in columns[], or Python will throw an exception.

Example: 'Four-Square Analysis!A:AX'

## Step 4: Run the program
Run the sample using the following command [optional flags]
```
python main.py -i 'guid/id from URL of MLS listings from broker/agent' \
-l 'filename for newline-separated list of MLS #s' -f 'temporary_folder_for_listings' -s 'MLS System ID/subdomain' -g 'Google Sheets ID'
```
The append_to_gsheet() code will attempt to open a new window or tab in your default browser. If this fails, copy the URL from the console and manually open it in your browser.

If you are not already logged into your Google account, you will be prompted to log in.
If you are logged into multiple Google accounts, you will be asked to select one account to use for the authorization.

Click the Accept button.
The sample will proceed automatically, and you may close the window/tab.

If you need help, type:
```
python main.py --help
```


## How did I figure all this out?

This is the "normal" desktop/legacy version of the Paragon MLS, usually provided by your real estate broker/agent.
http://{system_id}.paragonrels.com/publink/default.aspx?GUID={mls_id}


I was originally going to use the legacy version's request URL:
http://crmls.paragonrels.com/publink/Report.aspx?&GUID={mls_id}&ListingID={mls_number}:0&layout_id=3
and scrape the output HTML, but why do scraping when a perfectly good public API is available?


In the upper left corner, there is a button to "Switch to Mobile View", a nicer, cleaner, mobile-friendly, responsive UI that leads to:
http://{system_id}.paragonrels.com/CollabLink/#/?id={mls_id}


By using Chrome's <i>Inspect Element</i> > <i>Network</i> feature, I found out about the API
and proceeded to spend an entire weekend to essentially reverse-engineer how it works.
By understanding the public CollabLink API with little to no public documentation, I could theoretically create my own Zillow or StreetEasy.
But that's beyond the scope of this git repo.

Relevant reading: https://blog.hartleybrody.com/web-scraping/, I found after the fact.

Enjoy!

## Donate

If you like this program, please donate using any of the methods below!


Square Cash	http://cash.me/$digitalkid

Venmo	https://venmo.com/earlco

PayPal	http://paypal.me/earlco

Zelle	earlvanze@gmail.com

BTC	12icq2NfvXDYExaH3a4FVnWJwerb1oj31Z

ETH	0x234AD7D3225dC28f2B292cCBE05CdD321C4aCC5B

ZEC	t1duLU96HyXQ7dGwdesZB6C4iCPe5HZw5ar

LTC	LQymEUqGK9dBeugi2bNNtt4LEGpm6bMYjJ

NEO/GAS	ALfeqEsmEexzk5RFGUZinedMAtjnfUz4f7

SC	de1caac41616a762428a2c2baca667bde5fb27ff6b0717bb0d2c1b3493a3f972933524ef9d19


If you want me to build a version for YOUR region, please reach out by email: earlvanze@gmail.com
