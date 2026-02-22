import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog
import os, json, socket, threading, sys, time, traceback, io

class CheezzersAlpha:
    def __init__(self, root):
        self.root = root
        self.root.title("CHEEZZERS - ALPHA_0.4.3 (FULL INTEGRATION)")
        self.root.geometry("1100x800")
        
        self.port = 5005
        self.online_users = {}
        self.current_view = "editor" # 'editor' oder 'chat'
        
        self.load_settings()
        self.setup_ui()
        
        threading.Thread(target=self.network_listener, daemon=True).start()
        threading.Thread(target=self.broadcast_presence, daemon=True).start()

    def load_settings(self):
        self.config_file = "config.json"
        default = {"nickname": "User_" + str(time.time())[-4:], "font_size": 10, "last_dir": os.getcwd()}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: self.settings = json.load(f)
            except: self.settings = default
        else: self.settings = default

    def setup_ui(self):
        # MAIN CONTAINER (Verhindert Overlap)
        self.main_container = tk.Frame(self.root, bg="#ece9d8")
        self.main_container.pack(fill="both", expand=True)

        # SIDEBAR (Immer sichtbar)
        self.sidebar = tk.Frame(self.main_container, width=200, bg="#d6d3ce", relief="raised", bd=2)
        self.sidebar.pack(side="left", fill="y")
        
        tk.Label(self.sidebar, text="XP NAVIGATOR", bg="#0055e5", fg="white", font=("Tahoma", 8, "bold")).pack(fill="x")
        self.nav_btn = tk.Button(self.sidebar, text="GO TO CHAT 💬", bg="#ece9d8", command=self.toggle_view)
        self.nav_btn.pack(fill="x", padx=10, pady=10)

        tk.Label(self.sidebar, text="CONTACTS", bg="#7da2ce", fg="white", font=("Tahoma", 7, "bold")).pack(fill="x", pady=(10,0))
        self.user_listbox = tk.Listbox(self.sidebar, bg="white", font=("Tahoma", 8), bd=2, relief="sunken")
        self.user_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # CONTENT AREA (Hier wechseln Editor und Chat)
        self.content_frame = tk.Frame(self.main_container, bg="#ece9d8")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.setup_editor_view()
        self.setup_chat_view()
        self.show_editor() # Startansicht

    def setup_editor_view(self):
        self.editor_frame = tk.Frame(self.content_frame, bg="#ece9d8")
        tk.Label(self.editor_frame, text="PYTHON EDITOR", bg="#3a8a3a", fg="white", font=("Tahoma", 8, "bold")).pack(fill="x")
        
        self.editor = scrolledtext.ScrolledText(self.editor_frame, font=("Courier New", self.settings["font_size"]), bg="white", bd=2, relief="sunken")
        self.editor.pack(fill="both", expand=True, pady=2)
        
        tk.Button(self.editor_frame, text="▶ RUN CODE", bg="#ece9d8", bd=2, relief="raised", command=self.run_code).pack(fill="x")

    def setup_chat_view(self):
        self.chat_view_frame = tk.Frame(self.content_frame, bg="#ece9d8")
        tk.Label(self.chat_view_frame, text="MSN MESSENGER", bg="#0055e5", fg="white", font=("Tahoma", 8, "bold")).pack(fill="x")
        
        self.chat_display = scrolledtext.ScrolledText(self.chat_view_frame, height=20, state="disabled", bg="white")
        self.chat_display.pack(fill="both", expand=True, pady=2)
        
        # CHAT INPUT AREA
        input_area = tk.Frame(self.chat_view_frame, bg="#ece9d8")
        input_area.pack(fill="x", side="bottom")
        
        tk.Label(input_area, text="Drag .py file here or type:", bg="#ece9d8", font=("Tahoma", 7)).pack(anchor="w")
        self.chat_entry = tk.Entry(input_area, bd=2, relief="sunken")
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.chat_entry.bind("<Return>", lambda e: self.send_message())
        
        # Ermöglicht Drag & Drop Pfad-Erkennung
        self.chat_entry.bind("<Drop>", self.handle_drop) 

        tk.Button(input_area, text="SEND", bg="#d6d3ce", width=10, command=self.send_message).pack(side="right", padx=5)

    def handle_drop(self, event):
        file_path = event.data.strip('{ }')
        if file_path.endswith(".py"):
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                    self.chat_entry.delete(0, tk.END)
                    self.chat_entry.insert(0, f"[CODE]: {content[:50]}...")
                    self.pending_code = content # Speichert den Code zum Senden
            except: pass

    def toggle_view(self):
        if self.current_view == "editor": self.show_chat()
        else: self.show_editor()

    def show_editor(self):
        self.chat_view_frame.pack_forget()
        self.editor_frame.pack(fill="both", expand=True)
        self.nav_btn.config(text="GO TO CHAT 💬")
        self.current_view = "editor"

    def show_chat(self):
        self.editor_frame.pack_forget()
        self.chat_view_frame.pack(fill="both", expand=True)
        self.nav_btn.config(text="GO TO EDITOR 💻")
        self.current_view = "chat"

    def network_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.port))
        while True:
            data, addr = sock.recvfrom(4096)
            msg = data.decode()
            if msg.startswith("PING:"):
                self.online_users[addr] = msg[5:]
                self.update_user_list()
            elif msg.startswith("MSG:"):
                threading.Thread(target=lambda: os.system("beep -f 600 -l 150 || echo -e '\a'"), daemon=True).start()
                self.display_msg(f"{self.online_users.get(addr, addr)}: {msg[4:]}")

    def broadcast_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            sock.sendto(f"PING:{self.settings['nickname']}".encode(), ('<broadcast>', self.port))
            time.sleep(8)

    def update_user_list(self):
        self.user_listbox.delete(0, tk.END)
        for ip, name in self.online_users.items():
            self.user_listbox.insert(tk.END, f"🟢 {name} ({ip})")

    def send_message(self):
        content = self.chat_entry.get()
        if not content or not self.user_listbox.curselection(): return
        
        idx = self.user_listbox.curselection()
        target_ip = self.user_listbox.get(idx).split("(")[-1].strip(")")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(f"MSG:{content}".encode(), (target_ip, self.port))
        self.display_msg(f"You: {content}")
        self.chat_entry.delete(0, tk.END)

    def display_msg(self, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, text + "\n")
        self.chat_display.config(state="disabled"); self.chat_display.see(tk.END)

    def run_code(self):
        code = self.editor.get("1.0", tk.END)
        try: exec(code, {"tk": tk, "root": tk.Toplevel()})
        except: messagebox.showerror("Python Error", traceback.format_exc())

if __name__ == "__main__":
    root = tk.Tk()
    # Hinweis: Drag&Drop Pfade funktionieren nativ oft nur bei tkdnd. 
    # Alternativ kopiere den Pfad einfach in das Feld.
    app = CheezzersAlpha(root)
    root.mainloop()
