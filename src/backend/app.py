from datetime import timedelta
import logging, json, time
import time
import uuid

from urllib.parse import urlencode, urljoin
from fastapi import FastAPI, Response, Request, status
from fastapi.responses import HTMLResponse

from azure.communication.identity import CommunicationIdentityClient, CommunicationUserIdentifier, CommunicationTokenScope
from azure.communication.callautomation import (
    CallAutomationClient,
    PhoneNumberIdentifier,
    RecognizeInputType,
    TextSource
    )
from azure.core.messaging import CloudEvent

from dapr.clients import DaprClient
from dapr.ext.fastapi import DaprApp

from filelock import FileLock, Timeout
from user_store import UserStore
from settings import Settings
from azure.eventgrid import EventGridEvent, SystemEventNames

logging.basicConfig(level=logging.INFO)

app = FastAPI()
dapr_app = DaprApp(app)
dapr_client = DaprClient()
settings = Settings(dapr_client)
users_store = UserStore(settings)

target_participant_to_redirect = CommunicationUserIdentifier(
    "<ACS_USER_IDENTIFIER>"
)

# ------------------------------
# Call Management
# ------------------------------

@app.post("/api/events/incoming-call")
async def handle_incoming_call(request: Request):
    for event_dict in await request.json():
        event = EventGridEvent.from_dict(event_dict)
        logging.info(f'Event : {event.data}')
        
        # Validating Event Grid Subscription WebHook Registration
        if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
            logging.info("Validating subscription")
            validation_code = event.data['validationCode']
            validation_response = {'validationResponse': validation_code}
            return Response(content=json.dumps(validation_response), status_code=status.HTTP_200_OK)
        
        # Handle Incoming Call
        elif event.event_type =="Microsoft.Communication.IncomingCall":
            logging.info(f'Incoming Call : {event.data}')

            if event.data['from']['kind'] =="phoneNumber":
                caller_id =  event.data['from']["phoneNumber"]["value"]
            else :
                caller_id =  event.data['from']['rawId']

            logging.info(f"incoming call handler caller id: {caller_id}")
            incoming_call_context=event.data['incomingCallContext']
            
            # Call Automation Redirect Call (always redirect to a fixed number for demo purpose)
            call_automation_client = CallAutomationClient.from_connection_string(settings.acs_connection_string)
            call_automation_client.redirect_call(
                incoming_call_context=incoming_call_context, 
                target_participant=target_participant_to_redirect
            )
            
            # Call Automation Answer Call with Callback (Server Side Call Handling)
            # guid =uuid.uuid4()
            # query_parameters = urlencode({"callerId": caller_id})
            # callback_uri = f"{settings.callback_events_uri}/api/callbacks/{guid}?{query_parameters}" 
            # answer_call_result = call_automation_client.answer_call(
            #     incoming_call_context=incoming_call_context, 
            #     callback_url=callback_uri)

            user = event.data['from']
            logging.info(f'Incoming Call from User : {user}')
            return Response(status_code=status.HTTP_200_OK)
        
# ------------------------------        
# Callbacks server side handling (not required for routing)
# ------------------------------
        
# @app.post("/api/callbacks/{context_id}")
# async def callback_events_handler(request: Request):
#     try:
#         for event_dict in await request.json():       
#             event = CloudEvent.from_dict(event_dict)
#             logging.info(f'Event : {event.data}')

#             call_connection_id = event.data['callConnectionId']
#             logging.info(f'call connection id: {call_connection_id}, event type: {event.type}')

#             caller_id = request.args.get("callerId").strip()
#             if "+" not in caller_id:
#                 caller_id="+".strip()+caller_id.strip()
#             
#             # Call Automation Play Audio - Text to Speech
#                
#             logging.info(f"call connected : data={event.data}")
#         return Response(status=200) 
#     except Exception as ex:
#         logging.info("error in event handling")

# ------------------------------
# User Management
# ------------------------------
@app.get('/api/users')
def users(request: Request):
    try:
        all_users = users_store.get_all()
        return Response(content=json.dumps(all_users), media_type="application/json")
    except Exception as e:
        logging.error(f'Error: {e}')
        return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get('/api/users/{user_upn}')
def read_user(user_upn: str, request: Request):
    try:
        user = users_store.get(user_upn)
        if (user is None):
            user = users_store.create(user_upn)
        return Response(content=json.dumps(user), media_type="application/json")
    except Exception as e:
        logging.error(f'Error: {e}')
        return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get('/api/users/delete/{user_upn}')
def delete_user(user_upn: str, request: Request):
    try:
        user = users_store.get(user_upn)
        if user is not None:
            users_store.delete(user_upn)
            return Response(content=json.dumps(user), media_type="application/json")
        else: 
            return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_200_OK)
    except Exception as e:
        logging.error(f'Error: {e}')
        return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get('/', response_class = HTMLResponse)
def get_root():
    return """
    <html>
        <head>
            <title>Communication Service Backend API</title>
        </head>
        <body>
            <h1>Communication Service Backend API Ready !</h1>
        </body>
    </html>
    """