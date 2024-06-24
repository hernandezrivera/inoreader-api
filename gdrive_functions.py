import time
import datetime
import os.path
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
