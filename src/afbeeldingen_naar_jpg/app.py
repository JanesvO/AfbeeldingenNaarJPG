from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from afbeeldingen_naar_jpg import APP_NAME, AUTHOR, REPO_URL, WEBSITE_URL, __version__
from afbeeldingen_naar_jpg.converter import (
    ON_EXISTING_NUMBER,
    ON_EXISTING_OVERWRITE,
    ON_EXISTING_SKIP,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_SKIPPED,
    SUPPORTED_EXTENSIONS,
    Cancelled,
    ConversionOptions,
    ConversionResult,
    convert_files,
    find_images,
    output_dir_for,
)

CONFIG_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "AfbeeldingenNaarJPG"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
UPDATE_COMMAND = f"irm {REPO_URL.replace('github.com', 'raw.githubusercontent.com')}/main/get.ps1 | iex"

ON_EXISTING_LABELS = {
    "Nummer toevoegen (foto-2.jpg)": ON_EXISTING_NUMBER,
    "Overschrijven": ON_EXISTING_OVERWRITE,
    "Overslaan": ON_EXISTING_SKIP,
}
SIZE_LABELS = {
    "Originele grootte": None,
    "Max. 3840 px (4K)": 3840,
    "Max. 2560 px": 2560,
    "Max. 1920 px (Full HD)": 1920,
    "Max. 1280 px": 1280,
    "Max. 800 px (web)": 800,
}


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


class AfbeeldingenNaarJpgApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_NAME} {__version__}")
        self.root.geometry("1000x760")
        self.root.minsize(880, 640)

        settings = self._load_settings()
        self.folder_var = tk.StringVar(value=settings.get("folder", ""))
        self.quality_var = tk.IntVar(value=int(settings.get("quality", 92)))
        on_existing = settings.get("on_existing", ON_EXISTING_NUMBER)
        self.on_existing_var = tk.StringVar(
            value=next((label for label, value in ON_EXISTING_LABELS.items() if value == on_existing), list(ON_EXISTING_LABELS)[0])
        )
        max_size = settings.get("max_size")
        self.size_var = tk.StringVar(
            value=next((label for label, value in SIZE_LABELS.items() if value == max_size), list(SIZE_LABELS)[0])
        )
        self.subfolders_var = tk.BooleanVar(value=bool(settings.get("include_subfolders", False)))
        self.metadata_var = tk.BooleanVar(value=bool(settings.get("keep_metadata", True)))
        self.open_after_var = tk.BooleanVar(value=bool(settings.get("open_after", True)))
        self.status_var = tk.StringVar(value="Kies een map met afbeeldingen.")
        self.progress_var = tk.StringVar(value="")

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.processing = False
        self.cancel_event = threading.Event()
        self.files: list[Path] = []
        self.row_ids: dict[Path, str] = {}

        self._build_menu()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(150, self._poll_messages)

        folder = self.folder_var.get().strip()
        if folder and Path(folder).is_dir():
            self._load_images()

    # ------------------------------------------------------------------ instellingen

    def _load_settings(self) -> dict:
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self) -> None:
        settings = {
            "folder": self.folder_var.get().strip(),
            "quality": self.quality_var.get(),
            "on_existing": ON_EXISTING_LABELS[self.on_existing_var.get()],
            "max_size": SIZE_LABELS[self.size_var.get()],
            "include_subfolders": self.subfolders_var.get(),
            "keep_metadata": self.metadata_var.get(),
            "open_after": self.open_after_var.get(),
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _options(self) -> ConversionOptions:
        return ConversionOptions(
            quality=self.quality_var.get(),
            on_existing=ON_EXISTING_LABELS[self.on_existing_var.get()],
            include_subfolders=self.subfolders_var.get(),
            max_size=SIZE_LABELS[self.size_var.get()],
            keep_metadata=self.metadata_var.get(),
        )

    # ------------------------------------------------------------------ scherm

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Map kiezen...", command=self._choose_folder)
        file_menu.add_command(label="Map 'geconverteerd' openen", command=self._open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Afsluiten", command=self._on_close)
        menubar.add_cascade(label="Bestand", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Handleiding", command=lambda: webbrowser.open(REPO_URL + "#readme"))
        help_menu.add_command(label="Bijwerken naar nieuwste versie...", command=self._update_app)
        help_menu.add_separator()
        help_menu.add_command(label=f"Website {AUTHOR}", command=lambda: webbrowser.open(WEBSITE_URL))
        help_menu.add_command(label=f"Over {APP_NAME}", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container,
            text="Kies een map. De afbeeldingen worden als JPG opgeslagen in de submap 'geconverteerd'; "
            "de originelen blijven ongewijzigd.",
        ).grid(row=0, column=0, sticky="w")

        folder_row = ttk.Frame(container)
        folder_row.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        folder_row.columnconfigure(0, weight=1)
        folder_entry = ttk.Entry(folder_row, textvariable=self.folder_var)
        folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        folder_entry.bind("<Return>", lambda _event: self._load_images())
        ttk.Button(folder_row, text="Kies map", command=self._choose_folder).grid(row=0, column=1)
        ttk.Button(folder_row, text="Vernieuwen", command=self._load_images).grid(row=0, column=2, padx=(8, 0))

        options = ttk.LabelFrame(container, text="Instellingen", padding=10)
        options.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(options, text="JPG-kwaliteit").grid(row=0, column=0, sticky="w")
        quality_row = ttk.Frame(options)
        quality_row.grid(row=1, column=0, sticky="w")
        ttk.Scale(
            quality_row, from_=50, to=100, orient="horizontal", length=160,
            command=lambda value: self.quality_var.set(round(float(value))),
            variable=self.quality_var,
        ).pack(side="left")
        ttk.Label(quality_row, textvariable=self.quality_var, width=4).pack(side="left", padx=(6, 0))

        ttk.Label(options, text="Als de JPG al bestaat").grid(row=0, column=1, sticky="w", padx=(20, 0))
        ttk.Combobox(
            options, textvariable=self.on_existing_var, values=list(ON_EXISTING_LABELS), state="readonly", width=28
        ).grid(row=1, column=1, sticky="w", padx=(20, 0))

        ttk.Label(options, text="Afmeting").grid(row=0, column=2, sticky="w", padx=(20, 0))
        ttk.Combobox(
            options, textvariable=self.size_var, values=list(SIZE_LABELS), state="readonly", width=22
        ).grid(row=1, column=2, sticky="w", padx=(20, 0))

        checks = ttk.Frame(options)
        checks.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))
        ttk.Checkbutton(
            checks, text="Submappen meenemen", variable=self.subfolders_var, command=self._load_images
        ).pack(side="left")
        ttk.Checkbutton(checks, text="Fotogegevens (EXIF) behouden", variable=self.metadata_var).pack(
            side="left", padx=(16, 0)
        )
        ttk.Checkbutton(checks, text="Map openen als het klaar is", variable=self.open_after_var).pack(
            side="left", padx=(16, 0)
        )

        actions = ttk.Frame(container)
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(3, weight=1)
        self.start_button = ttk.Button(actions, text="Start conversie", command=self._start_conversion)
        self.start_button.grid(row=0, column=0)
        self.cancel_button = ttk.Button(actions, text="Annuleren", command=self._cancel, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=(8, 0))
        ttk.Button(actions, text="Open 'geconverteerd'", command=self._open_output_folder).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Label(actions, textvariable=self.status_var).grid(row=0, column=3, sticky="e")

        list_frame = ttk.LabelFrame(container, text="Afbeeldingen", padding=10)
        list_frame.grid(row=4, column=0, sticky="nsew", pady=(12, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        selection_row = ttk.Frame(list_frame)
        selection_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(
            selection_row,
            text="Geen selectie: alle bestanden. Met selectie (Ctrl/Shift+klik): alleen die bestanden.",
            foreground="gray",
        ).pack(side="left")
        ttk.Button(selection_row, text="Niets selecteren", command=lambda: self.tree.selection_remove(self.tree.selection())).pack(side="right")
        ttk.Button(selection_row, text="Alles selecteren", command=lambda: self.tree.selection_set(self.tree.get_children())).pack(
            side="right", padx=(0, 6)
        )

        columns = ("bestand", "type", "grootte", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        for column, title, width, anchor in (
            ("bestand", "Bestand", 460, "w"),
            ("type", "Type", 70, "w"),
            ("grootte", "Grootte", 90, "e"),
            ("status", "Status", 260, "w"),
        ):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor=anchor, stretch=column in ("bestand", "status"))
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.tag_configure(STATUS_FAILED, foreground="#c01c28")
        self.tree.tag_configure(STATUS_SKIPPED, foreground="#9a6700")
        self.tree.tag_configure(STATUS_DONE, foreground="#1a7f37")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        progress_row = ttk.Frame(container)
        progress_row.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        progress_row.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(progress_row, mode="determinate", maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(progress_row, textvariable=self.progress_var, width=28, anchor="e").grid(row=0, column=1, padx=(8, 0))

        footer = ttk.Frame(container)
        footer.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        formats = ", ".join(sorted(extension.lstrip(".") for extension in SUPPORTED_EXTENSIONS))
        ttk.Label(footer, text=f"{APP_NAME} {__version__}  ·  Formaten: {formats}", foreground="gray").pack(side="left")
        link = tk.Label(
            footer,
            text=f"Gemaakt door {AUTHOR} · {WEBSITE_URL.removeprefix('https://').rstrip('/')}",
            fg="#1a5fb4",
            cursor="hand2",
        )
        link.pack(side="right")
        link.bind("<Button-1>", lambda _event: webbrowser.open(WEBSITE_URL))

    # ------------------------------------------------------------------ map en lijst

    def _choose_folder(self) -> None:
        current = self.folder_var.get().strip()
        selected = filedialog.askdirectory(
            title="Kies een map met afbeeldingen",
            initialdir=current if current and Path(current).is_dir() else str(Path.home()),
        )
        if selected:
            self.folder_var.set(str(Path(selected)))
            self._load_images()

    def _load_images(self) -> None:
        if self.processing:
            return
        self.tree.delete(*self.tree.get_children())
        self.row_ids.clear()
        self.files = []
        self.progress_bar["value"] = 0
        self.progress_var.set("")

        folder_text = self.folder_var.get().strip()
        if not folder_text:
            self.status_var.set("Kies een map met afbeeldingen.")
            return
        folder = Path(folder_text).expanduser()
        try:
            self.files = find_images(folder, self.subfolders_var.get())
        except OSError as exc:
            self.status_var.set("Kies een geldige map.")
            messagebox.showerror("Map niet geldig", str(exc))
            return

        self._save_settings()
        for path in self.files:
            try:
                size = _format_size(path.stat().st_size)
            except OSError:
                size = ""
            row_id = self.tree.insert(
                "", "end", values=(str(path.relative_to(folder)), path.suffix.lower().lstrip("."), size, "wacht")
            )
            self.row_ids[path] = row_id

        if self.files:
            self.status_var.set(f"{len(self.files)} afbeelding(en) gevonden.")
        else:
            self.status_var.set("Geen ondersteunde afbeeldingen gevonden in deze map.")

    def _selected_files(self) -> list[Path]:
        selected = set(self.tree.selection())
        if not selected:
            return list(self.files)
        return [path for path in self.files if self.row_ids.get(path) in selected]

    # ------------------------------------------------------------------ omzetten

    def _start_conversion(self) -> None:
        if self.processing:
            return
        folder_text = self.folder_var.get().strip()
        if not folder_text:
            messagebox.showerror("Map ontbreekt", "Kies eerst een map.")
            return
        if not self.files:
            self._load_images()
            if not self.files:
                return

        files = self._selected_files()
        folder = Path(folder_text).expanduser().resolve()
        options = self._options()
        self._save_settings()

        for path in files:
            row_id = self.row_ids[path]
            values = self.tree.item(row_id, "values")
            self.tree.item(row_id, values=(*values[:3], "wacht"), tags=())

        self.processing = True
        self.cancel_event.clear()
        self.start_button.state(["disabled"])
        self.cancel_button.state(["!disabled"])
        self.progress_bar["value"] = 0
        self.status_var.set("Bezig met omzetten...")
        threading.Thread(target=self._run_conversion, args=(files, folder, options), daemon=True).start()

    def _run_conversion(self, files: list[Path], folder: Path, options: ConversionOptions) -> None:
        def on_progress(stage: str, current: int, total: int, source: Path, result: ConversionResult | None) -> None:
            self.messages.put(("progress", (stage, current, total, source, result)))

        try:
            results = convert_files(files, folder, options, on_progress, self.cancel_event)
            self.messages.put(("done", (folder, results, False)))
        except Cancelled:
            self.messages.put(("done", (folder, [], True)))
        except Exception as exc:
            self.messages.put(("error", str(exc)))

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.cancel_button.state(["disabled"])
        self.status_var.set("Annuleren na het huidige bestand...")

    def _poll_messages(self) -> None:
        while True:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                self._on_progress(*payload)
            elif kind == "done":
                self._on_done(*payload)
            elif kind == "error":
                self._finish()
                self.status_var.set("Gestopt door een fout.")
                messagebox.showerror("Fout", str(payload))
        self.root.after(100, self._poll_messages)

    def _on_progress(self, stage: str, current: int, total: int, source: Path, result: ConversionResult | None) -> None:
        row_id = self.row_ids.get(source)
        if row_id is None:
            return
        values = self.tree.item(row_id, "values")
        if stage == "started":
            self.tree.item(row_id, values=(*values[:3], "bezig..."))
            self.tree.see(row_id)
            return
        if result is None:
            return
        if result.status == STATUS_DONE:
            status = "klaar"
        elif result.status == STATUS_SKIPPED:
            status = f"overgeslagen ({result.message})"
        else:
            status = f"fout: {result.message}"
        self.tree.item(row_id, values=(*values[:3], status), tags=(result.status,))
        self.progress_bar["value"] = current / total * 100 if total else 0
        self.progress_var.set(f"{current} van {total} bestanden verwerkt")

    def _on_done(self, folder: Path, results: list[ConversionResult], cancelled: bool) -> None:
        self._finish()
        if cancelled:
            self.status_var.set("Geannuleerd.")
            return
        done = sum(result.status == STATUS_DONE for result in results)
        skipped = sum(result.status == STATUS_SKIPPED for result in results)
        failed = sum(result.status == STATUS_FAILED for result in results)
        summary = f"{done} omgezet, {skipped} overgeslagen, {failed} mislukt."
        self.status_var.set(f"Klaar: {summary}")
        if failed:
            messagebox.showwarning("Klaar", f"{summary}\n\nDe foutmelding per bestand staat in de lijst.")
        elif self.open_after_var.get() and done:
            self._open_folder(output_dir_for(folder))

    def _finish(self) -> None:
        self.processing = False
        self.start_button.state(["!disabled"])
        self.cancel_button.state(["disabled"])

    # ------------------------------------------------------------------ overig

    def _open_folder(self, folder: Path) -> None:
        if folder.exists():
            os.startfile(str(folder))

    def _open_output_folder(self) -> None:
        folder_text = self.folder_var.get().strip()
        if not folder_text:
            messagebox.showinfo("Map 'geconverteerd'", "Kies eerst een map.")
            return
        output = output_dir_for(Path(folder_text).expanduser())
        if not output.exists():
            messagebox.showinfo("Map 'geconverteerd'", "De map 'geconverteerd' bestaat nog niet. Start eerst een conversie.")
            return
        self._open_folder(output)

    def _update_app(self) -> None:
        if self.processing:
            messagebox.showinfo("Bijwerken", "Wacht tot de conversie klaar is.")
            return
        if not messagebox.askyesno(
            "Bijwerken",
            f"De nieuwste versie van {APP_NAME} wordt gedownload en geinstalleerd. Het programma wordt daarvoor gesloten.\n\nDoorgaan?",
        ):
            return
        script = (
            f"$Host.UI.RawUI.WindowTitle = '{APP_NAME} bijwerken'; {UPDATE_COMMAND}; "
            "Write-Host ''; Read-Host 'Klaar. Druk op Enter om dit venster te sluiten'"
        )
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        )
        self.root.destroy()

    def _show_about(self) -> None:
        messagebox.showinfo(
            f"Over {APP_NAME}",
            f"{APP_NAME} {__version__}\n\n"
            "Zet afbeeldingen in een map in een keer om naar JPG.\nGratis te gebruiken.\n\n"
            f"Gemaakt door {AUTHOR}\n{WEBSITE_URL}",
        )

    def _on_close(self) -> None:
        if self.processing and not messagebox.askyesno("Afsluiten", "Er wordt nog omgezet. Toch afsluiten?"):
            return
        self.cancel_event.set()
        self._save_settings()
        self.root.destroy()


def main() -> None:
    if sys.platform == "win32":
        try:
            # Scherpe tekst op schermen met schaalfactor.
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    # In de build staat het icoon naast de app; vanuit de broncode in assets/.
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2] / "assets"))
    icon = base / "icon.ico"
    if icon.exists():
        try:
            root.iconbitmap(default=str(icon))
        except tk.TclError:
            pass
    AfbeeldingenNaarJpgApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
