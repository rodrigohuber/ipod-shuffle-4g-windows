"""Shuffle Manager: a small window for the iPod shuffle 4th generation.

Wraps ipod_shuffle_4g.py (the database builder) and adds a song list with
titles, drag-and-drop adding, copying songs to the PC, deleting, backing
music off with readable names, and a free-space readout.
"""
import csv
import os
import queue
import re
import runpy
import shutil
import string
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import mutagen
except ImportError:
    mutagen = None

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    BaseTk = TkinterDnD.Tk
except Exception:  # drag and drop is optional; everything else works without it
    DND_FILES, BaseTk = None, tk.Tk

APP = "Shuffle Manager"
PLAYABLE = (".mp3", ".m4a", ".m4b", ".wav", ".aa")  # what the database builder indexes
RESERVE = 16 * 2**20  # keep 16 MB free for the database and file-system overhead
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(HERE, "ipod_shuffle_4g.py")
COLUMNS = (("title", "Title", 230), ("artist", "Artist", 150), ("album", "Album", 150),
           ("length", "Length", 55), ("file", "File on iPod", 200))


def run_tool_mode():
    """`shuffle_manager --run-tool <args>`: run the database builder in this process."""
    sys.argv = [TOOL] + sys.argv[2:]
    os.chdir(os.path.expanduser("~"))
    runpy.run_path(TOOL, run_name="__main__")


def find_ipods():
    drives = []
    for letter in string.ascii_uppercase:
        root = letter + ":" + os.sep
        if os.path.isdir(os.path.join(root, "iPod_Control")):
            drives.append(root)
    return drives


def songs_on(d, exts=PLAYABLE):
    """Every song file on the drive, as the database builder sees them: anywhere except the
    voice prompts in iPod_Control/Speakable and hidden (dot) files and folders."""
    speak = os.path.normcase(os.path.join(d, "iPod_Control", "Speakable"))
    found = []
    for r, dirs, fs in os.walk(d):
        dirs[:] = sorted(x for x in dirs if not x.startswith(".")
                         and os.path.normcase(os.path.join(r, x)) != speak
                         and x != "System Volume Information")
        found += [os.path.join(r, f) for f in sorted(fs) if not f.startswith(".") and f.lower().endswith(exts)]
    return found


def fmt_mb(n):
    return f"{n / 2**20:,.0f} MB"


def clean_name(s, fallback):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (s or "").strip()).rstrip(". ")
    return s[:80] or fallback


def read_tag(f, *keys):
    for k in keys:
        if f is not None and f.tags is not None and k in f.tags:
            v = f.tags[k]
            v = v[0] if isinstance(v, list) else v
            return str(v.text[0] if hasattr(v, "text") else v)
    return ""


def song_info(p):
    """Title, artist, album and length of one file; the title falls back to the file name."""
    try:
        f = mutagen.File(p) if mutagen else None
    except Exception:
        f = None
    secs = int(f.info.length) if f is not None and getattr(f, "info", None) else 0
    return {"path": p,
            "title": read_tag(f, "TIT2", "\xa9nam") or os.path.splitext(os.path.basename(p))[0],
            "artist": read_tag(f, "TPE1", "\xa9ART", "TPE2", "aART"),
            "album": read_tag(f, "TALB", "\xa9alb"),
            "secs": secs,
            "length": f"{secs // 60}:{secs % 60:02d}" if secs else ""}


def unique_path(path):
    base, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(path):
        path = f"{base} ({n}){ext}"
        n += 1
    return path


