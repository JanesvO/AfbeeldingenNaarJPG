# Afbeeldingen Naar JPG

Desktopprogramma om afbeeldingen uit een gekozen map om te zetten naar JPG in een submap `geconverteerd`.

## Structuur
- `desktop_app.py` bevat het formulier
- `src/convert_to_jpg.py` bevat de conversielogica
- `install-from-git.ps1` is de Python-ontwikkelinstallatie
- `Install-AfbeeldingenNaarJPG.cmd` is de Python-ontwikkelstarter
- `run-desktop-app.ps1` start de app vanuit de lokale ontwikkelomgeving
- `build-standalone.ps1` maakt een zelfstandige Windows-build
- `release/` bevat deelbare builds
- `bouwplan.md` bevat het fasenplan
- `wensen.md` bevat de functionele wensen

## Installatie

Voor gewone gebruikers op Windows:

```powershell
.\release\0.1\Install-AfbeeldingenNaarJPG-Standalone.cmd
```

Of zonder installatie:

```powershell
.\release\0.1\Start-AfbeeldingenNaarJPG.cmd
```

## Ontwikkelroute

De volgende bestanden zijn alleen bedoeld voor ontwikkeling en broncodegebruik:
- `Install-AfbeeldingenNaarJPG.cmd`
- `install-from-git.ps1`
- `run-desktop-app.ps1`

Die route probeert Python en packages te gebruiken en is niet de aanbevolen eindgebruikersroute.

## Gebruik

Na standalone installatie start je de GUI via:

```powershell
.\release\0.1\Start-AfbeeldingenNaarJPG.cmd
```

Of:

```powershell
.\release\0.1\standalone\AfbeeldingenNaarJPG\AfbeeldingenNaarJPG.exe
```

De gebruiker kiest daarna zelf een map. Het programma toont de gevonden afbeeldingen en zet ze om naar JPG in een map `geconverteerd` binnen die gekozen map.

## Standalone build

Voor een zelfstandige Windows-versie:

```powershell
.\build-standalone.ps1
```

De build komt daarna in `release\<versie>\standalone\`.

## Andere pc's

Voor andere Windows-pc's is de standalone release de enige aanbevolen route.

Daarvoor is normaal gesproken nodig:
- Windows 10 of 11
- verder geen Python
- geen aparte package-installatie

Gebruik in de release-map:

```powershell
.\Install-AfbeeldingenNaarJPG-Standalone.cmd
```

Dat script installeert het programma lokaal en maakt snelkoppelingen aan.

## Console-script
Voor rechtstreeks gebruik zonder GUI:

```powershell
.\.venv\Scripts\python.exe .\src\convert_to_jpg.py --input "C:\pad\naar\afbeeldingen"
```

## Ondersteunde formaten
- `.png`
- `.bmp`
- `.gif`
- `.tif`
- `.tiff`
- `.webp`
- `.jpeg`
- `.jpg`
