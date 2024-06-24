# import gdrive_functions
import inoreader_functions
import datetime
import os
import sys

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
debug = False

client_id = r'999999707'
client_secret = r'Ic1LlZ3yaPOnOfepzUJ5MsyWLOo3CAlB'
redirect_uri = 'https://google.com'

n_items = 100  # maximum number of articles to return in each call. Max 100 . The higher, the less API calls.
n_calls = 300  # maximum number of calls to do to the API for getting all articles. Maximum 117?
# Set low for testing purposes. 117 maximum before reaching quota limit.

# The ID of the GDrive folder where you want to upload the file
folder_id = '1vAzq3KU_dFsQbQCD-u1oBCFpbdbc3MSt'  # "Inoreader data" folder on ds@hrinfo

default_days_back = 7
# drive_creds = gdrive_functions.connect_to_googledrive()
init_date_unix, end_date_unix = inoreader_functions.prompt_variables(default_days_back)

print("Thanks for the input. Now we will connect to Inoreader")

oauth = inoreader_functions.make_connection(client_id, client_secret, redirect_uri)

if oauth is None:
    sys.exit()

print("\nConnection established. ")
print("\nGathering feeds from Inoreader.")
feeds_list = inoreader_functions.get_feeds(oauth, debug)

print("\n\nGathering articles from Inoreader.")
feeds, categories, articles, first_day, last_day = inoreader_functions.get_articles(oauth, n_items, n_calls,
                                                                                    init_date_unix, end_date_unix,
                                                                                    debug)
print("Articles gathered\n")

# Created the CSV files and save them to local disk
if len(articles) > 0:
    print("Saving data into local CSV files")
    # Create the names of the files based on the dates
    start_date = datetime.datetime.fromtimestamp(first_day)
    end_date = datetime.datetime.fromtimestamp(last_day)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    folder_name = "data"
    feeds_list_filename = f"feeds-list.csv"
    feeds_filename = f"feeds-{start_date_str}-{end_date_str}.csv"
    categories_filename = f"categories-{start_date_str}-{end_date_str}.csv"
    articles_filename = f"articles-{start_date_str}-{end_date_str}.csv"

    inoreader_functions.datalist_to_csv(folder_name, feeds_list_filename, feeds_list)
    inoreader_functions.datalist_to_csv(folder_name, feeds_filename, feeds)
    inoreader_functions.datalist_to_csv(folder_name, categories_filename, categories)
    inoreader_functions.datalist_to_csv(folder_name, articles_filename, articles)

    print("Data saved locally (" + folder_name + "/" + articles_filename + ").")

    # print("\nUploading files  to Google Drive")
    # inoreader_functions.upload_csv_to_googledrive(drive_creds, feeds_list_filename, folder_id, folder_name)
    # inoreader_functions.upload_csv_to_googledrive(drive_creds, feeds_filename, folder_id, folder_name)
    # inoreader_functions.upload_csv_to_googledrive(drive_creds, categories_filename, folder_id, folder_name)
    # inoreader_functions.upload_csv_to_googledrive(drive_creds, articles_filename, folder_id, folder_name)
    # print("Files uploaded. Your data can be found at https://drive.google.com/drive/folders/" + folder_id)