# Bing Wallpaper Downloader

Applicazione desktop multipiattaforma che scarica automaticamente gli sfondi Bing dalle **GitHub Releases** e li aggiorna periodicamente.

## Funzionalità

- 🖼️ **Download da Release**: Scarica tutti gli sfondi dalla release `wallpapers-archive` del progetto
- ⏰ **Aggiornamento Automatico**: Controllo periodico di nuovi sfondi (default: ogni 60 minuti)
- 📁 **Cartella Personalizzabile**: Scegli dove salvare gli sfondi
- 📊 **Progress Bar**: Monitora il download di tutti gli sfondi
- 🔄 **Rilevamento Nuovi**: Scarica solo gli sfondi mancanti
- 💻 **Multipiattaforma**: Funziona su Windows, macOS e Linux
- 🎨 **Zero Dipendenze**: Usa solo la libreria standard di Python

## Requisiti

- Python 3.6 o superiore
- Nessuna installazione di pacchetti esterni (solo libreria standard)

## Installazione

Nessuna installazione necessaria! Basta scaricare lo script ed eseguirlo.

```bash
# Rendi eseguibile il launcher (Linux/macOS)
chmod +x run-wallpaper-downloader.sh
```

## Utilizzo

### Avvio Rapido

```bash
# Linux/macOS
./run-wallpaper-downloader.sh

# Windows (Git Bash/WSL)
./run-wallpaper-downloader.sh

# Oppure direttamente con Python
python3 wallpaper_downloader.py
```

### Come Usare l'App

1. **Cartella Download**: Clicca "Browse" per scegliere dove salvare gli sfondi
2. **Intervallo Aggiornamento**: Ogni quanti minuti controllare nuovi sfondi
3. **Salva Impostazioni**: Clicca per applicare le modifiche
4. **Download All**: Scarica **tutti** gli sfondi dalla release (~120+ immagini)
5. **Check Updates**: Controlla e scarica solo i nuovi sfondi mancanti
6. **Auto**: Abilita il controllo periodico automatico
7. **Open Folder**: Apri la cartella degli sfondi
8. **View Gallery**: Apri la galleria online nel browser

### Pulsanti Principali

| Pulsante | Funzione |
|----------|----------|
| ⬇ Download All | Scarica **tutti** gli sfondi dalla release |
| 🔄 Check Updates | Controlla e scarica solo i nuovi |
| ▶ Auto | Avvia/ferma il monitoraggio automatico |

### Informazioni in Tempo Reale

L'app mostra tre contatori:
- **Available**: Numero totale di sfondi nella release
- **Downloaded**: Quanti ne hai già scaricati
- **Missing**: Quanti ne mancano all'appello

## Struttura File

```
scripts/
├── wallpaper_downloader.py      # Applicazione principale
├── run-wallpaper-downloader.sh  # Script launcher
└── WALLPAPER_DOWNLOADER.md     # Questo file
```

## Come Funziona

1. L'app scarica il **manifest** da `https://wafy80.github.io/img/releases-manifest.json`
2. Il manifest contiene la lista di tutti gli sfondi disponibili nella release
3. Per ogni sfondo, costruisce l'URL di download dalla release GitHub
4. Gli sfondi già presenti nella cartella locale vengono saltati
5. Se l'auto-update è attivo, ricarica il manifest periodicamente per cercare nuovi sfondi
6. Il progetto viene aggiornato quotidianamente dalla CI/CD con nuovi sfondi

## Sorgente Dati

- **Manifest**: `https://wafy80.github.io/img/releases-manifest.json`
- **Release GitHub**: `wallpapers-archive`
- **URL Base Download**: `https://github.com/wafy80/wafy80.github.io/releases/download/wallpapers-archive`
- **Galleria Online**: `https://wafy80.github.io/img/`

## Impostazioni

Le impostazioni vengono salvate automaticamente in `~/.bing_wallpaper_downloader/settings.ini`

**Opzioni configurabili:**
- `download_dir`: Dove salvare gli sfondi (default: `~/BingWallpapers`)
- `update_interval`: Minuti tra un controllo e l'altro (default: `60`)
- `auto_start`: Avvia auto-update all'apertura (default: `false`)

## Uso Avanzato

### Modalità solo riga di comando

Per sistemi headless, puoi usare la classe `WallpaperDownloader` direttamente:

```python
from wallpaper_downloader import WallpaperDownloader

downloader = WallpaperDownloader("/path/to/folder")

# Scarica tutti
downloaded, skipped, errors = downloader.download_all(
    progress_callback=lambda curr, tot, name, status: print(f"{curr}/{tot}: {name}")
)

# Oppure scarica uno specifico
filepath, status = downloader.download_image("bing-20260407.jpg")
print(f"Scaricato: {filepath} ({status})")
```

### Esempio: Script per cron (Linux)

```python
#!/usr/bin/env python3
from wallpaper_downloader import WallpaperDownloader

dl = WallpaperDownloader("/home/user/Wallpapers")
dl._load_manifest()
available = dl.get_available_wallpapers()
local = {f.name for f in Path("/home/user/Wallpapers").glob("bing-*.jpg")}
missing = [f for f in available if f not in local]

for f in missing:
    dl.download_image(f)
```

## Risoluzione Problemi

**D: L'app non parte / Python non trovato**
- Installa Python 3.6+ da [python.org](https://www.python.org/downloads/)

**D: Nessun sfondo viene scaricato**
- Controlla la connessione internet
- Verifica il manifest: `https://wafy80.github.io/img/releases-manifest.json`
- Controlla i messaggi di errore nel log

**D: Dove sono salvati gli sfondi?**
- Posizione default: `~/BingWallpapers` (o `C:\Users\Tu\BingWallpapers` su Windows)
- Clicca "Open Folder" nell'app per aprirla

**D: Come si aggiorna la release?**
- La CI/CD del progetto (`daily-wp.yml`) aggiunge automaticamente nuovi sfondi ogni giorno alle 06:00 UTC

## Script Correlati

Questa app complementa gli script esistenti nel repository:
- `download-today.sh` - Scarica il sfondo giornaliero da Bing API
- `sync-archive.sh` - Sincronizza dall'archivio storico
- `upload-to-releases.sh` - Carica gli sfondi sulla release GitHub (usato dalla CI)

## Licenza

MIT License
