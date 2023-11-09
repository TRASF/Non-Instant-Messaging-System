import socket

SERVER_ADDRESS = ("localhost", 2001)

userUID = None


def send_request(command, args=[]):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect(SERVER_ADDRESS)

            request = f"{command} {' '.join(args)}"
            client_socket.sendall(request.encode("utf-8"))

            response = client_socket.recv(1024).decode("utf-8")
            return response

        except ConnectionRefusedError:
            print("Connection to the server was refused.")
        except Exception as e:
            print(f"An error occurred: {e}")


def register_user():
    global userUID
    username = input("Enter the username to register: ")
    userUID = send_request("register", [username])
    if not userUID == "User already exists":
        userUID = userUID.split(" ")[-1]
    else:
        print("User already exists.")


def login_user():
    global userUID
    username = input("Enter the username to login: ")
    userUID = send_request("login", [username])


def get_latest_messages():
    global userUID
    if not userUID:
        userUID = input("Enter your username: ")
    response = send_request("updates", [userUID])

    if response == "No new messages":
        print(response)
        return

    message_list = response.split("\n")

    senders = {}
    current_sender = None
    current_time = None
    current_message = None

    for line in message_list:
        if line.startswith("From:") or line.startswith("\\nFrom:"):
            # print("From line", line)
            current_sender = line.split("From:")[1].strip()
        elif line.startswith("\\nTime:") or line.startswith("Time:"):
            # print("Time", line)
            current_time = line.split("Time:")[1].strip()
        elif line.startswith("\\nMessage:") or line.startswith("Message:"):
            # print("Message", line)
            current_message = line.split("Message:")[1].strip()

            if current_sender and current_time and current_message:
                if current_sender not in senders:
                    senders[current_sender] = []
                senders[current_sender].append(
                    {"time": current_time, "message": current_message}
                )

                # Reset the variables after processing a complete message
                current_time = None
                current_message = None

    # Display the messages
    for sender, messages in senders.items():
        print("\n")
        print("=" * 50)
        print(f"\t\tMessages from {sender}:")
        print("=" * 50)
        for msg in messages:
            print(f"Time: {msg['time']}")
            print(f"Message: {msg['message']}")
            print("-" * 50)
        print("\n")


def get_read_messages():
    username = input("Enter your username: ")
    message = input("Enter the message to read: ")
    send_request("write", [username, message])


def get_sent_messages():
    global userUID
    if not userUID:
        userUID = input("Enter your username: ")
    messages = send_request("sent", [userUID])

    receiver = {}
    current_receiver = None
    current_message = None

    for line in messages.split("\n"):
        line = line.strip()  # Remove leading/trailing whitespace
        if line.startswith("To:"):
            if current_message:
                if current_receiver not in receiver:
                    receiver[current_receiver] = []
                receiver[current_receiver].append(current_message)
            current_receiver = line.split("To:")[1].strip()
            current_message = {"Receiver": current_receiver}
        elif line.startswith("Time:"):
            current_message["Time"] = line.split("Time:")[1].strip()
        elif line.startswith("Message:"):
            current_message["Message"] = line.split("Message:")[1].strip()
        elif line.startswith("Read at:"):
            current_message["Read"] = line.split("Read at:")[1].strip()

    # Append the last message
    if current_message:
        if current_receiver not in receiver:
            receiver[current_receiver] = []
        receiver[current_receiver].append(current_message)

    # Display the messages
    for receiver, messages in receiver.items():
        print("\n")
        print("=" * 50)
        print(f"\t\tMessages to {receiver}:")
        print("=" * 50)
        for msg in messages:
            print(f"Time: {msg.get('Time', '')}")
            print(f"Message: {msg.get('Message', '')}")
            if msg.get("Read"):
                print(f"Read at: {msg.get('Read', '')}")
            print("-" * 50)
        print("\n")


def delete_message():
    username = input("Enter your username: ")
    message_id = input("Enter message ID to delete: ")
    send_request("delete", [username, message_id])


def write_message():
    # The client should send a request to the server to write a message.
    # Including receiverUID and message
    receiverUID = input("Enter the receiverUID: ")
    message = input("Enter the message to send: ")
    send_request("write", [userUID, receiverUID, message])


def save_message():
    username = input("Enter your username: ")
    message = input("Enter the message to save: ")
    send_request("save", [username, message])


def main():
    global userUID
    while True:
        if (
            userUID == "User does not exist"
            or userUID == "User already exists"
            or userUID is None
        ):
            print("----" * 10)
            print("You are not logged in.")
            print("----" * 10)
            choice = input(
                """Available commands
                1. Register a User
                2. Login a User
                6. Exit 
                Enter your choice (1, 2, or 6): """
            )
        else:
            print("___" * 10)
            print(f"You are logged in as {userUID}")
            print("___" * 10)
            if userUID:  # Check if the user is logged in
                choice = input(
                    f"""Available commands
                    3. Get Latest Messages
                    4. Write a Message
                    5. Get Sent Messages
                    6. Exit 
                    Enter your choice (3-6): """
                )
            else:
                choice = input(
                    """Available commands
                    6. Exit 
                    Enter your choice (6): """
                )

        if choice == "1":
            register_user()
        elif choice == "2":
            login_user()
        elif choice == "3":
            get_latest_messages()
        elif choice == "4":
            write_message()
        elif choice == "5":
            get_sent_messages()
        elif choice == "6":
            print("Exiting the client.")
            break
        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
