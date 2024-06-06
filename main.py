# from oauthlib.oauth2 import BackendApplicationClient  
from pip._vendor.distlib.compat import raw_input
from requests_oauthlib import OAuth2Session
import os
import json
import time
import datetime

from flask import Flask, request, jsonify, render_template


## To get all the feeds https://www.inoreader.com/reader/api/0/subscription/list
## To get item ids for each feed, and count them (one call for starred and one call for non starred)

app = Flask(__name__)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
debug = False
n_items = 100  # maximum number of articles to return. Max 100 . The higher, the less API calls.

client_id = r'999999707'
client_secret = r'Ic1LlZ3yaPOnOfepzUJ5MsyWLOo3CAlB'
days_back = 1

scope = ['read']
port = 5000

# redirect_uri = 'http://' + request.environ['REMOTE_ADDR'] + ':' + str(port) + '/code'
redirect_uri_local = 'http://localhost:' + str(port) + '/code'
redirect_uri_heroku = 'https://inoreader-api.herokuapp.com/code'
redirect_uri = redirect_uri_local

oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,
                      scope=scope)
authorization_url, state = oauth.authorization_url(
    'https://www.inoreader.com/oauth2/auth',
    # access_type and prompt are Google specific extra
    # parameters.
    state="test")


def make_call_to_json(url, debug=False):
    r = oauth.get(url)
    content_items = r.content

    my_json = content_items.decode('utf8').replace("'", '"')

    # Load the JSON to a Python list & dump it back out as formatted JSON
    data = json.loads(my_json)
    if debug:
        print('- ' * 20)
        result_string = json.dumps(data, indent=4, sort_keys=True)
        print(result_string)
        print('- ' * 20)
    return data


@app.route('/post', methods=['POST'])
def post_something():
    authorization_response = request.form.get('code')
    date = request.form.get('date')
    read_content = request.form.get('read-content')

    while True:
        try:
            date_str = date
            if (date_str is None) | (date_str == ''):
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

    print(date)

    non_read_str = read_content
    non_read = not ((non_read_str == 'N') or (non_read_str == 'n') or (non_read_str == 'No'))

    print(non_read)

    token = oauth.fetch_token(
        'https://www.inoreader.com/oauth2/token',
        code=authorization_response,
        # Google specific extra parameter used for client
        # authentication
        client_secret=client_secret)

    categories = {}
    continuation = ""

    while True:
        url = 'https://www.inoreader.com/reader/api/0/stream/contents?' \
              'n=' + str(n_items) + \
              '&ot=' + str(date_unix)
        # the parameter only gets non-read content, number of items and date_from
        if continuation != "":
            url = url + '&c=' + continuation
        if non_read:
            url = url + '&xt=user/-/state/com.google/read'

        contents = make_call_to_json(url, debug)
        for content in contents['items']:
            for category in content['categories']:
                if category not in categories:
                    categories[category] = 1
                else:
                    categories[category] += 1
        if 'continuation' not in contents:
            break
        else:
            continuation = contents['continuation']

    return render_template('results.html', results_dict=categories, date=date, non_read=non_read)


@app.route('/code')
def get_code():
    authorization_code = request.args.get('code')
    today = datetime.date.today()
    date = today - datetime.timedelta(days=days_back)

    return render_template('code.html', code=authorization_code, days_back=days_back, date=date)


# A welcome message to test our server
@app.route('/')
def index():
    return render_template('home.html', url=authorization_url, days_back=days_back)


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=port)
