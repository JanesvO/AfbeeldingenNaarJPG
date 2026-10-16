# Afbeeldingen Naar JPG

Gratis Windows-programma dat alle afbeeldingen in een map in één keer omzet naar JPG. De originele bestanden blijven ongewijzigd; de JPG's komen in een nieuwe submap `geconverteerd`.

```text
vakantiefotos\
  strand.png
  iphone-foto.heic
  logo.webp
  geconverteerd\        <- nieuw
    strand.jpg
    iphone-foto.jpg
    logo.jpg
```

- **Formaten:** PNG, HEIC/HEIF (iPhone), WebP, AVIF, GIF, BMP, TIFF, ICO en JPG
- **Doorzichtige delen** (bijvoorbeeld in een PNG-logo) worden wit in plaats van zwart
- **Gedraaide foto's** komen goed te staan (EXIF-oriëntatie)
- **Instelbaar:** kwaliteit, maximale afmeting (bijvoorbeeld voor web of e-mail), en wat er gebeurt als een JPG al bestaat
- **Submappen** kunnen worden meegenomen, met dezelfde mapindeling
- **Alleen een deel** van de bestanden omzetten kan, door ze te selecteren
- Python of andere software is **niet** nodig

Gemaakt door **[JvO ICT](https://jvoict.nl/)**.

---

## Installeren

### Optie A: met één opdracht (aanbevolen)

1. Druk op **Start**, typ `PowerShell` en open **Windows PowerShell**.
2. Plak deze regel en druk op **Enter**:

   ```powershell
   irm https://raw.githubusercontent.com/JanesvO/AfbeeldingenNaarJPG/main/get.ps1 | iex
   ```

3. Na een halve minuut staat **Afbeeldingen Naar JPG** in het Startmenu en op het bureaublad.

### Optie B: via een ZIP-bestand

1. Ga naar [**Releases**](https://github.com/JanesvO/AfbeeldingenNaarJPG/releases/latest) en download **AfbeeldingenNaarJPG.zip**. De bestanden "Source code" heb je niet nodig.
2. Klik met de rechtermuisknop op het ZIP-bestand en kies **Alles uitpakken…**.
3. Dubbelklik in de uitgepakte map op **Install.cmd**.
   - Verschijnt er een blauw venster "Windows heeft uw pc beveiligd"? Klik dan op **Meer informatie** en daarna op **Toch uitvoeren**.

Beheerdersrechten zijn niet nodig. Het programma wordt geïnstalleerd in `%LOCALAPPDATA%\Programs\AfbeeldingenNaarJPG`.

---

## Gebruik

1. Start **Afbeeldingen Naar JPG**.
2. Klik **Kies map** en selecteer de map met afbeeldingen. Je ziet meteen welke bestanden er worden gevonden.
3. Pas zo nodig de instellingen aan:

   | Instelling | Uitleg |
   |---|---|
   | JPG-kwaliteit | 92 is een goede standaard. Lager geeft kleinere bestanden. |
   | Als de JPG al bestaat | **Nummer toevoegen** (`foto-2.jpg`), **Overschrijven** of **Overslaan** |
   | Afmeting | **Originele grootte**, of verkleinen tot bijvoorbeeld 1920 px (Full HD) of 800 px (web). Kleinere afbeeldingen worden nooit vergroot. |
   | Submappen meenemen | Zet ook afbeeldingen in submappen om, met dezelfde mapindeling |
   | Fotogegevens (EXIF) behouden | Neemt opnamedatum, camera en eventueel locatie over. Zet dit uit als je foto's online deelt. |
   | Map openen als het klaar is | Opent `geconverteerd` na afloop |

4. Klik **Start conversie**. In de lijst zie je per bestand **klaar**, **overgeslagen** of **fout**, met de reden erbij.

Wil je maar een paar bestanden omzetten? Selecteer ze in de lijst met Ctrl+klik of Shift+klik. Zonder selectie worden alle bestanden omgezet.

Het programma onthoudt je laatste map en je instellingen.

## Bijwerken

Kies in het programma **Help > Bijwerken naar nieuwste versie...**, of voer optie A of B opnieuw uit. Je instellingen blijven bewaard.

## Verwijderen

Ga naar **Instellingen > Apps > Geïnstalleerde apps**, zoek **Afbeeldingen Naar JPG** en kies **Verwijderen**. Je geconverteerde afbeeldingen blijven gewoon staan.

## Problemen oplossen

| Probleem | Oplossing |
|---|---|
| Een bestand geeft "geen geldige afbeelding" | Het bestand is beschadigd of heeft een verkeerde extensie. Probeer het te openen in een fotoviewer. |
| "geen toegang" | Het bestand is geopend in een ander programma, of de map is alleen-lezen. |
| Een GIF of TIFF met meerdere beelden | Alleen het eerste beeld wordt omgezet. |
| Het blauwe venster "Windows heeft uw pc beveiligd" | Klik op **Meer informatie** en daarna op **Toch uitvoeren**. Het programma is niet digitaal ondertekend. |

---

## Voor ontwikkelaars

```text
src/afbeeldingen_naar_jpg/   app.py (venster), converter.py (omzetten, ook als opdrachtregel), __init__.py (versie)
scripts/                     build-release.ps1, install.ps1, uninstall.ps1, Install.cmd, make_icon.py, run-dev.ps1
assets/                      icon.ico / icon.png
get.ps1                      installatie met één opdracht (downloadt de nieuwste release)
docs/                        oorspronkelijke wensen en bouwplan
```

Vanuit de broncode starten:

```powershell
.\scripts\run-dev.ps1
```

Vanaf de opdrachtregel omzetten:

```powershell
$env:PYTHONPATH = "src"
.\.venv-build\Scripts\python.exe -m afbeeldingen_naar_jpg.converter --input "C:\map" --subfolders --max-size 1920
```

**Nieuwe versie uitbrengen:**

1. Verhoog `__version__` in `src/afbeeldingen_naar_jpg/__init__.py`.
2. Commit en push.
3. Draai `.\scripts\build-release.ps1 -Publish`. Dit:
   - bouwt de exe met PyInstaller in een schone `.venv-build`;
   - test of de app start;
   - maakt `dist\AfbeeldingenNaarJPG-<versie>.zip`;
   - maakt een GitHub-release met `AfbeeldingenNaarJPG.zip`.
