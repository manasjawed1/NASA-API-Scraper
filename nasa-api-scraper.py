import requests
import json
import os
import pandas as pd
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload

api_key = "DEMO_KEY"
date = "2016-02-02"
request_url = "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?api_key=" + api_key + "&earth_date=" + date
response = requests.get(request_url)

cwd = os.getcwd()
# import all image data into a DataFrame for exploration and easy CSV export
all_images = json.loads(response.content)['photos']
df = pd.read_json(json.dumps(all_images))
df.to_csv(cwd + '/metadata.csv', index = False)

# Set up Drive API v3 access
# The following scope gives complete upload/download/delete access
SCOPES = ['https://www.googleapis.com/auth/drive'] 
creds = None

# Once authenticated, file 'token.pickle' will store access codes so that 
# login does not need to occur again
# Code sourced from Drive API's Quickstart sample: https://developers.google.com/people/quickstart/python
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
        
# If file does not have valid creds, prompt user login
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)

# upload csv to Drive
file_metadata = {'name': "metadata.csv", 'parents': ['1zs1NkhuqKLHuaCpdZGwvMyXh79Xi-AsG']}
media = MediaFileUpload("metadata.csv")
file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

# try to make an "images" directory if it doesn't already exist
try:
    os.mkdir("images")

except:
    print("Directory 'images' already exists.")

# download image one by one and upload to drive
# even though all links are currently working, added try-except in case a link goes down 
# in the future
for image in all_images:
    try:
        file = requests.get(image['img_src'])
        file_name = str(image['id'])
        ext = "." + image['img_src'].split('.')[-1]
        open(cwd + '/images/' + file_name + ext, 'wb').write(file.content)
        file_metadata = {'name': file_name + ext, 'parents': ['1zs1NkhuqKLHuaCpdZGwvMyXh79Xi-AsG']}
        media = MediaFileUpload('images/'+ file_name + ext,
                                mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    except Exception as e:
        print(str(e))
        print("Image ID:", str(image['id']), "at:", str(image['img_src']), "not found.")