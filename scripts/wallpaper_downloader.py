#!/usr/bin/env python3
"""
Bing Wallpaper Downloader - Cross-platform desktop app
Downloads Bing wallpapers from GitHub Releases and updates them periodically.
Works on Windows, macOS, and Linux.
"""

import os
import sys
import json
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import configparser
import ssl


# Release configuration
RELEASE_MANIFEST_URL = "https://wafy80.github.io/img/releases-manifest.json"
RELEASE_BASE_URL = "https://github.com/wafy80/wafy80.github.io/releases/download/wallpapers-archive"


class WallpaperDownloader:
    """Core downloader - handles downloading from GitHub Releases."""

    def __init__(self, download_dir):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = None
        self._load_manifest()

    def _load_manifest(self):
        """Download and parse the releases manifest."""
        try:
            req = urllib.request.Request(
                RELEASE_MANIFEST_URL,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            context = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                data = json.loads(response.read().decode())
                self.manifest = data
        except Exception as e:
            raise RuntimeError(f"Failed to load manifest: {e}")

    def get_available_wallpapers(self):
        """Return list of available wallpapers from manifest."""
        if not self.manifest or "images" not in self.manifest:
            return []
        return sorted(self.manifest["images"].keys(), reverse=True)

    def get_download_url(self, filename):
        """Get the full download URL for a wallpaper."""
        if not self.manifest:
            return None
        base = self.manifest.get("base_url", RELEASE_BASE_URL)
        asset = self.manifest["images"].get(filename)
        if asset:
            return f"{base}/{asset}"
        return None

    def download_image(self, filename, callback=None):
        """Download a single wallpaper image."""
        filepath = self.download_dir / filename

        # Skip if already downloaded
        if filepath.exists():
            return filepath, "already_exists"

        url = self.get_download_url(filename)
        if not url:
            raise RuntimeError(f"No download URL for {filename}")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            context = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=120, context=context) as response:
                data = response.read()
                if len(data) > 51200:  # At least 50KB
                    with open(filepath, "wb") as f:
                        f.write(data)
                    return filepath, "downloaded"
                else:
                    raise RuntimeError(f"File too small: {filename}")
        except Exception as e:
            raise RuntimeError(f"Failed to download {filename}: {e}")

    def download_all(self, progress_callback=None):
        """Download all wallpapers from release."""
        wallpapers = self.get_available_wallpapers()
        if not wallpapers:
            raise RuntimeError("No wallpapers found in manifest")

        total = len(wallpapers)
        downloaded = 0
        skipped = 0
        errors = 0

        for i, filename in enumerate(wallpapers):
            try:
                filepath, status = self.download_image(filename)
                if status == "already_exists":
                    skipped += 1
                else:
                    downloaded += 1
                if progress_callback:
                    progress_callback(i + 1, total, filename, status)
            except Exception as e:
                errors += 1
                if progress_callback:
                    progress_callback(i + 1, total, filename, f"error: {e}")

        return downloaded, skipped, errors


class Settings:
    """Manage app settings."""

    def __init__(self):
        self.config_dir = Path.home() / ".bing_wallpaper_downloader"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.ini"
        self.settings = self._load()

    def _load(self):
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file, encoding="utf-8")
        return config

    def _save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.settings.write(f)

    def get(self, section, key, fallback=None):
        try:
            return self.settings.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def set(self, section, key, value):
        if not self.settings.has_section(section):
            self.settings.add_section(section)
        self.settings.set(section, key, value)
        self._save()

    @property
    def download_dir(self):
        return self.get("general", "download_dir", str(Path.home() / "BingWallpapers"))

    @download_dir.setter
    def download_dir(self, value):
        self.set("general", "download_dir", value)

    @property
    def update_interval(self):
        try:
            return int(self.get("general", "update_interval", "60"))
        except ValueError:
            return 60

    @update_interval.setter
    def update_interval(self, value):
        self.set("general", "update_interval", str(value))

    @property
    def auto_start(self):
        return self.get("general", "auto_start", "false") == "true"

    @auto_start.setter
    def auto_start(self, value):
        self.set("general", "auto_start", str(value).lower())


