# rasa-experiments
Experiments on rasa

[Rasa custom-connectors](https://rasa.com/docs/rasa/connectors/custom-connectors)

`addons/custom_socketio_channel.py` has ideas on  
- SocketIO custom channel implimetation
- How to access customData from client
- How to pass custom data in messages so that its accessible in actions. [custom-connectors#metadata-on-messages](https://rasa.com/docs/rasa/connectors/custom-connectors#metadata-on-messages)

`actions/actions.py` has ideas on  
- How to implement a custom action
- How to access metadata from tracker

### points to remember
- register actions in `domain.yml` file
- uncomment `action_endpoint` in `endpoints.yml` file
- add/register custom channel in `credentials.yml` file. see [custom-connectors#credentials-for-custom-channels](https://rasa.com/docs/rasa/connectors/custom-connectors#credentials-for-custom-channels) for more info on the naming

### useful commands
- source venv/bin/activate
- rasa -h
- rasa init
- rasa train  
- rasa shell  
- rasa interactive  
- rasa run --cors "*"  
- rasa run actions  
- rasa run -vv  

*print whole properties of an object*  
from pprint import pprint  
pprint(vars(your_object))