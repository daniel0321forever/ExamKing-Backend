import json
import random

import redis.cache

from gaming.models import User
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs

# redis 
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Set random seed based on current time
random.seed()

ROOM_PREFIX = "room"
ROOM_HOST_POSTFIX = "host"

class GameConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isMatched = False
        self.roomName = None

    def connect(self):
        """
        The behavior of the backend when client has connected to the game consumer. The following behavior is expected:

        1) We should check the client permission to join the game
        2) We would arrange client matching with a queue (explain later) using redis technique
        3) The client in a queue would create a group by its user_id. The client that match a queue would join the group with the queue's element user id

        ========================\n
        **Input Format**
        The following parameter should be added in the url
        - user: The id of the user
        - challenge: The challenge key\n

        **Return Format**
        1) For waiting response, the return format would be ```{ 'type': 'wait' }```
        2) For game starting response, the return format would be 
        ```
        {
            "type": 'start_game',
            "problems":[
                    {
                        'problem': '',
                        'options': ['','','',''],
                        'answer': 2
                    },
                    {
                        'problem': '',
                        'options': ['','','',''],
                        'answer': 1,
                    },
                ],
            "userIDs": ["Daniel", "Jimmy"],
        }
        ```

        ========================\n
        ### Queue Matching
        **Player enters queue**: When the first player joins, they are assigned to a queue.\n
        **Assign room ID**: The player is either assigned a new room ID (if they are the first) or matched with another player in the queue. The room ID would be the host userID\n
        **Remove matched players**: Once two players are assigned to the same room, remove them from the queue and establish the battle room.\n
        **Player cancelled**: If host player cancelled matching, we should record the roomName in redis server, while anyone match the cancelled room, they would move to the next room until the roomName is not recorded as cancelled.
        The roomName that has been matched as cancelled would then be remove from the cancelled record.
        """
        try:
            query = parse_qs(self.scope['query_string'].decode())
            
            # TODO: wrap in cleaner style
            self.username = query.get('user', None)
            challenge = query.get('challenge', None)

            if self.username is None:
                self.send("self.username is not provided in url")
                self.close()
            
            if challenge is None:
                self.send("challenge is not provided in url")
                self.close()
            
            self.username = self.username[0]
            challenge = challenge[0]
            
            # get waiting list
            self.challengeRoomKey = f'{challenge}_waiting'
            waitingRoom = r.lpop(self.challengeRoomKey)
            # print("\nget waiting ID", waitingRoom)

            # if no waiting list
            if waitingRoom is None:
                self.pushRoom(self.username)

            # if someone's waiting
            else:
                while r.get(waitingRoom.decode()):
                    # print(f"removing waiting room {waitingRoom.decode()}")
                    r.delete(waitingRoom.decode()) # remove canceled reord
                    waitingRoom = r.lpop(self.challengeRoomKey)

                    if waitingRoom is None:
                        break

                # if it does find match in waiting list
                if waitingRoom is not None:
                    self.roomName = waitingRoom.decode()
                # if it go the end of the waiting list but still does not find available room
                else:
                    self.pushRoom(self.username)

            async_to_sync(self.channel_layer.group_add)(
                self.roomName,
                self.channel_name,
            )

            self.accept()

            # if the player is host
            if waitingRoom is None:
                self.send(text_data=json.dumps({
                    "type": "wait",
                }))

            # if the player is guest who match the host
            else:
                # set group send to all consumer to set isMatched variable
                async_to_sync(self.channel_layer.group_send)(
                    self.roomName,
                    {
                        "type": "setIsMatched",
                        "isMatched": True
                    }
                )

                # TODO: read from database
                problems = None
                with open('gaming/problems.json', 'r') as f:
                    all_problems = json.load(f).get(challenge, None)

                    if all_problems is None:
                        print(f"error: challenge '{challenge}' is not found in problems.json")
                        self.send(json.dumps({"error": f"challenge '{challenge}' is not found in problems.json"}))
                        self.close()
                        return

                    problems = []

                    # randomize the problem and answer
                    for p in random.sample(all_problems, min(5, len(all_problems))):
                        ans = p['options'][p['answer']]
                        p['options'] = random.sample(p['options'], len(p['options']))
                        p['answer'] = p['options'].index(ans)
                        problems.append(p)

                hostUsername = r.get(f"{self.roomName}_{ROOM_HOST_POSTFIX}").decode()

                hostUser, created = User.objects.get_or_create(
                    username=hostUsername,
                    defaults={
                        "email": "computer@gmail.com", 
                        "name": "computer",
                    }
                )
                
                hostName = hostUser.name
                player, created = User.objects.get_or_create(
                    username=self.username,
                    defaults={
                        "email": "computer@gmail.com", 
                        "name": "computer",
                    }   
                )

                playerName = player.name

                async_to_sync(self.channel_layer.group_send)(
                    self.roomName,
                    {
                        "type": "startGame",
                        "problems": problems,
                        "usernames": [hostUsername, self.username],
                        "names": [hostName, playerName],
                    },
                )
                r.delete(f"{self.roomName}_{ROOM_HOST_POSTFIX}")

                
        except Exception as e:
            print(f"excepction {e} occurs as client connecting to GameConsumer")
            self.send(json.dumps({"error": f"exception {e} occurs as client connecting to game socket"}))
            self.close()

    def disconnect(self, code):
        """
        The behaviour of the consumer when its client has disconnected. The following behavoir is expected

        1) If it is the host that have not found match, the roomName would be recorded on redis cache, so that
        we could skip the room while it pop out from the queue
        
        """
        self.recordCancel()
        self.close()
    
    def receive(self, text_data=None, bytes_data=None):
        """
        The behavior of the backend when client has send to the game consumer. The following behavior is expected:

        1) The text message with json format including *score* and are received from the two clients
        2) A json format message that include the added_score and added_combo of the player who sent message are group_sent to both clients
        3) When both clients have sent the message to the server, the server would send message to both clients with "go next round" command
        4) NOTE: The end game message should be sent with http method, to avoid the repetition of memory update
        ========================\n
        ### Input format
        **Input**\n
        For answer type input, the format should be
        ```
        {
            'type': 'answer',
            'userID': daniel_00,
            'optionIndex': 2, # the index of the option that the user selected, could be null
            'score': 200,
        }
        ```
        ### Return Format
        For the answer type response, the format should be
        ```
        {
            'type': 'answer',
            'answered_user': answerUserId,
            'option_index': 2,
            'added_score': 200
        }
        ```
        """
        
        requiredField = ['type', 'userID', 'score']

        try:
            decodedContent = json.loads(text_data)
            contentType = decodedContent.get("type", None)

            if contentType is None:
                self.send(json.dumps({"error": "contentType field shoud not be None in json data"}))
                self.close()
                return
            
            # select content type
            if contentType == 'answer':
                # check if the required field is in the json data
                for field in requiredField:
                    if field not in decodedContent:
                        self.send(json.dumps({"error": f"required field '{field}' is not in the json data"}))
                        self.close()
                        return

                async_to_sync(self.channel_layer.group_send)(
                    self.roomName,
                    {
                        'type': 'answer',
                        'answered_user': decodedContent["userID"],
                        'option_index': decodedContent.get("optionIndex", None),
                        'added_score': decodedContent["score"],
                    }
                )

                return
            
            print("invalid contentType", contentType)
            self.send(json.dumps({"error": f"invalid contentType '{contentType}"}))
            self.close()


        except Exception as e:
            print(f"excepction '{e}' occurs as game consumer received data from client")
            self.send(json.dumps({'error': f"exception '{e}' occurs as game consumer received data from client"}))    

    def pushRoom(self, userID):
        hashedUserID = hash(userID)
        self.roomName = f"{ROOM_PREFIX}_{hashedUserID}_{self.challengeRoomKey}"
        r.rpush(self.challengeRoomKey, self.roomName)
        r.set(f"{self.roomName}_{ROOM_HOST_POSTFIX}", userID)

    def recordCancel(self):
        """
        Record the roomName in redis cache if the player is host and have not found match.
        The roomName being true means that the room has been cancelled, and the room corresponding to the roomName would be skipped
        when the consumer pop out the roomName from the redis cache.
        """
        # print("player disconnected!!!!")
        if not self.isMatched and self.roomName is not None: # the player is host and have been added to the waiting list with matching haven't occured yet
            # print(f"recording {self.roomName} to cancel table")
            r.set(self.roomName, 1) # The roomName being true means that the 
            r.delete(f"{self.roomName}_{ROOM_HOST_POSTFIX}")

    def answer(self, event):
        self.send(json.dumps({
            'type': 'answer',
            'answered_user': event.get('answered_user'),
            'added_score': event.get('added_score'),
            'option_index': event.get('option_index'),
        }))

    def startGame(self, event):
        self.send(json.dumps({
            'type': 'start_game',
            "problems": event["problems"],
            "usernames": event["usernames"],
            "names": event["names"],
        }))
    
    def setIsMatched(self, event):
        self.isMatched = event["isMatched"]