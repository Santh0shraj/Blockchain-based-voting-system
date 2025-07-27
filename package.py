import hashlib
import json
import threading
import os
import tkinter as tk
from tkinter import messagebox



BG_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
BUTTON_TEXT_COLOR = "white"
LABEL_COLOR = "#333333"
ENTRY_BG = "white"
ENTRY_FG = "black"
FONT = ("Arial", 12)
TITLE_FONT = ("Arial", 16, "bold")
VOTER_ID_FILE = "voter_ids.txt"
ELECTION_DURATION = 120  # 1 minute in seconds

class Block:
    def __init__(self, index, previous_hash, votes):
        self.index = index
        self.previous_hash = previous_hash
        self.votes = votes
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "votes": self.votes,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_data).hexdigest()

    def mine_block(self, difficulty):
        while self.hash[:difficulty] != "0" * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.lock = threading.Lock()
        self.file_path = "blockchain_data.json"
        self.load_chain()

    def create_genesis_block(self):
        return Block(0, "0", [])

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, votes):
        with self.lock:
            new_block = Block(len(self.chain), self.get_latest_block().hash, votes)
            new_block.mine_block(self.difficulty)
            self.chain.append(new_block)
            self.save_chain()

    def save_chain(self):
        with open(self.file_path, "w") as file:
            chain_data = [vars(block) for block in self.chain]
            json.dump(chain_data, file, indent=4)

    def load_chain(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as file:
                chain_data = json.load(file)
                self.chain = [Block(block["index"], block["previous_hash"], block["votes"]) for block in chain_data]

    def get_votes(self):
        votes_count = {}
        for block in self.chain:
            for vote in block.votes:
                votes_count[vote] = votes_count.get(vote, 0) + 1
        return votes_count

    def validate_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True


class VotingApp:
    def __init__(self, root):
        self.blockchain = Blockchain()
        self.valid_voter_ids = self.load_voter_ids()
        self.voted_users = []
        self.logged_in_user = None
        self.root = root
        self.root.title("Blockchain Voting System")
        self.election_time_over = False
        self.time_remaining = ELECTION_DURATION

        self.candidates = ["Alice", "Bob", "Charlie"]  # Define candidates here

        self.setup_login_frame()
        threading.Thread(target=self.start_election_timer).start()

    def setup_login_frame(self):
        self.login_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.login_frame.pack(pady=50)

        tk.Label(self.login_frame, text="Voter ID:", font=FONT, fg=LABEL_COLOR, bg=BG_COLOR).grid(row=0, column=0, padx=10, pady=5)
        
        # Timer display on the login screen
        self.timer_label = tk.Label(self.login_frame, text=f"Time Remaining: {self.time_remaining} seconds", font=FONT, fg=LABEL_COLOR, bg=BG_COLOR)
        self.timer_label.grid(row=1, column=0, columnspan=2)

        # Voter ID entry field and buttons
        self.voter_id_entry = tk.Entry(self.login_frame, font=FONT, bg=ENTRY_BG, fg=ENTRY_FG)
        self.voter_id_entry.grid(row=2, column=0, padx=10, pady=5)

        tk.Button(self.login_frame, text="Login", command=self.login, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR, font=FONT).grid(row=3, column=0, columnspan=2)
        tk.Button(self.login_frame, text="Register Voter ID", command=self.open_registration_window, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR, font=FONT).grid(row=4, column=0, columnspan=2, pady=5)
        
    def load_voter_ids(self):
        if os.path.exists(VOTER_ID_FILE):
            with open(VOTER_ID_FILE) as file:
                return [line.strip() for line in file]
        return []

    def save_voter_ids(self):
        with open(VOTER_ID_FILE, "w") as file:
            for voter_id in self.valid_voter_ids:
                file.write(voter_id + "\n")
                
    def load_voted_users(self):
        if os.path.exists("voted_users.json"):
            with open("voted_users.json", "r") as file:
                return json.load(file)
        return []

    def save_voted_users(self):
        with open("voted_users.json", "w") as file:
            json.dump(self.voted_users, file)

    def login(self):
        voter_id = self.voter_id_entry.get()
        if voter_id in self.valid_voter_ids:
            self.logged_in_user = voter_id
            self.login_frame.pack_forget()
            self.show_main_frame()
        else:
            messagebox.showerror("Invalid Credentials", "Invalid Voter ID.")

    def show_main_frame(self):
        self.main_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.main_frame.pack(pady=50)

        tk.Label(self.main_frame, text="Select Candidate:", font=TITLE_FONT, fg=LABEL_COLOR, bg=BG_COLOR).pack(pady=10)

        self.selected_candidate = tk.StringVar(value=self.candidates[0])

        for candidate in self.candidates:
            tk.Radiobutton(self.main_frame, text=candidate, variable=self.selected_candidate, value=candidate, font=FONT, fg=LABEL_COLOR, bg=BG_COLOR).pack(anchor=tk.W, padx=20)

        tk.Button(self.main_frame, text="Vote", command=self.cast_vote, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR, font=FONT).pack(pady=10)
        tk.Button(self.main_frame, text="Logout", command=self.logout, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR, font=FONT).pack(pady=10)



    def cast_vote(self):
        if self.logged_in_user and self.logged_in_user not in self.voted_users and not self.election_time_over:
            vote = self.selected_candidate.get()
            threading.Thread(target=self.blockchain.add_block, args=([vote],)).start()
            self.voted_users.append(self.logged_in_user)
            self.save_voted_users()
            messagebox.showinfo("Vote Cast", f"You voted for {vote}.")
            self.logout()
        elif self.election_time_over:
            messagebox.showerror("Election Over", "The election has ended.")
        elif self.logged_in_user in self.voted_users:
            messagebox.showerror("Already Voted", "You have already cast your vote.")
        else:
            messagebox.showerror("Not Logged In", "You must be logged in to vote.")

    def logout(self):
        self.logged_in_user = None
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()
        self.login_frame.pack(pady=50)

    def open_registration_window(self):
        registration_window = tk.Toplevel(self.root)
        registration_window.title("Register Voter ID")
        registration_window.configure(bg=BG_COLOR)

        tk.Label(registration_window, text="Enter Voter ID to Register:", font=FONT, fg=LABEL_COLOR, bg=BG_COLOR).pack(pady=10)
        new_voter_id_entry = tk.Entry(registration_window, font=FONT, bg=ENTRY_BG, fg=ENTRY_FG)
        new_voter_id_entry.pack(pady=5)

        def register():
            new_voter_id = new_voter_id_entry.get()
            if new_voter_id and new_voter_id not in self.valid_voter_ids:
                self.valid_voter_ids.append(new_voter_id)
                self.save_voter_ids()
                messagebox.showinfo("Registration Successful", "Voter ID registered successfully.")
                registration_window.destroy()
            elif new_voter_id in self.valid_voter_ids:
                messagebox.showerror("Registration Error", "Voter ID already registered.")
            else:
                messagebox.showerror("Registration Error", "Please enter a Voter ID.")

        tk.Button(registration_window, text="Register", command=register, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR, font=FONT).pack(pady=10)

    def start_election_timer(self):
        while self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_timer_label()
            time.sleep(1)
        self.end_election()
    
    def update_timer_label(self):
        self.timer_label.config(text=f"Time Remaining: {self.time_remaining} seconds")



    def end_election(self):
        self.election_time_over = True
        results = self.blockchain.get_votes()
        
        if results:
            winner = max(results, key=results.get)
            messagebox.showinfo("Election Results", f"The winner is {winner}!")
        else:
            messagebox.showinfo("Election Results", "No votes were cast.")
        
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()
        self.login_frame.pack(pady=50)


if __name__ == "__main__":
    root = tk.Tk()

    # Create a voter_ids.txt file with some valid IDs if it doesn't exist
    if not os.path.exists(VOTER_ID_FILE):
        with open(VOTER_ID_FILE, "w") as f:
            f.write("12345\n67890\n54321\n")

    app = VotingApp(root)
    import time
    root.mainloop()
