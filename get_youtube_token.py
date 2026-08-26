import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# SCOPES required to upload and verify the active YouTube channel
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    client_secrets_path = os.path.join(script_dir, 'client_secrets.json')
    token_path = os.path.join(script_dir, 'moltbuuk_token.json')
    
    if not os.path.exists(client_secrets_path):
        print(f"ERROR: Please put your Google Cloud 'client_secrets.json' in {script_dir}!")
        return

    print("Opening web browser to log into Google...")
    print("NOTE: On the Google screen, select your email, and if prompted, pick the 'Long Sleepy Story' channel.\n")
    
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
    
    # prompt='select_account consent' forces Google to show all accounts and brand channels
    creds = flow.run_local_server(
        port=0,
        prompt='select_account consent',
        access_type='offline'
    )

    # Verify which YouTube channel was actually selected
    from googleapiclient.discovery import build
    yt = build('youtube', 'v3', credentials=creds)
    channels_resp = yt.channels().list(mine=True, part='snippet').execute()
    
    channel_name = "Unknown"
    custom_url = ""
    if 'items' in channels_resp and len(channels_resp['items']) > 0:
        item = channels_resp['items'][0]['snippet']
        channel_name = item.get('title', 'Unknown')
        custom_url = item.get('customUrl', '')

    token_json = creds.to_json()
    
    with open(token_path, 'w') as token_file:
        token_file.write(token_json)
        
    print("\n=======================================================")
    print(f"AUTHENTICATED YOUTUBE CHANNEL: {channel_name} ({custom_url})")
    print("=======================================================")
    if "long" in channel_name.lower() or "sleepy" in channel_name.lower():
        print("PERFECT! You are connected to Long Sleepy Story.")
    else:
        print(f"NOTICE: You are currently connected to '{channel_name}'.")
        print("If you wanted '@longsleepystory', please re-run this script and")
        print("make sure you select the Long Sleepy Story channel from the channel list.")
        
    print(f"\nToken saved to: {token_path}")
    print("Copy the entire contents of 'moltbuuk_token.json' and")
    print("paste it into GitHub Secrets as 'YOUTUBE_OAUTH_TOKEN'")
    print("=======================================================\n")

if __name__ == '__main__':
    main()
