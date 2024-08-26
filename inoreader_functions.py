import json
import csv
import time
import datetime
import sys
import os.path
from requests_oauthlib import OAuth2Session

# ANSI escape codes for text formatting
BOLD = '\033[1m'
ITALIC = '\033[3m'
END = '\033[0m'


def prompt_variables(days_back):
    now = datetime.date.today()
    yesterday = now - datetime.timedelta(days=1)

    print(f"{BOLD}Welcome to the Inoreader Article Gatherer!{END} 📚✨")

    print(f"""
Ready to dive into your personalized news collection? We'll need a few details to get started:

1. {BOLD}Start and End Date{END}: Specify the date range for the articles you want to gather.
2. {BOLD}Authentication{END}: Authenticate with Inoreader and authorize the script in your browser 
(just follow the instructions).

Once done, your results will be saved in the data directory as:
- articles-[yyyymmdd]-[yyyymmdd].csv
- feeds-list.csv

Enjoy your curated content! 🎉
""")

    while True:  # start_date
        try:
            date_str = input(f'Enter the {BOLD}START{END} date for gathering articles (yyyy-mm-dd) '
                             f'(Default: {days_back} days ago):\n')
            if date_str == '':
                past_date = now - datetime.timedelta(days=days_back)
                date = datetime.datetime(past_date.year, past_date.month, past_date.day, 0, 0, 0)
            else:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            start_date_unix = time.mktime(date.timetuple())
        except ValueError:
            print(f"{BOLD}Please, type a valid date format (yyyy-mm-dd).{END}\n")
            continue
        else:
            break

    while True:  # end_date
        try:
            date_str = input(f'Enter the {BOLD}END{END} date for gathering articles (yyyy-mm-dd). NOT INCLUDED. '
                             f'(Default: Today):\n'
                             f'{ITALIC}NOTE: With more than 20 days, you might exceed your quota and need to come '
                             f'back tomorrow to complete the period.{END}\n')
            if date_str == '':
                date = datetime.datetime(now.year, now.month, now.day, 23, 59, 59)
            else:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            end_date_unix = time.mktime(date.timetuple())
        except ValueError:
            print(f"{BOLD}Please, type a valid date format (yyyy-mm-dd).{END}\n")
            continue
        else:
            break

    print(
        f"\n{BOLD}We will gather data from {datetime.datetime.fromtimestamp(start_date_unix).strftime('%Y-%m-%d')} to "
        f"{datetime.datetime.fromtimestamp(end_date_unix).strftime('%Y-%m-%d')}.{END}\n"
        f"NOTE: Articles from the start or end date may be partial. "
        f"Ensure these dates are included in the next script execution.{END}"
    )

    return start_date_unix, end_date_unix


def make_connection(client_id, client_secret, redirect_uri):
    scope = ['read']
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = oauth.authorization_url(
        'https://www.inoreader.com/oauth2/auth',
        state="test"
    )

    print(f"Please go to the following URL and authorize access:\n{authorization_url}")
    authorization_response = input(
        f"Enter the {BOLD}value following the code parameter{END} in the redirected URL:\n")

    try:
        token = oauth.fetch_token(
            'https://www.inoreader.com/oauth2/token',
            code=authorization_response,
            client_secret=client_secret
        )
    except Exception as e:
        print(f"{BOLD}ERROR:{END} An error occurred while fetching the token: {e}")
        return None

    print(f"\n{BOLD}Authorization successful!{END} ✅")
    return oauth


def make_call_to_json(oauth, url, debug=False):
    r = oauth.get(url)

    # Check if the quota has been exceeded
    if r.status_code == 429:
        print(f"\n{BOLD}WARNING:{END} Quota exceeded. Results may not be complete. Please try again tomorrow."
              f"\n{ITALIC}Last API call:{END} {url}\n")
        return None

    contents = r.content
    my_json = contents.decode('utf8').replace("'", '"')
    try:
        data = json.loads(my_json)  # Load the JSON to a Python list & dump it back out as formatted JSON
    except json.decoder.JSONDecodeError:
        print(f"{BOLD}ERROR:{END} Invalid or empty JSON string.")
        return None
    else:
        if debug:
            print('- ' * 20)
            s = json.dumps(data, indent=4, sort_keys=True)
            print(s)
            print('- ' * 20)
        return data


def datalist_to_csv(dir_path, filename, data_list):
    # This function asks the user to overwrite the file if it already exists.

    # Get the keys (column names) from the first dictionary in the list
    full_filename = os.path.join(dir_path, filename)
    if data_list:
        keys = data_list[0].keys()

        # Create the directory if it doesn't exist
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Directory {dir_path} created.")

        # Check if the file already exists
        file_exists = os.path.isfile(full_filename)
        if file_exists:
            overwrite = input(
                f"The file {full_filename} already exists. Do you want to overwrite it? (yes/no / Default: no): "
            ).strip().lower()
            if overwrite not in ["yes", "y"]:
                print("The file was not overwritten.")
                return

        # Overwrite the results
        with open(full_filename, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, keys)
            dict_writer.writeheader()
            # Write the data rows
            dict_writer.writerows(data_list)
            print(f"Data successfully saved to {full_filename}.")
    else:
        print("No data to save.")


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
        print(f"Successfully retrieved {len(feeds)} feeds. 📚\n")
        return feeds
    else:
        print("Failed to retrieve feeds. ❌\n")
        return None


def get_articles(oauth, n_items, n_calls, init_date_unix, end_date_unix, debug):
    categories = []
    feeds = []
    articles = []
    continuation = ""
    i = 0
    first_date = None  # default first date
    last_date = None
    skipped = 0  # The script won't add the articles from today to avoid including not processed articles

    # now = datetime.datetime.now()  # Get the current date and time

    def print_progress_bar(iteration, total, length=50):
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = '█' * filled_length + '-' * (length - filled_length)
        sys.stdout.write(f'\rProgress: |{bar}| {percent}% Complete')
        sys.stdout.flush()

    while True:
        print_progress_bar(i, n_calls)
        i += 1
        url_all = 'https://www.inoreader.com/reader/api/0/stream/contents?' \
                  'n=' + str(n_items) + \
                  '&ot=' + str(init_date_unix) + \
                  '&nt=' + str(end_date_unix)
        if continuation != "":
            url_all = url_all + '&c=' + continuation

        contents_all = make_call_to_json(oauth, url_all, debug)

        if contents_all is None:
            break

        for content in contents_all['items']:
            # skip if the article is not within the specific date
            if (content['published'] < init_date_unix) or (content['published'] > end_date_unix):
                skipped += 1
                continue

            if last_date is None or content['published'] > last_date:
                last_date = content['published']
            if first_date is None or content['published'] < first_date:
                first_date = content['published']

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

        if ('continuation' not in contents_all) or (i >= n_calls) or not contents_all:
            break
        else:
            continuation = contents_all['continuation']

    print_progress_bar(n_calls, n_calls)
    print("\n")

    if last_date is None:
        print(f"With {i} calls, we have gathered {len(articles)} articles. \n"
              f"We have skipped {skipped} articles not in the dates interval.\n")
    else:
        print(f"With {i} calls, we have gathered {len(articles)} articles. "
              f"From {convert_timestamp_to_str(first_date)} to {convert_timestamp_to_str(last_date)} "
              f"covering {datediff_in_days(first_date, last_date)} days.\n"
              f"We have skipped {skipped} articles not in the dates interval.\n")

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
