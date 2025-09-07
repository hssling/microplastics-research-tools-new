import psutil
import win32gui
import win32process
import pyautogui
import os
import pefile
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import csv

# ----------------------------
# Core Functions
# ----------------------------
def list_processes():
    output.delete(1.0, tk.END)
    output.insert(tk.END, "=== Running Processes ===\n")
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            line = (f"PID: {proc.info['pid']:<6} | "
                    f"Name: {proc.info['name']:<30} | "
                    f"Memory: {proc.info['memory_info'].rss / (1024*1024):.2f} MB\n")
            output.insert(tk.END, line)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def enum_windows():
    output.delete(1.0, tk.END)
    output.insert(tk.END, "=== Open Windows ===\n")
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if title.strip():
                line = f"HWND: {hwnd:<10} | PID: {pid:<6} | Title: {title}\n"
                output.insert(tk.END, line)
    win32gui.EnumWindows(callback, None)

def automate_gui():
    messagebox.showinfo("Automation", "Moving mouse and typing 'Hello from Python!'")
    pyautogui.moveTo(200, 200, duration=1)
    pyautogui.click()
    pyautogui.typewrite("Hello from Python!\n")

def analyze_exe():
    file_path = filedialog.askopenfilename(
        title="Select an EXE file",
        filetypes=[("Executable files", "*.exe")]
    )
    if not file_path:
        return
    if not os.path.exists(file_path):
        messagebox.showerror("Error", f"File not found: {file_path}")
        return

    output.delete(1.0, tk.END)
    output.insert(tk.END, f"=== PE Metadata for {file_path} ===\n")
    try:
        pe = pefile.PE(file_path)
        output.insert(tk.END, f"Machine: {hex(pe.FILE_HEADER.Machine)}\n")
        output.insert(tk.END, f"Number of Sections: {pe.FILE_HEADER.NumberOfSections}\n")
        output.insert(tk.END, f"TimeDateStamp: {pe.FILE_HEADER.TimeDateStamp}\n")
        output.insert(tk.END, f"Characteristics: {hex(pe.FILE_HEADER.Characteristics)}\n")
    except Exception as e:
        output.insert(tk.END, f"Error analyzing file: {e}\n")

# ----------------------------
# Search, Kill, Export
# ----------------------------
def search_process():
    query = search_entry.get().strip().lower()
    if not query:
        messagebox.showwarning("Warning", "Enter a process name to search")
        return

    output.delete(1.0, tk.END)
    output.insert(tk.END, f"=== Search Results for '{query}' ===\n")
    found = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if query in proc.info['name'].lower():
                output.insert(tk.END, f"PID: {proc.info['pid']} | Name: {proc.info['name']}\n")
                found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if not found:
        output.insert(tk.END, "No matching processes found.\n")

def kill_process():
    try:
        pid = int(kill_entry.get().strip())
        p = psutil.Process(pid)
        p.terminate()
        messagebox.showinfo("Success", f"Process {pid} terminated")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to kill process: {e}")

def export_results():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text file", "*.txt"), ("CSV file", "*.csv")]
    )
    if not file_path:
        return
    content = output.get(1.0, tk.END).strip()
    if file_path.endswith(".csv"):
        lines = [line.split("|") for line in content.split("\n") if line.strip()]
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(lines)
            messagebox.showinfo("Export", f"Results saved as CSV: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV: {e}")
    else:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Export", f"Results saved as TXT: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save TXT: {e}")

# ----------------------------
# Real-Time Monitor
# ----------------------------
def update_monitor():
    for row in monitor_tree.get_children():
        monitor_tree.delete(row)

    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem = f"{proc.info['memory_info'].rss / (1024*1024):.2f} MB"
            monitor_tree.insert("", "end", values=(proc.info['pid'], proc.info['name'], mem))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    interval = int(refresh_entry.get())
    root.after(interval * 1000, update_monitor)

# ----------------------------
# GUI Setup
# ----------------------------
root = tk.Tk()
root.title("Desktop Toolkit (Inspector & Automation)")
root.geometry("950x700")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# --- Tab 1: Tools ---
tab1 = tk.Frame(notebook)
notebook.add(tab1, text="Toolkit")

frame = tk.Frame(tab1)
frame.pack(side=tk.TOP, pady=10)

btn1 = tk.Button(frame, text="List Processes", command=list_processes, width=20)
btn2 = tk.Button(frame, text="Show Windows", command=enum_windows, width=20)
btn3 = tk.Button(frame, text="Automate GUI", command=automate_gui, width=20)
btn4 = tk.Button(frame, text="Analyze EXE", command=analyze_exe, width=20)
btn5 = tk.Button(frame, text="Export Results", command=export_results, width=20)

btn1.grid(row=0, column=0, padx=5, pady=5)
btn2.grid(row=0, column=1, padx=5, pady=5)
btn3.grid(row=0, column=2, padx=5, pady=5)
btn4.grid(row=1, column=0, padx=5, pady=5)
btn5.grid(row=1, column=1, padx=5, pady=5)

search_frame = tk.Frame(tab1)
search_frame.pack(pady=5)

tk.Label(search_frame, text="Search Process:").grid(row=0, column=0, padx=5)
search_entry = tk.Entry(search_frame, width=25)
search_entry.grid(row=0, column=1, padx=5)
tk.Button(search_frame, text="Search", command=search_process).grid(row=0, column=2, padx=5)

tk.Label(search_frame, text="Kill Process (PID):").grid(row=1, column=0, padx=5)
kill_entry = tk.Entry(search_frame, width=25)
kill_entry.grid(row=1, column=1, padx=5)
tk.Button(search_frame, text="Kill", command=kill_process).grid(row=1, column=2, padx=5)

output = scrolledtext.ScrolledText(tab1, wrap=tk.WORD, width=110, height=25)
output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# --- Tab 2: Real-Time Monitor ---
tab2 = tk.Frame(notebook)
notebook.add(tab2, text="Real-Time Monitor")

columns = ("PID", "Name", "Memory")
monitor_tree = ttk.Treeview(tab2, columns=columns, show="headings", height=20)
for col in columns:
    monitor_tree.heading(col, text=col)
    monitor_tree.column(col, width=200)
monitor_tree.pack(fill="both", expand=True, padx=10, pady=10)

refresh_frame = tk.Frame(tab2)
refresh_frame.pack(pady=5)
tk.Label(refresh_frame, text="Refresh Interval (seconds):").pack(side=tk.LEFT, padx=5)
refresh_entry = tk.Entry(refresh_frame, width=5)
refresh_entry.insert(0, "3")
refresh_entry.pack(side=tk.LEFT, padx=5)

# Start auto refresh
update_monitor()

root.mainloop()
