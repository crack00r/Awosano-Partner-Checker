import sys
import os
import json
import tkinter as tk
from tkinter import ttk, IntVar  # Importieren von IntVar für die Checkbox
import threading
import pygame
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import http.client

file_path = "appointments.json"
config = {}  # Globale Konfigurationsvariable


            
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def play_sound():
    pygame.mixer.init()  # Initialisieren Sie den Mixer hier
    sound_path = get_resource_path("alert_sound.mp3")
    pygame.mixer.music.load(sound_path)
    pygame.mixer.music.play(loops=-1)

def stop_sound(root):
    if pygame.mixer.get_init() is not None:  # Überprüfen Sie, ob der Mixer initialisiert ist
        pygame.mixer.music.stop()
        pygame.mixer.quit()  # Beenden Sie den Mixer, nachdem der Sound gestoppt wurde
    root.destroy()


def send_pushover_notification(message, user_key, app_token):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
                 body=f"token={app_token}&user={user_key}&message=" + message,
                 headers={"Content-type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    print(response.status, response.reason)

def show_popup(changes):
    root = tk.Tk()
    root.title("Benachrichtigung über neue Termine")
    for change in changes:
        tk.Label(root, text=change, padx=20, pady=10).pack()
    tk.Button(root, text="OK", command=lambda: stop_sound(root), padx=20, pady=20).pack()
    root.mainloop()

def get_appointment_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    appointments = set()

    # Durchsuchen Sie alle Tabellen
    tables = soup.find_all('table', class_='table')
    for table in tables:
        location = ""
        for row in table.find_all('tr'):
            if 'borderless' in row.get('class', []):  # Dies prüft, ob es sich um eine Standortzeile handelt
                location = row.find('h4').text.strip() if row.find('h4') else ""
            else:
                cols = row.find_all('td')
                if len(cols) == 3:
                    appointment = (location, cols[0].text.strip(), cols[1].text.strip(), cols[2].text.strip())
                    appointments.add(appointment)
                    print("Gefundener Termin:", appointment)

    print("Insgesamt gefundene Termine:", len(appointments))
    return appointments

def save_config(kind_id, payer_id, count_children, age_min, age_max, pushover_user, pushover_token, sound_alarm, window):
    config = {
        "cure_kind_id": kind_id,
        "cure_payer_id": payer_id,
        "count_children": count_children,
        "age_children_min": age_min,
        "age_children_max": age_max,
        "pushover_user": pushover_user,
        "pushover_token": pushover_token,
        "sound_alarm": sound_alarm.get()  # Speichern des Zustands der Checkbox
    }
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)
    window.destroy()

def show_config_window():
    global config  # Füge diese Zeile hinzu, um auf die globale Variable zuzugreifen

    window = tk.Tk()
    window.title("Konfigurationseinstellungen")

    cure_kind_options = {
        "Mutter/Kind": "0",
        "Vater/Kind": "1",
        "Mütterkur": "3"
    }
    cure_payer_options = {
        "Alle anderen gesetzlichen Krankenkassen": "0",
        "TK": "1",
        "BIG Direkt": "2",
        "AOK Plus": "3",
        "IKK BB": "4",
        "IKK GPlus": "5",
        "Knappschaft": "6",
        "DAK": "7",
        "Privat": "8"
    }

    # Kurart Dropdown
    tk.Label(window, text="Art der Kur:").grid(row=0, column=0)
    cure_kind = ttk.Combobox(window, values=list(cure_kind_options.keys()))
    cure_kind.grid(row=0, column=1)

    # Krankenkasse Dropdown
    tk.Label(window, text="Krankenkasse:").grid(row=1, column=0)
    cure_payer = ttk.Combobox(window, values=list(cure_payer_options.keys()))
    cure_payer.grid(row=1, column=1)

    # Anzahl Kinder
    tk.Label(window, text="Anzahl Kinder:").grid(row=2, column=0)
    count_children = tk.Entry(window)
    count_children.grid(row=2, column=1)

    # Alter jüngstes Kind
    tk.Label(window, text="Alter jüngstes Kind:").grid(row=3, column=0)
    age_min = tk.Entry(window)
    age_min.grid(row=3, column=1)

    # Alter ältestes Kind
    tk.Label(window, text="Alter ältestes Kind:").grid(row=4, column=0)
    age_max = tk.Entry(window)
    age_max.grid(row=4, column=1)

    # Pushover User-Key Eingabefeld
    tk.Label(window, text="Pushover User-Key:").grid(row=6, column=0)
    pushover_user = tk.Entry(window)
    pushover_user.grid(row=6, column=1)

    # Pushover API-Token Eingabefeld
    tk.Label(window, text="Pushover API-Token:").grid(row=7, column=0)
    pushover_token = tk.Entry(window)
    pushover_token.grid(row=7, column=1)

    # Sound Alarm Checkbox
    sound_alarm = IntVar(value=config.get("sound_alarm", 1))  # Standardwert ist aktiviert
    sound_alarm_checkbox = tk.Checkbutton(window, text="Soundalarm aktivieren", variable=sound_alarm)
    sound_alarm_checkbox.grid(row=9, column=0, columnspan=2)

    # Speichern Button
    save_button = tk.Button(window, text="Speichern", command=lambda: save_config(
        cure_kind_options[cure_kind.get()], cure_payer_options[cure_payer.get()],
        count_children.get(), age_min.get(), age_max.get(),
        pushover_user.get(), pushover_token.get(), sound_alarm, window))
    save_button.grid(row=10, column=1)

    window.mainloop()
    
    
    # Überprüfen Sie, ob Pushover-Einstellungen vorhanden sind
    if config.get("pushover_user") and config.get("pushover_token"):
        pushover_enabled = True
        pushover_user = config["pushover_user"]
        pushover_token = config["pushover_token"]
    else:
        pushover_enabled = False
        
