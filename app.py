import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from netmiko import ConnectHandler
import sqlite3
from datetime import datetime

# Global variables
router_ip = ""
router_username = ""
router_password = ""
ssh = None
db_connection = None
db_cursor = None
entry_version = None

# Rauterio prisijungimo funkcija
def authenticate_router():
    global router_ip, router_username, router_password, ssh

    router_ip = ip_entry.get()
    router_username = username_entry.get()
    router_password = password_entry.get()

    router = {
        'device_type': 'mikrotik_routeros',
        'host': router_ip,
        'username': router_username,
        'password': router_password,
    }

    try:
        ssh = ConnectHandler(**router)
        messagebox.showinfo("Success", "Authentication successful!")
        auth_window.destroy()
        main()
    except Exception as e:
        messagebox.showerror("Error", f"Authentication failed: {str(e)}")

# Duomenų ištraukimas ir atvaizdavimas
def fetch_router_data():
    try:
        output = ssh.send_command("/interface ethernet print")
        formatted_output = format_router_data(output)
        text_router_data.configure(state='normal')
        text_router_data.delete(1.0, tk.END)
        text_router_data.insert(tk.END, formatted_output)
        text_router_data.configure(state='disabled')  #tik skaitomas
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch router data: {str(e)}")

# Lenteles formatavimas
def format_router_data(raw_data):
    lines = raw_data.strip().split("\n")
    formatted_lines = []

    # Lenteles pavadinimai
    formatted_lines.append("Flags: X - disabled, R - running, S - slave")
    formatted_lines.append("#     NAME      MTU        MAC-ADDRESS        ARP   SWITCH")

    for line in lines[2:]:
        if line.strip():
            parts = line.split()
            if len(parts) >= 7:  # Adjusted to include switch name
                formatted_line = f"{parts[0]} {parts[1]}   {parts[2]}   {parts[3]}   {parts[4]}   {parts[5]}   {parts[6]}"
                formatted_lines.append(formatted_line)

    return "\n".join(formatted_lines)

# Routerio Terminaliniai duomenys
def fetch_additional_data():
    try:
        output = ssh.send_command("/export")
        text_additional_data.configure(state='normal')
        text_additional_data.delete(1.0, tk.END)
        text_additional_data.insert(tk.END, output)
        text_additional_data.configure(state='disabled')
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch additional data: {str(e)}")

# Portu konfiguravimas
def configure_port():
    try:
        port = entry_port.get()
        name = entry_name.get()
        mtu = entry_mtu.get()
        mac = entry_mac.get()
        arp = entry_arp.get()

        command = f"/interface ethernet set [ find default-name=ether{port} ]"
        if name:
            command += f" name={name}"
        if mtu:
            command += f" mtu={mtu}"
        if mac:
            command += f" mac-address={mac}"
        if arp:
            command += f" arp={arp}"

        output = ssh.send_command(command)
        messagebox.showinfo("Success", f"Port {port} configured successfully!")
        save_version(output)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to configure port: {str(e)}")

# Routerio versijos duomenų išsaugojimas
def save_version(router_data):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db_cursor.execute("INSERT INTO router_versions (timestamp, data) VALUES (?, ?)", (timestamp, router_data))
        db_connection.commit()
        messagebox.showinfo("Success", "Router data version saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save router data version: {str(e)}")

# Duomenys paimami is duombazes
def fetch_router_versions():
    try:
        db_cursor.execute("SELECT version_id, timestamp, data FROM router_versions ORDER BY timestamp DESC")
        versions = db_cursor.fetchall()
        text_versions.configure(state='normal')
        text_versions.delete(1.0, tk.END)
        for version in versions:
            text_versions.insert(tk.END, f"Version {version[0]} - {version[1]}:\n{version[2]}\n\n")
        text_versions.configure(state='disabled')
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch router data versions: {str(e)}")

# Duombazes duomenu vizualicija
def load_selected_version():
    try:
        version_id = entry_version.get()
        db_cursor.execute("SELECT data FROM router_versions WHERE version_id=?", (version_id,))
        version_data = db_cursor.fetchone()
        if version_data:
            text_router_data.configure(state='normal')
            text_router_data.delete(1.0, tk.END)
            text_router_data.insert(tk.END, version_data[0])
            text_router_data.configure(state='disabled')
            messagebox.showinfo("Success", "Data loaded from selected version.")
        else:
            messagebox.showwarning("Warning", "Selected version does not exist.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load selected version: {str(e)}")

