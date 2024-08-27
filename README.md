# Magic Machine Installation Guide

## Living Document
For the most up-to-date instructions, refer to the living document [here](https://docs.google.com/document/d/11KbF64kkdb88O7S9eYw-QZyXgLDLNvABqoMZUrAR2_Q/edit).

## How to Install the Magic Machine

### Instructions for Mac OS X
To install the Magic Machine on your Mac, follow the instructions below:

1. Install Python from [here](https://www.python.org/downloads/).
2. Install Git from [here](https://git-scm.com/downloads).
3. Install Homebrew by following the instructions [here](https://www.atlassian.com/git/tutorials/install-git).
4. Open Terminal (apple+space bar > type terminal) and execute the following commands:
    ```sh
    git clone https://github.com/hernandezrivera/inoreader-api.git
    cd inoreader-api
    pip3 help
    ```
5. If `pip3 help` does not display help instructions, install pip by typing:
    ```sh
    sudo easy_install pip
    ```
6. Ensure you are in the project directory by typing:
    ```sh
    ls
    ```
7. Install the project dependencies:
    ```sh
    pip3 install -r requirements.txt
    ```
8. Run the script:
    ```sh
    python3 main.py
    ```
9. Go to the URL provided and specify the parameters for the documents you want to have counted.

### Instructions for Windows
To install the Magic Machine on your Windows, follow the instructions below:

1. Install Python from [here](https://www.python.org/downloads/). Ensure to check the boxes to add Python to PATH and enable environment variables.
2. Install Git from [here](https://git-scm.com/downloads).
3. Open the Command Shell (windows + R > type cmd.exe) and execute the following commands:
    ```sh
    cd Documents
    git clone https://github.com/hernandezrivera/inoreader-api.git
    cd inoreader-api
    pip help
    ```
4. If `pip help` does not display help instructions, install pip by first downloading the `get-pip.py` file from [here](https://phoenixnap.com/kb/install-pip-windows) and then typing:
    ```sh
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    pip help
    ```
5. Install the project dependencies:
    ```sh
    pip install -r requirements.txt
    ```
    If you get an error, type:
    ```sh
    python.exe -m pip install -r requirements.txt
    ```
6. Run the script:
    ```sh
    py main.py
    ```
7. Go to the URL provided and specify the parameters for the documents you want to have counted.

**Note:** If pip needs to be added to PATH, follow the steps outlined [here](https://phoenixnap.com/kb/install-pip-windows) to add pip to the system environment variables.

## How to Run the Script Once Installed

### Run it on Mac OS X
Open Terminal and type the following:
```sh
cd inoreader-api
python3 main.py
```

### Run it on Windows
Search for “Command Prompt” and type the following:
```sh
cd Documents\inoreader-api
py main.py
```

## How to Find the Resulting Spreadsheet
To get the CSV, navigate to the `inoreader-api` folder. There should be a `data` directory. The command shell/terminal will also tell you the name of the CSV document it just created. The important files are:
- `articles-[yyyymmdd]-[yyyymmdd].csv` (with the dates being the start and end date of the articles).
- `feeds-list.csv`

Copy those two files to OneDrive:
- `\Digital Services Section\04_Monitoring and Reporting\ReliefWeb Content\Inoreader\Articles` (the first file)
- `\Digital Services Section\04_Monitoring and Reporting\ReliefWeb Content\Inoreader\Feeds` (the second file - overwrite the existing one)

## Add ReliefWeb Content Stats Data
The dashboard also has information about ReliefWeb Content Stats. Copy the new datasets from [this Trello card](https://trello.com/c/YtU0591M) to:
`\Digital Services Section\04_Monitoring and Reporting\ReliefWeb Content\Inoreader\RW Content Stats`

Note that this process could be automated with Zapier.

## Fixing Editors Without Duty Station
Edit the Excel file in `\Digital Services Section\04_Monitoring and Reporting\ReliefWeb Content\Inoreader\Editors information - Manual.xlsx` and add the editor name, editor ID (ReliefWeb User ID), and duty station. After the changes sync in OneDrive and you refresh the data of the dashboard, the editors will display correctly.

## Analyzing the Data in PowerBI

### [Dashboard in PowerBI](https://app.powerbi.com/groups/1f9045df-b2d2-40af-a5e9-da55309bb379/reports/7a8970ef-04c3-4ed8-ba5d-b9ecbdae67e4/ReportSection?experience=power-bi)
Click on [Refresh](https://app.powerbi.com/groups/1f9045df-b2d2-40af-a5e9-da55309bb379/datasets/d72522fb-a80a-49b7-b169-3b54cd029be8/details?experience=power-bi) to get the new data. The “To” date on the top right corner of the dashboard should change to the last update once the process is completed. Also, you will see a difference in the number of reports.

The other option is to wait until the next day. The data is refreshed automatically every day at 4pm UTC (12pm NYC) and 4am UTC (00:00 NYC).

If there is an error in the refreshing, an email will be sent to hernandezrivera@un.org and valencia@reliefweb.int for troubleshooting.
