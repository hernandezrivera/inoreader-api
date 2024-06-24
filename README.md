# Inoreader API Interaction Script

This script is designed to interact with the Inoreader API and Google Drive. It fetches articles from Inoreader based on a specified date range, saves them to CSV files, and optionally uploads those files to Google Drive.

## Features

- Fetches a list of feeds and articles from Inoreader.
- Saves the fetched data to CSV files.
- Optionally uploads the generated CSV files to Google Drive.

## Dependencies

- Python 3
- Git
- Pip
- Inoreader_functions module

## Setup Instructions

Please refer to the detailed setup instructions for Mac OS X and Windows in the script.

## Usage

After setting up the script, you can run it by typing `python3 main.py` (for Mac OS X) or `py main.py` (for Windows) in the terminal or command shell. Then, go to the URL provided and specify the parameters for the documents you want to have counted.

## Note

This script requires the `inoreader_functions` module, which contains the definitions for the functions used in the script. The exact workings of these functions are not shown in this script. Also, the script uses OAuth for authentication, so you'll need to have the client ID and client secret for the Inoreader API. The script is currently set up to use placeholder values for these. 

Remember to replace these placeholder values with your actual client ID and client secret before running the script. Also, uncomment the Google Drive upload section if you want to use that functionality. 

This script is a great starting point for anyone looking to automate the process of fetching articles from Inoreader, saving them to CSV files, and optionally uploading those files to Google Drive. It's well-structured and modular, making it easy to modify and extend according to your needs. 

Please ensure that you have the necessary permissions and credentials before running the script. Also, be aware of the API usage limits to avoid hitting the quota. 
