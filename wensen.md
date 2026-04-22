# Wensen Afbeeldingen Naar JPG

## Doel
We willen een eenvoudig programma maken waarmee een gebruiker een map met afbeeldingen kan kiezen en daarna alle afbeeldingen in die map kan omzetten naar JPG.

Het programma moet geschikt zijn voor eindgebruikers zonder technische kennis.

## Gewenste werking

### 1. Formulier / scherm
Het programma moet een formulier of venster hebben waarin de gebruiker:
- een map kan kiezen;
- een lijst ziet van de afbeeldingen in die gekozen map;
- een startknop ziet om de omzetting te starten;
- de voortgang van de omzetting kan volgen.

### 2. Map kiezen
De gebruiker moet via een knop een map kunnen selecteren.

Na het kiezen van de map moet het programma:
- de inhoud van die map controleren;
- alleen de ondersteunde afbeeldingsbestanden tonen;
- de gevonden afbeeldingen zichtbaar maken in een lijst.

### 3. Lijst met afbeeldingen
Na het kiezen van de map moet een overzicht worden getoond van de gevonden afbeeldingen.

Per bestand willen we minimaal kunnen zien:
- bestandsnaam;
- eventueel bestandstype;
- eventueel status tijdens de omzetting, bijvoorbeeld `wacht`, `bezig`, `klaar` of `fout`.

### 4. Start knop
Als de gebruiker op `Start` klikt, moet het programma:
- in de gekozen map automatisch een nieuwe map `geconverteerd` aanmaken;
- alle ondersteunde afbeeldingen uit de gekozen map omzetten naar JPG;
- de nieuwe JPG-bestanden opslaan in die map `geconverteerd`;
- de originele bestanden ongemoeid laten.

### 5. Outputmap
De outputmap moet dus niet ergens anders staan, maar echt in de gekozen bronmap:

Voorbeeld:

```text
vakantie-fotos\
  foto1.png
  foto2.webp
  geconverteerd\
    foto1.jpg
    foto2.jpg
```

### 6. Voortgang tonen
Tijdens het converteren moet het programma duidelijk laten zien wat er gebeurt.

Gewenst:
- een voortgangsbalk;
- een teller zoals `3 van 25 bestanden verwerkt`;
- per bestand een zichtbare status in de lijst;
- een duidelijke melding als alles klaar is.

### 7. Foutafhandeling
Als een bestand niet geconverteerd kan worden, moet het programma:
- doorgaan met de andere bestanden;
- duidelijk melden welk bestand fout ging;
- aan het eind laten zien hoeveel bestanden gelukt en mislukt zijn.

## Installatie en gebruiksgemak

### 8. Volledig zelf installerend
Het programma moet zichzelf volledig kunnen installeren voor de gebruiker.

Dat betekent dat de gebruiker zo min mogelijk handmatig hoeft te doen.

Gewenst:
- een installatiebestand of startscript;
- automatische installatie van alle benodigde software;
- automatische installatie van Python als dat nodig is, of een oplossing waarbij Python niet apart nodig is;
- automatische installatie van alle benodigde packages;
- het programma moet daarna direct gestart kunnen worden.

### 9. Eindgebruikersvriendelijk
De gebruiker moet het programma kunnen gebruiken zonder kennis van:
- Python;
- PowerShell;
- pip;
- virtual environments;
- de terminal.

Voorkeur:
- een Windows-programma met venster;
- eventueel een standalone executable of installer.

## Functionele wensen

### 10. Ondersteunde formaten
We willen in ieder geval ondersteuning voor:
- `.png`
- `.bmp`
- `.gif`
- `.tif`
- `.tiff`
- `.webp`
- `.jpeg`
- `.jpg`

### 11. JPG output
Alle output moet als `.jpg` worden opgeslagen.

Gewenst:
- nette bestandsnamen;
- bestaande extensies vervangen door `.jpg`;
- geen wijziging van de originele bestanden.

### 12. Dubbele namen
We moeten vooraf bepalen wat er gebeurt als een JPG met dezelfde naam al bestaat in `geconverteerd`.

Mogelijke keuzes voor later:
- overschrijven;
- overslaan;
- automatisch een oplopend nummer toevoegen.

## Technische richting

### 13. Voorkeursrichting
De meest logische richting lijkt:
- een desktopprogramma met een eenvoudige GUI;
- lokaal draaien op Windows;
- een build of installer voor eindgebruikers.

### 14. Mogelijke technische invulling
Waarschijnlijke aanpak:
- Python met Tkinter of vergelijkbare eenvoudige GUI;
- afbeelding-conversie via Pillow;
- standalone build voor distributie.

## Resultaat van fase 1
De eerste versie moet in elk geval:
- een map kunnen laten kiezen;
- de afbeeldingen in die map tonen;
- een map `geconverteerd` aanmaken;
- de bestanden naar JPG omzetten;
- voortgang tonen tijdens het proces.

## Vervolgopties voor later
Mogelijke uitbreidingen:
- selecteren welke bestanden wel of niet geconverteerd worden;
- kwaliteitsinstelling voor JPG;
- submappen meenemen;
- logbestand opslaan;
- automatisch openen van de map `geconverteerd` na afloop.
