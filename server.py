# Non-instant messaging system server
import datetime
from datetime import datetime
from socketserver import *
import os, socket

USER_DIR = "users"


class RequestHandler(BaseRequestHandler):
    # -------- Interactions with client -------- #
    def getLatestMessage(self, userUID):
        if userUID not in os.listdir(USER_DIR):
            self.request.sendall(b"User does not exist")
            return

        userDir = os.path.join(USER_DIR, userUID)
        unreadMessageDir = os.path.join(userDir, "unread")
        files = os.listdir(unreadMessageDir)

        if len(files) == 0:
            self.request.sendall(b"No new messages")
            return

        all_messages = []
        senderUID = ""
        filename = ""
        for file in files:
            message_path = os.path.join(unreadMessageDir, file)
            with open(message_path, "r") as message_file:
                lines = message_file.readlines()
                senderUID = lines[0].split("From:")[1].strip()
                filename = lines[1]
                file_obj = datetime.strptime(
                    filename.strip(), "Time: %d %m %Y at %H:%M:%S"
                )
                formatted_file = file_obj.strftime("%Y-%m-%d_%H-%M-%S")
                all_messages.extend(lines)
                message_file.close()
            if not "Read at:" in lines[-1]:
                with open(
                    os.path.join(USER_DIR, senderUID, "sent", formatted_file), "a"
                ) as message_file:
                    message_file.write(
                        "\nRead at: {}\n".format(
                            datetime.now().strftime("%d %m %Y at %H:%M:%S")
                        )
                    )
                    message_file.close()
            # Uncomment the line below if you wish to delete the message after reading
            # os.remove(message_path)

        response = "\\n".join(all_messages)
        self.request.sendall(response.encode("utf-8"))
        # self.request.shutdown(socket.SHUT_WR)

    def writeMessage(self, userUID, receiverUID, message):
        senderDir = os.path.join(USER_DIR, userUID)
        receiverDir = os.path.join(USER_DIR, receiverUID)

        if receiverUID not in os.listdir(USER_DIR):
            self.request.sendall(b"User does not exist")
            return

        if not os.path.exists(os.path.join(senderDir, "sent")):
            os.makedirs(os.path.join(senderDir, "sent"))

        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        open(os.path.join(receiverDir, "unread", filename), "w").write(
            "From: "
            + userUID
            + "\nTime: "
            + datetime.now().strftime("%d %m %Y at %H:%M:%S")
            + "\nMessage: "
            + message
            + "\n"
        )
        open(os.path.join(senderDir, "sent", filename), "w").write(
            "To: "
            + receiverUID
            + "\nTime: "
            + datetime.now().strftime("%d %m %Y at %H:%M:%S")
            + "\nMessage:"
            + message
        )
        self.request.sendall(b"Message sent successfully")

    def getSentMessages(self, senderUID):
        # Get the filepath for the sender's messages
        folderPath = os.path.join(USER_DIR, senderUID, "sent")

        sent_messages = []

        # Open the file and read all the messages
        for file in os.listdir(folderPath):
            with open(os.path.join(folderPath, file), "r") as fileReader:
                lines = fileReader.readlines()
                sent_messages.extend(lines)
        print(sent_messages)
        # If no messages found
        if not sent_messages:
            self.request.sendall("No sent messages.".encode())
        else:
            formatted_messages = "\n".join(sent_messages)
            self.request.sendall(formatted_messages.encode())

    def deleteMessage(self, userUID, messageID):
        pass

    def saveMessage(self, userUID, message):
        pass

    # -------- Facilities Functions -------- #
    def getFileFormat(self, filename):
        return filename.split(".")[-1]

    def handleRequestResponse(self, *_):
        try:
            self.request.sendall(b"Invalid command")
        except BrokenPipeError:
            print("Client disconnected unexpectedly.")
            return

    def registerUser(self, username, *args):
        print("Registering user: {}".format(username))
        if not os.path.exists(os.path.join(USER_DIR, username)):
            os.makedirs(os.path.join(USER_DIR, username))
            self.request.sendall(
                b"User registered successfully as " + username.encode("utf-8")
            )
            os.makedirs(os.path.join(USER_DIR, username, "messages"))
            os.makedirs(os.path.join(USER_DIR, username, "unread"))
        else:
            self.request.sendall(b"User already exists")

    def loginUser(self, username):
        if username in os.listdir(USER_DIR):
            self.request.sendall(username.encode("utf-8"))
        else:
            self.request.sendall(b"User does not exist")

    # Commands dictionary
    def __init__(self, request, client_address, server):
        self.commands = {
            "register": self.registerUser,
            "updates": self.getLatestMessage,
            "sent": self.getSentMessages,
            "delete": self.deleteMessage,
            "save": self.saveMessage,
            "login": self.loginUser,
            "write": self.writeMessage,
        }
        super().__init__(request, client_address, server)

    def handle(self):
        while True:
            # Receive request from client
            # Format: command [args]
            request = self.request.recv(1024).decode("utf-8")
            print("Request: {}".format(request))

            parts = request.split(" ")
            command = parts[0]
            args = parts[1:]

            handler = self.commands.get(command)
            if handler is not None:
                handler(*args)
            else:
                self.handleRequestResponse()
                break


if __name__ == "__main__":
    server = ThreadingTCPServer(("localhost", 2001), RequestHandler)

    print(
        "Server Address: {}:{}".format(
            server.server_address[0], server.server_address[1]
        )
    )

    server.serve_forever()
