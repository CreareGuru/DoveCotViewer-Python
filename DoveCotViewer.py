import os
import mailparser
import ttkbootstrap as ttk
from ttkbootstrap import Style
from tkinter import filedialog, Listbox
from bs4 import BeautifulSoup
from datetime import datetime

class DovecotMailViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Dovecot Mail Viewer")
        self.root.geometry("1000x600")

        # Apply ttkbootstrap style
        self.style = Style(theme="solar")

        # Main Paned Window (Resizable)
        self.paned_window = ttk.PanedWindow(root, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True)

        # Folder Structure Frame
        self.folder_frame = ttk.Frame(self.paned_window, width=200)
        self.paned_window.add(self.folder_frame, weight=1)

        # Mail List Frame
        self.mail_list_frame = ttk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.mail_list_frame, weight=2)

        # Mail View Frame
        self.mail_view_frame = ttk.Frame(self.paned_window, width=500)
        self.paned_window.add(self.mail_view_frame, weight=3)

        # Load Maildir Button
        self.load_button = ttk.Button(root, text="Load Maildir", command=self.load_maildir)
        self.load_button.pack(fill="x")

        # Folder Structure (Treeview)
        self.tree = ttk.Treeview(self.folder_frame, show="tree")
        self.tree.heading("#0", text="Mail Folders", anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.load_mail_list)

        # Mail Listbox (Using tkinter Listbox)
        self.listbox = Listbox(self.mail_list_frame, selectmode="browse")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.display_email)

        # Scrollbar for Listbox
        self.scrollbar = ttk.Scrollbar(self.mail_list_frame, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Mail View (Headers + Body)
        self.textbox = ttk.Text(self.mail_view_frame, wrap="word")
        self.textbox.pack(fill="both", expand=True)

        # Storage
        self.maildir_path = None
        self.current_folder = None
        self.emails = []

    def load_maildir(self):
        """Select Maildir Folder and Populate Folder Tree"""
        self.maildir_path = filedialog.askdirectory(title="Select Dovecot Maildir Folder")
        if not self.maildir_path:
            return

        self.tree.delete(*self.tree.get_children())

        # Add Maildir structure to the tree
        for folder in os.listdir(self.maildir_path):
            folder_path = os.path.join(self.maildir_path, folder)
            if os.path.isdir(folder_path):
                self.tree.insert("", "end", folder, text=folder)

    def load_mail_list(self, event):
        """Load emails when a folder is selected"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        self.current_folder = selected_item[0]
        folder_path = os.path.join(self.maildir_path, self.current_folder)

        self.listbox.delete(0, "end")
        self.emails = []

        mail_files = []
        for subfolder in ["cur", "new"]:
            sub_path = os.path.join(folder_path, subfolder)
            if os.path.exists(sub_path):
                mail_files.extend([os.path.join(sub_path, f) for f in os.listdir(sub_path)])

        for mail_file in mail_files:
            try:
                mail = mailparser.parse_from_file(mail_file)
                mail_date = mail.date or "Unknown Date"
                
                if isinstance(mail_date, datetime):
                    mail_date = mail_date.strftime("%Y-%m-%d %H:%M")
                elif isinstance(mail_date, str):
                    try:
                        parsed_date = datetime.strptime(mail_date, "%a, %d %b %Y %H:%M:%S %z")
                        mail_date = parsed_date.strftime("%Y-%m-%d %H:%M")
                    except:
                        mail_date = "Unknown Date"

                subject = mail.subject or "(No Subject)"
                display_text = f"[{mail_date}] {subject}"

                self.listbox.insert("end", display_text)
                self.emails.append(mail_file)
            except Exception as e:
                print(f"Error reading {mail_file}: {e}")

    def display_email(self, event):
        """Show email headers and content when selected"""
        selection = self.listbox.curselection()
        if not selection:
            return

        mail_file = self.emails[selection[0]]
        try:
            mail = mailparser.parse_from_file(mail_file)

            # Extract all headers (including non-standard ones)
            headers = mail.headers

            headers_text = "\n".join(f"{key}: {value}" for key, value in headers.items() if value)

            # Extract Body (Plain or HTML)
            email_body = mail.text_plain[0] if mail.text_plain else None
            if not email_body and mail.text_html:
                soup = BeautifulSoup(mail.text_html[0], "html.parser")
                email_body = soup.get_text(separator="\n", strip=True)

            email_body = email_body or "(No Body Found)"

            # Combine Headers + Body
            email_content = f"{headers_text}\n\n{'-'*40}\n\n{email_body}"

            self.textbox.delete(1.0, "end")
            self.textbox.insert("end", email_content)
        except Exception as e:
            self.textbox.delete(1.0, "end")
            self.textbox.insert("end", f"Error reading email: {e}")

if __name__ == "__main__":
    root = ttk.Window(themename="solar")
    app = DovecotMailViewer(root)
    root.mainloop()
