# Hälsingetoppen Web Admin Interface

Ett webbaserat administrationsverktyg för att hantera Hälsingetoppens artist- och låtdatabas.

## Funktioner

### 📊 Dashboard
- Översikt över databasstatistik
- Snabb tillgång till huvudfunktioner
- Visar senast tillagda artister

### 👨‍🎤 Artisthantering
- **Lista artister**: Visa alla artister med sortering och filtrering
- **Lägg till artist**: Manuellt eller via Spotify-sökning
- **Redigera artist**: Uppdatera artistinformation
- **Ta bort artist**: Ta bort artist och associerade låtar
- **Spotify-integration**: Automatisk hämtning av artistdata

### 🎵 Låthantering
- **Lista låtar**: Visa alla låtar med sök- och filterfunktioner
- **Redigera låtar**: Uppdatera låtinformation
- **Ta bort låtar**: Ta bort enskilda låtar
- **Artistkoppling**: Låtar är kopplade till sina artister

### 🔧 Generering och synkronisering
- **Generera HTML-topplista**: Skapa publikfärdig topplista (ersätter `ht.py`)
- **Generera HTML-låtlista**: Skapa lista med alla låtar (ersätter `topp_songs.py`)
- **Synkronisera låtar**: Hämta top tracks från Spotify (ersätter `tracks.py`)
- **Uppdatera artist-data**: Hämta senaste popularitet och följare från Spotify
- **Nedladdning**: Ladda ner genererade HTML-filer

## Installation och start

### Förutsättningar
- Python 3.7+
- Virtuell miljö (rekommenderas)
- SQLite3
- Internet-anslutning (för Spotify-integration)

### Snabbstart
```bash
# Starta webservern
./start_web_admin.sh
```

### Manuell start
```bash
# Aktivera virtuell miljö
source .venv/bin/activate

# Installera beroenden (om inte redan gjort)
pip install flask

# Starta applikationen
python web_admin.py
```

Webgränssnittet blir tillgängligt på: http://localhost:5000

## Användning

### Lägg till en artist

1. **Via Spotify-sökning** (rekommenderas):
   - Klicka på "Lägg till artist"
   - Använd Spotify-sökningen i högra kolumnen
   - Klicka på önskad artist i sökresultaten
   - Kontrollera och spara

2. **Manuellt**:
   - Klicka på "Lägg till artist"
   - Fyll i artistnamn (obligatoriskt)
   - Valfritt: Ange Spotify-URL för automatisk datahämtning
   - Spara

### Hantera artister

- **Visa detaljer**: Klicka på artistnamnet för att se alla låtar
- **Redigera**: Använd redigeringsknappen för att uppdatera information
- **Inaktivera**: Markera artist som inaktiv istället för att ta bort
- **Ta bort**: Permanent borttagning (tar även bort alla låtar)

### Hantera låtar

- **Lista**: Visa alla låtar med sortering efter popularitet, namn, artist eller datum
- **Filtrera**: Filtrera låtar efter artist
- **Redigera**: Uppdatera låtinformation som namn, popularitet, album typ
- **Ta bort**: Ta bort enskilda låtar

### Sök- och filterfunktioner

- **Textsökning**: Sök i artist- och låtnamn (skiftlägesokänslig)
- **Sortering**: Sortera efter olika kriterier (popularitet, namn, följare)
- **Filter**: Visa/dölja inaktiva artister, filtrera efter specifik artist
- **Case insensitive**: All sökning fungerar oavsett stora/små bokstäver

### Generering av HTML-listor

Webinterfacet inkluderar nu alla funktioner från de ursprungliga skripten:

#### 🏆 Generera topplista (tidigare ht.py)
- Skapar publikfärdig HTML-topplista
- Uppdaterar artist-data från Spotify först (valfritt)
- Sorterar efter popularitet och följare
- Inkluderar artistbilder och länkar
- Sparas som `topplista-ÅÅÅÅ-MM-DD.html`

#### 🎵 Generera låtlista (tidigare topp_songs.py)
- Skapar HTML-lista med alla låtar
- Alfabetisk sortering
- Länkar till både låtar och artister på Spotify
- Visar album-typ och utgivningsdatum
- Sparas som `songs.html`

#### 🔄 Synkronisera låtar (tidigare tracks.py)
- Hämtar top 10 tracks från Spotify för alla artister
- Uppdaterar hela låtdatabasen
- Rate limiting för att respektera Spotify API
- Valfritt: uppdatera Spotify-spellista
- Visar progress och statistik

