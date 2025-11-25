# File: gui.py
# Description: Simple and clean Tkinter GUI for the Schedule Builder
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Modified: 2025-11-24

import tkinter as tk
from tkinter import ttk, messagebox
import re
from src.task_repo import TaskRepo
from src.categories import CategoryRepo


class SchedulerGUI:
    def __init__(self, master, user_id: int):
        # Create a new Toplevel window 
        self.root = tk.Toplevel(master)
        self.user_id = user_id
        
        # Initialize Repos
        self.repo = TaskRepo(user_id=user_id)
        self.category_repo = CategoryRepo(user_id=user_id)
        
        # Configure the pop-up window
        self.root.title("Manage Tasks - Schedule Builder")
        self.root.geometry("600x650")
        self.root.configure(bg="#ffffff")
        
        # Ensures the pop-up window stays on top and blocks interaction with the main CLI terminal
        self.root.grab_set()
        
        self.current_frame = None

        self.show_manage_tasks_menu()

    def clear(self):
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = tk.Frame(self.root, bg="#ffffff")
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_manage_tasks_menu(self):
        self.clear()
        
        tk.Button(self.current_frame, text="← Close GUI", command=self.root.destroy, 
                  font=("Helvetica", 10), bg="#ecf0f1", bd=0).pack(anchor="w", padx=10, pady=10)
                  
        tk.Label(self.current_frame, text="Manage Tasks", font=("Helvetica", 24, "bold"), 
                 bg="#ffffff").pack(pady=20)
                 
        btn_frame = tk.Frame(self.current_frame, bg="#ffffff")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="1. Add a new task", 
                  command=self.show_add_task,
                  font=("Helvetica", 12), width=25, bg="#3498db", fg="white", bd=0).pack(pady=5)
        tk.Button(btn_frame, text="2. View, Select, & Delete Tasks", 
                  command=self.show_tasks,
                  font=("Helvetica", 12), width=25, bg="#2ecc71", fg="white", bd=0).pack(pady=5)
                  
        tk.Button(btn_frame, text="3. Back to CLI", 
                  command=self.root.destroy,
                  font=("Helvetica", 12), width=25, bg="#e74c3c", fg="white", bd=0).pack(pady=5)
    
    def show_add_task(self):
        self.clear()
        
        # Back button - Navigates back to the GUI's menu
        tk.Button(self.current_frame, text="← Back", command=self.show_manage_tasks_menu, 
                  font=("Helvetica", 10), bg="#ecf0f1", bd=0).pack(anchor="w", padx=10, pady=10)
        
        tk.Label(self.current_frame, text="Add New Task", font=("Helvetica", 24, "bold"), 
                  bg="#ffffff").pack(pady=20)
        
        # Form
        form = tk.Frame(self.current_frame, bg="#ffffff")
        form.pack(pady=20)
        
        entries = {}
        fields = [
            ("Task Name:", "name"),
            ("Duration (minutes):", "duration"),
            ("Location:", "location"),
            ("Cost ($):", "cost"),
        ]
        
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, font=("Helvetica", 12), bg="#ffffff").grid(
                row=i, column=0, sticky="w", padx=10, pady=8)
            entry = tk.Entry(form, font=("Helvetica", 12), width=25)
            entry.grid(row=i, column=1, padx=10, pady=8)
            entries[key] = entry
        
        # Category dropdown
        tk.Label(form, text="Category:", font=("Helvetica", 12), bg="#ffffff").grid(
            row=len(fields), column=0, sticky="w", padx=10, pady=8)
        
        categories = self.category_repo.list_categories()
        cat_names = ["None"] + [cat[1] for cat in categories]
        cat_var = tk.StringVar(value="None")
        ttk.Combobox(form, textvariable=cat_var, values=cat_names, 
                      font=("Helvetica", 12), width=23, state="readonly").grid(
            row=len(fields), column=1, padx=10, pady=8)
        
        def save():
            name = entries["name"].get().strip()
            duration = entries["duration"].get().strip()
            
            if not name or not duration:
                messagebox.showerror("Error", "Name and duration required")
                return
            
            try:
                duration = int(duration)
                location = entries["location"].get().strip() or None
                # Clean cost input
                cost = re.sub('[^0-9,.]', '', entries["cost"].get().strip()) or None
                
                cat_id = None
                if cat_var.get() != "None":
                    for cat in categories:
                        if cat[1] == cat_var.get():
                            cat_id = cat[0]
                            break
                
                self.repo.add_task(name, duration, category_id=cat_id, 
                                   location=location, cost=cost)
                
                messagebox.showinfo("Success", "Task added!")
                self.show_manage_tasks_menu() # Navigate back to the GUI menu
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(self.current_frame, text="Save Task", command=save, font=("Helvetica", 14, "bold"),
                  bg="#27ae60", fg="white", width=15, height=2, bd=0).pack(pady=30)
    
    
    def show_tasks(self):
        self.clear()
        
        # Back button
        tk.Button(self.current_frame, text="← Back", command=self.show_manage_tasks_menu, 
                  font=("Helvetica", 10), bg="#ecf0f1", bd=0).pack(anchor="w", padx=10, pady=10)
        
        tk.Label(self.current_frame, text="My Tasks", font=("Helvetica", 24, "bold"), 
                  bg="#ffffff").pack(pady=20)
        
        # Task list
        frame = tk.Frame(self.current_frame, bg="#ffffff")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        listbox = tk.Listbox(frame, font=("Courier", 11), yscrollcommand=scrollbar.set,
                              selectmode=tk.SINGLE, height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        def refresh_list():
            listbox.delete(0, tk.END)
            all_tasks = self.repo.list_tasks() 
            
            tasks.clear()
            tasks.extend(all_tasks) 

            for task in tasks:
                task_id, name, duration, selected, task_type, fixed_time, cost = task
                check = "✓" if selected else "☐"
                listbox.insert(tk.END, f"{check} {name} ({duration}min) ${cost or 0}")

        tasks = [] 
        refresh_list()
        
        def toggle():
            sel = listbox.curselection()
            if sel:
                idx = sel[0]
                task_id = tasks[idx][0]
                self.repo.toggle_select(task_id)
                refresh_list()
            
        def delete():
            sel = listbox.curselection()
            if sel:
                idx = sel[0]
                task_id = tasks[idx][0]
                if messagebox.askyesno("Delete", "Delete this task?"):
                    self.repo.delete_task(task_id)
                    refresh_list()
        
        # Buttons
        btn_frame = tk.Frame(self.current_frame, bg="#ffffff")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Select/Unselect", command=toggle, font=("Helvetica", 11),
                  bg="#3498db", fg="white", width=15, bd=0).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Delete", command=delete, font=("Helvetica", 11),
                  bg="#e74c3c", fg="white", width=15, bd=0).pack(side=tk.LEFT, padx=5)