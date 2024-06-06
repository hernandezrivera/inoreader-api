import json
import csv
from click._compat import raw_input
from requests_oauthlib import OAuth2Session
import time
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
from google.oauth2.credentials import Credentials


def prompt_variables(days_back):
    while True:
        try:
            date_str = raw_input(
                'Enter the start date for the counting (yyyy-mm-dd) (Default: %i days ago)\n' % days_back)
            if date_str == '':
                today = datetime.date.today()
                date = today - datetime.timedelta(days=days_back)
            else:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            date_unix = time.mktime(date.timetuple())
        except ValueError:
            print("Please, type a valid date format (yyyy-mm-dd).\n")
            continue
        else:
            break

    non_read = False
    non_read_str = raw_input('Do you want to get ONLY non-read articles? (Y = Non-read / N = all | Default is N - all '
                             ')\n')
    non_read = ((non_read_str == 'Y') or (non_read_str == 'y') or (non_read_str == 'Yes') or (non_read_str == 'yes'))

    return date_unix, non_read


def make_connection(client_id, client_secret, redirect_uri):
    scope = ['read']
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,
                          scope=scope)
    authorization_url, state = oauth.authorization_url(
        'https://www.inoreader.com/oauth2/auth',
        # access_type and prompt are Google specific extra
        # parameters.
        state="test")

    print('Please go to %s and authorize access.\n' % authorization_url)

    authorization_response = raw_input('Enter the value following the code parameter in the redirected URL\n')

    token = oauth.fetch_token(
        'https://www.inoreader.com/oauth2/token',
        code=authorization_response,
        # Google specific extra parameter used for client
        # authentication
        client_secret=client_secret)

    return oauth


def make_call_to_json(oauth, url, debug=False):
    r = oauth.get(url)

    # Check if the quota has been exceeded
    if r.status_code == 429:
        print("Quota exceeded - Try again tomorrow\nLast API call :" + url)
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
    # Get the keys (column names) from the first dictionary in the list
    if data_list:
        keys = data_list[0].keys()

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data_list)


def dictionary_to_csv(filename, collection):
    # writing to csv file
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        # Creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # Writing the headers
        csvwriter.writerow(['Key', 'Value'])
        # Writing the data rows
        csvwriter.writerows(collection.items())


def get_categories(oauth, n_items, n_calls, date_unix, non_read, debug):
    categories = []
    feeds = []
    articles = []
    continuation = ""
    i = 0
    first_date = date_unix  # default first date

    while True:
        i = i + 1
        url_all = 'https://www.inoreader.com/reader/api/0/stream/contents?' \
                  'n=' + str(n_items) + \
                  '&ot=' + str(date_unix)
        if continuation != "":
            url_all = url_all + '&c=' + continuation
        if non_read:
            url_all = url_all + '&xt=user/-/state/com.google/read'

        contents_all = make_call_to_json(oauth, url_all, debug)

        if not contents_all:
            break

        for content in contents_all['items']:
            articles.append({'id': content['id'],
                             'categories': content['categories'],
                             'title': content['title'],
                             'published': content['published'],
                             'canonical': content['canonical'][0]['href'],
                             'origin.name': content['origin']['title'],
                             'origin.htmlUrl': content['origin']['htmlUrl'],
                             'origin.feed_url': content['origin']['streamId'],
                             'starred': False
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

        if ('continuation' not in contents_all) or (i >= n_calls):
            print("Number of calls made for getting all articles: " + str(i))
            i = 0
            break
        else:
            continuation = contents_all['continuation']

    # get starred items
    while True:
        i = i + 1
        # items from the date of the previous subset
        url_starred = 'https://www.inoreader.com/reader/api/0/stream/contents?' \
                      'n=' + str(n_items) + \
                      '&ot=' + str(first_date) + \
                      '&it=user/-/state/com.google/starred'
        if continuation != "":
            url_starred = url_starred + '&c=' + continuation
        if non_read:
            url_starred = url_starred + '&xt=user/-/state/com.google/read'

        contents_starred = make_call_to_json(oauth, url_starred, debug)

        if not contents_starred:
            print("Number of calls made for getting starred articles: " + str(i))
            break

        for content in contents_starred['items']:
            # Mark the item in articles with a new column "Starred"
            for article in articles:
                if article['id'] == content['id']:
                    article.update({'starred': True})

            for category in content['categories']:
                for item in categories:
                    if 'category' in item and item['category'] == category:
                        item['starred'] += 1
                        break
                else:
                    # Code shouldn't get here
                    categories.append({'category': category, 'total': 1, 'starred': 1})

            for item in feeds:
                if 'feed' in item and item['feed'] == content['origin']['streamId']:
                    item['starred'] += 1
                    break
            else:
                # Code shouldn't get here
                feeds.append({'feed': content['origin']['streamId'], 'total': 1, 'starred': 1})

        if 'continuation' not in contents_starred:
            print("Number of calls made for getting starred articles: " + str(i))
            break
        else:
            continuation = contents_starred['continuation']

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


def upload_csv_to_googledrive(filename, filepath):
    """Shows basic usage of the Drive v3 API.
    Uploads a file to Google Drive.
    """
    creds_filename = 'client_secret_460853965554.json'

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_filename, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Drive v3 API
        drive_service = build('drive', 'v3', credentials=creds)

        # The ID of the folder where you want to upload the file
        folder_id = '1vAzq3KU_dFsQbQCD-u1oBCFpbdbc3MSt'  # "Inoreader data" folder on ds@hrinfo

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
