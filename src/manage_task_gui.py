# File: gui.py
# Description: Simple and clean Tkinter GUI for the Schedule Builder
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Modified: 2025-11-24

import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime
# Assuming TaskRepo and CategoryRepo are in src/
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
        
        # 1. Add a new task (CLI 1)
        tk.Button(btn_frame, text="1. Add a new task", 
                  command=self.show_add_task,
                  font=("Helvetica", 12), width=30, bg="#3498db", fg="white", bd=0).pack(pady=5)
        
        # 2/3/4. View, Select, & Delete Tasks
        tk.Button(btn_frame, text="2. View, Select, & Delete Tasks", 
                  command=self.show_tasks,
                  font=("Helvetica", 12), width=30, bg="#2ecc71", fg="white", bd=0).pack(pady=5)
                  
        # 7. Back to CLI
        tk.Button(btn_frame, text="3. Back to CLI", 
                  command=self.root.destroy,
                  font=("Helvetica", 12), width=30, bg="#e74c3c", fg="white", bd=0).pack(pady=5)
        
    def show_add_task(self):
        self.clear()
        
        # Back button - Navigates back to the GUI's menu
        tk.Button(self.current_frame, text="← Back", command=self.show_manage_tasks_menu, 
                  font=("Helvetica", 10), bg="#ecf0f1", bd=0).pack(anchor="w", padx=10, pady=10)
        
        tk.Label(self.current_frame, text="Add New Task", font=("Helvetica", 24, "bold"), 
                  bg="#ffffff").pack(pady=20)
        
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
        
        tk.Button(self.current_frame, text="← Back", command=self.show_manage_tasks_menu, 
                  font=("Helvetica", 10), bg="#ecf0f1", bd=0).pack(anchor="w", padx=10, pady=10)
        
        tk.Label(self.current_frame, text="My Tasks", font=("Helvetica", 24, "bold"), 
                  bg="#ffffff").pack(pady=20)
        
        frame = tk.Frame(self.current_frame, bg="#ffffff")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, font=("Courier", 11), yscrollcommand=scrollbar.set,
                             selectmode=tk.SINGLE, height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        tasks = [] # To store task objects corresponding to listbox items
        
        def refresh_list():
            listbox.delete(0, tk.END)
            # Retrieve all task data from the repository
            all_tasks = self.repo.list_tasks() 
            
            tasks.clear()
            tasks.extend(all_tasks) 

            # Header for clarity
            listbox.insert(tk.END, f"{'ID':<4} {'Sel':<3} {'Task Name':<30} {'Dur':<4} {'Type':<8} {'Fixed Time':<12}")
            listbox.insert(tk.END, "-" * 70)
            
            for task in tasks:
                task_id, name, duration, selected, task_type, fixed_time, cost = task
                check = "✓" if selected else "☐"
                
                # Format fixed time for display
                fixed_time_display = ""
                if task_type == 'fixed' and fixed_time:
                    try:
                        # fixed_time is stored as HH:MM (24-hour)
                        time_obj = datetime.strptime(fixed_time, "%H:%M")
                        fixed_time_display = time_obj.strftime("%I:%M %p") # Display as 12-hour
                    except ValueError:
                        fixed_time_display = "Error"
                        
                duration_str = f"{duration}m"
                
                listbox.insert(tk.END, 
                               f"{str(task_id):<4} {check:<3} {name:<30} {duration_str:<4} "
                               f"{task_type or 'flexible':<8} {fixed_time_display:<12}")

        refresh_list()
        
        def toggle():
            sel = listbox.curselection()
            if sel and sel[0] > 1: # Ignore header rows
                idx = sel[0] - 2 
            
                if idx < len(tasks):
                    task_id = tasks[idx][0]
                    self.repo.toggle_select(task_id)
                    refresh_list()
                else:
                    messagebox.showerror("Error", "Invalid task selection.")
            
        def delete():
            sel = listbox.curselection()
            if sel and sel[0] > 1: # Ignore header rows
                idx = sel[0] - 2
                
                if idx < len(tasks):
                    task_id = tasks[idx][0]
                    if messagebox.askyesno("Delete", f"Delete task ID {task_id}?"):
                        self.repo.delete_task(task_id)
                        refresh_list()
                else:
                    messagebox.showerror("Error", "Invalid task selection.")
        
        # Buttons
        btn_frame = tk.Frame(self.current_frame, bg="#ffffff")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Select/Unselect", command=toggle, font=("Helvetica", 11),
                  bg="#3498db", fg="white", width=15, bd=0).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Delete", command=delete, font=("Helvetica", 11),
                  bg="#e74c3c", fg="white", width=15, bd=0).pack(side=tk.LEFT, padx=5)
                  
        # New Button to jump to the Type Setting menu for the selected item
        def edit_type_for_selected():
             sel = listbox.curselection()
             if sel and sel[0] > 1: # Ignore header rows
                idx = sel[0] - 2 
                if idx < len(tasks):
                    task_id = tasks[idx][0]
                    self.show_set_task_type_menu(initial_task_id=task_id)
                else:
                    messagebox.showerror("Error", "Please select a valid task.")
             else:
                messagebox.showerror("Selection Required", "Please select a task from the list first.")

        tk.Button(btn_frame, text="Change Type", command=edit_type_for_selected, font=("Helvetica", 11),
                  bg="#f39c12", fg="white", width=15, bd=0).pack(side=tk.LEFT, padx=5)

    
    def show_set_task_type_menu(self, initial_task_id=None):
        self.clear()
        
        # Back button
        tk.Button(self.current_frame, text="← Back to Menu", command=self.show_manage_tasks_menu, 
                  font=("Helvetica", 10), bg="#ecf0f1", bd=0).pack(anchor="w", padx=10, pady=10)
        
        tk.Label(self.current_frame, text="Set Task Type", font=("Helvetica", 24, "bold"), 
                  bg="#ffffff").pack(pady=20)
                  
        # --- Task Selection Frame ---
        task_frame = tk.Frame(self.current_frame, bg="#ffffff")
        task_frame.pack(pady=10)
        
        tk.Label(task_frame, text="Enter Task ID:", font=("Helvetica", 12), bg="#ffffff").pack(side=tk.LEFT, padx=5)
        task_id_entry = tk.Entry(task_frame, font=("Helvetica", 12), width=10)
        task_id_entry.pack(side=tk.LEFT, padx=5)
        
        # Variable to store task information once loaded
        task_info_var = tk.StringVar(value="No task loaded.")
        task_details_label = tk.Label(self.current_frame, textvariable=task_info_var, 
                                      font=("Courier", 11), fg="#34495e", bg="#ecf0f1", justify=tk.LEFT)
        task_details_label.pack(pady=10, padx=20, fill=tk.X)
        
        self.current_task_id = initial_task_id 
        
        # --- Type Selection and Time Input Widgets ---
        type_frame = tk.Frame(self.current_frame, bg="#ffffff")
        type_frame.pack(pady=15)
        
        type_var = tk.StringVar(value="flexible")
        
        time_frame = tk.Frame(self.current_frame, bg="#ffffff")
        time_frame.pack(pady=10)
        
        tk.Label(time_frame, text="Fixed Time (HH:MM AM/PM):", font=("Helvetica", 12), bg="#ffffff").pack(side=tk.LEFT, padx=5)
        fixed_time_entry = tk.Entry(time_frame, font=("Helvetica", 12), width=15, state=tk.DISABLED)
        fixed_time_entry.pack(side=tk.LEFT, padx=5)
        
        def update_time_entry_state():
            """Enables/Disables the fixed time entry based on the radio button selection."""
            if type_var.get() == "fixed":
                fixed_time_entry.config(state=tk.NORMAL)
            else:
                fixed_time_entry.config(state=tk.DISABLED)

        tk.Radiobutton(type_frame, text="Flexible", variable=type_var, value="flexible",
                       font=("Helvetica", 12), bg="#ffffff", command=update_time_entry_state).pack(side=tk.LEFT, padx=15)
        tk.Radiobutton(type_frame, text="Fixed Time", variable=type_var, value="fixed",
                       font=("Helvetica", 12), bg="#ffffff", command=update_time_entry_state).pack(side=tk.LEFT, padx=15)
        
        def load_task_details(task_id):
            all_tasks = self.repo.list_tasks()
            task = next((t for t in all_tasks if t[0] == task_id), None)
            
            if task:
                # task_id, name, duration, selected, task_type, fixed_time, cost
                _, name, duration, selected, task_type, fixed_time, cost = task
                
                self.current_task_id = task_id
                
                # Update info label
                status = "✓ Selected" if selected else "✗ Unselected"
                details = f"Task ID: {task_id}\nName: {name}\nDuration: {duration} min\nCost: ${cost or 0}\nStatus: {status}\n"
                
                # Format fixed time for display (24h storage -> 12h display)
                current_time_display = "None"
                entry_time = ""
                if fixed_time:
                    try:
                        time_obj = datetime.strptime(fixed_time, "%H:%M") # Stored in 24h
                        current_time_display = time_obj.strftime("%I:%M %p") # Display 12h
                        entry_time = current_time_display
                    except ValueError:
                        pass 
                        
                details += f"Current Type: {task_type or 'flexible'}\nFixed Time: {current_time_display}"
                task_info_var.set(details)
                
                type_var.set(task_type or "flexible")
                update_time_entry_state()
                
                fixed_time_entry.delete(0, tk.END)
                if task_type == 'fixed' and entry_time:
                    fixed_time_entry.insert(0, entry_time)
                elif task_type == 'fixed':
                    fixed_time_entry.insert(0, "HH:MM AM/PM")
                    
            else:
                self.current_task_id = None
                task_info_var.set(f"Error: Task ID {task_id} not found.")
                fixed_time_entry.config(state=tk.DISABLED)
                fixed_time_entry.delete(0, tk.END)
                
        def validate_and_load():
            try:
                task_id = int(task_id_entry.get().strip())
                load_task_details(task_id)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid integer for Task ID.")
                
        def apply_changes():
            if not self.current_task_id:
                messagebox.showerror("Error", "Please load a task first.")
                return
                
            task_type = type_var.get()
            fixed_time_input = None

            if task_type == "fixed":
                time_str = fixed_time_entry.get().strip()
                if not time_str:
                    messagebox.showerror("Error", "Fixed Time is required for fixed tasks (HH:MM AM/PM).")
                    return

            try:
                self.repo.set_task_type(self.current_task_id, task_type, time_str)
                
                load_task_details(self.current_task_id) 
                
                messagebox.showinfo("Success", f"Task type set to {task_type}!")
                
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        # Initial Load if an ID was passed
        if initial_task_id is not None:
            task_id_entry.insert(0, str(initial_task_id))
            load_task_details(initial_task_id)
        
        # Load button
        tk.Button(task_frame, text="Load Task", command=validate_and_load, 
                  font=("Helvetica", 11), bg="#3498db", fg="white", bd=0).pack(side=tk.LEFT, padx=10)
                  
        # Apply Button
        tk.Button(self.current_frame, text="Apply Changes", command=apply_changes, 
                  font=("Helvetica", 14, "bold"), bg="#27ae60", fg="white", width=20, height=2, bd=0).pack(pady=30)