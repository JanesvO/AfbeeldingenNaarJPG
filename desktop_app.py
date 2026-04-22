from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.convert_to_jpg import ConversionResult, convert_directory, iter_source_images


class AfbeeldingenNaarJpgApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Afbeeldingen Naar JPG")
        self.root.geometry("980x720")
        self.root.minsize(880, 620)

        self.folder_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Kies een map met afbeeldingen.")
        self.progress_var = tk.StringVar(value="0 van 0 bestanden verwerkt")
        self.quality_var = tk.StringVar(value="92")

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.processing = False
        self.current_files: list[Path] = []
        self.rows_by_name: dict[str, str] = {}

        self._build_ui()
        self.root.after(150, self._poll_messages)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container,
            text="Kies een map en zet alle afbeeldingen om naar JPG in een map 'geconverteerd'.",
        ).grid(row=0, column=0, sticky="w")

        folder_row = ttk.Frame(container)
        folder_row.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        folder_row.columnconfigure(0, weight=1)
        ttk.Entry(folder_row, textvariable=self.folder_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(folder_row, text="Kies map", command=self._choose_folder).grid(row=0, column=1)

        options_row = ttk.Frame(container)
        options_row.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(options_row, text="JPG-kwaliteit").pack(side="left")
        ttk.Entry(options_row, textvariable=self.quality_var, width=6).pack(side="left", padx=(8, 0))
        self.start_button = ttk.Button(options_row, text="Start conversie", command=self._start_conversion)
        self.start_button.pack(side="left", padx=(16, 0))
        ttk.Button(options_row, text="Open geconverteerd", command=self._open_output_folder).pack(side="left", padx=(8, 0))

        progress_frame = ttk.Frame(container)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        progress_frame.columnconfigure(0, weight=1)
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=2, column=0, sticky="w", pady=(8, 0))

        list_frame = ttk.LabelFrame(container, text="Afbeeldingen in gekozen map", padding=12)
        list_frame.grid(row=4, column=0, sticky="nsew", pady=(16, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("bestand", "type", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=16)
        self.tree.heading("bestand", text="Bestand")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")
        self.tree.column("bestand", width=520, anchor="w")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("status", width=160, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Kies een map met afbeeldingen")
        if not selected:
            return
        folder = Path(selected)
        self.folder_var.set(str(folder))
        self._load_images(folder)

    def _load_images(self, folder: Path) -> None:
        self.tree.delete(*self.tree.get_children())
        self.rows_by_name.clear()
        self.current_files = []

        try:
            self.current_files = iter_source_images(folder)
        except Exception as exc:
            messagebox.showerror("Map niet geldig", str(exc))
            self.status_var.set("Kies een geldige map.")
            self.progress_var.set("0 van 0 bestanden verwerkt")
            return

        if not self.current_files:
            self.status_var.set("Geen ondersteunde afbeeldingen gevonden in deze map.")
            self.progress_var.set("0 van 0 bestanden verwerkt")
            self.progress_bar["value"] = 0
            return

        for path in self.current_files:
            row_id = self.tree.insert("", "end", values=(path.name, path.suffix.lower(), "wacht"))
            self.rows_by_name[path.name] = row_id

        self.status_var.set(f"{len(self.current_files)} afbeelding(en) gevonden.")
        self.progress_var.set(f"0 van {len(self.current_files)} bestanden verwerkt")
        self.progress_bar["value"] = 0

    def _start_conversion(self) -> None:
        if self.processing:
            return

        folder_text = self.folder_var.get().strip()
        if not folder_text:
            messagebox.showerror("Map ontbreekt", "Kies eerst een map.")
            return

        folder = Path(folder_text).expanduser()
        if not self.current_files:
            self._load_images(folder)
            if not self.current_files:
                return

        try:
            quality = int(self.quality_var.get().strip())
        except ValueError:
            messagebox.showerror("Kwaliteit ongeldig", "Vul een numerieke JPG-kwaliteit in.")
            return

        self.processing = True
        self.start_button.state(["disabled"])
        self.status_var.set("Conversie gestart...")
        self.progress_bar["value"] = 0

        worker = threading.Thread(target=self._run_conversion, args=(folder.resolve(), quality), daemon=True)
        worker.start()

    def _run_conversion(self, folder: Path, quality: int) -> None:
        current_files = list(self.current_files)

        def on_progress(stage: str, current: int, total: int, result: ConversionResult | None) -> None:
            source_name = current_files[current - 1].name if current_files and current - 1 < len(current_files) else ""
            self.messages.put(("progress", (stage, current, total, source_name, result)))

        try:
            results = convert_directory(folder, quality=quality, progress_callback=on_progress)
            self.messages.put(("done", results))
        except Exception as exc:
            self.messages.put(("error", str(exc)))

    def _poll_messages(self) -> None:
        while True:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break

            if kind == "progress":
                stage, current, total, source_name, result = payload
                if stage == "started":
                    row_id = self.rows_by_name.get(source_name)
                    if row_id:
                        values = self.tree.item(row_id, "values")
                        self.tree.item(row_id, values=(values[0], values[1], "bezig"))
                    self.status_var.set(f"Bezig met converteren... {source_name}")
                elif stage == "finished" and result is not None:
                    percent = int((current / total) * 100) if total else 0
                    self.progress_bar["value"] = percent
                    self.progress_var.set(f"{current} van {total} bestanden verwerkt")
                    status = "klaar" if result.success else "fout"
                    row_id = self.rows_by_name.get(result.source_path.name)
                    if row_id:
                        self.tree.item(row_id, values=(result.source_path.name, result.source_path.suffix.lower(), status))
                    self.status_var.set(f"Bezig met converteren... {result.source_path.name}")
            elif kind == "done":
                results = payload
                self.processing = False
                self.start_button.state(["!disabled"])
                success_count = sum(1 for result in results if result.success)
                failed_count = len(results) - success_count
                self.status_var.set(f"Klaar. {success_count} gelukt, {failed_count} mislukt.")
                self.progress_var.set(f"{len(results)} van {len(results)} bestanden verwerkt")
                if failed_count == 0:
                    messagebox.showinfo("Conversie voltooid", f"Alle {success_count} bestand(en) zijn omgezet.")
                else:
                    messagebox.showwarning(
                        "Conversie voltooid",
                        f"{success_count} bestand(en) gelukt, {failed_count} mislukt.",
                    )
            elif kind == "error":
                self.processing = False
                self.start_button.state(["!disabled"])
                self.status_var.set("Conversie gestopt door een fout.")
                messagebox.showerror("Fout", str(payload))

        self.root.after(150, self._poll_messages)

    def _open_output_folder(self) -> None:
        folder_text = self.folder_var.get().strip()
        if not folder_text:
            messagebox.showinfo("Outputmap", "Kies eerst een map.")
            return

        output_dir = Path(folder_text).expanduser() / "geconverteerd"
        if not output_dir.exists():
            messagebox.showinfo("Outputmap", "De map 'geconverteerd' bestaat nog niet.")
            return

        os.startfile(str(output_dir))


def main() -> None:
    root = tk.Tk()
    app = AfbeeldingenNaarJpgApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
