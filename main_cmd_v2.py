from click._compat import raw_input
from requests_oauthlib import OAuth2Session
import requests
import time
from collections import defaultdict
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Not sure about his credentials
# app_id = r'999999707'
# app_key = r'Ic1LlZ3yaPOnOfepzUJ5MsyWLOo3CAlB'
# redirect_uri = 'http://google.com'

# Inoreader Items counter - feedback@rw
# app_id = r'999999712'
# app_key = r'o9tWqx7hNoBG2C5feSFU6gs6qx9qbIiK'
# redirect_uri = 'http://localhost:5000/code'

# Content counter - feedback@rw
app_id = r'999999493'
app_key = r'dsASdbFxABOoBr2jG5d88UADF0anbGaK'
redirect_uri = 'https://localhost'

base_url = 'https://www.inoreader.com/reader/api/0/'  # The base URL for the Inoreader API
n_articles = 2
period = 2 * 60 * 60  # Get articles from the last 24 hours


def authenticate(_app_id, _app_key, _redirect_uri):
    # Authenticate with the Inoreader API
    # scope = 'read'
    oauth = OAuth2Session(client_id=_app_id, redirect_uri=_redirect_uri)  # , scope=scope)
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
        client_secret=_app_key)

    print(token)
    return token


# Get the number of articles posted for each feed in the last period
def get_articles(_auth_token, _n_articles, _period):
    headers = {
        'Authorization': f'GoogleLogin auth={_auth_token}',
        'AppId': app_id,
        'AppKey': app_key,
    }
    params = {
        'n': _n_articles,  # Get the last n items
        'ot': int(time.time()) - _period,  # Get items from the last 'period' seconds
    }
    # 'stream/contents/user/-/state/com.google/reading-list'
    response = requests.get(base_url + 'stream/contents', headers=headers,
                            params=params)
    response.raise_for_status()  # Raise an exception if the request failed
    return response.json()


# Get the number of starred articles for each feed
def get_starred(_auth_token):
    headers = {
        'Authorization': f'GoogleLogin auth={_auth_token}',
        'AppId': app_id,
        'AppKey': app_key,
    }
    response = requests.get(base_url + 'stream/contents/user/-/state/com.google/starred', headers=headers)
    response.raise_for_status()  # Raise an exception if the request failed
    return response.json()


# Use the functions
auth_token = authenticate(app_id, app_key, redirect_uri)
articles = get_articles(auth_token, n_articles, period)
starred = get_starred(auth_token)

# Count the number of articles posted and starred for each feed
feeds_articles = defaultdict(int)
feeds_starred = defaultdict(int)

for article in articles["items"]:
    feeds_articles[article["origin"]["title"]] += 1

for article in starred["items"]:
    feeds_starred[article["origin"]["title"]] += 1

# Print the results
print("Number of articles posted in the last 24 hours for each feed:")
for feed, count in feeds_articles.items():
    print(f"{feed}: {count}")

print("\nNumber of starred articles for each feed:")
for feed, count in feeds_starred.items():
    print(f"{feed}: {count}")
