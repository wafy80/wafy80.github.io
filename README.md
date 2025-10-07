# EPG IPTV Service

[![Update EPG](https://github.com/wafy80/wafy80.github.io/actions/workflows/daily-epg.yml/badge.svg)](https://github.com/wafy80/wafy80.github.io/actions/workflows/daily-epg.yml)

Questo repository fornisce un servizio automatizzato di Electronic Program Guide (EPG) per canali IPTV, con aggiornamenti programmati tre volte a settimana.

## Cosa Puoi Fare?

### 📺 Utilizzare il Servizio EPG

Puoi utilizzare direttamente i file EPG generati da questo repository per la tua configurazione IPTV:

#### File Disponibili

1. **EPG Light** (Consigliato)
   - URL: `https://wafy80.github.io/epg_light.xml`
   - Contiene solo i canali presenti nella playlist M3U
   - File più leggero e veloce da caricare
   - Aggiornato automaticamente 3 volte a settimana (lunedì, mercoledì, venerdì alle 9:00 UTC)

2. **M3U Playlist**
   - URL: `https://wafy80.github.io/m3u`
   - Playlist dei canali IPTV supportati
   - Include riferimenti all'EPG light

### 📋 Configurazione

#### In Applicazioni IPTV (es. VLC, Kodi, Perfect Player)

1. Aggiungi la playlist M3U: `https://wafy80.github.io/m3u`
2. L'EPG verrà caricato automaticamente dalla playlist

Oppure, configura manualmente:

1. URL Playlist: `https://wafy80.github.io/m3u`
2. URL EPG: `https://wafy80.github.io/epg_light.xml`

### 🔄 Aggiornamenti Automatici

Il repository utilizza GitHub Actions per aggiornare automaticamente l'EPG:
- **Frequenza**: Lunedì, Mercoledì, Venerdì alle 9:00 UTC
- **Workflow**: `.github/workflows/daily-epg.yml`
- Puoi anche attivare manualmente l'aggiornamento dalla scheda Actions su GitHub

## Funzionalità Tecniche

### Script Disponibili

1. **`process_epg_light.py`** (Utilizzato dal workflow)
   - Scarica l'EPG da `iptvx.one`
   - Filtra solo i canali presenti in `docs/m3u`
   - Translittera testo cirillico in caratteri ASCII
   - Genera `docs/epg_light.xml`

2. **`process_epg.py`** (Legacy)
   - Processa l'intero EPG senza filtraggio
   - Genera un file compresso `docs/epg.xml.gz`

### Caratteristiche

- ✅ Translitterazione automatica di testo cirillico
- ✅ Filtraggio canali basato sulla playlist M3U
- ✅ Supporto carattere speciale "⋗" per programmi live
- ✅ Compressione della cronologia Git per ottimizzare lo storage
- ✅ Aggiornamenti automatici programmati

## Sviluppo

### Prerequisiti

```bash
pip install requests unidecode
```

### Esecuzione Locale

```bash
# Genera EPG light (solo canali in m3u)
python scripts/process_epg_light.py

# Genera EPG completo (tutti i canali)
python scripts/process_epg.py
```

## Licenza

Questo è un progetto personale per uso privato. L'EPG source proviene da [iptvx.one](https://iptvx.one/).
