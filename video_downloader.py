#!/usr/bin/env python3
"""Video Downloader — a small macOS app wrapped around yt-dlp.

Downloads video or audio from YouTube, Vimeo, and the 1,000+ other sites
yt-dlp supports. Auto-names files from the video title (and re-names when
you paste a new URL), trims clips, and keeps everything h264/QuickTime-
friendly by default.
"""

import json
import os
import queue
import re
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# ---------------------------------------------------------------- palette
BG = "#0f1014"
CARD = "#17181d"
FIELD = "#1f2127"
BORDER = "#2a2d35"
TEXT = "#eceef4"
MUTED = "#7f8494"
LOG_FG = "#9aa0b0"
ACCENT = "#6a7cff"
ACCENT_HOVER = "#5468f0"
ACCENT_2 = "#a06bff"
DISABLED = "#3d4049"
OK = "#4cd07d"
ERR = "#ff6b5e"

FONT = "Helvetica Neue"
MONO = "Menlo"

# label -> (kind, extension)
FORMATS = {
    "Video · MP4 (recommended)": ("video", "mp4"),
    "Video · MOV": ("video", "mov"),
    "Video · MKV": ("video", "mkv"),
    "Video · WebM": ("video", "webm"),
    "Audio only · M4A": ("audio", "m4a"),
    "Audio only · MP3": ("audio", "mp3"),
}

SEARCH_DIRS = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]

# 52px PNG of the app icon, embedded so this file stays standalone
ICON_B64 = "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"
CONFIG_DIR = Path.home() / "Library" / "Application Support" / "Video Downloader"
CONFIG_FILE = CONFIG_DIR / "config.json"


def find_tool(name):
    """Find an executable in Homebrew/system locations or PATH."""
    for d in SEARCH_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return shutil.which(name)


