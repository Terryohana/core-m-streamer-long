import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# SCOPES required to upload to YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    if not os.path.exists('client_secrets.json'):
        print("ERROR: Please put your Google Cloud 'client_secrets.json' in this folder!")
        return

    print("Opening web browser to log into Google...")
    flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
    
    # This will open your web browser. 
    # IMPORTANT: Make sure to select the "@longsleepystory" Brand Account!
    creds = flow.run_local_server(port=0)

    token_json = creds.to_json()
    
    with open('moltbuuk_token.json', 'w') as token_file:
        token_file.write(token_json)
        
    print("\n=======================================================")
    print("SUCCESS! Your YouTube Token has been generated.")
    print("Copy the entire contents of 'moltbuuk_token.json' and")
    print("paste it into GitHub Secrets as 'YOUTUBE_OAUTH_TOKEN'")
    print("=======================================================\n")

if __name__ == '__main__':
    main()
