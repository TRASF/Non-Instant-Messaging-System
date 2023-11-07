# server.py
import os
import json
import socket
import logging
from datetime import datetime
from socketserver import ThreadingMixIn, TCPServer, BaseRequestHandler
from pathlib import Path
import shutil

USER_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "users"
print(USER_DIR)


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    """Handle requests in a separate thread."""


def get_all_users(exclude_user=None):
    user_directory_path = USER_DIR
    all_users = [user.name for user in user_directory_path.iterdir() if user.is_dir()]
    if exclude_user:
        all_users = [user for user in all_users if user != exclude_user]
    return all_users


def get_chat_history(username, partner):
    messages = []
    user_dir = Path("users") / username / "read"
    partner_dir = Path("users") / partner / "read"

    # Read user's messages from the partner
    for message_file in user_dir.glob(f"{partner}_*.json"):
        with open(message_file, "r") as file:
            messages.append(json.load(file))

    # Read partner's messages to the user
    for message_file in partner_dir.glob(f"{username}_*.json"):
        with open(message_file, "r") as file:
            messages.append(json.load(file))

    # Sort messages by timestamp
    messages.sort(key=lambda msg: msg["timestamp"])

    return messages


def mark_message_as_read(user_dir, partner, message_filename):
    # Define the current time when the message is read
    read_time = datetime.now().strftime("%Y%m%d%H%M%S")
    unread_message_path = user_dir / "unread" / message_filename
    read_message_path = user_dir / "read" / message_filename

    # Load the message, add the read time
    with open(unread_message_path, "r") as file:
        message = json.load(file)

    message["read_at"] = read_time  # Add 'read_at' key

    # Write the updated message with the 'read_at' back to the file
    with open(unread_message_path, "w") as file:
        json.dump(message, file)

    # Move the file to the read directory
    shutil.move(str(unread_message_path), str(read_message_path))

    return message


def get_chat_history(username, partner):
    messages = []
    added_messages = set()
    user_dir = Path("users") / username
    partner_dir = Path("users") / partner

    # Read unread messages first, mark as read, then append to the messages list
    for message_file in user_dir.glob("unread/{}_*.json".format(partner)):
        message = mark_message_as_read(user_dir, partner, message_file.name)
        message_key = (
            message.get("from"),
            message.get("message"),
            message.get("sent_at"),
        )
        if message_key not in added_messages:
            messages.append(message)
            added_messages.add(message_key)

    # Read user's read messages from the partner
    for message_file in user_dir.glob("read/{}_*.json".format(partner)):
        with open(message_file, "r") as file:
            message = json.load(file)
            message_key = (
                message.get("from"),
                message.get("message"),
                message.get("sent_at"),
            )
            if message_key not in added_messages:
                messages.append(message)
                added_messages.add(message_key)

    # Read partner's messages to the user
    for message_file in partner_dir.glob("read/{}_*.json".format(username)):
        with open(message_file, "r") as file:
            message = json.load(file)
            message_key = (
                message.get("from"),
                message.get("message"),
                message.get("sent_at"),
            )
            if message_key not in added_messages:
                messages.append(message)
                added_messages.add(message_key)

    # Sort messages by 'sent_at' instead of 'timestamp'
    messages.sort(key=lambda msg: msg["sent_at"])

    return messages


class RequestHandler(BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        data = json.loads(data.decode("utf-8"))
        if data["action"] == "register":
            self.handle_register(data["username"])
        elif data["action"] == "login":
            self.handle_login(data["username"])
        elif data["action"] == "get_messages":
            self.get_latest_messages(data["userUID"])
        elif data["action"] == "send_message":
            self.send_message(data["from_user"], data["to_user"], data["message"])
        elif data["action"] == "list_users":
            self.list_users(data.get("exclude_user"))
        elif data["action"] == "get_chat_history":
            chat_history = get_chat_history(data["userUID"], data["partner"])
            response = json.dumps({"success": True, "history": chat_history})
            self.request.sendall(response.encode())

    def handle_login(self, username):
        user_dir = USER_DIR / username
        if user_dir.exists():
            self.request.sendall(
                json.dumps({"success": True, "message": "User logged in"}).encode()
            )
        else:
            self.request.sendall(
                json.dumps(
                    {"success": False, "message": "User does not exist"}
                ).encode()
            )

    def handle_register(self, username):
        user_dir = USER_DIR / username
        if not user_dir.exists():
            os.makedirs(user_dir)
            os.makedirs(user_dir / "unread")
            os.makedirs(user_dir / "read")
            self.request.sendall(
                json.dumps({"success": True, "message": "User registered"}).encode()
            )
        else:
            self.request.sendall(
                json.dumps(
                    {"success": False, "message": "Username already taken"}
                ).encode()
            )

    def get_latest_messages(self, userUID):
        user_dir = USER_DIR / userUID
        unread_dir = user_dir / "unread"
        read_dir = user_dir / "read"
        unread_messages = list(unread_dir.glob("*"))
        messages = []
        for message_file in unread_messages:
            with message_file.open() as mf:
                message = json.load(mf)
                message["read_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                messages.append(message)
            read_message_file = read_dir / message_file.name
            message_file.rename(read_message_file)
        self.request.sendall(json.dumps(messages).encode())

    def send_message(self, userUID, recipient, message_content):
        recipient_dir = USER_DIR / recipient / "unread"
        if not recipient_dir.exists():
            self.request.sendall(
                json.dumps(
                    {"success": False, "message": "Recipient does not exist"}
                ).encode()
            )
            return
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        message_filename = f"{userUID}_{timestamp}.json"
        message_file_path = recipient_dir / message_filename
        with message_file_path.open("w") as message_file:
            json.dump(
                {"from": userUID, "message": message_content, "sent_at": timestamp},
                message_file,
            )
        self.request.sendall(
            json.dumps({"success": True, "message": "Message sent"}).encode()
        )

    def list_users(self, exclude_user):
        user_list = get_all_users(exclude_user=exclude_user)
        self.request.sendall(json.dumps({"success": True, "users": user_list}).encode())


def run_server(host="0.0.0.0", port=2004):
    server = ThreadedTCPServer((host, port), RequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