# Konfiguruotų duomenų issaugojimas
def save_current_version():
    try:
        current_data = text_router_data.get(1.0, tk.END)
        save_version(current_data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save current version: {str(e)}")

# Jei duomenys geri, cia prasideda pati programa
def main():
    global text_router_data, text_additional_data, entry_port, text_versions, entry_version
    global entry_name, entry_mtu, entry_mac, entry_arp

    # Meniu langokūrimas
    root = tk.Tk()
    root.title("Router Management Tool")

    # Valdymo irankių kūrimas
    tab_control = ttk.Notebook(root)
    tab_control.pack(expand=1, fill='both')

    # Tab 1: Routerio duomenys
    tab1 = ttk.Frame(tab_control)
    tab_control.add(tab1, text='Router Data')

    label_router_data = ttk.Label(tab1, text="Router Interface Data:")
    label_router_data.pack(padx=10, pady=10)

    text_router_data = scrolledtext.ScrolledText(tab1, height=15, width=100, wrap=tk.WORD)
    text_router_data.pack(padx=10, pady=10)
    text_router_data.configure(state='disabled')

    button_fetch_data = ttk.Button(tab1, text="Fetch Router Data", command=fetch_router_data)
    button_fetch_data.pack(pady=10)

    button_save_version = ttk.Button(tab1, text="Save Version", command=save_current_version)
    button_save_version.pack(pady=10)

    # Tab 2: Papildomi duomenys
    tab2 = ttk.Frame(tab_control)
    tab_control.add(tab2, text='Additional Data')

    label_additional_data = ttk.Label(tab2, text="Additional Configuration Data:")
    label_additional_data.pack(padx=10, pady=10)

    text_additional_data = scrolledtext.ScrolledText(tab2, height=15, width=100, wrap=tk.WORD)
    text_additional_data.pack(padx=10, pady=10)
    text_additional_data.configure(state='disabled')

    button_fetch_additional_data = ttk.Button(tab2, text="Fetch Additional Data", command=fetch_additional_data)
    button_fetch_additional_data.pack(pady=10)

    # Tab 3: Porto konfiguravimas
    tab3 = ttk.Frame(tab_control)
    tab_control.add(tab3, text='Configure Port')

    label_port = ttk.Label(tab3, text="Enter port number:")
    label_port.grid(row=0, column=0, padx=10, pady=10)

    entry_port = ttk.Entry(tab3, width=10)
    entry_port.grid(row=0, column=1, padx=10, pady=10)

    label_name = ttk.Label(tab3, text="Name:")
    label_name.grid(row=1, column=0, padx=10, pady=10)
    entry_name = ttk.Entry(tab3, width=20)
    entry_name.grid(row=1, column=1, padx=10, pady=10)

    label_mtu = ttk.Label(tab3, text="MTU:")
    label_mtu.grid(row=2, column=0, padx=10, pady=10)
    entry_mtu = ttk.Entry(tab3, width=20)
    entry_mtu.grid(row=2, column=1, padx=10, pady=10)

    label_mac = ttk.Label(tab3, text="MAC Address:")
    label_mac.grid(row=3, column=0, padx=10, pady=10)
    entry_mac = ttk.Entry(tab3, width=20)
    entry_mac.grid(row=3, column=1, padx=10, pady=10)

    label_arp = ttk.Label(tab3, text="ARP State:")
    label_arp.grid(row=4, column=0, padx=10, pady=10)
    entry_arp = ttk.Entry(tab3, width=20)
    entry_arp.grid(row=4, column=1, padx=10, pady=10)

    button_configure_port = ttk.Button(tab3, text="Configure Port", command=configure_port)
    button_configure_port.grid(row=5, column=0, columnspan=2, pady=10)

    # Tab 4: Routerio verdija
    tab4 = ttk.Frame(tab_control)
    tab_control.add(tab4, text='Router Versions')

    label_versions = ttk.Label(tab4, text="Saved Router Data Versions:")
    label_versions.pack(padx=10, pady=10)

    text_versions = scrolledtext.ScrolledText(tab4, height=15, width=100, wrap=tk.WORD)
    text_versions.pack(padx=10, pady=10)
    text_versions.configure(state='disabled')  # Set to read-only initially

    button_fetch_versions = ttk.Button(tab4, text="Fetch Router Versions", command=fetch_router_versions)
    button_fetch_versions.pack(pady=10)

    label_version_id = ttk.Label(tab4, text="Enter version ID to load:")
    label_version_id.pack(padx=10, pady=5)

    entry_version = ttk.Entry(tab4, width=10)
    entry_version.pack(padx=10, pady=5)

    button_load_version = ttk.Button(tab4, text="Load Version Data", command=load_selected_version)
    button_load_version.pack(pady=10)

    # Initialize database connection
    global db_connection, db_cursor
    db_connection = sqlite3.connect('router_versions.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute('''CREATE TABLE IF NOT EXISTS router_versions
                             (version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                              timestamp TEXT,
                              data TEXT)''')
    db_connection.commit()

    # Run the main loop
    root.mainloop()


# Pati pradzia, autentifikacija
if __name__ == "__main__":
    # Prisijungimo nlangas
    auth_window = tk.Tk()
    auth_window.title("Router Authentication")

    label_ip = ttk.Label(auth_window, text="Router IP:")
    label_ip.grid(row=0, column=0, padx=10, pady=10)
    ip_entry = ttk.Entry(auth_window, width=30)
    ip_entry.grid(row=0, column=1, padx=10, pady=10)

    label_username = ttk.Label(auth_window, text="Username:")
    label_username.grid(row=1, column=0, padx=10, pady=10)
    username_entry = ttk.Entry(auth_window, width=30)
    username_entry.grid(row=1, column=1, padx=10, pady=10)

    label_password = ttk.Label(auth_window, text="Password:")
    label_password.grid(row=2, column=0, padx=10, pady=10)
    password_entry = ttk.Entry(auth_window, show="*", width=30)
    password_entry.grid(row=2, column=1, padx=10, pady=10)

    button_authenticate = ttk.Button(auth_window, text="Authenticate", command=authenticate_router)
    button_authenticate.grid(row=3, column=0, columnspan=2, pady=10)

    auth_window.mainloop()

