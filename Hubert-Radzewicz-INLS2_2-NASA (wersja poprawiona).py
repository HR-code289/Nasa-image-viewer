# Importujemy niezbędne biblioteki
import tkinter as tk  # Biblioteka do tworzenia graficznego interfejsu użytkownika (GUI)
from tkinter import messagebox, scrolledtext, filedialog  # Dodatkowe komponenty GUI (okna dialogowe, przewijane pole tekstowe)
from PIL import Image, ImageTk, UnidentifiedImageError # Biblioteka Pillow do obsługi obrazów (otwieranie, manipulacja, wyświetlanie)
import requests  # Biblioteka do wysyłania żądań HTTP (np. do API)
from io import BytesIO  # Moduł do obsługi strumieni bajtów w pamięci (np. dla danych obrazu)

# --- Klasa stylu do przechowywania wspólnych ustawień wyglądu ---
class Style:
    """
    Przechowuje wspólne ustawienia wyglądu dla aplikacji,
    aby zapewnić spójny interfejs użytkownika i ułatwić zarządzanie stylami.
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
        # Specyficzne kolory dla przycisków
        self.BUTTON_BG_COLOR = "#1f1f1f" # Ciemnoszary
        self.BUTTON_ACTIVE_BG_COLOR = "#003300" # Ciemnozielony przy najechaniu/kliknięciu


# --- Klasa loggera do wyświetlania logów w GUI ---
class Logger:
    """
    Zarządza wyświetlaniem komunikatów (logów) w dedykowanym polu tekstowym w GUI.
    Umożliwia śledzenie działań aplikacji w czasie rzeczywistym.
    """
    def __init__(self, parent, style_config): # Zmieniono nazwę argumentu style na style_config dla jasności
        """
        Inicjalizuje komponent loggera.

        Args:
            parent (tk.Widget): Rodzicielski widget Tkinter, w którym logger ma być umieszczony.
            style_config (Style): Obiekt klasy Style z ustawieniami wyglądu.
        """
        # Tworzymy przewijane pole tekstowe do logowania zdarzeń
        self.log_box = scrolledtext.ScrolledText(
            parent,  # Widget nadrzędny
            wrap=tk.WORD,  # Zawijanie tekstu na granicy słów
            bg=style_config.BG_COLOR,  # Kolor tła z obiektu stylu
            fg=style_config.FG_COLOR,  # Kolor tekstu z obiektu stylu
            font=(style_config.FONT_FAMILY, 10),  # Czcionka (mniejsza niż standardowa)
            insertbackground=style_config.FG_COLOR,  # Kolor kursora w polu tekstowym
            width=30,  # Szerokość pola tekstowego (w znakach)
            height=25, # Wysokość pola tekstowego (w liniach)
            relief=tk.SUNKEN, # Styl ramki
            bd=1 # Szerokość ramki
        )
        # Umieszczamy pole tekstowe w rodzicu, używając wspólnych ustawień wypełnienia
        self.log_box.pack(**style_config.EXPAND_FILL)

    def log(self, message):
        """
        Dodaje wiadomość do pola logów i przewija widok do najnowszego wpisu.

        Args:
            message (str): Wiadomość do zalogowania.
        """
        self.log_box.insert(tk.END, f"{message}\n")  # Dodajemy wiadomość na końcu pola tekstowego, z nową linią
        self.log_box.see(tk.END)  # Automatycznie przewijamy do ostatniego wpisu

# --- Główna aplikacja NASA Viewer ---
class NASAImageViewer:
    """
    Główna klasa aplikacji do przeglądania obrazów z API NASA.
    Odpowiada za inicjalizację interfejsu, obsługę zdarzeń i komunikację z API.
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
        self.root.minsize(800, 500) # Minimalny rozmiar okna

        self.style = Style()  # Inicjalizacja obiektu stylu
        self.root.configure(bg=self.style.BG_COLOR)  # Ustawiamy kolor tła głównego okna

        self.image_references = [] # Lista do przechowywania referencji do obrazów Tkinter (zapobiega GC)

        self.setup_layout()  # Wywołanie metody budującej interfejs użytkownika

    # --- Metody pomocnicze do tworzenia stylizowanych widgetów ---
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
        # Użyj domyślnej czcionki, jeśli nie podano innej
        if font is None:
            font = self.style.FONT_MAIN
        # Łączymy domyślne kolory i czcionkę z przekazanymi argumentami
        # Ustawienia stylów mogą być nadpisane przez kwargs
        label_kwargs = {
            'bg': self.style.BG_COLOR,
            'fg': self.style.FG_COLOR,
            'font': font,
            **kwargs # Pozwala na przekazanie dodatkowych opcji, np. wraplength
        }
        return tk.Label(parent, text=text, **label_kwargs)

    def _create_styled_entry(self, parent, **kwargs):
        """
        Tworzy pole tekstowe (Entry) z domyślnymi stylami.

        Args:
            parent (tk.Widget): Rodzicielski widget.
            **kwargs: Dodatkowe argumenty przekazywane do konstruktora tk.Entry.

        Returns:
            tk.Entry: Nowo utworzone pole tekstowe.
        """
        entry_kwargs = {
            'bg': self.style.BG_COLOR,
            'fg': self.style.FG_COLOR,
            'insertbackground': self.style.FG_COLOR, # Kolor kursora
            'font': self.style.FONT_MAIN,
            'relief': tk.SUNKEN, # Styl ramki
            'bd': 1, # Szerokość ramki
            **kwargs # Pozwala na nadpisanie domyślnych stylów lub dodanie nowych opcji
        }
        return tk.Entry(parent, **entry_kwargs)

    def _create_styled_button(self, parent, text, command, **kwargs):
        """
        Tworzy przycisk (Button) z domyślnymi stylami.

        Args:
            parent (tk.Widget): Rodzicielski widget.
            text (str): Tekst na przycisku.
            command (callable): Funkcja wywoływana po kliknięciu.
            **kwargs: Dodatkowe argumenty przekazywane do konstruktora tk.Button.

        Returns:
            tk.Button: Nowo utworzony przycisk.
        """
        button_kwargs = {
            'bg': self.style.BUTTON_BG_COLOR,
            'fg': self.style.FG_COLOR,
            'font': self.style.FONT_BOLD,
            'activebackground': self.style.BUTTON_ACTIVE_BG_COLOR,
            'activeforeground': self.style.FG_COLOR,
            'relief': tk.RAISED, # Styl ramki
            'bd': 1, # Szerokość ramki
            'padx': self.style.PAD_X,
            'pady': 2, # Mniejszy padding pionowy dla przycisków
            **kwargs # Pozwala na nadpisanie domyślnych stylów lub dodanie nowych opcji
        }
        return tk.Button(parent, text=text, command=command, **button_kwargs)

    def setup_layout(self):
        """
        Konfiguruje układ głównych komponentów interfejsu użytkownika.
        Dzieli okno na sekcję wyszukiwania, sekcję wyników i sekcję logów.
        Wykorzystuje metody pomocnicze do tworzenia stylizowanych widgetów.
        """
        # --- Pasek wyszukiwania na górze okna ---
        top_frame = self._create_styled_frame(self.root)
        top_frame.pack(fill=tk.X, pady=self.style.PAD_Y, padx=self.style.PAD_X) # Rozciągnij w poziomie, dodaj marginesy

        # Pole do wpisywania zapytania, używając metody pomocniczej
        self.entry = self._create_styled_entry(top_frame, width=50)
        self.entry.pack(side=tk.LEFT, padx=(0, self.style.PAD_X), fill=tk.X, expand=True) # Wypełnij i rozszerzaj
        self.entry.focus_set() # Ustawienie focusu na pole wprowadzania

        # Przycisk wyszukiwania, używając metody pomocniczej
        search_btn = self._create_styled_button(top_frame, text="Szukaj 🚀", command=self.search_images)
        search_btn.pack(side=tk.LEFT)
        # Powiązanie naciśnięcia klawisza Enter w głównym oknie z funkcją wyszukiwania
        # Działa, gdy focus jest na dowolnym elemencie w głównym oknie, który nie przechwytuje Entera inaczej.
        self.root.bind('<Return>', self.search_images)

        # --- Główna ramka z podziałem na wyniki i logi ---
        main_frame = self._create_styled_frame(self.root)
        main_frame.pack(**self.style.EXPAND_FILL)

        # --- Ramka na wyniki obrazów (lewa strona) ---
        image_results_frame = self._create_styled_frame(main_frame, bd=1, relief=tk.SUNKEN)
        image_results_frame.pack(side=tk.LEFT, **self.style.EXPAND_FILL)

        # Canvas jako kontener dla przewijalnej zawartości (obrazów)
        self.canvas = tk.Canvas(image_results_frame, bg=self.style.BG_COLOR, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, **self.style.EXPAND_FILL)

        # Pionowy pasek przewijania dla Canvas
        scrollbar = tk.Scrollbar(image_results_frame, orient="vertical", command=self.canvas.yview, relief=tk.FLAT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set) # Połącz pasek z Canvas

        # Ramka wewnętrzna w Canvas, która będzie faktycznie zawierać miniatury
        self.scrollable_frame = self._create_styled_frame(self.canvas)
        # Umieść scrollable_frame wewnątrz Canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Konfiguracja Canvas, aby region przewijania dopasowywał się do rozmiaru scrollable_frame
        self.scrollable_frame.bind("<Configure>", self._on_scrollable_frame_configure)
        # Powiązanie kółka myszy z przewijaniem Canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) # Dla Windows i macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel) # Dla Linux (scroll up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel) # Dla Linux (scroll down)


        # --- Ramka na logi (prawa strona) ---
        log_container_frame = self._create_styled_frame(main_frame, width=280) # Kontener dla logów i etykiety
        log_container_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(self.style.PAD_X, 0))
        log_container_frame.pack_propagate(False) # Zapobiega zmianie rozmiaru ramki przez jej zawartość

        # Ramka właściwa dla logów, z obramowaniem
        log_frame = self._create_styled_frame(log_container_frame, bd=1, relief=tk.SUNKEN)
        log_frame.pack(**self.style.EXPAND_FILL)


        # Etykieta nad polem logów
        log_label = self._create_styled_label(log_frame, text="Akcje programu 🛰️", font=self.style.FONT_BOLD)
        log_label.pack(pady=self.style.PAD_Y, fill=tk.X)

        self.logger = Logger(log_frame, self.style)  # Inicjalizacja obiektu loggera w ramce log_frame

    def _on_scrollable_frame_configure(self, event):
        """Aktualizuje region przewijania Canvas i szerokość scrollable_frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Dopasuj szerokość scrollable_frame do szerokości Canvas minus ewentualny pasek przewijania
        # Zapobiega to horyzontalnemu przewijaniu, jeśli nie jest potrzebne.
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())


    def _on_mousewheel(self, event):
        """Obsługuje przewijanie kółkiem myszy na Canvas."""
        if event.num == 5 or event.delta < 0: # Przewijanie w dół
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0: # Przewijanie w górę
            self.canvas.yview_scroll(-1, "units")

    def search_images(self, event=None): # event=None pozwala na wywołanie z przycisku i przez bind
        """
        Pobiera zapytanie użytkownika, wyszukuje obrazy za pomocą API NASA
        i wyświetla miniatury wyników.
        """
        query = self.entry.get().strip()  # Pobieramy zapytanie z pola tekstowego i usuwamy białe znaki
        if not query:
            messagebox.showwarning("Uwaga", "Wpisz zapytanie przed wyszukiwaniem!", parent=self.root)
            self.logger.log("Próba wyszukiwania bez zapytania.")
            return

        self.logger.log(f"Rozpoczynam wyszukiwanie dla: '{query}'")
        self.image_references.clear() # Czyścimy referencje przed nowym wyszukiwaniem

        # Czyszczenie poprzednich wyników z scrollable_frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Etykieta "Wyniki:" nad miniaturami
        results_label = self._create_styled_label(
            self.scrollable_frame,
            text=f"Wyniki dla: '{query}'", # Wyświetlenie zapytania w tytule wyników
            font=(self.style.FONT_FAMILY, 14, "bold")
        )
        # Umieszczenie etykiety w siatce, rozciągając na wszystkie kolumny
        results_label.grid(row=0, column=0, columnspan=self.style.COLUMNS, pady=self.style.PAD_Y, padx=self.style.PAD_X, sticky="w")

        try:
            # Pobieranie danych z API NASA
            data = self.fetch_nasa_images(query)
            items = data.get("collection", {}).get("items", [])

            if not items:
                self.logger.log(f"Brak wyników dla zapytania: '{query}'.")
                no_results_label = self._create_styled_label(self.scrollable_frame, text="Brak wyników.")
                no_results_label.grid(row=1, column=0, columnspan=self.style.COLUMNS, pady=self.style.PAD_Y)
                return

            self.logger.log(f"Znaleziono {len(items)} elementów. Wyświetlam do 30.")
            row, col = 1, 0 # Zaczynamy od wiersza 1 (wiersz 0 jest dla etykiety "Wyniki:")
            displayed_count = 0 # Licznik wyświetlonych obrazów

            # Iterujemy przez maksymalnie 30 znalezionych elementów
            for item_index, item in enumerate(items[:35]): # Trochę więcej, bo niektóre mogą być pominięte
                if displayed_count >= 30: # Limit wyświetlanych miniatur
                    break

                links = item.get("links", [])
                data_info_list = item.get("data", [])

                title = "Bez tytułu"
                if data_info_list:
                    title = data_info_list[0].get("title", "Bez tytułu")

                img_url = ""
                # Szukamy linku do obrazu (href), który jest typu 'image'
                if links:
                    for link_info in links:
                        if link_info.get("render") == "image" and link_info.get("href"):
                            img_url = link_info.get("href")
                            break # Znaleziono pierwszy link do obrazu
                    if not img_url and links[0].get("href","").lower().endswith(('.png', '.jpg', '.jpeg', '.gif')): # Zapasowy, jeśli nie ma 'render'
                        img_url = links[0].get("href")


                if img_url:
                    try:
                        # Pobieranie danych obrazu z URL
                        response = requests.get(img_url, timeout=10) # Timeout dla żądania
                        response.raise_for_status() # Rzuci wyjątkiem dla złych statusów HTTP
                        img_data = response.content

                        img = Image.open(BytesIO(img_data))
                        img.thumbnail(self.style.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                        img_tk = ImageTk.PhotoImage(img)
                        self.image_references.append(img_tk) # Zapisz referencję!

                        # Kontener dla obrazka i tytułu, aby były razem i miały tło
                        item_frame = self._create_styled_frame(self.scrollable_frame)
                        item_frame.grid(row=row, column=col, padx=self.style.PAD_X, pady=self.style.PAD_Y, sticky="n")

                        panel = tk.Label(item_frame, image=img_tk, bg=self.style.BG_COLOR, cursor="hand2")
                        panel.image = img_tk # Już zapisane w self.image_references, ale dla pewności
                        panel.pack()

                        title_label = self._create_styled_label(
                            item_frame,
                            text=title,
                            font=(self.style.FONT_FAMILY, 10), # Mniejsza czcionka dla tytułu
                            wraplength=self.style.THUMBNAIL_SIZE[0] - 10 # Zawijanie tekstu
                        )
                        title_label.pack(pady=(2,0))

                        # Pobranie oryginalnego URL obrazu o lepszej jakości, jeśli dostępny
                        # NASA API często dostarcza link do pliku JSON z metadanymi, skąd można wziąć 'orig'
                        # Dla uproszczenia, używamy img_url, który jest już miniaturą lub obrazem z 'links'
                        # W bardziej zaawansowanej wersji, można by tu pobrać `collection.json` i szukać linku "orig"
                        original_img_url = img_url # Domyślnie ten sam, co miniatura

                        panel.bind("<Button-1>", lambda e, url=original_img_url, t=title: self.show_full_image(url, t))
                        panel.bind("<Button-3>", lambda e, url=original_img_url, t=title: self.save_image_prompt(url, t))
                        panel.bind("<Button-2>", lambda e, url=original_img_url, t=title: self.save_image_prompt(url, t)) # Dla macOS

                        col += 1
                        displayed_count += 1
                        if col >= self.style.COLUMNS:
                            col = 0
                            row += 1 # Tylko jeden wiersz na item_frame

                    except requests.exceptions.Timeout:
                        self.logger.log(f"Timeout podczas ładowania miniatury: {img_url}")
                    except requests.exceptions.RequestException as e:
                        self.logger.log(f"Błąd sieciowy (miniatura) {img_url}: {e}")
                    except UnidentifiedImageError:
                        self.logger.log(f"Nie można zidentyfikować formatu obrazu (miniatura): {img_url}")
                    except Exception as e:
                        self.logger.log(f"Błąd ładowania miniatury {img_url}: {type(e).__name__} - {e}")
                else:
                    self.logger.log(f"Brak URL obrazu w elemencie {item_index} dla '{title}'.")

            if displayed_count == 0 and items: # Jeśli były itemy, ale żaden się nie załadował
                self.logger.log("Nie udało się załadować żadnej miniatury z dostępnych danych.")
                no_valid_images_label = self._create_styled_label(self.scrollable_frame, text="Brak poprawnych obrazów do wyświetlenia.")
                no_valid_images_label.grid(row=1, column=0, columnspan=self.style.COLUMNS, pady=self.style.PAD_Y)

        except requests.exceptions.Timeout:
            self.logger.log(f"Timeout podczas połączenia z API NASA.")
            messagebox.showerror("Błąd API", f"Przekroczono czas oczekiwania na odpowiedź od API NASA.", parent=self.root)
        except requests.exceptions.RequestException as e:
            self.logger.log(f"Błąd połączenia z API NASA: {e}")
            messagebox.showerror("Błąd API", f"Nie udało się połączyć z API NASA: {e}", parent=self.root)
        except Exception as e:
            self.logger.log(f"Nieoczekiwany błąd podczas wyszukiwania: {type(e).__name__} - {e}")
            messagebox.showerror("Błąd krytyczny", f"Wystąpił nieoczekiwany błąd: {e}", parent=self.root)
        finally:
            # Po zakończeniu wyszukiwania, zaktualizuj scrollregion, aby był poprawny nawet przy małej liczbie wyników
            self.scrollable_frame.update_idletasks() # Upewnij się, że wszystkie zmiany w GUI zostały przetworzone
            self._on_scrollable_frame_configure(None) # Przekazujemy None, bo event nie jest tu potrzebny


    def fetch_nasa_images(self, query):
        """
        Pobiera dane obrazów z API NASA na podstawie zapytania.

        Args:
            query (str): Słowo kluczowe do wyszukania w API NASA.

        Returns:
            dict: Odpowiedź JSON z API jako słownik.

        Raises:
            requests.exceptions.RequestException: Jeśli wystąpi błąd podczas żądania HTTP (w tym timeout).
        """
        url = "https://images-api.nasa.gov/search"
        params = {'q': query, 'media_type': 'image'}
        self.logger.log(f"Wysyłanie żądania do API: {url} z parametrami: {params}")
        # Dodano timeout do żądania, aby aplikacja nie zawieszała się na zbyt długo
        response = requests.get(url, params=params, timeout=15) # 15 sekund timeout
        response.raise_for_status()  # Rzuci wyjątkiem dla kodów błędów HTTP (4xx lub 5xx)
        self.logger.log(f"Otrzymano odpowiedź od API, status: {response.status_code}")
        return response.json()

    def _load_image_from_url(self, img_url, title_for_log=""):
        """
        Pobiera i otwiera obraz z podanego URL. Prywatna metoda pomocnicza.

        Args:
            img_url (str): URL obrazu.
            title_for_log (str, optional): Tytuł obrazu używany w logach dla lepszej identyfikacji.

        Returns:
            PIL.Image.Image or None: Obiekt obrazu PIL lub None w przypadku błędu.
        """
        try:
            log_identifier = title_for_log if title_for_log else img_url.split('/')[-1]
            self.logger.log(f"Pobieranie pełnego obrazu: {log_identifier}")
            # Dłuższy timeout dla pobierania pełnych obrazów, które mogą być większe
            response = requests.get(img_url, timeout=30) # 30 sekund timeout
            response.raise_for_status() # Sprawdzenie statusu HTTP
            img_data = response.content
            img = Image.open(BytesIO(img_data)) # Otwarcie obrazu z danych binarnych
            return img
        except requests.exceptions.Timeout:
            self.logger.log(f"Timeout podczas ładowania obrazu '{log_identifier}'.")
            messagebox.showerror("Błąd sieciowy", f"Przekroczono czas oczekiwania na pobranie obrazu: {title_for_log}", parent=self.root)
        except requests.exceptions.RequestException as e:
            self.logger.log(f"Błąd sieciowy podczas ładowania obrazu '{log_identifier}': {e}")
            messagebox.showerror("Błąd sieciowy", f"Nie udało się pobrać obrazu '{title_for_log}': {e}", parent=self.root)
        except UnidentifiedImageError: # Błąd specyficzny dla Pillow, gdy format obrazu jest nierozpoznany
            self.logger.log(f"Nie można zidentyfikować formatu obrazu: {img_url}")
            messagebox.showerror("Błąd obrazu", "Nie udało się otworzyć obrazu (nieznany format lub uszkodzony plik).", parent=self.root)
        except Exception as e: # Inne, nieprzewidziane błędy
            self.logger.log(f"Ogólny błąd otwierania obrazu '{log_identifier}': {type(e).__name__} - {e}")
            messagebox.showerror("Błąd", f"Nie udało się załadować obrazu '{title_for_log}'.", parent=self.root)
        return None # Zwrócenie None w przypadku jakiegokolwiek błędu

    def show_full_image(self, img_url, title=""):
        """
        Wyświetla pełnowymiarowy obraz w nowym oknie (Toplevel).

        Args:
            img_url (str): URL obrazu do wyświetlenia.
            title (str, optional): Tytuł obrazu, wyświetlany w oknie podglądu.
        """
        img = self._load_image_from_url(img_url, title) # Użycie metody pomocniczej do załadowania obrazu
        if img is None: # Jeśli ładowanie obrazu się nie powiodło, zakończ
            return

        try:
            # Utworzenie nowego okna (popup) jako Toplevel, zależnego od głównego okna
            popup = tk.Toplevel(self.root)
            popup.title(f"Podgląd: {title if title else 'Obraz'} 🛸")
            popup.configure(bg=self.style.BG_COLOR)
            popup.grab_set() # Uczynienie okna modalnym (blokuje interakcję z głównym oknem)

            # Dostosowanie rozmiaru obrazu, jeśli jest zbyt duży dla ekranu
            # Ograniczenie do 80% szerokości i wysokości ekranu, na którym jest główne okno
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)

            # Zachowanie proporcji obrazu podczas skalowania
            original_width, original_height = img.size
            ratio = min(max_width / original_width, max_height / original_height)
            if ratio < 1: # Skaluj tylko jeśli obraz jest większy niż dostępne miejsce
                 new_width = int(original_width * ratio)
                 new_height = int(original_height * ratio)
                 img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)


            img_tk = ImageTk.PhotoImage(img) # Konwersja obrazu PIL na format Tkinter

            # Etykieta do wyświetlenia obrazu
            image_label = tk.Label(popup, image=img_tk, bg=self.style.BG_COLOR)
            image_label.image = img_tk  # WAŻNE: Zachowaj referencję do obrazu!
            self.image_references.append(img_tk) # Dodaj do globalnej listy referencji
            image_label.pack(padx=10, pady=10)

            # Etykieta z tytułem pod obrazem, jeśli tytuł istnieje
            if title:
                title_label_popup = self._create_styled_label(popup, text=title, font=self.style.FONT_BOLD)
                title_label_popup.pack(pady=(0, 10)) # Padding tylko na dole

            self.logger.log(f"Otworzono podgląd obrazu: {title if title else img_url.split('/')[-1]}")

        except Exception as e: # Ogólny błąd na wypadek problemów z Tkinter lub innymi operacjami
            self.logger.log(f"Błąd wyświetlania pełnego obrazu '{title}': {type(e).__name__} - {e}")
            messagebox.showerror("Błąd wyświetlania", f"Nie udało się wyświetlić obrazu '{title}'.", parent=self.root)

    def save_image_prompt(self, img_url, title):
        """
        Wyświetla okno dialogowe "Zapisz jako" i inicjuje zapis obrazu,
        jeśli użytkownik wybierze lokalizację.

        Args:
            img_url (str): URL obrazu do zapisania.
            title (str): Sugerowana nazwa pliku (tytuł obrazu).
        """
        # Sugerowana nazwa pliku, oczyszczona z niebezpiecznych znaków
        # Zamienia spacje na podkreślenia i usuwa inne nie-alfanumeryczne znaki (poza '_', '-')
        safe_title = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in title.replace(' ', '_'))
        default_filename = f"{safe_title}.jpg" if safe_title else "nasa_image.jpg"

        # Otwarcie systemowego okna dialogowego "Zapisz jako"
        filename = filedialog.asksaveasfilename(
            parent=self.root, # Okno nadrzędne dla dialogu
            defaultextension=".jpg", # Domyślne rozszerzenie pliku
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("Wszystkie pliki", "*.*")], # Dostępne typy plików
            initialfile=default_filename, # Sugerowana początkowa nazwa pliku
            title="Zapisz obraz jako..." # Tytuł okna dialogowego
        )

        # Jeśli użytkownik wybrał nazwę pliku (tzn. nie anulował dialogu)
        if filename:
            img_to_save = self._load_image_from_url(img_url, title) # Pobierz obraz ponownie (oryginalny)
            if img_to_save: # Jeśli obraz został pomyślnie załadowany
                try:
                    # Zapis obrazu PIL do wybranego pliku
                    # Format jest zwykle dedukowany z rozszerzenia, ale można go podać jawnie
                    img_to_save.save(filename)
                    self.logger.log(f"Zapisano obraz: {filename}")
                    messagebox.showinfo("Sukces", f"Obraz zapisany jako:\n{filename}", parent=self.root)
                except Exception as e:
                    self.logger.log(f"Błąd zapisu obrazu '{title}' do pliku {filename}: {type(e).__name__} - {e}")
                    messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać obrazu: {e}", parent=self.root)
            else:
                self.logger.log(f"Anulowano zapis obrazu '{title}', ponieważ nie udało się go ponownie załadować.")
        else: # Użytkownik anulował okno dialogowe
            self.logger.log(f"Anulowano zapis obrazu '{title}'.")


# --- Uruchomienie aplikacji ---
if __name__ == "__main__":
    # Ten blok kodu jest wykonywany tylko wtedy, gdy skrypt jest uruchamiany bezpośrednio
    # (a nie importowany jako moduł).

    # Utworzenie głównego okna aplikacji Tkinter
    root = tk.Tk()
    # Utworzenie instancji naszej aplikacji, przekazując główne okno
    app = NASAImageViewer(root)
    # Uruchomienie głównej pętli zdarzeń Tkinter.
    # Ta pętla utrzymuje okno otwarte, nasłuchuje na zdarzenia (np. kliknięcia myszą, naciśnięcia klawiszy)
    # i aktualizuje interfejs użytkownika.
    root.mainloop()