class App:
    """GUI Application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bing Wallpaper Downloader - GitHub Releases")
        self.root.geometry("700x600")
        self.root.minsize(550, 450)

        self.settings = Settings()
        self.downloader = None
        self.is_running = False
        self.update_thread = None
        self.is_downloading_all = False

        self._build_ui()
        self._load_settings()
        self._center_window()

    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the user interface."""
        # Main frame with padding
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Settings Section ---
        settings_frame = ttk.LabelFrame(main, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Download directory
        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dir_frame, text="Download folder:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=40)
        self.dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Browse", command=self._browse_dir).pack(side=tk.LEFT, padx=(5, 0))

        # Update interval
        interval_frame = ttk.Frame(settings_frame)
        interval_frame.pack(fill=tk.X)

        ttk.Label(interval_frame, text="Check for updates (minutes):").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="60")
        self.interval_spin = ttk.Spinbox(interval_frame, from_=5, to=1440, textvariable=self.interval_var, width=10)
        self.interval_spin.pack(side=tk.LEFT, padx=5)

        # --- Control Section ---
        control_frame = ttk.Frame(main)
        control_frame.pack(fill=tk.X, pady=10)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT)

        self.download_all_btn = ttk.Button(btn_frame, text="⬇ Download All", command=self._download_all)
        self.download_all_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.check_updates_btn = ttk.Button(btn_frame, text="🔄 Check Updates", command=self._check_updates)
        self.check_updates_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.auto_btn = ttk.Button(btn_frame, text="▶ Auto", command=self._toggle_auto_update)
        self.auto_btn.pack(side=tk.LEFT)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        # --- Info Section ---
        info_frame = ttk.Frame(main)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.available_var = tk.StringVar(value="Available: 0")
        ttk.Label(info_frame, textvariable=self.available_var, foreground="gray").pack(side=tk.LEFT)

        self.downloaded_var = tk.StringVar(value="Downloaded: 0")
        ttk.Label(info_frame, textvariable=self.downloaded_var, foreground="gray").pack(side=tk.LEFT, padx=(20, 0))

        self.missing_var = tk.StringVar(value="Missing: 0")
        ttk.Label(info_frame, textvariable=self.missing_var, foreground="gray").pack(side=tk.LEFT, padx=(20, 0))

        # --- Log Section ---
        log_frame = ttk.LabelFrame(main, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Footer ---
        footer = ttk.Frame(main)
        footer.pack(fill=tk.X)

        ttk.Button(footer, text="Open Folder", command=self._open_folder).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(footer, text="Save Settings", command=self._save_settings).pack(side=tk.RIGHT)
        ttk.Button(footer, text="View Gallery", command=self._open_gallery).pack(side=tk.RIGHT, padx=(5, 0))

    def _load_settings(self):
        """Load settings into UI."""
        self.dir_var.set(self.settings.download_dir)
        self.interval_var.set(str(self.settings.update_interval))

    def _save_settings(self):
        """Save settings from UI."""
        self.settings.download_dir = self.dir_var.get()
        self.settings.update_interval = int(self.interval_var.get())
        self._init_downloader()
        self._log("Settings saved")
        self._update_counts()

    def _browse_dir(self):
        """Open directory browser."""
        dir_path = filedialog.askdirectory(initialdir=self.dir_var.get())
        if dir_path:
            self.dir_var.set(dir_path)

    def _init_downloader(self):
        """Initialize the downloader with current settings."""
        download_dir = self.dir_var.get()
        self.downloader = WallpaperDownloader(download_dir)

    def _log(self, message):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _update_counts(self):
        """Update wallpaper counts."""
        if not self.downloader:
            self._init_downloader()

        try:
            available = self.downloader.get_available_wallpapers()
            total_available = len(available)
            self.available_var.set(f"Available: {total_available}")

            if os.path.exists(self.dir_var.get()):
                downloaded = len(list(Path(self.dir_var.get()).glob("bing-*.jpg")))
                self.downloaded_var.set(f"Downloaded: {downloaded}")

                available_set = set(available)
                local_files = {f.name for f in Path(self.dir_var.get()).glob("bing-*.jpg")}
                missing = len(available_set - local_files)
                self.missing_var.set(f"Missing: {missing}")
        except Exception as e:
            self._log(f"Error updating counts: {e}")

    def _toggle_auto_update(self):
        """Start/stop auto-update."""
        if not self.is_running:
            self._start_auto_update()
        else:
            self._stop_auto_update()

    def _start_auto_update(self):
        """Start automatic update loop."""
        self._save_settings()
        self.is_running = True
        self.auto_btn.config(text="⏹ Stop")
        self.status_var.set("Monitoring")
        self._log("Auto-update started")
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _stop_auto_update(self):
        """Stop automatic update."""
        self.is_running = False
        self.auto_btn.config(text="▶ Auto")
        self.status_var.set("Stopped")
        self._log("Auto-update stopped")

    def _update_loop(self):
        """Background loop for periodic updates."""
        interval_minutes = int(self.interval_var.get())
        interval_seconds = interval_minutes * 60

        while self.is_running:
            try:
                self.root.after(0, self._check_new_wallpapers)
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error: {e}"))

            # Sleep in small increments to allow stopping
            for _ in range(interval_seconds):
                if not self.is_running:
                    break
                time.sleep(1)

    def _check_new_wallpapers(self):
        """Check and download new wallpapers."""
        if not self.downloader:
            self._init_downloader()

        self.status_var.set("Checking...")
        try:
            # Reload manifest
            self.downloader._load_manifest()
            available = self.downloader.get_available_wallpapers()

            local_files = {f.name for f in Path(self.dir_var.get()).glob("bing-*.jpg")}
            missing = [f for f in available if f not in local_files]

            if not missing:
                self.status_var.set("Up to date")
                self._log("No new wallpapers found")
                return

            self._log(f"Found {len(missing)} new wallpaper(s), downloading...")

            for filename in missing:
                try:
                    filepath, status = self.downloader.download_image(filename)
                    if status == "already_exists":
                        self._log(f"  ⏭  {filename}")
                    else:
                        self._log(f"  ✅ {filename}")
                except Exception as e:
                    self._log(f"  ❌ {filename}: {e}")

            self.status_var.set("Updated!")
            self.root.after(0, self._update_counts)
        except Exception as e:
            self.status_var.set("Error")
            self._log(f"Check failed: {e}")

    def _download_all(self):
        """Download all wallpapers from release."""
        if self.is_downloading_all:
            return

        self._save_settings()
        if not self.downloader:
            self._init_downloader()

        self.is_downloading_all = True
        self.download_all_btn.config(state=tk.DISABLED)
        self.status_var.set("Downloading all...")
        self._log("Starting full download...")

        def progress(current, total, filename, status):
            pct = (current / total) * 100
            self.root.after(0, lambda: self.progress_var.set(pct))
            icon = "✅" if status == "downloaded" else "⏭" if status == "already_exists" else "❌"
            self.root.after(0, lambda: self._log(f"  {icon} {filename}"))

        def run():
            try:
                downloaded, skipped, errors = self.downloader.download_all(progress_callback=progress)
                self.root.after(0, lambda: self._log(f"Complete: {downloaded} downloaded, {skipped} skipped, {errors} errors"))
                self.root.after(0, lambda: self.status_var.set(f"Complete!"))
                self.root.after(0, self._update_counts)
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error: {e}"))
                self.root.after(0, lambda: self.status_var.set("Error"))
            finally:
                self.root.after(0, lambda: self.download_all_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: setattr(self, 'is_downloading_all', False))
                self.root.after(0, lambda: self.progress_var.set(0))

        threading.Thread(target=run, daemon=True).start()

    def _check_updates(self):
        """Manually check for new wallpapers."""
        self._save_settings()
        if not self.downloader:
            self._init_downloader()

        self.check_updates_btn.config(state=tk.DISABLED)
        self.status_var.set("Checking...")

        def run():
            try:
                self._check_new_wallpapers()
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error: {e}"))
                self.root.after(0, lambda: self.status_var.set("Error"))
            finally:
                self.root.after(0, lambda: self.check_updates_btn.config(state=tk.NORMAL))

        threading.Thread(target=run, daemon=True).start()

    def _open_folder(self):
        """Open download folder in file explorer."""
        download_dir = self.dir_var.get()
        if sys.platform == "win32":
            os.startfile(download_dir)
        elif sys.platform == "darwin":
            os.system(f"open '{download_dir}'")
        else:
            os.system(f"xdg-open '{download_dir}'")

    def _open_gallery(self):
        """Open online gallery in browser."""
        import webbrowser
        webbrowser.open("https://wafy80.github.io/img/")

    def run(self):
        """Start the application."""
        self._update_counts()
        self._log("Bing Wallpaper Downloader started")
        self._log(f"Platform: {sys.platform}")
        self._log(f"Source: GitHub Releases (wallpapers-archive)")

        # Auto-start if enabled
        if self.settings.auto_start:
            self.root.after(1000, self._start_auto_update)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        """Clean shutdown."""
        self._stop_auto_update()
        self._save_settings()
        self.root.destroy()


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