## Databasstruktur

### Artister (artists)
- `id`: Spotify Artist ID eller lokalt genererat ID
- `name`: Artistnamn
- `popularity`: Popularitetspoäng (0-100)
- `followers`: Antal följare på Spotify
- `link`: Spotify-länk
- `picture_small`: URL till artistbild
- `bInactivate`: Inaktiveringsflagga (0=aktiv, 1=inaktiv)

### Låtar (tracks)
- `id`: Spotify Track ID
- `artist_id`: Koppling till artist
- `name`: Låtnamn
- `popularity`: Popularitetspoäng (0-100)
- `album_type`: Typ av album (album, single, compilation, appears_on)
- `url`: Spotify-länk till låten
- `release_date`: Utgivningsdatum

## Spotify-integration

För att använda Spotify-funktioner behöver du:

1. **Spotify-utvecklarkonto**: Skapa på https://developer.spotify.com
2. **Miljövariabler**: Sätt `SPOTIPY_CLIENT_ID` och `SPOTIPY_CLIENT_SECRET`

```bash
export SPOTIPY_CLIENT_ID="ditt_client_id"
export SPOTIPY_CLIENT_SECRET="ditt_client_secret"
```

### Funktioner med Spotify
- Automatisk hämtning av artistdata (popularitet, följare, bilder)
- Sök efter artister
- Validering av Spotify-ID:n
- Direktlänkar till Spotify

## Säkerhet

⚠️ **Viktigt**: Detta är ett utvecklingsverktyg för lokalt bruk.

För produktionsmiljö:
- Ändra `app.secret_key` till en säker slumpmässig sträng
- Använd en produktions-WSGI-server (t.ex. Gunicorn)
- Implementera autentisering
- Konfigurera HTTPS
- Säkra databasåtkomst

## Teknisk information

### Teknologier
- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, jQuery
- **Databas**: SQLite3
- **API**: Spotify Web API (via spotipy)

### Filstruktur
```
.
├── web_admin.py              # Huvudapplikation
├── start_web_admin.sh        # Startskript
├── config.py                 # Konfiguration
├── templates/                # HTML-mallar
│   ├── base.html            # Basmall
│   ├── dashboard.html       # Dashboard
│   ├── artists.html         # Artistlista
│   ├── artist_detail.html   # Artistdetaljer
│   ├── add_artist.html      # Lägg till artist
│   ├── edit_artist.html     # Redigera artist
│   ├── tracks.html          # Låtlista
│   ├── edit_track.html      # Redigera låt
│   ├── generate_menu.html   # Genereringsmeny
│   ├── generate_toplist.html # Generera topplista
│   └── sync_tracks.html     # Synkronisera låtar
└── toppen.sqlite3           # Databas
```

### API-endpoints
- `GET /`: Dashboard
- `GET /artists`: Lista artister
- `GET /artist/<id>`: Artistdetaljer
- `GET/POST /artist/add`: Lägg till artist
- `GET/POST /artist/<id>/edit`: Redigera artist
- `POST /artist/<id>/delete`: Ta bort artist
- `GET /tracks`: Lista låtar
- `GET/POST /track/<id>/edit`: Redigera låt
- `POST /track/<id>/delete`: Ta bort låt
- `GET /api/search_spotify`: Sök Spotify
- `GET /generate`: Genereringsmeny
- `GET/POST /generate/toplist`: Generera HTML-topplista
- `POST /generate/songs`: Generera HTML-låtlista
- `GET/POST /sync/tracks`: Synkronisera låtar från Spotify
- `GET /download/<filename>`: Ladda ner genererade filer

## Felsökning

### Vanliga problem

**"Spotify not configured"**
- Kontrollera att miljövariablerna SPOTIPY_CLIENT_ID och SPOTIPY_CLIENT_SECRET är satta

**"Database not found"**
- Applikationen skapar databasen automatiskt vid första start
- Kontrollera att du har skrivbehörighet i katalogen

**"Port already in use"**
- Ändra port genom att modifiera `app.run(port=5000)` i web_admin.py

### Loggning
Applikationen kör i debug-läge och loggar fel till konsolen.

## Licens

Se huvudprojektets licensfil.

## Bidrag

Förbättringar och buggrapporter är välkomna!