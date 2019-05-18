from flask import Flask, request, abort
import requests
import dialogflow
from google.api_core.exceptions import InvalidArgument
import os

# Initialize flask app
app = Flask(__name__)

# set facebook api url for messenger
FB_API_URL = 'https://graph.facebook.com/v2.6/me/messages'
# set page access token - get from messenger page - replace with your own page access key
PAGE_ACCESS_TOKEN = 'EAAhCAPX5avYBAJdAIgWrgBGkAZAxYAtRfyqo0pwilk7g1qaq2MpR0JSPKdMkKokETEZAR3wYOZAZC9PP69hMZAmHqHZBBF68JcCDpETg1Rg4qMu60iVzY8w8ZBTcLGoFKKZAIHf3sywpZBItLQZCdEZAf18reeeDsWxAKySuN4ll9KtYQZDZD'

# we will need an environment variable for service.json file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service.json"

# Dialogflow project id for dialogflow integration
DIALOGFLOW_PROJECT_ID = 'psappmentalhealth'
DIALOGFLOW_LANGUAGE_CODE = 'en-US'

# this function gets the appropriate bot response
def get_bot_response(message,sessionId):

    # dialogflow integration happens here - completely optional
    SESSION_ID = sessionId
    
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    
    text_input = dialogflow.types.TextInput(text=message, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise

    print("Session ID: " + str(SESSION_ID))
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    return response.query_result.fulfillment_text


# this function gets back to user on messenger
def send_message(recipient_id, text):
    """Send a response to Facebook"""
    payload = {
        'message': {
            'text': text
        },
        'recipient': {
            'id': recipient_id
        },
        'notification_type': 'regular'
    }
    auth = {
        'access_token': PAGE_ACCESS_TOKEN
    }
    response = requests.post(
        FB_API_URL,
        params=auth,
        json=payload
    )
    return response.json()


# making sure that it is a user message and not an echo
def is_user_message(message):
    """Check if the message is a message from the user"""
    return (message.get('message') and
            message['message'].get('text') and
            not message['message'].get("is_echo"))



# user message handler
@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print(request.json)
        payload = request.json
        event = payload['entry'][0]['messaging']
        for x in event:
            if is_user_message(x):
                text = x['message']['text']
                sender_id = x['sender']['id']
                response = get_bot_response(text,sender_id)
                send_message(sender_id , response)
        return '', 200

    else:
        abort(400)



# this is just verification of token
@app.route('/', methods=['GET'])
def handle_verification():
    if (request.args.get('hub.verify_token', '') == 'psappmentalhealth'):
        print("Verified")
        return request.args.get('hub.challenge', '')
    else:
        print("Wrong token")
        return "Error, wrong validation token"


# start flask
if __name__ == '__main__':
    app.run()