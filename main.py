import os
import json
from datetime import datetime, timezone
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google.oauth2 import service_account
from googleapiclient.discovery import build
import inspirobot

slack_token = os.environ['SLACK_BOT_TOKEN']
channel_id = os.environ['SLACK_CHANNEL_ID']
calendar_id = os.environ['CALENDAR_ID']
credentials_json = os.environ['GOOGLE_APPLICATION_CREDENTIALS']



def get_google_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        credentials_json,
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

def get_upcoming_events(service, calendar_id):
    now = datetime.now(timezone.utc).isoformat()
    events_result = service.events().list(
        calendarId=calendar_id, timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    
    # Log the entire response for inspection
    print(json.dumps(events_result, indent=2))
    
    events = events_result.get('items', [])
    return events

def get_days_until(event_date):
    now = datetime.now(timezone.utc)
    event = datetime.fromisoformat(event_date).replace(tzinfo=timezone.utc)
    diff = event - now
    return diff.days

def post_daily_countdown(request):
    client = WebClient(token=slack_token)
    service = get_google_calendar_service()
    events = get_upcoming_events(service, calendar_id)
    quote = inspirobot.generate()
    blocks = [
        {
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": "Daily Motivation.. kinda :rickdance:",
                "emoji": True
            },
            "image_url": quote.url,
            "alt_text": "courtesy of inspirobot.me"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Countdown!!",
                "emoji": True
            }
        }
    ]
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        days_until = get_days_until(start)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f" - *{event['summary']}* is in {days_until} days!"
            }
        })
        blocks.append({"type": "divider"})

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text="Daily Countdown"  # Fallback text
        )
        print(f"Message posted: {response['ts']}")
    except SlackApiError as e:
        print(f"Error posting message: {e.response['error']}")

    return 'OK'
