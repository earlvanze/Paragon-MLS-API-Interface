# This file contains the functions and classes required to parse property listings

import json
import pandas as pd
import time
import glob
import requests
import shutil
import argparse
import traceback
import datetime
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from gunicornconf import *

# You should change these to match your own spreadsheet
GSHEET_ID = '1QkDOfVxw0rtfB-XNEbWCAZEqY5njoIm8PDpvjpNCRrI'
RANGE_NAME = 'Four-Square Analysis!A:AX'

# MLS_ID gets passed in by user but default is here if none passed in
MLS_ID = "6d70b762-36a4-4ac0-bedd-d0dae2920867"
SYSTEM_ID = "CRMLS"

# You generally don't need to change these
PROPERTIES_FOLDER = "listings"
# {0} is the SYSTEM_ID, {1} is the MLS number for a property,
# and {2} is a guid generated from http://{args['system_id']}.paragonrels.com/CollabLink/public/CreateGuid
PARAGON_API_URL = "http://{0}.paragonrels.com/CollabLink/public/BlazeGetRequest?ApiAction=listing%2FGetListingDetails%2F" \
                  "&UrlData={1}%2F0%2F2%2Ffalse%2F{2}"

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/39.0.2171.95 Safari/537.36',
           'Cookie': 'psystemid={0};pagentid={1};pofficeid={2};'        # this gets updated in get_mls_numbers
}


class ReusableForm(Form):
#    mls_list = TextAreaField('List of MLS Numbers:', validators=[validators.required()])
    gsheet_id = StringField('Google Sheet ID:', validators=[validators.required()])
    range_name = StringField('Range Name:', validators=[validators.required()])
#    mls_id = StringField('MLS ID:', validators=[validators.required()])
    system_id = StringField('System ID:', validators=[validators.required()])


