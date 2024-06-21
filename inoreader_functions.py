import json
import csv
import time
import datetime
import os.path
from requests_oauthlib import OAuth2Session
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def get_last_file_date(creds, folder_id):
    # Prints the date of the last file in the specified folder.

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API to get the files in the specified folder
        results = service.files().list(
            q="'{}' in parents".format(folder_id),
            pageSize=10, fields="nextPageToken, files(id, name, createdTime)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            # Sort the files by creation date
            items.sort(key=lambda x: x['createdTime'], reverse=True)
            # Get the creation date of the last file
            last_file_date = items[0]['createdTime']
            # Convert the date to unix timestamp
            unix_timestamp = time.mktime(
                datetime.datetime.strptime(last_file_date, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
            # Print the date in "%Y-%m-%d" format
            print(
                "The date of the last call is " + datetime.datetime.fromtimestamp(unix_timestamp).strftime('%Y-%m-%d'))
    except Exception as e:
        print('ERROR: %s' % e)
    return unix_timestamp


def prompt_variables(days_back):
    now = datetime.date.today()
    yesterday = now - datetime.timedelta(days=1)

    while True:  # start_date
        try:
            date_str = input(
                'Enter the START date for the counting (yyyy-mm-dd) (Default: %i days ago)\n' % days_back)
            if date_str == '':
                past_date = now - datetime.timedelta(days=days_back)
                date = datetime.datetime(past_date.year, past_date.month, past_date.day, 0, 0, 0)
            else:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            start_date_unix = time.mktime(date.timetuple())
        except ValueError:
            print("Please, type a valid date format (yyyy-mm-dd).\n")
            continue
        else:
            break

    while True:  # start_date
        try:
            date_str = input('Enter the END date for the counting (yyyy-mm-dd) (Default: Yesterday)\n')
            if date_str == '':
                date = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
            else:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            end_date_unix = time.mktime(date.timetuple())
        except ValueError:
            print("Please, type a valid date format (yyyy-mm-dd).\n")
            continue
        else:
            break

    print("We will gather data from " + (datetime.datetime.fromtimestamp(start_date_unix)).strftime('%Y-%m-%d') + " to "
          + (datetime.datetime.fromtimestamp(end_date_unix)).strftime('%Y-%m-%d'))

    return start_date_unix, end_date_unix


def make_connection(client_id, client_secret, redirect_uri):
    scope = ['read']
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,
                          scope=scope)
    authorization_url, state = oauth.authorization_url(
        'https://www.inoreader.com/oauth2/auth',
        # access_type and prompt are Google specific extra
        # parameters.
        state="test")

    print('\nPlease go to %s and authorize access.' % authorization_url)
    authorization_response = input('Enter the value following the code parameter in the redirected URL\n')

    try:
        token = oauth.fetch_token(
            'https://www.inoreader.com/oauth2/token',
            code=authorization_response,
            # Google specific extra parameter used for client
            # authentication
            client_secret=client_secret)
    except Exception as e:
        print(f"ERROR: An error occurred while fetching the token: {e}")
        return None

    return oauth


def make_call_to_json(oauth, url, debug=False):
    r = oauth.get(url)

    # Check if the quota has been exceeded
    if r.status_code == 429:
        print("\nWARNING: Quota exceeded. Results probably are not complete - Try again tomorrow"
              "\nLast API call :" + url)
        return None

    contents = r.content
    my_json = contents.decode('utf8').replace("'", '"')
    try:
        data = json.loads(my_json)  # Load the JSON to a Python list & dump it back out as formatted JSON
    except json.decoder.JSONDecodeError:
        print("Invalid or empty JSON string")
    else:
        if debug:
            print('- ' * 20)
            s = json.dumps(data, indent=4, sort_keys=True)
            print(s)
            print('- ' * 20)
        return data


def get_categories_old(oauth, n_items, n_calls, date_unix, non_read, debug):
    # not used . First version of the function
    categories = {}
    feeds = {}
    articles = []
    continuation = ""
    i = 0

    while True:
        i = i + 1
        url = 'https://www.inoreader.com/reader/api/0/stream/contents?' \
              'n=' + str(n_items) + \
              '&ot=' + str(date_unix)
        if continuation != "":
            url = url + '&c=' + continuation
        if non_read:  # articles pending to read
            url = url + '&xt=user/-/state/com.google/read'

        contents = make_call_to_json(oauth, url, debug)

        for content in contents['items']:
            articles.append({'id': content['id'],
                             'categories': content['categories'],
                             'title': content['title'],
                             'published': content['published'],
                             'canonical': content['canonical'][0]['href'],
                             'origin.name': content['origin']['title'],
                             'origin.htmlUrl': content['origin']['htmlUrl'],
                             'origin.feed_url': content['origin']['streamId']
                             })
            for category in content['categories']:
                if category not in categories:
                    categories[category] = 1
                else:
                    categories[category] += 1
            feed = content['origin']['streamId']
            if feed not in feeds:
                feeds[feed] = 1
            else:
                feeds[feed] += 1
        if ('continuation' not in contents) or (i >= n_calls):
            break
        else:
            continuation = contents['continuation']

    if debug:
        print('- ' * 20)
        print('Categories and number of items')
        print('- ' * 20)
        s = json.dumps(categories, indent=4, sort_keys=True)
        print(s)
        print('- ' * 20)
        print('Feeds and number of items')
        print('- ' * 20)
        s = json.dumps(feeds, indent=4, sort_keys=True)
        print(s)
        print('- ' * 20)

    return feeds, categories, articles


def datalist_to_csv(filename, data_list):
    # This function asks the user to overwrite the file if already exists.

    # Get the keys (column names) from the first dictionary in the list
    if data_list:
        keys = data_list[0].keys()
        # Check if the file already exists
        file_exists = os.path.isfile(filename)
        if file_exists:
            overwrite = input(f"The file {filename} already exists. Do you want to overwrite it? (yes/no / Default: "
                              f"no): ")
            if (overwrite.lower() != "yes") and (overwrite.lower() != "y"):
                print("The file was not overwritten.")
                return
        # it will append the results at the end
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, keys)
            dict_writer.writeheader()
            # Write the data rows
            dict_writer.writerows(data_list)


def dictionary_to_csv(filename, collection):
    # This function appends new results to end of the file if it exists.
    # writing to csv file
    file_exists = os.path.isfile(filename)
    # it will append the results at the end
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        # Creating a csv writer object
        csvwriter = csv.writer(csvfile)
        if not file_exists:
            # Writing the headers
            csvwriter.writerow(['Key', 'Value'])
        # Writing the data rows
        csvwriter.writerows(collection.items())


def convert_timestamp_to_str(timestamp):
    # Convert the timestamp to datetime object
    dt_object = datetime.datetime.fromtimestamp(timestamp)

    # Format the datetime object to string
    dt_string = dt_object.strftime("%d-%m-%Y %H:%M:%S")

    return dt_string


def datediff_in_days(timestamp1, timestamp2):
    # Convert the timestamps to datetime objects
    dt_object1 = datetime.datetime.fromtimestamp(timestamp1)
    dt_object2 = datetime.datetime.fromtimestamp(timestamp2)

    # Calculate the difference in days
    diff = dt_object2 - dt_object1
    diff_in_days = diff.days

    return diff_in_days


def get_feeds(oauth, debug):
    url = "https://www.inoreader.com/reader/api/0/subscription/list"
    response = make_call_to_json(oauth, url, debug)
    if response is not None:
        feeds = response['subscriptions']
        print(f"We have retrieved : {str(len(feeds))} feeds")
        return feeds
    else:
        return None

def get_articles(oauth, n_items, n_calls, init_date_unix, end_date_unix, debug):
    categories = []
    feeds = []
    articles = []
    continuation = ""
    i = 0
    first_date = init_date_unix  # default first date
    last_date = None
    skipped = 0  # The script won't add the articles from today to avoid including not processed articles
    now = datetime.datetime.now()  # Get the current date and time

    print("Progress: ", end="")
    while True:
        print("#", end="")  # Progression bar
        i += 1
        url_all = 'https://www.inoreader.com/reader/api/0/stream/contents?' \
                  'n=' + str(n_items) + \
                  '&ot=' + str(init_date_unix)
        if continuation != "":
            url_all = url_all + '&c=' + continuation

        contents_all = make_call_to_json(oauth, url_all, debug)

        if contents_all is None:
            break

        for content in contents_all['items']:

            if content['published'] >= end_date_unix:
                # If it was, skip this iteration of the loop
                skipped += 1
                continue  # keep the for loop
            if last_date is None or content['published'] > last_date:
                last_date = content['published']

            articles.append({'id': content['id'],
                             'categories': content['categories'],
                             'title': content['title'],
                             'published': content['published'],
                             'canonical': content['canonical'][0]['href'],
                             'origin.name': content['origin']['title'],
                             'origin.htmlUrl': content['origin']['htmlUrl'],
                             'origin.feed_url': content['origin']['streamId'],
                             'starred': 'user/1006063842/state/com.google/starred' in content['categories'],
                             'read': 'user/1006063842/state/com.google/read' not in content['categories']
                             })

            for category in content['categories']:
                for item in categories:
                    if 'category' in item and item['category'] == category:
                        item['total'] += 1
                        break
                else:
                    categories.append({'category': category, 'total': 1, 'starred': 0})

            for item in feeds:
                if 'feed' in item and item['feed'] == content['origin']['streamId']:
                    item['total'] += 1
                    break
            else:
                feeds.append({'feed': content['origin']['streamId'], 'total': 1, 'starred': 0})

            first_date = content['published']

        if ('continuation' not in contents_all) or (i >= n_calls) or not contents_all:
            break
        else:
            continuation = contents_all['continuation']

    if last_date is None:
        print("\n\nWith " + str(i) + " calls , we have gathered " + str(len(articles)) + " articles. \n" +
              "We have skipped " + str(skipped) + " articles published after the end date.")
    else:
        print("\n\nWith " + str(i) + " calls , we have gathered " + str(len(articles)) + " articles. " +
              "From " +
              convert_timestamp_to_str(first_date) + " to " + convert_timestamp_to_str(last_date) +
              " covering " + str(datediff_in_days(first_date, last_date)) + " days.\n" +
              "We have skipped " + str(skipped) + " articles that appeared after the end date \n" )

    if debug:
        print('- ' * 20)
        print('Categories and number of items')
        print('- ' * 20)
        s = json.dumps(categories, indent=4, sort_keys=True)
        print(s)
        print('- ' * 20)
        print('Feeds and number of items')
        print('- ' * 20)
        s = json.dumps(feeds, indent=4, sort_keys=True)
        print(s)
        print('- ' * 20)

    return feeds, categories, articles, first_date, last_date


def upload_to_googledrive(filename):
    # Upload the results to Google Drive

    token_filename = 'client_secret_460853965554.json'
    # Load credentials from the 'token.json' file
    creds = Credentials.from_authorized_user_file(token_filename)

    # Build the service
    drive_service = build('drive', 'v3', credentials=creds)

    # The ID of the folder where you want to upload the file
    folder_id = '1vAzq3KU_dFsQbQCD-u1oBCFpbdbc3MSt'  # "Inoreader data" folder on ds@hrinfo

    # Metadata about the file
    file_metadata = {
        'name': filename,  # replace with your file name
        'parents': [folder_id]
    }

    # The actual file to upload
    media = MediaFileUpload(filename, mimetype='text/csv')  # replace with your file path

    # Upload the file
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"File uploaded with ID {file.get('id')}")


# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def connect_to_googledrive():
    creds_filename = 'client_secret_460853965554.json'
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('data/token.json'):
        creds = Credentials.from_authorized_user_file('data/token.json')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_filename, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('data/token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def upload_csv_to_googledrive(creds, filename, folder_id, filepath):
    # Uploads a file to Google Drive.
    try:
        # Call the Drive v3 API
        drive_service = build('drive', 'v3', credentials=creds)

        # Metadata about the file
        file_metadata = {
            'name': filename,  # replace with your file name
            'parents': [folder_id]
        }

        # The actual file to upload
        media = MediaFileUpload(filepath + "/" + filename, mimetype='text/csv')  # replace with your file path

        # Upload the file
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print(f"File uploaded with ID {file.get('id')}")
    except Exception as e:
        print(e)
