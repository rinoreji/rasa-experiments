# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from pprint import pprint

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # traker has access to the message and its metadata.
        # the data passed can be accessed from slot 'session_started_metadata' too.
        print("tracker:")
        pprint(vars(tracker))
        dispatcher.utter_message(text=f"Metadata from action: {tracker.latest_message['metadata']}")

        return []
