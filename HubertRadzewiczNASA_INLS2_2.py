import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import requests
from io import BytesIO

def fetch_nasa_images(query):
    url = "https://images-api.nasa.gov/search"
    params_query = {'q': query, 'media_type': 'image'}
    response = requests.get(url, params=params_query)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Nie udało się pobrać danych, kod statusu: {response.status_code}')

def log_action(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

def show_full_image(img_url, title=""):
    try:
        img_data = requests.get(img_url).content
        img = Image.open(BytesIO(img_data))

        popup = tk.Toplevel(root)
        popup.title("Podgląd obrazu 🛸")
        popup.configure(bg="#000000")

        img = img.resize((800, 600)) if img.width > 800 else img
        img_tk = ImageTk.PhotoImage(img)

        label = tk.Label(popup, image=img_tk, bg="#000000")
        label.image = img_tk
        label.pack(padx=10, pady=10)

        # Display the title under the image in the popup
        if title:
            tk.Label(popup, text=title, bg="#000000", fg="#00ff00", font=("Consolas", 12, "bold")).pack(pady=5)

        log_action(f"Otworzono podgląd: {img_url.split('/')[-1]}")

    except Exception as e:
        log_action(f"Błąd otwierania obrazu: {e}")
        messagebox.showerror("Błąd", f"Nie udało się załadować obrazu.")

def save_image(img_url, filename):
    try:
        img_data = requests.get(img_url).content
        with open(filename, 'wb') as f:
            f.write(img_data)
        log_action(f"Zapisano obraz do: {filename}")
        messagebox.showinfo("Sukces", f"Obraz został zapisany jako: {filename}")
    except Exception as e:
        log_action(f"Błąd zapisywania obrazu: {e}")
        messagebox.showerror("Błąd", "Nie udało się zapisać obrazu.")

def on_right_click(event, img_url, title):
    # Okno dialogowe zapyta o nazwę pliku, aby zapisać obraz
    filename = f"{title}.jpg"  # Nazwa domyślna
    filename = tk.filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")], initialfile=filename)
    if filename:
        save_image(img_url, filename)

def search_images(event=None):
    query = entry.get()
    if not query:
        messagebox.showwarning("Uwaga", "Wpisz zapytanie przed wyszukiwaniem!")
        return

    log_action(f"Rozpoczynanie wyszukiwania dla: '{query}'")

    # Usunięcie poprzednich wyników (obrazków i tytułów)
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    # Dodanie napisu "Wyniki:" nad obrazkami
    results_label = tk.Label(scrollable_frame, text="Wyniki:", fg="#00ff00", bg="#000000", font=("Consolas", 14, "bold"))
    results_label.grid(row=0, column=0, columnspan=7, pady=5)

    try:
        data = fetch_nasa_images(query)
        items = data.get("collection", {}).get("items", [])

        if not items:
            log_action("Brak wyników.")
            tk.Label(scrollable_frame, text="Brak wyników.", fg="#00ff00", bg="#000000").grid(row=1, column=0, columnspan=7)
            return

        row = 1
        col = 0
        for item in items[:30]:  # Zmieniono na 20 wyników
            links = item.get("links", [])
            data_info = item.get("data", [])
            title = data_info[0].get("title", "Bez tytułu") if data_info else "Bez tytułu"

            if links:
                img_url = links[0].get("href", "")
                if img_url:
                    try:
                        img_data = requests.get(img_url).content
                        img = Image.open(BytesIO(img_data))

                        # Maksymalny rozmiar
                        max_size = 150
                        img.thumbnail((max_size, max_size))
                        img_tk = ImageTk.PhotoImage(img)

                        # Stworzenie panelu z obrazkiem i tytułem
                        panel = tk.Label(scrollable_frame, image=img_tk, bg="#000000", cursor="hand2")
                        panel.image = img_tk  # Przypisanie obrazka do panelu
                        panel.grid(row=row, column=col, padx=5, pady=5)

                        # Ograniczenie szerokości etykiety z tytułem i zawijanie tekstu
                        title_label = tk.Label(scrollable_frame, text=title, fg="#00ff00", bg="#000000", font=("Consolas", 10),
                                               wraplength=140)  # Ustawienie maksymalnej szerokości
                        title_label.grid(row=row + 1, column=col, padx=5, pady=5, sticky="nsew")

                        # Dodanie obsługi kliknięcia prawym przyciskiem myszy na obrazek
                        panel.bind("<Button-1>", lambda e, url=img_url, t=title: show_full_image(url, t))
                        panel.bind("<Button-3>", lambda e, url=img_url, t=title: on_right_click(e, url, t))

                        col += 1
                        if col > 6:  # Zwiększona liczba kolumn na stronę (7 kolumn)
                            col = 0
                            row += 2  # Przesunięcie wiersza, żeby tytuł był poniżej obrazu

                    except Exception as e:
                        log_action(f"Błąd ładowania obrazu: {e}")

        # Zaktualizowanie zakresu przewijania po dodaniu nowych wyników
        canvas.config(scrollregion=canvas.bbox("all"))

    except Exception as e:
        log_action(f"Błąd: {e}")
        messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")

# ---------- GUI ----------
root = tk.Tk()
root.title("NASA Image Viewer 🌌")
root.geometry("1000x600")
root.configure(bg="#000000")

entry = tk.Entry(root, width=50, bg="#000000", fg="#00ff00", insertbackground="#00ff00", font=("Consolas", 12))
entry.pack(pady=10)

# Przycisk "Szukaj" - przycisk wyszukiwania
search_btn = tk.Button(root, text="Szukaj 🚀", command=search_images, bg="#1f1f1f", fg="#00ff00",
                        font=("Consolas", 12, "bold"), activebackground="#003300", activeforeground="#00ff00")
search_btn.pack()

# Umożliwienie wyszukiwania za pomocą klawisza Enter
root.bind('<Return>', search_images)

# Główna ramka (split na 75% / 25%)
main_frame = tk.Frame(root, bg="#000000")
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Ramka z obrazkami (75% szerokości)
image_frame = tk.Frame(main_frame, bg="#000000", bd=2, relief=tk.GROOVE)
image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

# Dodanie Canvas do przewijania
canvas = tk.Canvas(image_frame, bg="#000000")
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(image_frame, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)
scrollable_frame = tk.Frame(canvas, bg="#000000")
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Ramka z logami (25% szerokości)
log_frame = tk.Frame(main_frame, bg="#000000", bd=2, relief=tk.GROOVE, width=250)
log_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=5, pady=5)

log_label = tk.Label(log_frame, text="Akcje programu 🛰️", bg="#000000", fg="#00ff00", font=("Consolas", 12, "bold"))
log_label.pack(pady=5)

log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg="#000000", fg="#00ff00",
                                     font=("Consolas", 10), insertbackground="#00ff00", width=30, height=25)
log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

root.mainloop()
