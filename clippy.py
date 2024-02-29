import os
import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import ttk, messagebox
import pyperclip

class RemovableListbox(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.tree = ttk.Treeview(self, columns=('File', 'Select'), show='headings')
        self.tree.heading('File', text='File Path')
        self.tree.heading('Select', text='Select')
        self.tree.column('Select', width=50, anchor='center')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.config(yscrollcommand=self.scrollbar.set)
        
        self.remove_button = ttk.Button(self, text='Remove', command=self.remove_item)
        self.remove_button.pack(side=tk.BOTTOM)

        self.tree.bind('<Double-1>', self.toggle_select)  # Bind double-click event to toggle_select method

    def insert(self, file_path):
        self.tree.insert('', 'end', values=(file_path, "True"))  # Use string "True" for visual representation

    def remove_item(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            self.tree.delete(item)

    def toggle_select(self, event):
        # Get the item row and column clicked
        row_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if self.tree.heading(column_id)['text'] == 'Select':  # Check if the 'Select' column was clicked
            current_value = self.tree.item(row_id, 'values')[1]
            new_value = "False" if current_value == "True" else "True"  # Toggle between "True" and "False"
            self.tree.item(row_id, values=(self.tree.item(row_id, 'values')[0], new_value))

def copy_to_clipboard():
    try:
        selected_items = listbox.tree.selection()
        if not selected_items:  # Check if the selection is empty
            messagebox.showwarning("Warning", "No file selected.")
            return
        pyperclip.copy('')  # Clear the clipboard before copying new content
        full_contents = ""  # Initialize an empty string to hold all file contents
        for item in selected_items:
            file_path, selected = listbox.tree.item(item, 'values')
            if selected == "True":  # Ensure the selected value is checked as a string "True"
                header = f"##file:{os.path.basename(file_path)}\n\n"  # Prepends the file name as a header
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read()
                full_contents += header + file_content + "\n\n"  # Append this file's content to the full contents
        if full_contents:  # Check if there's anything to copy
            pyperclip.copy(full_contents)  # Copy all selected files' contents at once
            # messagebox.showinfo("Success", "Selected files' content copied to clipboard.")
        else:
            messagebox.showwarning("Warning", "No files were selected or files selected have no content.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def drop(event):
    if event.data:
        file_paths = root.tk.splitlist(event.data)
        for file_path in file_paths:
            listbox.insert(file_path)

# Setup TkinterDnD window
root = TkinterDnD.Tk()
root.title('Clipboard Buddy')

# Layout
listbox = RemovableListbox(root)
listbox.pack(fill='both', expand=True, padx=10, pady=10)
copy_button = ttk.Button(root, text='Copy to Clipboard', command=copy_to_clipboard)
copy_button.pack(pady=5)

# Drag and Drop setup
listbox.tree.drop_target_register(DND_FILES)
listbox.tree.dnd_bind('<<Drop>>', drop)

root.mainloop()