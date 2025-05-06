# Importujemy niezbędne biblioteki
import tkinter as tk  # Biblioteka do tworzenia graficznego interfejsu użytkownika (GUI)
from tkinter import messagebox, scrolledtext, filedialog  # Dodatkowe komponenty GUI (okna dialogowe, przewijane pole tekstowe)
from PIL import Image, ImageTk  # Biblioteka Pillow do obsługi obrazów (otwieranie, manipulacja, wyświetlanie)
import requests  # Biblioteka do wysyłania żądań HTTP (np. do API)
from io import BytesIO  # Moduł do obsługi strumieni bajtów w pamięci (np. dla danych obrazu)

# --- Klasa stylu do przechowywania wspólnych ustawień wyglądu ---
class Style:
    """
    Przechowuje wspólne ustawienia wyglądu dla aplikacji,
    aby zapewnić spójny interfejs użytkownika.
    """
    def __init__(self):
        self.BG_COLOR = "#000000"  # Kolor tła aplikacji (czarny - styl NASA)
        self.FG_COLOR = "#00ff00"  # Kolor tekstu (zielony - kontrastujący i futurystyczny)
        self.FONT_FAMILY = "Consolas"  # Nazwa czcionki używanej w całej aplikacji
        self.FONT_SIZE = 12  # Standardowy rozmiar czcionki
        self.FONT_MAIN = (self.FONT_FAMILY, self.FONT_SIZE)  # Standardowa czcionka ( кортеж )
        self.FONT_BOLD = (self.FONT_FAMILY, self.FONT_SIZE, "bold")  # Pogrubiona czcionka ( кортеж )
        self.THUMBNAIL_SIZE = (150, 150)  # Rozmiar miniatur obrazów ( кортеж )
        self.COLUMNS = 7  # Liczba kolumn do wyświetlania miniatur
        self.PAD_X = 5  # Padding (dopełnienie) poziomy dla elementów interfejsu
        self.PAD_Y = 5  # Padding (dopełnienie) pionowy dla elementów interfejsu
        # Słownik z standardowymi opcjami 'pack' dla rozszerzania i wypełniania
        self.EXPAND_FILL = dict(fill=tk.BOTH, expand=True, padx=self.PAD_X, pady=self.PAD_Y)

# --- Klasa loggera do wyświetlania logów w GUI ---
class Logger:
    """
    Zarządza wyświetlaniem komunikatów (logów) w dedykowanym polu tekstowym w GUI.
    """
    def __init__(self, parent, style):
        """
        Inicjalizuje komponent loggera.

        Args:
            parent (tk.Widget): Rodzicielski widget Tkinter, w którym logger ma być umieszczony.
            style (Style): Obiekt klasy Style z ustawieniami wyglądu.
        """
        # Tworzymy przewijane pole tekstowe do logowania zdarzeń
        self.log_box = scrolledtext.ScrolledText(
            parent,  # Widget nadrzędny
            wrap=tk.WORD,  # Zawijanie tekstu na granicy słów
            bg=style.BG_COLOR,  # Kolor tła
            fg=style.FG_COLOR,  # Kolor tekstu
            font=(style.FONT_FAMILY, 10),  # Czcionka (mniejsza niż standardowa)
            insertbackground=style.FG_COLOR,  # Kolor kursora w polu tekstowym
            width=30,  # Szerokość pola tekstowego
            height=25  # Wysokość pola tekstowego
        )
        # Umieszczamy pole tekstowe w rodzicu, używając wspólnych ustawień wypełnienia
        self.log_box.pack(**style.EXPAND_FILL)

    def log(self, message):
        """
        Dodaje wiadomość do pola logów i przewija widok do najnowszego wpisu.

        Args:
            message (str): Wiadomość do zalogowania.
        """
        self.log_box.insert(tk.END, message + "\n")  # Dodajemy wiadomość na końcu pola tekstowego
        self.log_box.see(tk.END)  # Automatycznie przewijamy do ostatniego wpisu