class App(BaseTk):
    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("900x680")
        self.minsize(720, 560)
        self.log_q = queue.Queue()
        self.busy = False
        self.pending = []      # files/folders queued to add
        self.songs = []        # song_info dicts for the current drive
        self.tag_cache = {}    # (path, size, mtime) -> song_info, so refreshes are fast
        self.sort_key, self.sort_rev = "artist", False
        self.action_buttons = []

        pad = {"padx": 8, "pady": 4}

        # --- device row
        dev = ttk.LabelFrame(self, text="iPod shuffle")
        dev.pack(fill="x", **pad)
        ttk.Label(dev, text="Drive:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.drive = tk.StringVar()
        self.drive_box = ttk.Combobox(dev, textvariable=self.drive, width=8, state="readonly")
        self.drive_box.grid(row=0, column=1, sticky="w")
        self.drive_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_all())
        ttk.Button(dev, text="Refresh", command=self.refresh_drives).grid(row=0, column=2, padx=6)
        ttk.Button(dev, text="Open in Explorer", command=self.open_drive).grid(row=0, column=3)
        self.space_lbl = ttk.Label(dev, text="")
        self.space_lbl.grid(row=0, column=4, sticky="w", padx=10)
        self.space_bar = ttk.Progressbar(dev, length=200, maximum=100)
        self.space_bar.grid(row=1, column=0, columnspan=5, sticky="ew", padx=6, pady=(0, 6))
        dev.columnconfigure(4, weight=1)

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, **pad)
        self.build_songs_tab(tabs)
        self.build_add_tab(tabs)
        self.build_backup_tab(tabs)

        # --- log
        lg = ttk.LabelFrame(self, text="Log")
        lg.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(lg, mode="determinate")
        self.progress.pack(fill="x", padx=6, pady=(4, 0))
        self.log = tk.Text(lg, height=7, wrap="word", state="disabled", font=("Consolas", 9))
        sb = ttk.Scrollbar(lg, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=4)
        self.log.pack(fill="both", expand=True, padx=(6, 0), pady=4)
        self.status = ttk.Label(self, text="", anchor="w")
        self.status.pack(fill="x", padx=10, pady=(0, 6))

        if DND_FILES:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self.on_drop)

        self.after(100, self.drain_log)
        self.refresh_drives()

    # ---------- layout
    def build_songs_tab(self, tabs):
        tab = ttk.Frame(tabs)
        tabs.add(tab, text="Songs on iPod")
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Search:").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *a: self.fill_tree())
        ttk.Entry(top, textvariable=self.search, width=30).pack(side="left", padx=4)
        self.count_lbl = ttk.Label(top, text="")
        self.count_lbl.pack(side="left", padx=10)
        hint = "Drag songs or folders from Explorer onto this window to add them." if DND_FILES \
            else "Use the 'Add music' tab to add songs."
        ttk.Label(top, text=hint, foreground="#555").pack(side="right")

        mid = ttk.Frame(tab)
        mid.pack(fill="both", expand=True, padx=6)
        self.tree = ttk.Treeview(mid, columns=[c[0] for c in COLUMNS], show="headings", selectmode="extended")
        for key, label, width in COLUMNS:
            self.tree.heading(key, text=label, command=lambda k=key: self.sort_by(k))
            self.tree.column(key, width=width, anchor="w", stretch=key != "length")
        ysb = ttk.Scrollbar(mid, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        ysb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.play_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<Control-a>", lambda e: self.tree.selection_set(self.tree.get_children()))

        bot = ttk.Frame(tab)
        bot.pack(fill="x", padx=6, pady=6)
        b = ttk.Button(bot, text="Copy selected to PC...", command=self.copy_selected_to_pc)
        b.pack(side="left")
        self.action_buttons.append(b)
        b = ttk.Button(bot, text="Delete selected", command=self.delete_selected)
        b.pack(side="left", padx=6)
        self.action_buttons.append(b)
        ttk.Button(bot, text="Play", command=self.play_selected).pack(side="left")
        ttk.Button(bot, text="Reload list", command=self.refresh_all).pack(side="right")

    def build_add_tab(self, tabs):
        tab = ttk.Frame(tabs)
        tabs.add(tab, text="Add music & options")
        add = ttk.LabelFrame(tab, text="Add music")
        add.pack(fill="x", padx=6, pady=6)
        btns = ttk.Frame(add)
        btns.pack(fill="x", padx=6, pady=4)
        ttk.Button(btns, text="Add files...", command=self.add_files).pack(side="left")
        ttk.Button(btns, text="Add folder...", command=self.add_folder).pack(side="left", padx=6)
        ttk.Button(btns, text="Clear list", command=self.clear_pending).pack(side="left")
        ttk.Label(btns, text="Folder on iPod:").pack(side="left", padx=(16, 4))
        self.target = tk.StringVar(value="Added")
        ttk.Entry(btns, textvariable=self.target, width=22).pack(side="left")
        self.pending_lbl = ttk.Label(add, text="Nothing queued.")
        self.pending_lbl.pack(anchor="w", padx=6)
        row = ttk.Frame(add)
        row.pack(fill="x", padx=6, pady=4)
        self.copy_btn = ttk.Button(row, text="Copy to iPod", command=self.copy_to_ipod)
        self.copy_btn.pack(side="right")
        self.action_buttons.append(self.copy_btn)
        ttk.Label(row, text="Dragged-in songs go straight on; songs listed here go on when you press Copy.",
                  foreground="#555").pack(side="left")

        opt = ttk.LabelFrame(tab, text="Song list options (used every time the song list is rebuilt)")
        opt.pack(fill="x", padx=6, pady=6)
        self.pl_mode = tk.StringVar(value="none")
        r = ttk.Frame(opt)
        r.pack(fill="x", padx=6, pady=2)
        ttk.Label(r, text="Playlists:").pack(side="left")
        ttk.Radiobutton(r, text="None (all songs)", value="none", variable=self.pl_mode,
                        command=self.sync_options).pack(side="left", padx=4)
        ttk.Radiobutton(r, text="One per folder", value="dir", variable=self.pl_mode,
                        command=self.sync_options).pack(side="left", padx=4)
        ttk.Radiobutton(r, text="By tag:", value="id3", variable=self.pl_mode,
                        command=self.sync_options).pack(side="left", padx=4)
        self.id3_tpl = tk.StringVar(value="{artist}")
        self.id3_box = ttk.Combobox(r, textvariable=self.id3_tpl, width=20,
                                    values=["{artist}", "{album}", "{genre}", "{artist} - {album}"])
        self.id3_box.pack(side="left")
        r2 = ttk.Frame(opt)
        r2.pack(fill="x", padx=6, pady=2)
        ttk.Label(r2, text="Folder depth:").pack(side="left")
        self.depth = tk.StringVar(value="Unlimited")
        self.depth_box = ttk.Combobox(r2, textvariable=self.depth, width=10, state="readonly",
                                      values=["Unlimited", "1", "2", "3"])
        self.depth_box.pack(side="left", padx=4)
        ttk.Label(r2, text="Volume boost (0-99):").pack(side="left", padx=(16, 4))
        self.gain = tk.IntVar(value=0)
        ttk.Spinbox(r2, from_=0, to=99, textvariable=self.gain, width=5).pack(side="left")
        r3 = ttk.Frame(opt)
        r3.pack(fill="x", padx=6, pady=2)
        self.rename_u = tk.BooleanVar(value=True)
        ttk.Checkbutton(r3, text="Rename files with characters the iPod can't store",
                        variable=self.rename_u).pack(side="left")
        self.verbose = tk.BooleanVar(value=False)
        ttk.Checkbutton(r3, text="Detailed log", variable=self.verbose).pack(side="left", padx=12)
        self.rebuild_btn = ttk.Button(r3, text="Rebuild now", command=self.rebuild)
        self.rebuild_btn.pack(side="right")
        self.action_buttons.append(self.rebuild_btn)
        ttk.Label(opt, text="The song list is rebuilt automatically after adding or deleting songs here. "
                            "Press Rebuild now after changing files in Explorer.",
                  foreground="#555").pack(anchor="w", padx=6, pady=(0, 4))
        self.sync_options()

    def build_backup_tab(self, tabs):
        tab = ttk.Frame(tabs)
        tabs.add(tab, text="Back up")
        ttk.Label(tab, text="Copy every song off the iPod into Artist\\Album\\Title folders, "
                            "with a song list (song-list.csv).").pack(anchor="w", padx=10, pady=(12, 6))
        self.backup_btn = ttk.Button(tab, text="Back up to folder...", command=self.backup)
        self.backup_btn.pack(anchor="w", padx=10)
        self.action_buttons.append(self.backup_btn)

    def sync_options(self):
        mode = self.pl_mode.get()
        self.depth_box.configure(state="readonly" if mode == "dir" else "disabled")
        self.id3_box.configure(state="normal" if mode == "id3" else "disabled")

    # ---------- helpers
    def say(self, msg):
        self.log_q.put(("log", msg))

    def drain_log(self):
        try:
            while True:
                kind, val = self.log_q.get_nowait()
                if kind == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", val + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "progress":
                    self.progress.configure(value=val[0], maximum=max(val[1], 1))
                elif kind == "status":
                    self.status.configure(text=val)
                elif kind == "songs":
                    self.songs = val
                    self.fill_tree()
                    self.refresh_space()
                elif kind == "done":
                    self.set_busy(False)
                    self.refresh_all()
        except queue.Empty:
            pass
        self.after(100, self.drain_log)

    def set_busy(self, busy):
        self.busy = busy
        for w in self.action_buttons:
            w.configure(state="disabled" if busy else "normal")

    def root(self):
        d = self.drive.get()
        if not d or not os.path.isdir(os.path.join(d, "iPod_Control")):
            messagebox.showwarning(APP, "No iPod shuffle found. Plug it in and press Refresh.")
            return None
        return d

    def start(self, fn, *args):
        if self.busy:
            messagebox.showinfo(APP, "Wait for the current job to finish.")
            return False
        self.set_busy(True)

        def wrap():
            try:
                fn(*args)
            except Exception as e:  # show any failure in the log rather than dying silently
                self.say(f"ERROR: {e}")
                self.log_q.put(("status", f"Failed: {e}"))
            finally:
                self.log_q.put(("done", None))
        threading.Thread(target=wrap, daemon=True).start()
        return True

    # ---------- device and song list
    def refresh_drives(self):
        drives = find_ipods()
        self.drive_box.configure(values=drives)
        if drives and self.drive.get() not in drives:
            self.drive.set(drives[0])
        if not drives:
            self.drive.set("")
        self.refresh_all()

    def refresh_all(self):
        self.refresh_space()
        d = self.drive.get()
        if not d or not os.path.isdir(d):
            self.songs = []
            self.fill_tree()
            return
        threading.Thread(target=self.load_songs, args=(d,), daemon=True).start()

    def load_songs(self, d):
        files = songs_on(d)
        out = []
        for i, p in enumerate(files, 1):
            try:
                st = os.stat(p)
            except OSError:
                continue
            key = (p, st.st_size, st.st_mtime)
            if key not in self.tag_cache:
                self.tag_cache[key] = dict(song_info(p), size=st.st_size)
            out.append(self.tag_cache[key])
            if not self.busy and i % 25 == 0:
                self.log_q.put(("status", f"Reading song titles {i}/{len(files)}..."))
        if not self.busy:
            self.log_q.put(("status", f"{len(out)} songs on the iPod."))
        self.log_q.put(("songs", out))

    def refresh_space(self):
        d = self.drive.get()
        if not d or not os.path.isdir(d):
            self.space_lbl.configure(text="No iPod shuffle found. Plug it in and press Refresh.")
            self.space_bar.configure(value=0)
            return
        u = shutil.disk_usage(d)
        self.space_lbl.configure(text=f"{len(self.songs)} songs   |   {fmt_mb(u.free)} free of {fmt_mb(u.total)}")
        self.space_bar.configure(value=100 * u.used / u.total)

    def fill_tree(self):
        q = self.search.get().strip().casefold()
        d = self.drive.get()
        rows = [s for s in self.songs
                if not q or q in f"{s['title']} {s['artist']} {s['album']}".casefold()]
        key = self.sort_key
        rows.sort(key=lambda s: (s["secs"] if key == "length" else
                                 (s["artist"].casefold(), s["album"].casefold(), s["title"].casefold())
                                 if key == "artist" else str(s.get(key, "")).casefold()),
                  reverse=self.sort_rev)
        self.tree.delete(*self.tree.get_children())
        for s in rows:
            rel = os.path.relpath(s["path"], d) if d else s["path"]
            self.tree.insert("", "end", iid=s["path"],
                             values=(s["title"], s["artist"], s["album"], s["length"], rel))
        total = len(self.songs)
        self.count_lbl.configure(text=f"{len(rows)} of {total} songs" if q else f"{total} songs")

    def sort_by(self, key):
        self.sort_rev = not self.sort_rev if self.sort_key == key else False
        self.sort_key = key
        self.fill_tree()

    def selected_songs(self):
        return [p for p in self.tree.selection() if os.path.isfile(p)]

    def open_drive(self):
        if self.root():
            os.startfile(self.drive.get())

    def play_selected(self):
        sel = self.selected_songs()
        if sel:
            os.startfile(sel[0])

    # ---------- copy songs to the PC
    def copy_selected_to_pc(self):
        sel = self.selected_songs()
        if not sel:
            messagebox.showinfo(APP, "Select one or more songs first (Ctrl+A selects all).")
            return
        out = filedialog.askdirectory(title="Copy the selected songs to...")
        if out:
            self.start(self._copy_to_pc, sel, out)

    def _copy_to_pc(self, paths, out):
        info = {s["path"]: s for s in self.songs}
        need = sum(os.path.getsize(p) for p in paths)
        if shutil.disk_usage(out).free < need + RESERVE:
            raise RuntimeError(f"Not enough space: need {fmt_mb(need)} in {out}.")
        for i, p in enumerate(paths, 1):
            self.log_q.put(("progress", (i, len(paths))))
            self.log_q.put(("status", f"Copying to PC {i}/{len(paths)}"))
            s = info.get(p) or song_info(p)
            name = clean_name(f"{s['artist']} - {s['title']}" if s["artist"] else s["title"],
                              os.path.splitext(os.path.basename(p))[0])
            dest = unique_path(os.path.join(out, name + os.path.splitext(p)[1].lower()))
            shutil.copy2(p, dest)
            if os.path.getsize(dest) != os.path.getsize(p):
                raise IOError(f"copy of {p} came out the wrong size")
        self.say(f"Copied {len(paths)} songs to {out}")
        self.log_q.put(("status", "Copy to PC finished."))

    # ---------- delete
    def delete_selected(self):
        d = self.root()
        sel = self.selected_songs()
        if not d or not sel:
            return
        names = [self.tree.set(p, "title") for p in sel]
        preview = "\n".join(names[:10]) + (f"\n... and {len(names) - 10} more" if len(names) > 10 else "")
        if messagebox.askyesno(APP, f"Delete {len(sel)} songs from the iPod? This can't be undone.\n\n{preview}",
                               icon="warning"):
            self.start(self._delete, d, sel)

    def _delete(self, d, paths):
        for p in paths:
            os.remove(p)
        # tidy up folders the deletes left empty (never the iPod's own folders)
        keep = {os.path.normcase(os.path.join(d, "iPod_Control", x)) for x in ("", "Music")}
        for p in paths:
            folder = os.path.dirname(p)
            while (os.path.normcase(folder) not in keep and os.path.normcase(folder) != os.path.normcase(d)
                   and os.path.isdir(folder) and not os.listdir(folder)):
                os.rmdir(folder)
                folder = os.path.dirname(folder)
        self.say(f"Deleted {len(paths)} songs.")
        self._rebuild(d)

    # ---------- add music
    def add_files(self):
        files = filedialog.askopenfilenames(title="Choose songs",
                                            filetypes=[("Audio", "*.mp3 *.m4a *.m4b *.wav"), ("All files", "*.*")])
        self.pending += list(files)
        self.update_pending()

    def add_folder(self):
        d = filedialog.askdirectory(title="Choose a folder of songs")
        if d:
            self.pending.append(d)
            if self.target.get() in ("", "Added"):
                self.target.set(clean_name(os.path.basename(d), "Added")[:40])
            self.update_pending()

    def clear_pending(self):
        self.pending = []
        self.update_pending()

    @staticmethod
    def expand(items):
        """Files and folders, flattened to (path, size); unplayable files split out."""
        ok, bad = [], []
        for p in items:
            paths = [p] if os.path.isfile(p) else sorted(
                os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs)
            for f in paths:
                if os.path.basename(f).startswith("."):
                    continue
                (ok if f.lower().endswith(PLAYABLE) else bad).append(f)
        return [(f, os.path.getsize(f)) for f in ok], bad

    def update_pending(self):
        ok, bad = self.expand(self.pending)
        total = sum(s for _, s in ok)
        text = f"{len(ok)} songs queued ({fmt_mb(total)})" if ok else "Nothing queued."
        if bad:
            text += f"; {len(bad)} other files will be skipped (not a format the shuffle plays)"
        self.pending_lbl.configure(text=text)

    def on_drop(self, event):
        items = [p for p in self.tk.splitlist(event.data) if os.path.exists(p)]
        d = self.root()
        if not d or not items:
            return
        drive = os.path.normcase(os.path.splitdrive(d)[0])
        if any(os.path.normcase(os.path.splitdrive(p)[0]) == drive for p in items):
            messagebox.showinfo(APP, "Those files are already on the iPod.")
            return
        ok, bad = self.expand(items)
        if not ok:
            messagebox.showinfo(APP, "None of the dropped files are songs the shuffle can play (MP3, M4A, WAV).")
            return
        folder = clean_name(os.path.basename(items[0]), "Added") if len(items) == 1 and os.path.isdir(items[0]) \
            else clean_name(self.target.get(), "Added")
        self.start(self._copy, d, ok, bad, folder)

    def copy_to_ipod(self):
        d = self.root()
        if not d:
            return
        ok, bad = self.expand(self.pending)
        if not ok:
            messagebox.showinfo(APP, "Add some songs first.")
            return
        if self.start(self._copy, d, ok, bad, clean_name(self.target.get(), "Added")):
            self.pending = []
            self.update_pending()

    def _copy(self, d, songs, bad, folder):
        dst = os.path.join(d, "iPod_Control", "Music", folder)
        os.makedirs(dst, exist_ok=True)
        copied, nofit, same = 0, [], 0
        for i, (src, size) in enumerate(songs, 1):
            self.log_q.put(("progress", (i, len(songs))))
            self.log_q.put(("status", f"Copying {i}/{len(songs)}: {os.path.basename(src)}"))
            out = os.path.join(dst, os.path.basename(src))
            if os.path.exists(out) and os.path.getsize(out) == size:
                same += 1
                continue
            if shutil.disk_usage(d).free - size < RESERVE:
                nofit.append(src)  # keep going: a smaller song may still fit
                continue
            shutil.copy2(src, out)
            if os.path.getsize(out) != size:
                raise IOError(f"copy of {src} came out the wrong size")
            copied += 1
        self.say(f"Copied {copied} songs into {folder}." + (f" {same} were already there." if same else ""))
        if nofit:
            self.say(f"{len(nofit)} songs did not fit:")
            for f in nofit[:50]:
                self.say("   " + os.path.basename(f))
            if len(nofit) > 50:
                self.say(f"   ... and {len(nofit) - 50} more")
        if bad:
            self.say(f"Skipped {len(bad)} files the shuffle can't play (e.g. {os.path.basename(bad[0])}).")
        self._rebuild(d)

    # ---------- rebuild
    def tool_args(self, d):
        args = []
        mode = self.pl_mode.get()
        if mode == "dir":
            depth = self.depth.get()
            args += ["-d", "-1" if depth == "Unlimited" else depth]
        elif mode == "id3":
            if mutagen is None:
                raise RuntimeError("Playlists by tag need the mutagen library, which is missing.")
            args += ["-i", self.id3_tpl.get() or "{artist}"]
        if self.gain.get():
            args += ["-g", str(int(self.gain.get()))]
        if self.rename_u.get():
            args.append("-u")
        if self.verbose.get():
            args.append("-v")
        return args + [d]

    def rebuild(self):
        d = self.root()
        if d:
            self.start(self._rebuild, d)

    def _rebuild(self, d):
        args = self.tool_args(d)
        self.log_q.put(("status", "Rebuilding the song list..."))
        self.log_q.put(("progress", (0, 1)))
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--run-tool"] + args
        else:
            cmd = [sys.executable, os.path.abspath(__file__), "--run-tool"] + args
        self.say("> rebuild " + " ".join(args))
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                             cwd=os.path.expanduser("~"), encoding="utf-8", errors="replace",
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for line in p.stdout:
            self.say(line.rstrip())
        p.wait()
        self.log_q.put(("progress", (1, 1)))
        if p.returncode == 0:
            self.log_q.put(("status", "Song list rebuilt. Eject the iPod in Windows before unplugging it."))
        else:
            self.log_q.put(("status", f"Rebuild FAILED (exit code {p.returncode}); see the log."))
            raise RuntimeError(f"rebuild exited with code {p.returncode}")

    # ---------- backup
    def backup(self):
        d = self.root()
        if not d:
            return
        out = filedialog.askdirectory(title="Choose where to save the backup")
        if out:
            self.start(self._backup, d, out)

    def _backup(self, d, dst_root):
        songs = songs_on(d, PLAYABLE + (".m4p",))
        if not songs:
            raise RuntimeError("There are no songs on the iPod to back up.")
        need = sum(os.path.getsize(s) for s in songs)
        if shutil.disk_usage(dst_root).free < need + RESERVE:
            raise RuntimeError(f"Not enough space: need {fmt_mb(need)} in {dst_root}.")
        dst = os.path.join(dst_root, "iPod shuffle backup")
        n = 2
        while os.path.exists(dst):
            dst = os.path.join(dst_root, f"iPod shuffle backup ({n})")
            n += 1
        rows = []
        for i, p in enumerate(songs, 1):
            self.log_q.put(("progress", (i, len(songs))))
            self.log_q.put(("status", f"Backing up {i}/{len(songs)}"))
            s = song_info(p)
            ext = os.path.splitext(p)[1].lower()
            folder = os.path.join(dst, clean_name(s["artist"], "Unknown Artist"), clean_name(s["album"], "Unknown Album"))
            os.makedirs(folder, exist_ok=True)
            out = unique_path(os.path.join(folder, clean_name(s["title"], "Untitled") + ext))
            shutil.copy2(p, out)
            if os.path.getsize(out) != os.path.getsize(p):
                raise IOError(f"copy of {p} came out the wrong size")
            rows.append([s["artist"], s["album"], s["title"], s["length"],
                         os.path.relpath(out, dst), os.path.relpath(p, d)])
        rows.sort(key=lambda r: [x.lower() for x in r[:3]])
        with open(os.path.join(dst, "song-list.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Artist", "Album", "Title", "Length", "Backup file", "Original on iPod"])
            w.writerows(rows)
        self.say(f"Backed up {len(rows)} songs to {dst}")
        self.log_q.put(("status", "Backup finished."))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run-tool":
        run_tool_mode()
    else:
        try:  # sharp text on scaled displays (and correct window coordinates)
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        App().mainloop()
