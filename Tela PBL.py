import subprocess
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def start_game():

    subprocess.run(["python", "Jogo PBL.py"])

def open_dashboard():

    subprocess.run(["python", "Dashboard PBL.py"])

window = tk.Tk()
window.title("RehabQuest")
window.geometry("250x350")
window.resizable(False, False)
window.configure(bg = "#2B2B2B")

border_frame = ttk.Frame(window, padding = 10, style = "Border.TFrame")
border_frame.pack(expand = True, fill = "both", padx = 10, pady = 10)

try:

    original_image = Image.open("Logo PBL.png")
    resized_image = original_image.resize((200, 135))
    logo_image = ImageTk.PhotoImage(resized_image)

    logo_label = tk.Label(border_frame, image = logo_image, bg = "#444444")
    logo_label.pack(pady = 20, padx = 10)

except Exception as e:

    print(f"Erro ao carregar a imagem: {e}")

start_button = ttk.Button(border_frame,
                          text = "Jogar",
                          command = start_game,
                          style = "TButton")
start_button.pack(pady = 10)

dashboard_button = ttk.Button(border_frame,
                              text = "Dashboard",
                              command = open_dashboard,
                              style = "TButton")
dashboard_button.pack(pady = 10)

style = ttk.Style()
style.configure("TButton", font = ("Helvetica Neue", 12), padding = 6)
style.configure("Border.TFrame", background = "#444444")

window.mainloop()