# --- Główna aplikacja NASA Viewer ---
class NASAImageViewer:
    """
    Główna klasa aplikacji do przeglądania obrazów z API NASA.
    """
    def __init__(self, root_window):
        """
        Inicjalizuje główne okno aplikacji i jego komponenty.

        Args:
            root_window (tk.Tk): Główne okno aplikacji Tkinter.
        """
        self.root = root_window  # Przypisanie głównego okna
        self.root.title("NASA Image Viewer 🌌")  # Ustawienie tytułu okna
        self.root.geometry("1000x600")  # Ustawienie początkowych wymiarów okna

        self.style = Style()  # Inicjalizacja obiektu stylu
        self.root.configure(bg=self.style.BG_COLOR)  # Ustawiamy kolor tła głównego okna

        self.setup_layout()  # Wywołanie metody budującej interfejs użytkownika

    def _create_styled_frame(self, parent, **kwargs):
        """
        Tworzy ramkę (Frame) z domyślnym tłem ze stylu.

        Args:
            parent (tk.Widget): Rodzicielski widget.
            **kwargs: Dodatkowe argumenty przekazywane do konstruktora tk.Frame.

        Returns:
            tk.Frame: Nowo utworzona ramka.
        """
        # Łączymy domyślny kolor tła z przekazanymi argumentami
        # Jeśli 'bg' jest w kwargs, użyje wartości z kwargs, w przeciwnym razie self.style.BG_COLOR
        frame_kwargs = {'bg': self.style.BG_COLOR, **kwargs}
        return tk.Frame(parent, **frame_kwargs)

    def _create_styled_label(self, parent, text, font=None, **kwargs):
        """
        Tworzy etykietę (Label) z domyślnymi kolorami i czcionką ze stylu.

        Args:
            parent (tk.Widget): Rodzicielski widget.
            text (str): Tekst etykiety.
            font (tuple, optional): Czcionka etykiety. Domyślnie self.style.FONT_MAIN.
            **kwargs: Dodatkowe argumenty przekazywane do konstruktora tk.Label.

        Returns:
            tk.Label: Nowo utworzona etykieta.
        """
        if font is None:
            font = self.style.FONT_MAIN
        # Łączymy domyślne kolory i czcionkę z przekazanymi argumentami
        label_kwargs = {
            'bg': self.style.BG_COLOR,
            'fg': self.style.FG_COLOR,
            'font': font,
            **kwargs
        }
        return tk.Label(parent, text=text, **label_kwargs)


    def setup_layout(self):
        """
        Konfiguruje układ głównych komponentów interfejsu użytkownika.
        Dzieli okno na sekcję wyszukiwania, sekcję wyników i sekcję logów.
        """
        # --- Pasek wyszukiwania na górze okna ---
        top_frame = self._create_styled_frame(self.root) # Użycie metody pomocniczej
        top_frame.pack(fill=tk.X, pady=10) # Rozciągnij w poziomie, dodaj margines pionowy

        # Pole do wpisywania zapytania
        self.entry = tk.Entry(
            top_frame,
            width=50,
            bg=self.style.BG_COLOR,
            fg=self.style.FG_COLOR,
            insertbackground=self.style.FG_COLOR, # Kolor kursora
            font=self.style.FONT_MAIN
        )
        self.entry.pack(side=tk.LEFT, padx=10) # Umieść po lewej stronie, dodaj margines poziomy

        # Przycisk wyszukiwania
        search_btn = tk.Button(
            top_frame,
            text="Szukaj 🚀",
            command=self.search_images, # Funkcja wywoływana po kliknięciu
            bg="#1f1f1f",  # Ciemnoszary kolor tła przycisku
            fg=self.style.FG_COLOR,
            font=self.style.FONT_BOLD,
            activebackground="#003300",  # Kolor tła przycisku po najechaniu/kliknięciu
            activeforeground=self.style.FG_COLOR
        )
        search_btn.pack(side=tk.LEFT) # Umieść po lewej stronie, obok pola tekstowego
        # Powiązanie naciśnięcia klawisza Enter w głównym oknie z funkcją wyszukiwania
        self.root.bind('<Return>', self.search_images)

        # --- Główna ramka z podziałem na wyniki i logi ---
        main_frame = self._create_styled_frame(self.root) # Użycie metody pomocniczej
        main_frame.pack(**self.style.EXPAND_FILL) # Rozciągnij i wypełnij dostępną przestrzeń

        # --- Ramka na wyniki obrazów (lewa strona) ---
        # bd to borderwidth (szerokość ramki), relief to styl ramki
        image_results_frame = self._create_styled_frame(main_frame, bd=2, relief=tk.GROOVE) # Użycie metody pomocniczej
        image_results_frame.pack(side=tk.LEFT, **self.style.EXPAND_FILL)

        # Canvas jako kontener dla przewijalnej zawartości (obrazów)
        self.canvas = tk.Canvas(image_results_frame, bg=self.style.BG_COLOR, highlightthickness=0) # highlightthickness=0 usuwa ramkę canvas
        self.canvas.pack(side=tk.LEFT, **self.style.EXPAND_FILL)

        # Pionowy pasek przewijania dla Canvas
        scrollbar = tk.Scrollbar(image_results_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # Umieść po prawej, wypełnij w pionie
        self.canvas.configure(yscrollcommand=scrollbar.set) # Połącz pasek z Canvas

        # Ramka wewnętrzna w Canvas, która będzie faktycznie zawierać miniatury
        # Ta ramka będzie przewijana
        self.scrollable_frame = self._create_styled_frame(self.canvas) # Użycie metody pomocniczej
        # Umieść scrollable_frame wewnątrz Canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw") # nw = north-west (lewy górny róg)
        # Konfiguracja Canvas, aby region przewijania dopasowywał się do rozmiaru scrollable_frame
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # --- Ramka na logi (prawa strona) ---
        log_frame = self._create_styled_frame(main_frame, bd=2, relief=tk.GROOVE, width=250) # Użycie metody pomocniczej
        log_frame.pack(side=tk.RIGHT, fill=tk.Y) # Wypełnij w pionie, nie rozszerzaj w poziomie
        log_frame.pack_propagate(False) # Zapobiega zmianie rozmiaru ramki przez jej zawartość

        # Etykieta nad polem logów
        log_label = self._create_styled_label(log_frame, text="Akcje programu 🛰️", font=self.style.FONT_BOLD) # Użycie metody pomocniczej
        log_label.pack(pady=self.style.PAD_Y)

        self.logger = Logger(log_frame, self.style)  # Inicjalizacja obiektu loggera w ramce log_frame

    def search_images(self, event=None):
        """
        Pobiera zapytanie użytkownika, wyszukuje obrazy za pomocą API NASA
        i wyświetla miniatury wyników.
        Parametr 'event' jest potrzebny, gdy funkcja jest wywoływana przez powiązanie zdarzenia (np. Enter).
        """
        query = self.entry.get().strip()  # Pobieramy zapytanie z pola tekstowego i usuwamy białe znaki
        if not query:
            messagebox.showwarning("Uwaga", "Wpisz zapytanie przed wyszukiwaniem!")
            self.logger.log("Próba wyszukiwania bez zapytania.")
            return

        self.logger.log(f"Rozpoczynam wyszukiwanie dla: '{query}'")

        # Czyszczenie poprzednich wyników z scrollable_frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Etykieta "Wyniki:" nad miniaturami
        results_label = self._create_styled_label(
            self.scrollable_frame,
            text="Wyniki:",
            font=(self.style.FONT_FAMILY, 14, "bold")
        )
        results_label.grid(row=0, column=0, columnspan=self.style.COLUMNS, pady=self.style.PAD_Y, sticky="w") # sticky="w" (west) wyrównuje do lewej

        try:
            # Pobieranie danych z API NASA
            data = self.fetch_nasa_images(query)
            # Wyodrębnianie listy elementów (obrazów) z odpowiedzi JSON
            # .get zapewnia bezpieczny dostęp, zwracając pusty słownik/listę jeśli klucz nie istnieje
            items = data.get("collection", {}).get("items", [])

            if not items:
                self.logger.log(f"Brak wyników dla zapytania: '{query}'.")
                no_results_label = self._create_styled_label(self.scrollable_frame, text="Brak wyników.")
                no_results_label.grid(row=1, column=0, columnspan=self.style.COLUMNS, pady=self.style.PAD_Y)
                return

            self.logger.log(f"Znaleziono {len(items)} elementów. Wyświetlam do 30.")
            row, col = 1, 0 # Zaczynamy od wiersza 1, bo wiersz 0 jest dla etykiety "Wyniki:"
            # Iterujemy przez pierwsze 30 znalezionych elementów
            for item_index, item in enumerate(items[:30]):
                # Dostęp do linków i danych obrazu, z domyślnymi wartościami na wypadek braku danych
                links = item.get("links", [])
                data_info_list = item.get("data", []) # 'data' to lista w API NASA

                # Tytuł obrazu, jeśli istnieje
                title = "Bez tytułu"
                if data_info_list: # Sprawdzamy czy lista data_info_list nie jest pusta
                    # Zakładamy, że interesuje nas pierwszy element listy 'data'
                    title = data_info_list[0].get("title", "Bez tytułu")

                # Sprawdzamy, czy są dostępne linki do obrazu
                if links:
                    # Zakładamy, że pierwszy link to miniatura lub obraz do wyświetlenia
                    img_url = links[0].get("href", "")
                    if img_url and img_url.endswith(('.png', '.jpg', '.jpeg', '.gif')): # Prosta walidacja URL obrazu
                        try:
                            # Pobieranie danych obrazu z URL
                            response = requests.get(img_url, timeout=10) # Dodano timeout
                            response.raise_for_status() # Rzuci wyjątkiem dla złych statusów HTTP
                            img_data = response.content

                            # Tworzenie obiektu obrazu PIL z pobranych danych
                            img = Image.open(BytesIO(img_data))
                            img.thumbnail(self.style.THUMBNAIL_SIZE) # Zmniejszanie obrazu do rozmiaru miniatury
                            img_tk = ImageTk.PhotoImage(img) # Konwersja obrazu PIL na format Tkinter

                            # Tworzenie etykiety (panelu) do wyświetlenia miniatury
                            # cursor="hand2" zmienia kursor na "rączkę" po najechaniu
                            panel = tk.Label(self.scrollable_frame, image=img_tk, bg=self.style.BG_COLOR, cursor="hand2")
                            panel.image = img_tk  # Ważne: zachowaj referencję do obrazu, aby nie został "usunięty przez garbage collector"
                            panel.grid(row=row, column=col, padx=self.style.PAD_X, pady=self.style.PAD_Y)

                            # Tworzenie etykiety z tytułem pod miniaturą
                            title_label = self._create_styled_label(
                                self.scrollable_frame,
                                text=title,
                                font=(self.style.FONT_FAMILY, 10), # Mniejsza czcionka dla tytułu
                                wraplength=self.style.THUMBNAIL_SIZE[0] # Zawijanie tekstu do szerokości miniatury
                            )
                            title_label.grid(row=row + 1, column=col, padx=self.style.PAD_X, pady=self.style.PAD_Y, sticky="n") # sticky="n" (north)

                            # Powiązanie zdarzeń kliknięcia myszą z panelem miniatury
                            # Lewy przycisk myszy (<Button-1>): pokaż pełny obraz
                            panel.bind("<Button-1>", lambda e, url=img_url, t=title: self.show_full_image(url, t))
                            # Prawy przycisk myszy (<Button-3> na Windows/Linux, <Button-2> na macOS): pokaż opcję zapisu
                            panel.bind("<Button-3>", lambda e, url=img_url, t=title: self.save_image_prompt(url, t))
                            panel.bind("<Button-2>", lambda e, url=img_url, t=title: self.save_image_prompt(url, t)) # Dla macOS

                            col += 1 # Przejście do następnej kolumny
                            if col >= self.style.COLUMNS: # Jeśli osiągnięto limit kolumn
                                col = 0 # Wróć do pierwszej kolumny
                                row += 2 # Przejdź do następnego wiersza (wiersz na obraz + wiersz na tytuł)
                        except requests.exceptions.RequestException as e:
                            self.logger.log(f"Błąd sieciowy podczas ładowania miniatury {img_url}: {e}")
                        except UnidentifiedImageError: # Złap błąd jeśli PIL nie rozpozna formatu obrazu
                            self.logger.log(f"Nie można zidentyfikować formatu obrazu: {img_url}")
                        except Exception as e:
                            self.logger.log(f"Błąd ładowania miniatury {img_url}: {e}")
                    else:
                        self.logger.log(f"Brakujący lub nieprawidłowy URL obrazu w elemencie {item_index}.")
                else:
                    self.logger.log(f"Brak linków w elemencie {item_index}.")
            if row == 1 and col == 0 : # Jeśli nie dodano żadnych poprawnych miniatur
                self.logger.log("Nie udało się załadować żadnej miniatury z dostępnych danych.")
                no_valid_images_label = self._create_styled_label(self.scrollable_frame, text="Brak poprawnych obrazów do wyświetlenia.")
                no_valid_images_label.grid(row=1, column=0, columnspan=self.style.COLUMNS, pady=self.style.PAD_Y)


        except requests.exceptions.RequestException as e: # Błąd połączenia z API
            self.logger.log(f"Błąd połączenia z API NASA: {e}")
            messagebox.showerror("Błąd API", f"Nie udało się połączyć z API NASA: {e}")
        except Exception as e: # Inne nieoczekiwane błędy
            self.logger.log(f"Nieoczekiwany błąd podczas wyszukiwania: {e}")
            messagebox.showerror("Błąd krytyczny", f"Wystąpił nieoczekiwany błąd: {e}")

    def fetch_nasa_images(self, query):
        """
        Pobiera dane obrazów z API NASA na podstawie zapytania.

        Args:
            query (str): Słowo kluczowe do wyszukania w API NASA.

        Returns:
            dict: Odpowiedź JSON z API jako słownik.

        Raises:
            requests.exceptions.RequestException: Jeśli wystąpi błąd podczas żądania HTTP.
            Exception: Jeśli status odpowiedzi nie jest 200.
        """
        url = "https://images-api.nasa.gov/search"
        params = {'q': query, 'media_type': 'image'} # Parametry zapytania: zapytanie i typ mediów (obraz)
        self.logger.log(f"Wysyłanie żądania do API: {url} z parametrami: {params}")
        response = requests.get(url, params=params, timeout=15) # Dodano timeout
        response.raise_for_status() # Rzuci wyjątkiem dla kodów błędów HTTP (4xx lub 5xx)
        self.logger.log(f"Otrzymano odpowiedź od API, status: {response.status_code}")
        return response.json() # Zwraca sparsowaną odpowiedź JSON

    def _load_image_from_url(self, img_url, title_for_log=""):
        """
        Pobiera i otwiera obraz z podanego URL.

        Args:
            img_url (str): URL obrazu.
            title_for_log (str, optional): Tytuł obrazu używany w logach.

        Returns:
            Image.Image or None: Obiekt obrazu PIL lub None w przypadku błędu.
        """
        try:
            self.logger.log(f"Pobieranie pełnego obrazu: {title_for_log if title_for_log else img_url.split('/')[-1]}")
            response = requests.get(img_url, timeout=20) # Dłuższy timeout dla pełnych obrazów
            response.raise_for_status()
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            return img
        except requests.exceptions.RequestException as e:
            self.logger.log(f"Błąd sieciowy podczas ładowania obrazu '{title_for_log}': {e}")
            messagebox.showerror("Błąd sieciowy", f"Nie udało się pobrać obrazu: {e}")
        except UnidentifiedImageError:
            self.logger.log(f"Nie można zidentyfikować formatu obrazu: {img_url}")
            messagebox.showerror("Błąd obrazu", "Nie udało się otworzyć obrazu (nieznany format).")
        except Exception as e:
            self.logger.log(f"Błąd otwierania obrazu '{title_for_log}': {e}")
            messagebox.showerror("Błąd", f"Nie udało się załadować obrazu '{title_for_log}'.")
        return None

    def show_full_image(self, img_url, title=""):
        """
        Wyświetla pełnowymiarowy obraz w nowym oknie (Toplevel).

        Args:
            img_url (str): URL obrazu do wyświetlenia.
            title (str, optional): Tytuł obrazu, wyświetlany pod obrazem.
        """
        img = self._load_image_from_url(img_url, title)
        if img is None:
            return

        try:
            # Utworzenie nowego okna (popup)
            popup = tk.Toplevel(self.root)
            popup.title(f"Podgląd: {title if title else 'Obraz'} 🛸")
            popup.configure(bg=self.style.BG_COLOR)

            # Dostosowanie rozmiaru obrazu, jeśli jest zbyt duży dla ekranu
            # Przykładowe ograniczenie do 80% szerokości i wysokości ekranu głównego
            max_width = int(self.root.winfo_screenwidth() * 0.8)
            max_height = int(self.root.winfo_screenheight() * 0.8)

            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS) # Lepsza jakość skalowania

            img_tk = ImageTk.PhotoImage(img) # Konwersja na format Tkinter

            # Etykieta do wyświetlenia obrazu
            image_label = tk.Label(popup, image=img_tk, bg=self.style.BG_COLOR)
            image_label.image = img_tk  # Zachowaj referencję!
            image_label.pack(padx=10, pady=10)

            # Etykieta z tytułem pod obrazem, jeśli tytuł istnieje
            if title:
                title_label_popup = self._create_styled_label(popup, text=title, font=self.style.FONT_BOLD)
                title_label_popup.pack(pady=5)

            self.logger.log(f"Otworzono podgląd obrazu: {title if title else img_url.split('/')[-1]}")

        except Exception as e: # Ogólny błąd na wypadek problemów z Tkinter lub innymi operacjami
            self.logger.log(f"Błąd wyświetlania pełnego obrazu '{title}': {e}")
            messagebox.showerror("Błąd wyświetlania", f"Nie udało się wyświetlić obrazu '{title}'.")


    def save_image_prompt(self, img_url, title):
        """
        Wyświetla okno dialogowe "Zapisz jako" i zapisuje obraz, jeśli użytkownik wybierze lokalizację.

        Args:
            img_url (str): URL obrazu do zapisania.
            title (str): Sugerowana nazwa pliku (tytuł obrazu).
        """
        # Sugerowana nazwa pliku, oczyszczona z niebezpiecznych znaków (prosta wersja)
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in title)
        default_filename = f"{safe_title}.jpg" if safe_title else "nasa_image.jpg"

        # Otwarcie systemowego okna dialogowego "Zapisz jako"
        filename = filedialog.asksaveasfilename(
            parent=self.root, # Okno nadrzędne dla dialogu
            defaultextension=".jpg", # Domyślne rozszerzenie pliku
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("Wszystkie pliki", "*.*")], # Dostępne typy plików
            initialfile=default_filename, # Sugerowana początkowa nazwa pliku
            title="Zapisz obraz jako..."
        )

        # Jeśli użytkownik wybrał nazwę pliku (nie anulował dialogu)
        if filename:
            img = self._load_image_from_url(img_url, title)
            if img:
                try:
                    # Zapis obrazu PIL do wybranego pliku
                    # Format jest zwykle dedukowany z rozszerzenia, ale można go podać jawnie
                    img.save(filename)
                    self.logger.log(f"Zapisano obraz: {filename}")
                    messagebox.showinfo("Sukces", f"Obraz zapisany jako: {filename}")
                except Exception as e:
                    self.logger.log(f"Błąd zapisu obrazu '{title}' do pliku {filename}: {e}")
                    messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać obrazu: {e}")
        else:
            self.logger.log("Anulowano zapis obrazu.")


# --- Uruchomienie aplikacji ---
if __name__ == "__main__":
    # Utworzenie głównego okna aplikacji Tkinter
    root = tk.Tk()
    # Utworzenie instancji naszej aplikacji
    app = NASAImageViewer(root)
    # Uruchomienie głównej pętli zdarzeń Tkinter, która utrzymuje okno otwarte i reaguje na akcje użytkownika
    root.mainloop()

