import inoreader_functions
import datetime
import os

# TODO: Add error control: (1) Token expired / not valid (2) Exceed number of requests/quota

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
debug = False

client_id = r'999999707'
client_secret = r'Ic1LlZ3yaPOnOfepzUJ5MsyWLOo3CAlB'
redirect_uri = 'https://google.com'

n_items = 100  # maximum number of articles to return in each call. Max 100 . The higher, the less API calls.
n_calls = 75  # maximum number of calls to do to the API for getting all articles (there will be more calls than this)
# Set low for testing purposes. 117 maximum before reaching quota limit.
# 75 is a good number, so we can allow also calls for getting starred articles.
# TRY 1: with 99999 calls, it reaches the quota limit after getting 11700 articles, \
# a timespan of 11.79 days from 5/22/24 16:36 to 6/3/24 11:35 (which makes 117 calls maximum to do)
# TRY 2: 70 calls / 7 to starred. Gathered 7009 articles from 28/5/2024 13:23:07 to 4/6/2024 11:55:00 \
# (6.94 days, not getting to 7 days)
# TRY 3: 75 calls / 8 to starred. Gathered 7510 articles from 5/28/24 21:41 to 6/5/24 10:15 (7.52380787 days)

default_days_back = 7

date_unix, non_read = inoreader_functions.prompt_variables(default_days_back)
print("Thanks for the input. Now we will connect to Inoreader")
oauth = inoreader_functions.make_connection(client_id, client_secret, redirect_uri)
print("Connection established. Gathering data from inoreader.")
feeds, categories, articles = inoreader_functions.get_categories(oauth, n_items, n_calls, date_unix, non_read, debug)
print("Data gathered and saved locally. Uploading to Google Drive")

# Create the names of the files based on the dates
start_date = datetime.datetime.fromtimestamp(date_unix)
now_date = datetime.datetime.now()
start_date_str = start_date.strftime('%Y%m%d-%H%M')
now_date_str = now_date.strftime('%Y%m%d-%H%M')
feeds_filename = f"feeds-{start_date_str}-{now_date_str}.csv"
categories_filename = f"categories-{start_date_str}-{now_date_str}.csv"
articles_filename = f"articles-{start_date_str}-{now_date_str}.csv"
foldername = "data"

inoreader_functions.datalist_to_csv(foldername + "/" + feeds_filename, feeds)
inoreader_functions.datalist_to_csv(foldername + "/" + categories_filename, categories)
inoreader_functions.datalist_to_csv(foldername + "/" + articles_filename, articles)
inoreader_functions.upload_csv_to_googledrive(feeds_filename, foldername)
inoreader_functions.upload_csv_to_googledrive(categories_filename, foldername)
inoreader_functions.upload_csv_to_googledrive(articles_filename, foldername)