config_path = 'config.json'
if not os.path.exists(config_path):
    show_config_window()

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

cure_kind_value = config["cure_kind_id"]
cure_payer_value = config["cure_payer_id"]
count_children_value = config["count_children"]
age_min_value = config["age_children_min"]
age_max_value = config["age_children_max"]

if config.get("pushover_user") and config.get("pushover_token"):
    pushover_enabled = True
    pushover_user = config["pushover_user"]
    pushover_token = config["pushover_token"]
else:
    pushover_enabled = False
    
# Definiere Chrome-Optionen
chrome_options = Options()
chrome_options.add_argument("--headless")

def send_notifications(changes, pushover_user, pushover_token, sound_alarm):
    # Sound abspielen, wenn aktiviert
    if sound_alarm:
        play_sound()

    # Senden einer Pushover-Benachrichtigung, wenn aktiviert
    if pushover_enabled:
        for change in changes:
            send_pushover_notification(change, pushover_user, pushover_token)
while True:
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://1crm.awosano.de/app/find_appointments/new")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "cure_search_kind")))
    kind_select = Select(driver.find_element(By.ID, "cure_search_kind"))
    kind_select.select_by_value(cure_kind_value)
    payer_select = Select(driver.find_element(By.ID, "cure_search_payer"))
    payer_select.select_by_value(cure_payer_value)
    driver.find_element(By.ID, "cure_search_count_children").send_keys(count_children_value)
    driver.find_element(By.ID, "cure_search_age_children_min").send_keys(age_min_value)
    driver.find_element(By.ID, "cure_search_age_children_max").send_keys(age_max_value)
    search_button = driver.find_element(By.XPATH, '//button[text()="Suche"]')
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(search_button))
    search_button.click()
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))
        html_content = driver.page_source
        print("Tabelle gefunden und Daten ausgelesen.")
    except Exception as e:
        print("Fehler beim Auslesen der Tabelle:", e)
    driver.quit()
    new_appointments = get_appointment_data(html_content)

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            old_appointments = set(tuple(appointment) for appointment in json.load(file))
        print("Alte Termine geladen:", len(old_appointments))
    else:
        old_appointments = set()

    new_appointment_set = set(new_appointments)

    added = new_appointment_set - old_appointments
    removed = old_appointments - new_appointment_set

    print("Neue Termine:", len(added))
    print("Entfernte Termine:", len(removed))

    changes = []
    for appointment in added:
        changes.append(f"Neuer Termin hinzugefügt: {appointment}")
    for appointment in removed:
        changes.append(f"Termin entfernt: {appointment}")

    if changes:
        # Starten eines neuen Threads für Benachrichtigungen
        # Zugriff auf pushover_user und pushover_token aus dem config-Dictionary
        notification_thread = threading.Thread(target=send_notifications, args=(changes, config.get("pushover_user"), config.get("pushover_token"), config.get("sound_alarm")))
        notification_thread.start()

        # Anzeigen des Popups
        show_popup(changes)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(list(new_appointment_set), file)

    time.sleep(3600)
