# Paragon Real Estate Multiple Listing Service API Interface
### For Automated Four-Square Analysis of Rental Properties

This program takes in an ID from a Paragonrels.com URL and automatically populates the following Google Spreadsheet:
https://docs.google.com/spreadsheets/d/1QkDOfVxw0rtfB-XNEbWCAZEqY5njoIm8PDpvjpNCRrI/edit?pli=1#gid=2102309284
in order to calculate Cash Flow and Cash-on-Cash Return for investment properties.


This spreadsheet was derived from the PDF available at:
https://www.biggerpockets.com/renewsblog/easily-analyzing-rental-properties-four-square-method/

## Instructions

Requirements:
In Terminal:

```
pip install pandas
pip install httplib2
pip install google-api-python-client
pip install oauth2client
```

To run:
```
python main.py [-id "{guid/id from URL of MLS listings from broker/agent}"] [-f "{temporary_folder_for_listings}"]
```
