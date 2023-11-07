import tkinter as tk
from tkinter import ttk

from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import functions as f
from datetime import datetime
import sv_ttk


def convert_timestamp(timestamp_str):
    # Parse the timestamp to a datetime object
    dt_object = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    # Convert the datetime object to the desired string format
    return dt_object.strftime("%b %d, %Y, %I:%M:%S %p")


class MessagingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Messaging App")
        self.geometry("400x600")

        # self.tk.call("source", "./Azure-ttk-theme-2.1.0/azure.tcl")
        # # ttk.Style().theme_use("azure")
        sv_ttk.use_dark_theme()

        self.username = None
        self.chat_partner = None
        self.init_login_interface()
        self.client = f.Client()

    def init_login_interface(self):
        for widget in self.winfo_children():
            widget.destroy()

        login_frame = tk.Frame(self)
        login_frame.pack(pady=20)

        ttk.Label(login_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1)
        self.username_entry.focus_set()

        ttk.Button(login_frame, text="Login", command=self.login).grid(row=1, column=0)
        ttk.Button(login_frame, text="Register", command=self.register).grid(
            row=1, column=1
        )

    def show_chat_list(self):
        # Clear the current GUI
        for widget in self.winfo_children():
            widget.destroy()

        # Set up the chat list GUI
        chat_list_frame = tk.Frame(self)
        chat_list_frame.pack(pady=20)

        style = ttk.Style()
        style.configure("CustomListbox.TListbox", background="white", borderwidth=0)

        self.chat_listbox = tk.Listbox(
            chat_list_frame,
            height=15,
            width=50,
            bd=1,
            highlightthickness=0,
            selectbackground="#b6d7a8",
            activestyle="none",
            exportselection=False,
            relief="flat",
        )
        self.chat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Button(
            chat_list_frame, text="Back", command=self.init_login_interface
        ).pack(side=tk.BOTTOM)

        # Retrieve the chat list from the server and update the chat listbox
        success, chat_list = self.client.get_chat_list()
        if success:
            self.update_chat_list(chat_list)
        else:
            messagebox.showerror("Error", "Could not retrieve chat list.")

        self.chat_listbox.bind("<Double-Button-1>", self.on_select_chat_partner)

        # Add a refresh button
        refresh_button = ttk.Button(
            chat_list_frame, text="Refresh", command=self.refresh_chat_list
        )
        refresh_button.pack(side=tk.BOTTOM)

    def update_chat_list(self, chat_list):
        self.chat_listbox.delete(0, tk.END)  # Clear the current list
        for chat_partner in chat_list:
            self.chat_listbox.insert(tk.END, chat_partner)

    def refresh_chat_list(self):
        success, chat_list = self.client.get_chat_list()
        if success:
            self.update_chat_list(chat_list)
        else:
            messagebox.showerror("Error", "Could not refresh chat list.")

    def on_select_chat_partner(self, event):
        selection = self.chat_listbox.curselection()
        if selection:
            index = selection[0]
            self.chat_partner = self.chat_listbox.get(index)
            self.show_chat_history(self.chat_partner)

    def show_chat_history(self, target_user):
        for widget in self.winfo_children():
            widget.destroy()

        chat_frame = ttk.Frame(self)
        style = ttk.Style()
        chat_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        style.configure("CustomText.TText", background="white", borderwidth=0)
        self.chat_text = ScrolledText(chat_frame, state="disabled", height=20, width=50)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.message_entry = ttk.Entry(chat_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.focus_set()

        ttk.Button(chat_frame, text="Send", command=self.send_message).pack(
            side=tk.LEFT
        )
        ttk.Button(chat_frame, text="Back", command=self.show_chat_list).pack(
            side=tk.BOTTOM
        )

        # Fetch the chat history from the server and display it
        success, chat_history = self.client.get_chat_history(target_user)
        if success:
            self.display_chat_history(
                chat_history
            )  # Call the function to display the history
        else:
            messagebox.showerror("Error", "Could not retrieve chat history.")

    def display_chat_history(self, chat_history):
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", tk.END)  # Clear existing text

        for message in chat_history:
            sender = message["from"]
            content = message["message"]
            sent_at = convert_timestamp(message["sent_at"])
            read_at = message.get("read_at")

            display_message = f"{sent_at} {sender}: {content}"
            if read_at:
                read_at_formatted = convert_timestamp(read_at)
                display_message += f" (Read at: {read_at_formatted})"

            self.chat_text.insert(tk.END, f"{display_message}\n")

        self.chat_text.yview(tk.END)  # Scroll to the bottom
        self.chat_text.configure(state="disabled")

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            # Send the message to the server
            success, response_message = self.client.send_message(
                self.chat_partner, message
            )
            if success:
                self.message_entry.delete(0, "end")  # Clear the input field
                self.update_chat_history(
                    self.chat_partner, message
                )  # Update the chat history with the new message
            else:
                messagebox.showerror("Error", response_message)
        else:
            messagebox.showwarning("Warning", "You cannot send an empty message.")

    def update_chat_history(self, target_user, message):
        # This method should be updated to actually fetch and display the chat history
        # For now, it simply appends the new message to the chat history text box
        self.chat_text.configure(state="normal")
        self.chat_text.insert(tk.END, f"{self.username}: {message}\n")
        self.chat_text.yview(tk.END)  # Scroll to the bottom
        self.chat_text.configure(state="disabled")

    def login(self):
        self.username = self.username_entry.get()
        if self.username:
            success, message = self.client.login_user(self.username)
            if success:
                self.show_chat_list()
            else:
                messagebox.showerror("Login Failed", message)
        else:
            messagebox.showerror("Login Failed", "Please enter a username.")

    def register(self):
        self.username = self.username_entry.get()
        if self.username:
            success, message = self.client.register_user(self.username)
            if success:
                self.show_chat_list()
            else:
                messagebox.showerror("Registration Failed", message)
        else:
            messagebox.showerror("Registration Failed", "Please enter a username.")

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


if __name__ == "__main__":
    app = MessagingApp()
    app.mainloop()
