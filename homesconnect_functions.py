import json
import zipfile
import glob
import traceback
from functions import *

with open("HomesConnect/listings/1545-willow-street-denver-co-80220.json", 'r') as file:
	json_repr = file.read()
	data = json.loads(json_repr)
	print(json.dumps(data, indent=4, sort_keys=True))	


def get_listings():
	return


def parse_hc_json(properties_folder = args['properties_folder']):
    # Parse the json files saved in args['properties_folder'] and returns 2D array of properties
    filenames = []
    for filename in glob.iglob('{}/*.json'.format(properties_folder)):
         filenames.append(filename)

    output_data = [[None] * 50 for i in range(len(filenames))]

    for i in range(len(filenames)):
        with open(filenames[i], 'r') as file:
            json_repr = file.read()
            data = json.loads(json_repr)

            try:
                address = DictQuery(data).get("Address")
                city = DictQuery(data).get("City")
                state = DictQuery(data).get("State")
                zip = DictQuery(data).get("Zip")
                full_address = address + ' \n' + city + ', ' + state + ' ' + zip
                address_link = '=HYPERLINK("https://www.google.com/maps/search/?api=1&query={0}","{0}")'.format(full_address)
                mls_number = DictQuery(data).get("ListingID")
                price_current = DictQuery(data).get("Price")      # Asking price
                price_prev = int(price_current) + int(DictQuery(data).get("PriceReductionAmount"))           # Original price, before price changes
                status = DictQuery(data).get("ListingStatus")
                beds = DictQuery(data).get("BedRooms")
                baths = DictQuery(data).get("BathRooms")
                public_remarks = DictQuery(data).get("SalesCopy")
                mls_link = '=HYPERLINK("https://www.zillow.com/homes/{0}_rb/","{1}")' \
                    .format(full_address, mls_number)
                age = DictQuery(data).get("YearBuilt")
                type = DictQuery(data).get("Headline1")
                unit1_rent = DictQuery(data).get("RentalPrice")
                unit2_rent = DictQuery(data).get("RentalPrice")
                unit3_rent = DictQuery(data).get("RentalPrice")
                unit4_rent = DictQuery(data).get("RentalPrice")
                total_taxes = int(DictQuery(data).get("Taxes")) // 12
                fees = int(DictQuery(data).get("Fees")) // 12
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
                    output_data[i][4] = price_current * 0.85
                    output_data[i][9] = age
                    output_data[i][10] = xstr(type) + '\n' + xstr(beds) + 'BD' + '/' + xstr(baths) + 'BA'
                    output_data[i][11] = public_remarks + "\n{0} as of {1}-{2}-{3}".format(status, str(now.year), str(now.month), str(now.day))
                    output_data[i][12] = unit1_rent
                    output_data[i][13] = unit2_rent
                    output_data[i][14] = unit3_rent
                    output_data[i][15] = unit4_rent
                    output_data[i][23] = total_taxes
                    output_data[i][24] = fees
                else:
                    print ("{0} ({1}) status is {2}".format(address, mls_number, status))
    output_data = [x for x in output_data if x[0] != None]    # delete empty rows (inactive listings) from output_data
#    print (output_data)
    return (output_data)