def sanitize_filename(name, max_len=120):
    """Keep a human-readable but filesystem-safe name."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:max_len].strip(" .")


class RoundButton(tk.Canvas):
    """Flat or gradient pill button (native tk buttons ignore colors on macOS)."""

    def __init__(self, parent, text, command, width=180, height=44,
                 color=ACCENT, hover=ACCENT_HOVER, font_size=15, radius=None,
                 gradient=None, gradient_hover=None):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=parent["bg"])
        self.command = command
        self.enabled = True
        self.w, self.h = width, height
        self.r = radius if radius is not None else min(12, height // 3)
        self.color, self.hover_color = color, hover
        self.gradient = gradient          # (top_hex, bottom_hex) or None
        self.gradient_hover = gradient_hover or gradient
        self.lines = []                   # (item, t) rows of a gradient pill
        self.shapes = []                  # pieces of a solid pill
        if gradient:
            self._draw_gradient_pill(gradient)
        else:
            self._draw_solid_pill(color)
        self.label = self.create_text(width // 2, height // 2, text=text,
                                      fill="white", font=(FONT, font_size, "bold"))
        self.bind("<Button-1>", lambda e: self.enabled and self.command())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.config(cursor="pointinghand")

    @staticmethod
    def _lerp(c1, c2, t):
        a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02x%02x%02x" % tuple(
            round(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _draw_solid_pill(self, color):
        w, h, r = self.w, self.h, self.r
        for coords in [(r, 0, w - r, h), (0, r, w, h - r)]:
            self.shapes.append(self.create_rectangle(*coords, fill=color, outline=""))
        for cx, cy in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]:
            self.shapes.append(self.create_oval(cx - r, cy - r, cx + r, cy + r,
                                                fill=color, outline=""))

    def _draw_gradient_pill(self, colors):
        # smooth oval caps in the end colors, full-width gradient band between
        # (per-row insets at the corners alias badly on retina)
        w, h, r = self.w, self.h, self.r
        c1, c2 = colors
        for item in (self.create_oval(0, 0, 2 * r, 2 * r, fill=c1, outline=""),
                     self.create_oval(w - 2 * r, 0, w, 2 * r, fill=c1, outline=""),
                     self.create_rectangle(r, 0, w - r, r, fill=c1, outline="")):
            self.lines.append((item, 0.0))
        for item in (self.create_oval(0, h - 2 * r, 2 * r, h, fill=c2, outline=""),
                     self.create_oval(w - 2 * r, h - 2 * r, w, h, fill=c2, outline=""),
                     self.create_rectangle(r, h - r, w - r, h, fill=c2, outline="")):
            self.lines.append((item, 1.0))
        band = max(h - 2 * r - 1, 1)
        for y in range(r, h - r):
            t = (y - r) / band
            item = self.create_line(0, y, w, y, fill=self._lerp(c1, c2, t))
            self.lines.append((item, t))

    def _paint(self, colors=None, flat=None):
        if self.gradient:
            for item, t in self.lines:
                self.itemconfig(item, fill=flat or self._lerp(*colors, t))
        else:
            for s in self.shapes:
                self.itemconfig(s, fill=flat or colors)

    def _set_hover(self, on):
        if not self.enabled:
            return
        if self.gradient:
            self._paint(colors=self.gradient_hover if on else self.gradient)
        else:
            self._paint(colors=self.hover_color if on else self.color)

    def set_state(self, enabled, text=None, color=None):
        self.enabled = enabled
        if color:
            self.color = color
        if enabled:
            self._paint(colors=self.gradient if self.gradient else self.color)
        else:
            self._paint(flat=DISABLED)
        if text is not None:
            self.itemconfig(self.label, text=text)
        self.config(cursor="pointinghand" if enabled else "arrow")


class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        root.title("Video Downloader")
        root.geometry("780x740")
        root.minsize(680, 620)
        root.configure(bg=BG)
        try:  # dark title bar on macOS
            root.tk.call("wm", "attributes", root._w, "-appearance", "darkaqua")
        except tk.TclError:
            pass

        self.ytdlp_path = find_tool("yt-dlp")
        self.ffmpeg_path = find_tool("ffmpeg")

        # make sure yt-dlp can find ffmpeg when launched from an .app bundle
        os.environ["PATH"] = ":".join(SEARCH_DIRS) + ":" + os.environ.get("PATH", "")

        cfg = self._load_config()
        self.url_var = tk.StringVar()
        self.filename_var = tk.StringVar()
        self.format_var = tk.StringVar(value=cfg.get("format", list(FORMATS)[0]))
        self.clip_var = tk.BooleanVar(value=False)
        self.start_var = tk.StringVar(value="00:00")
        self.end_var = tk.StringVar(value="00:10")
        self.save_var = tk.StringVar(value=cfg.get("save_to", str(Path.home() / "Downloads")))
        self.cookies_var = tk.StringVar(value=cfg.get("cookies", "No cookies"))
        if self.format_var.get() not in FORMATS:
            self.format_var.set(list(FORMATS)[0])
        if not os.path.isdir(self.save_var.get()):
            self.save_var.set(str(Path.home() / "Downloads"))

        self.downloading = False
        self.cancelled = False
        self.process = None
        self.last_output_file = None

        # title auto-fetch state
        self._auto_title = None      # last name WE put in the field
        self._fetched_url = None     # url we last fetched a title for
        self._fetch_gen = 0          # ignore stale fetch results
        self._debounce_id = None

        # worker threads push UI callables here; the main thread drains it
        # (calling root.after from a thread is unsafe on newer Tk)
        self._ui_queue = queue.Queue()

        self._styles()
        self._build_ui()
        self.url_var.trace_add("write", self._on_url_changed)
        for var in (self.format_var, self.save_var, self.cookies_var):
            var.trace_add("write", lambda *_: self._save_config())
        self.root.after(50, self._drain_ui_queue)

        if not self.ytdlp_path:
            messagebox.showwarning(
                "yt-dlp not found",
                "yt-dlp is not installed.\n\nInstall it with:\n  brew install yt-dlp")
        elif not self.ffmpeg_path:
            messagebox.showwarning(
                "ffmpeg not found",
                "ffmpeg is needed to merge video and audio.\n\nInstall it with:\n  brew install ffmpeg")

    # -------------------------------------------------------------- config
    def _load_config(self):
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}

    def _save_config(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps({
                "format": self.format_var.get(),
                "save_to": self.save_var.get(),
                "cookies": self.cookies_var.get(),
            }))
        except Exception:
            pass

    # ------------------------------------------------------------- styling
    def _styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Dl.Horizontal.TProgressbar", troughcolor=FIELD,
                        background=ACCENT, bordercolor=BG,
                        lightcolor=ACCENT, darkcolor=ACCENT, thickness=5)
        style.configure("Dark.TCombobox", fieldbackground=FIELD, background=FIELD,
                        foreground=TEXT, arrowcolor=MUTED, bordercolor=BORDER,
                        lightcolor=FIELD, darkcolor=FIELD,
                        selectbackground=FIELD, selectforeground=TEXT)
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", FIELD)],
                  foreground=[("readonly", TEXT)])
        style.configure("Dark.TCheckbutton", background=CARD, foreground=TEXT,
                        indicatorcolor=FIELD, bordercolor=BORDER,
                        lightcolor=CARD, darkcolor=CARD)
        style.map("Dark.TCheckbutton",
                  indicatorcolor=[("selected", ACCENT)],
                  background=[("active", CARD)])
        self.root.option_add("*TCombobox*Listbox.background", CARD)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "white")

    def _entry(self, parent, var, **kw):
        return tk.Entry(parent, textvariable=var, bg=FIELD, fg=TEXT,
                        insertbackground=TEXT, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER,
                        highlightcolor=ACCENT, font=(FONT, 13),
                        readonlybackground=FIELD, disabledbackground=CARD, **kw)

    def _label(self, parent, text, size=12, color=MUTED, bold=False):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                        font=(FONT, size, "bold" if bold else "normal"))

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(22, 18))

        # header: glyph + name
        head = tk.Frame(outer, bg=BG)
        head.pack(fill="x", pady=(0, 18))
        self._icon_img = None
        if ICON_B64:
            try:
                self._icon_img = tk.PhotoImage(data=ICON_B64)
                tk.Label(head, image=self._icon_img, bg=BG, bd=0).pack(
                    side="left", padx=(0, 12))
            except tk.TclError:
                self._icon_img = None
        if self._icon_img is None:
            glyph = tk.Canvas(head, width=40, height=40, bg=BG, highlightthickness=0)
            glyph.pack(side="left", padx=(0, 12))
            self._draw_glyph(glyph, 40)
        titles = tk.Frame(head, bg=BG)
        titles.pack(side="left")
        self._label(titles, "Video Downloader", 21, TEXT, bold=True).pack(anchor="w")
        self._label(titles, "YouTube, Vimeo, and 1,000+ other sites · powered by yt-dlp",
                    11, MUTED).pack(anchor="w")

        # --- URL hero
        card = tk.Frame(outer, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 14))
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=18, pady=(16, 12))

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x")
        self.url_entry = self._entry(row, self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=9)
        RoundButton(row, "Paste", self._paste_url, width=80, height=38,
                    color=FIELD, hover=BORDER, font_size=12).pack(side="left", padx=(10, 0))

        self.title_status = self._label(inner, " ", 12, MUTED)
        self.title_status.pack(anchor="w", pady=(8, 0))

        # --- options card
        card = tk.Frame(outer, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=18, pady=16)
        inner.columnconfigure(1, weight=1)

        self._label(inner, "SAVE AS", 10, MUTED, bold=True).grid(
            row=0, column=0, sticky="w")
        self._entry(inner, self.filename_var).grid(
            row=1, column=0, columnspan=2, sticky="ew", ipady=8, pady=(6, 14))

        fmt_row = tk.Frame(inner, bg=CARD)
        fmt_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self._label(fmt_row, "Format", 12, TEXT).pack(side="left")
        ttk.Combobox(fmt_row, textvariable=self.format_var, values=list(FORMATS),
                     state="readonly", style="Dark.TCombobox", width=25,
                     font=(FONT, 12)).pack(side="left", padx=(12, 34))

        ttk.Checkbutton(fmt_row, text="  Clip a section", variable=self.clip_var,
                        command=self._toggle_clip,
                        style="Dark.TCheckbutton").pack(side="left")
        self.start_entry = self._entry(fmt_row, self.start_var, width=7, justify="center")
        self.end_entry = self._entry(fmt_row, self.end_var, width=7, justify="center")
        self.clip_dash = self._label(fmt_row, "–", 12, MUTED)
        self.start_entry.pack(side="left", padx=(16, 5), ipady=5)
        self.clip_dash.pack(side="left")
        self.end_entry.pack(side="left", padx=(5, 0), ipady=5)

        cookie_row = tk.Frame(inner, bg=CARD)
        cookie_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self._label(cookie_row, "Cookies", 12, TEXT).pack(side="left")
        ttk.Combobox(cookie_row, textvariable=self.cookies_var,
                     values=["No cookies", "Chrome", "Safari", "Firefox"],
                     state="readonly", style="Dark.TCombobox", width=11,
                     font=(FONT, 12)).pack(side="left", padx=(12, 12))
        self._label(cookie_row, "use your browser login for private or age-restricted videos",
                    11, MUTED).pack(side="left")

        save_row = tk.Frame(inner, bg=CARD)
        save_row.grid(row=4, column=0, columnspan=2, sticky="ew")
        self._label(save_row, "Save to", 12, TEXT).pack(side="left")
        self._entry(save_row, self.save_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(12, 10), ipady=7)
        RoundButton(save_row, "Browse…", self._browse, width=92, height=34,
                    color=FIELD, hover=BORDER, font_size=12).pack(side="left")

        # --- action row
        action = tk.Frame(outer, bg=BG)
        action.pack(fill="x", pady=(0, 14))
        self.download_btn = RoundButton(action, "Download", self._start_download,
                                        width=210, height=48, radius=14, font_size=16,
                                        gradient=(ACCENT, ACCENT_2),
                                        gradient_hover=("#5a6af0", "#8f5ae8"))
        self.download_btn.pack(side="left")
        self.cancel_btn = RoundButton(action, "Cancel", self._cancel, width=100,
                                      height=48, radius=14, color=FIELD,
                                      hover=ERR, font_size=13)
        self.reveal_btn = RoundButton(action, "Reveal in Finder", self._reveal,
                                      width=156, height=48, radius=14,
                                      color=FIELD, hover=BORDER, font_size=13)

        # --- progress row
        prog_row = tk.Frame(outer, bg=BG)
        prog_row.pack(fill="x", pady=(0, 12))
        self.progress = ttk.Progressbar(prog_row, style="Dl.Horizontal.TProgressbar",
                                        maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress_label = self._label(prog_row, "", 11, MUTED)
        self.progress_label.pack(side="right", padx=(12, 0))

        # --- log
        log_frame = tk.Frame(outer, bg=CARD, highlightbackground=BORDER,
                             highlightthickness=1)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, bg=CARD, fg=LOG_FG, insertbackground=TEXT,
                           relief="flat", font=(MONO, 11), wrap="word",
                           state="disabled", padx=14, pady=12,
                           highlightthickness=0, borderwidth=0)
        self.log.pack(fill="both", expand=True)  # scrolls with trackpad
        self.log.tag_configure("ok", foreground=OK)
        self.log.tag_configure("err", foreground=ERR)

        self._toggle_clip()

    def _draw_glyph(self, c, size):
        """App glyph: accent rounded square with a play/download mark."""
        r = size * 0.28
        w = size - 2
        # rounded-square plate
        for coords in [(r, 1, w - r + 1, w + 1), (1, r, w + 1, w - r + 1)]:
            c.create_rectangle(*coords, fill=ACCENT, outline="")
        for cx, cy in [(r, r), (w - r + 1, r), (r, w - r + 1), (w - r + 1, w - r + 1)]:
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=ACCENT, outline="")
        # downward play triangle over a landing bar, echoing the app icon
        m = size / 2
        c.create_polygon(m - 9, m - 8, m + 9, m - 8, m, m + 5,
                         fill="white", outline="")
        c.create_rectangle(m - 9, m + 9, m + 9, m + 12, fill="white", outline="")

    # ------------------------------------------------------------- helpers
    def _ui(self, fn, *args):
        """Schedule a UI update from any thread."""
        self._ui_queue.put((fn, args))

    def _drain_ui_queue(self):
        try:
            while True:
                fn, args = self._ui_queue.get_nowait()
                fn(*args)
        except queue.Empty:
            pass
        self.root.after(50, self._drain_ui_queue)

    def _paste_url(self):
        try:
            self.url_var.set(self.root.clipboard_get().strip())
        except tk.TclError:
            pass

    def _browse(self):
        folder = filedialog.askdirectory(title="Select download folder",
                                         initialdir=self.save_var.get())
        if folder:
            self.save_var.set(folder)

    def _toggle_clip(self):
        state = "normal" if self.clip_var.get() else "disabled"
        self.start_entry.configure(state=state)
        self.end_entry.configure(state=state)
        self.clip_dash.configure(fg=TEXT if self.clip_var.get() else DISABLED)

    def _log(self, msg, tag=None):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag or ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _reveal(self):
        if self.last_output_file and os.path.exists(self.last_output_file):
            subprocess.run(["open", "-R", self.last_output_file])

    # -------------------------------------------------- title auto-naming
    def _on_url_changed(self, *_):
        if self._debounce_id:
            self.root.after_cancel(self._debounce_id)
        self._debounce_id = self.root.after(800, self._maybe_fetch_title)

    def _maybe_fetch_title(self):
        self._debounce_id = None
        url = self.url_var.get().strip()
        if not re.match(r"^https?://\S+$", url) or url == self._fetched_url:
            return
        if not self.ytdlp_path:
            return
        self._fetched_url = url
        self._fetch_gen += 1
        gen = self._fetch_gen
        self.title_status.configure(text="Fetching video info…", fg=MUTED)
        threading.Thread(target=self._fetch_title_worker, args=(url, gen),
                         daemon=True).start()

    def _fetch_title_worker(self, url, gen):
        try:
            result = subprocess.run(
                [self.ytdlp_path, "--no-playlist", "--no-warnings", "--get-title", url],
                capture_output=True, text=True, timeout=30)
            title = result.stdout.strip().splitlines()[0] if result.returncode == 0 and result.stdout.strip() else None
        except Exception:
            title = None
        self._ui(self._apply_title, title, gen)

    def _apply_title(self, title, gen):
        if gen != self._fetch_gen:
            return  # a newer URL was pasted while this fetch was in flight
        current = self.filename_var.get().strip()
        if title:
            clean = sanitize_filename(title)
            # only overwrite the field if the user hasn't typed their own name
            if not current or current == self._auto_title:
                self.filename_var.set(clean)
            self._auto_title = clean
            self.title_status.configure(text=f"✓ {title}", fg=OK)
        else:
            # new source but no title: clear a stale auto-name, keep user text
            if current and current == self._auto_title:
                self.filename_var.set("")
            self._auto_title = None
            self.title_status.configure(
                text="Couldn't read the video title — the download may still work.", fg=MUTED)

    # ----------------------------------------------------------- download
    def _validate(self):
        url = self.url_var.get().strip()
        if not re.match(r"^https?://\S+$", url):
            messagebox.showerror("Invalid URL", "Paste a full video URL starting with http:// or https://")
            return None
        if not self.ytdlp_path:
            messagebox.showerror("yt-dlp missing", "Install yt-dlp first:\n  brew install yt-dlp")
            return None
        if not os.path.isdir(self.save_var.get()):
            messagebox.showerror("Bad folder", f"Save location does not exist:\n{self.save_var.get()}")
            return None
        if self.clip_var.get():
            for t in (self.start_var.get().strip(), self.end_var.get().strip()):
                if not re.match(r"^\d{1,2}(:\d{1,2}){1,2}$", t):
                    messagebox.showerror("Invalid time",
                                         f"'{t}' is not a valid time.\nUse MM:SS or HH:MM:SS.")
                    return None
        return url

    def _build_cmd(self, url):
        kind, ext = FORMATS[self.format_var.get()]
        save_path = self.save_var.get()
        filename = sanitize_filename(self.filename_var.get().strip())

        cmd = [self.ytdlp_path, "--no-playlist", "--newline", "--no-warnings",
               "--windows-filenames"]
        if self.cookies_var.get() != "No cookies":
            cmd += ["--cookies-from-browser", self.cookies_var.get().lower()]
        if kind == "video":
            if ext == "webm":
                cmd += ["-f", "bestvideo[ext=webm]+bestaudio[ext=webm]/bestvideo+bestaudio/best"]
            else:
                # h264 + m4a preferred for QuickTime/Resolve; fall back to best
                cmd += ["-f", "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"]
            cmd += ["--merge-output-format", ext, "--remux-video", ext]
        else:
            cmd += ["-f", "bestaudio/best", "-x", "--audio-format", ext]

        if self.clip_var.get():
            start = self.start_var.get().strip()
            end = self.end_var.get().strip()
            cmd += ["--download-sections", f"*{start}-{end}", "--force-keyframes-at-cuts"]

        if filename:
            base = os.path.join(save_path, filename)
            if os.path.exists(f"{base}.{ext}"):
                n = 1
                while os.path.exists(f"{base} ({n}).{ext}"):
                    n += 1
                base = f"{base} ({n})"
            cmd += ["-o", f"{base}.%(ext)s"]
        else:
            cmd += ["-o", os.path.join(save_path, "%(title)s.%(ext)s")]

        cmd.append(url)
        return cmd

    def _start_download(self):
        if self.downloading:
            return
        url = self._validate()
        if not url:
            return
        self.downloading = True
        self.cancelled = False
        self.last_output_file = None
        self.reveal_btn.pack_forget()
        self.cancel_btn.pack(side="left", padx=(12, 0))
        self.download_btn.set_state(False, "Downloading…")
        self.progress["value"] = 0
        self.progress_label.configure(text="")
        self._clear_log()
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def _cancel(self):
        if self.process:
            self.cancelled = True
            self.process.terminate()

    def _download_worker(self, url):
        try:
            cmd = self._build_cmd(url)
            self._ui(self._log, "$ " + " ".join(cmd) + "\n")
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT,
                                            universal_newlines=True, bufsize=1)
            dest_re = re.compile(
                r'Merging formats into "(.+)"|\[download\] Destination: (.+)'
                r'|\[ExtractAudio\] Destination: (.+)')
            stat_re = re.compile(
                r"\[download\]\s+([\d.]+)%(?:.*?at\s+(\S+))?(?:.*?ETA\s+(\S+))?")
            for line in self.process.stdout:
                line = line.rstrip()
                m = stat_re.search(line)
                if m:
                    pct = float(m.group(1))
                    parts = [f"{pct:.0f}%"]
                    if m.group(2) and "Unknown" not in m.group(2):
                        parts.append(m.group(2))
                    if m.group(3) and "Unknown" not in m.group(3):
                        parts.append(f"ETA {m.group(3)}")
                    self._ui(self.progress.configure, {"value": pct})
                    self._ui(self.progress_label.configure,
                             {"text": " · ".join(parts)})
                d = dest_re.search(line)
                if d:
                    self.last_output_file = next(g for g in d.groups() if g)
                self._ui(self._log, line)
            self.process.wait()
            code = self.process.returncode

            if self.cancelled:
                self._ui(self._finish, None, "Cancelled.")
            elif code == 0:
                self._ui(self.progress.configure, {"value": 100})
                self._ui(self._finish, True,
                         f"Saved: {self.last_output_file or self.save_var.get()}")
            else:
                self._ui(self._finish, False,
                         f"Download failed (exit code {code}). See log above.")
        except Exception as e:
            self._ui(self._finish, False, f"Error: {e}")
        finally:
            self.process = None
            self.downloading = False

    def _finish(self, success, msg):
        self.download_btn.set_state(True, "Download")
        self.cancel_btn.pack_forget()
        if success:
            self.progress_label.configure(text="done")
            self._log("\n✓ " + msg, "ok")
            if self.last_output_file and os.path.exists(self.last_output_file):
                self.reveal_btn.pack(side="left", padx=(12, 0))
        elif success is False:
            self.progress_label.configure(text="")
            self._log("\n✗ " + msg, "err")
        else:
            self.progress_label.configure(text="")
            self._log("\n" + msg)


def main():
    root = tk.Tk()
    VideoDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
