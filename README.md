# Paragon Real Estate Multiple Listing Service API Interface
### For Automated Four-Square Cash Flow Analysis of Investment Properties

Accompanying spreadsheet available at: https://docs.google.com/spreadsheets/d/1QkDOfVxw0rtfB-XNEbWCAZEqY5njoIm8PDpvjpNCRrI/edit?pli=1#gid=2102309284

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
python main.py -id "[guid/id from URL of MLS listings from broker/agent]" [-l "mls_list.txt"]
```
where mls_list.txt is a file containing MLS numbers separated by commas