# Used to search for keys in nested dictionaries and handles when key does not exist
# Example: DictQuery(dict).get("dict_key/subdict_key")
class DictQuery(dict):
    def get(self, path, default = None):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [ v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break;

        return val


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


# Returns empty string if s is None
def xstr(s):
    if s is None:
        return ''
    return str(s)


def user_args():
    args = argparse.ArgumentParser()
    args.add_argument(
        "-i",
        "--id",
        dest="mls_id",
        default=MLS_ID,
        help="ID of Paragonrels listings from URL"
    )
    args.add_argument(
        '-f',
        '--folder',
        dest='properties_folder',
        default=PROPERTIES_FOLDER,
        help='Name of folder/path for storing properties files temporarily'
    )
    args.add_argument(
        '-l',
        '--list',
        dest='mls_list_path',
        default=None,
        help='File name or path of newline-separated MLS numbers to search for'
    )
    args.add_argument(
        '-s',
        '--system',
        dest='system_id',
        default=SYSTEM_ID,
        help='ID of MLS region (ex. CRMLS)'
    )
    args.add_argument(
        '-g',
        '--gsheet_id',
        dest='gsheet_id',
        default=GSHEET_ID,
        help='Google Sheets ID derived from the URL https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID})'
    )
    return args.parse_args()

# args = user_args()
args = {
	"gsheet_id": "1QkDOfVxw0rtfB-XNEbWCAZEqY5njoIm8PDpvjpNCRrI",
	"range_name": "Four-Square Analysis!A:AX",
	"mls_id": "6d70b762-36a4-4ac0-bedd-d0dae2920867",
	"system_id": "CRMLS",
	"properties_folder": "listings",
	"mls_list_path": None,
}

def get_mls_numbers_and_cookies(mls_id = args['mls_id'], system_id = args['system_id'], mls_list = None):
    # Takes in an MLS ID of MLS listings and returns list of MLS numbers
    # If path to list of MLS #s is given in user arguments, uses that instead
    mls_numbers = []
    listings = []
    agent_id = 1
    office_id = 1
    print("MLS ID: " + mls_id)
    mls_scope = "http://{0}.paragonrels.com/CollabLink/public/BlazePublicGetRequest?ApiAction=GetNotificationAppData%2F&UrlData={1}".format(system_id, mls_id)
    r = requests.get(mls_scope)
    r_json = json.loads(r.text)
#    print (r.text)

    # Need to get cookie data from MLS response to retrieve property information later
    # If an MLS ID is passed in (not default MLS_ID), update the cookies accordingly for good measure
    if mls_id != MLS_ID:
        agent_id = DictQuery(r_json).get("Agent/AgentId")
        office_id = DictQuery(r_json).get("Agent/OfficeId")

    data = json.loads(r.text.split('[]')[0])
    listings = data["listings"]
    print ("Listings found from MLS ID: " + str(listings))
    print (args['mls_list_path'])
    if mls_list:
        mls_numbers = [x.strip() for x in mls_list.split('\n')]
    elif args['mls_list_path']:
        with open(args['mls_list_path'], 'r') as mls_list:
            mls_numbers = [x.strip() for x in mls_list.read().split('\n')]
    else:
        if listings:
            for listing in listings:
                mls_number = listing.pop('Id')
                mls_numbers.append(mls_number)
        else:
            print ("No listings found in " + mls_id)

    headers['Cookie'] = 'psystemid={0};pagentid={1};pofficeid={2};'.format(system_id.upper(), agent_id, office_id)
#    print ("Cookies: " + headers['Cookie'])
    return (mls_numbers)


def get_properties(mls_numbers = [], system_id = args['system_id'], properties_folder = args['properties_folder']):
    # Takes in list of MLS numbers, gets json for each property from Paragon API, and saves each json to {ADDRESS}.json
    print (mls_numbers)
    guid = requests.get("http://{0}.paragonrels.com/CollabLink/public/CreateGuid".format(system_id), headers = headers).text
#    print ("GUID: " + GUID)
    for mls_number in mls_numbers:
        try:
            resp = requests.get(PARAGON_API_URL.format(system_id, mls_number, guid), headers = headers)
            out_json = "%s.json" % (xstr(DictQuery(resp.json()).get("PROP_INFO/ADDRESS")))
            with open("{0}/{1}".format(properties_folder,out_json), 'w') as outfile:
                outfile.write(resp.text)
        except:
            print(mls_number)
            traceback.print_exc()
            continue


def parse_json(properties_folder = args['properties_folder']):
    # Parse the json files saved in args['properties_folder'] and returns 2D array of properties
    filenames = []
    for filename in glob.iglob('{}/*.json'.format(properties_folder)):
         filenames.append(filename)

    output_data = [[None] * 50 for i in range(len(filenames))]

    for i in range(len(filenames)):
        with open(filenames[i], 'r') as file:
            json_repr = file.read()
            data = json.loads(json_repr)
            property_info_list, schools_list, features_list, misc_list = ([] for i in range(4))
            property_info = {}
            schools = {}
            features = {}
            misc = {}
            status = ''
            try:
                address = DictQuery(data).get("PROP_INFO/ADDRESS")
                city = DictQuery(data).get("PROP_INFO/CITY")
                state = DictQuery(data).get("PROP_INFO/STATE")
                zip = DictQuery(data).get("PROP_INFO/ZIP")
                full_address = address + ' \n' + city + ', ' + state + ' ' + zip
                address_link = '=HYPERLINK("https://www.google.com/maps/search/?api=1&query={0}","{0}")'.format(full_address)
                mls_number = data["HISTDATA"][0]["MLS_NUMBER"]
                price_prev = DictQuery(data).get("PROP_INFO/PRICE_PREV")            # Original price, before price changes
                price_current = DictQuery(data).get("PROP_INFO/PRICE_CURRENT")      # Asking price
                beds = DictQuery(data).get("PROP_INFO/BDRMS")
                baths_full = DictQuery(data).get("PROP_INFO/BATHS_FULL")
                baths_part = DictQuery(data).get("PROP_INFO/BATHS_PART")
                public_remarks = DictQuery(data).get("PROP_INFO/REMARKS_GENERAL")
                mls_link = '=HYPERLINK("http://{0}.paragonrels.com/publink/Report.aspx?GUID={1}&ListingID={2}:0&layout_id=3","{2}")'\
                    .format(args['system_id'], args['mls_id, mls_number'])
                # If an MLS ID is NOT passed in (default MLS_ID used), mls_link should be zillow address search
                if args['mls_id'] == MLS_ID:
                    mls_link = '=HYPERLINK("https://www.zillow.com/homes/{0}_rb/","{1}")' \
                        .format(full_address, mls_number)
                # Two possible formats for MLS sheet encountered so far:
                # 1st format, more common: [[Property Information], [Schools], [Features], [Miscellaneous]]
                try:
                    list_of_lists = DictQuery(data).get("PROP_INFO/DetailOptions/Data")
                    property_info_list = list_of_lists[0]
                    schools_list = list_of_lists[1]
    #                features_list = list_of_lists[2]
    #                misc_list = list_of_lists[3]
                    for item in property_info_list:
                        label = item.pop('Label')
                        property_info[label] = item.pop('Value')
    #                    print(label, property_info[label])
                    for item in schools_list:
                        label = item.pop('Label')
                        schools[label] = item.pop('Value')
    #                    print(label, schools[label])
                    age = DictQuery(property_info).get("Age (NOT year built)")
                    type = DictQuery(property_info).get("Type")
                    unit1_rent = DictQuery(property_info).get("Unit #1 Rent")
                    unit2_rent = DictQuery(property_info).get("Unit #2 Rent")
                    unit3_rent = DictQuery(property_info).get("Unit #3 Rent")
                    unit4_rent = DictQuery(property_info).get("Unit #4 Rent")
                    total_taxes = int(DictQuery(property_info).get("Total Taxes").replace(",", "")) // 12
                    school_taxes = 0
                    if DictQuery(schools).get("School Taxes"):
                        school_taxes = int(DictQuery(schools).get("School Taxes").replace(",", "")) // 12
                    status = DictQuery(property_info).get("Status")
                except:
                    traceback.print_exc()
                    # 2nd format, less common: [{Schools}, {Features}, {Miscellaneous}]
                    try:
                        # WEIRD BUG where original data dict ended up being modified so that
                        # each object (key) in schools_list[] has no key "Label" or "Value"
                        # Solved by reloading json_repr into new dict data2
                        data2 = json.loads(json_repr)
                        list_of_dicts = DictQuery(data2).get("PROP_INFO/DetailOptions")
                        schools_list = DictQuery(list_of_dicts[0]).get("Data")
                        features_list = DictQuery(list_of_dicts[1]).get("Data")
                        misc_list = DictQuery(list_of_dicts[2]).get("Data")
                        for item in schools_list:
                            label = item.pop('Label')
                            schools[label] = item.pop('Value')
                        #                            print(label, schools[label])
                        for item in features_list:
                            label = item.pop('Label')
                            features[label] = item.pop('Value')
                        #                            print(label, features[label])
                        for item in misc_list:
                            label = item.pop('Label')
                            misc[label] = item.pop('Value')
                        #                            print(label, misc[label])
                        age = DictQuery(misc).get("Age (NOT year built)")
                        type = DictQuery(data).get("PROP_INFO/PROP_TYPE_LONG")
                        unit1_rent = DictQuery(misc).get("Unit 1 Monthly Rent")
                        unit2_rent = DictQuery(misc).get("Unit 2 Monthly Rent")
                        unit3_rent = DictQuery(misc).get("Unit 3 Monthly Rent")
                        unit4_rent = DictQuery(misc).get("Unit 4 Monthly Rent")
                        total_taxes = 0
                        if DictQuery(misc).get("Total Taxes"):
                            total_taxes = int(DictQuery(misc).get("Total Taxes").replace(",", "")) // 12
                        school_taxes = 0
                        if DictQuery(schools).get("School Taxes"):
                            school_taxes = int(DictQuery(schools).get("School Taxes").replace(",", "")) // 12
                        status = DictQuery(data).get("PROP_INFO/STATUS_LONG")
                    except:
                        traceback.print_exc()
                        continue
                    continue
            except:
                traceback.print_exc()
                continue
            finally:
                now = datetime.datetime.now()
                # Fill in list only if property is an active listing
                if (status == 'Active' or 'New' or 'Price Change') or ('Pend' in status):
                    output_data[i][0] = address_link
                    output_data[i][1] = mls_link
                    output_data[i][2] = price_prev
                    output_data[i][3] = price_current
                    output_data[i][9] = age
                    output_data[i][10] = type + '\n' + beds + 'BD' + '/' + baths_full + '.' + xstr(baths_part) + 'BA'
                    output_data[i][11] = public_remarks + "\n{0} as of {1}-{2}-{3}".format(status, str(now.year), str(now.month), str(now.day))
                    output_data[i][12] = unit1_rent
                    output_data[i][13] = unit2_rent
                    output_data[i][14] = unit3_rent
                    output_data[i][15] = unit4_rent
                    output_data[i][23] = total_taxes - school_taxes
                    output_data[i][24] = school_taxes
                else:
                    print ("{0} ({1}) status is {2}".format(address, mls_number, status))
    output_data = [x for x in output_data if x[0] != None]    # delete empty rows (inactive listings) from output_data
#    print (output_data)
    return (output_data)


def save_csv(output_data = [[None] * 50]):
    columns = ['Address',
               'MLS #',
               'Original Price',
               'List Price',
               'Offer Price',
               'Total Investment',
               'Total Monthly Cash Flow',
               'Cash on Cash Return',
               'Capitalization Rate',
               'Age (years)',
               'Type',
               'Notes',
               'Rental (Unit 1)',
               'Rental (Unit 2)',
               'Rental (Unit 3)',
               'Rental (Unit 4)',
               'Rental (Unit 5)',
               'Rental (Unit 6)',
               'Rental (Unit 7)',
               'Laundry Income',
               'Storage Income',
               'Misc Income',
               'Total Monthly Income',
               'Property Taxes',
               'School Taxes',
               'Insurance',
               'Water',
               'Sewer',
               'Garbage',
               'Electric',
               'Gas',
               'HOA Fees',
               'Lawn/Snow',
               'Vacancy',
               'Repairs',
               'Capital Expenditures',
               'Property Management',
               'Mortgage',
               'Total Monthly Expenses',
               'Total Monthly Income',
               'Total Monthly Expenses',
               'Total Monthly Cash Flow',
               'Total Annual Cash Flow',
               'Down Payment',
               'Closing Costs',
               'Rehab Budget',
               'Reserve / Prepaid',
               'Deposit / Misc Other',
               'Total Investment',
               'Cash on Cash Return'
               ]

    # Write data to data frame, then save to CSV file
    out_csv = "%s_%s.csv" % (str(time.strftime("%Y-%m-%d")),
                               str(time.strftime("%H%M%S")))
    pd.DataFrame(output_data, columns = columns).to_csv(
        out_csv, index = False, encoding = "UTF-8"
    )


def empty_folder(properties_folder = args['properties_folder']):
    try:
        shutil.rmtree(properties_folder)
    except:
        traceback.print_exc()
        pass