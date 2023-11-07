import socket
import json

SERVER_ADDRESS = ("localhost", 2004)


class Client:
    def __init__(self):
        self.userUID = None

    def register_user(self, username):
        response = self.send_request({"action": "register", "username": username})
        if response.get("success"):
            self.userUID = username  # Assuming the username is the user identifier
            return True, response.get("message")
        else:
            return False, response.get("message")

    def login_user(self, username):
        response = self.send_request({"action": "login", "username": username})
        if response.get("success"):
            self.userUID = username  # Assuming the username is the user identifier
            return True, response.get("message")
        else:
            return False, response.get("message")

    def get_latest_messages(self):
        if self.userUID:
            response = self.send_request(
                {"action": "get_messages", "userUID": self.userUID}
            )
            if response:
                return True, response
            else:
                return False, "No new messages."
        else:
            return False, "User is not logged in."

    def get_sent_messages(self):
        # This method's implementation would depend on how the server provides sent messages.
        # Assuming the server can send back sent messages with a specific request.
        if self.userUID:
            response = self.send_request(
                {"action": "get_sent_messages", "userUID": self.userUID}
            )
            return True, response
        else:
            return False, "User is not logged in."

    def write_message(self, receiverUID, message):
        # This method now accepts receiverUID and message as parameters.
        if self.userUID:
            response = self.send_request(
                {
                    "action": "send_message",
                    "userUID": self.userUID,
                    "recipient": receiverUID,
                    "message": message,
                }
            )
            return response.get("success"), response.get("message")
        else:
            return False, "User is not logged in."

    def send_request(self, request_data):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the server's address
        sock.connect(SERVER_ADDRESS)
        response_data = None
        try:
            # Send data as a JSON-encoded string
            message_json = json.dumps(request_data)
            sock.sendall(message_json.encode())
            # Receive the response from the server
            response = sock.recv(
                1024
            ).decode()  # Assuming the server sends back a JSON response
            if not response:
                print("Received an empty response from the server.")
                return None
            else:
                print(f"Response from server: {response}")
            response_data = json.loads(response)
            return response_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from server response: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_chat_list(self):
        # Send a request to the server to get the chat list excluding the current user
        response = self.send_request(
            {"action": "list_users", "exclude_user": self.userUID}
        )
        if response.get("success"):
            # Return the list of users, excluding the current user
            return True, response.get("users")
        else:
            return False, response.get("message")

    def send_message(self, recipient, message):
        # Construct the message request
        request = {
            "action": "send_message",
            "from_user": self.userUID,  # Ensure this is the correct way to reference the user's ID
            "to_user": recipient,
            "message": message,
        }
        # Send the request to the server
        response = self.send_request(request)
        if response and response.get("success"):
            return True, "Message sent successfully."
        elif response:
            return False, response.get("message")
        else:
            return False, "Failed to get a valid response from the server."

    def get_chat_history(self, partner):
        request = {
            "action": "get_chat_history",
            "userUID": self.userUID,
            "partner": partner,
        }
        response = self.send_request(request)
        if response and response.get("success"):
            return True, response.get("history")
        else:
            return (
                False,
                response.get("message") if response else "Failed to get chat history.",
            )
