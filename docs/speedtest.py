#!/usr/bin/env python3
import sys
import subprocess
import os
import time
import random

# --- 1. AUTO-INSTALLAZIONE DIPENDENZE ---
def ensure_httpx():
    try:
        import httpx
    except ImportError:
        print("📦 Dipendenza 'httpx' mancante. Installazione in corso...")
        try:
            # Tenta installazione user (non richiede root)
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "httpx", 
                "--user", "--break-system-packages", "-q"
            ])
            print("✅ Installazione completata.")
            # Aggiungi il path user se necessario
            import site
            sys.path.append(site.getusersitepackages())
        except subprocess.CalledProcessError:
            print("❌ Errore: Impossibile installare 'httpx'.")
            print("   Installa manualmente: sudo apt install python3-httpx")
            sys.exit(1)

ensure_httpx()
import httpx # Ora è sicuro importarlo

# --- 2. CONFIGURAZIONE ---
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0'
}

def run_test(direction, size_mb, iterations=3):
    """Esegue test multipli e calcola la media"""
    print(f"\n{direction} ({size_mb} MB x {iterations})...")
    results = []
    
    # Generazione payload istantanea (nativa C) per l'upload
    payload = os.urandom(size_mb * 1_000_000) if "Upload" in direction else None
    
    for i in range(iterations):
        print(f"   Test {i+1}/{iterations}...", end=' ', flush=True)
        
        if "Download" in direction:
            cache_buster = random.randint(1000, 9999)
            url = f"https://speed.cloudflare.com/__down?bytes={size_mb * 1_000_000}&cache={cache_buster}"
            try:
                with httpx.Client(timeout=60.0, headers=BROWSER_HEADERS, follow_redirects=True) as client:
                    start = time.time()
                    with client.stream("GET", url) as r:
                        r.raise_for_status()
                        for chunk in r.iter_bytes(): pass
                    mbps = ((size_mb * 1_000_000 * 8) / ((time.time() - start) * 1_000_000))
            except Exception as e: mbps = 0
        else:
            url = "https://speed.cloudflare.com/__up"
            try:
                with httpx.Client(timeout=60.0, headers={**BROWSER_HEADERS, 'Content-Type': 'application/octet-stream'}) as client:
                    start = time.time()
                    client.post(url, content=payload).raise_for_status()
                    mbps = ((len(payload) * 8) / ((time.time() - start) * 1_000_000))
            except Exception as e: mbps = 0

        if mbps > 0:
            results.append(mbps)
            print(f"✅ {mbps:.1f} Mbps")
        else:
            print("❌ Fallito")
        time.sleep(1) # Pausa anti-ban

    if results:
        avg = sum(results) / len(results)
        print(f"   📊 Media: {avg:.2f} Mbps")
        return avg
    return 0

# --- 3. ESECUZIONE ---
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Cloudflare Speedtest (Universale)")
    print("=" * 50)
    down = run_test("⬇️  Download", 50, 3)
    up = run_test("⬆️  Upload", 20, 3)
    print("=" * 50)
    if down and up:
        print(f"🏁 Risultato: ↓ {down:.1f} Mbps | ↑ {up:.1f} Mbps")
