# Shuffle Manager — User manual

This manual explains every part of the Shuffle Manager window: **what it does, why it matters, and
how to use it**. For installing or building the app, see the [README](../README.md).

**Contents**

1. [How the iPod shuffle stores music, and why that matters](#1-how-the-ipod-shuffle-stores-music-and-why-that-matters)
2. [First use: a safe start](#2-first-use-a-safe-start)
3. [The window at a glance](#3-the-window-at-a-glance)
4. [The iPod shuffle panel: drive, free space, Explorer](#4-the-ipod-shuffle-panel-drive-free-space-explorer)
5. [Tab "Songs on iPod": list, search, sort, play, copy, delete](#5-tab-songs-on-ipod)
6. [Adding music: drag and drop, or queue and copy](#6-adding-music)
7. [Song list options: playlists, volume boost, renaming, detailed log](#7-song-list-options)
8. [Rebuild now: when you need it](#8-rebuild-now-when-you-need-it)
9. [Tab "Back up"](#9-tab-back-up)
10. [The Log and the status line](#10-the-log-and-the-status-line)
11. [Unplugging the iPod safely](#11-unplugging-the-ipod-safely)
12. [Troubleshooting](#12-troubleshooting)
13. [Quick reference](#13-quick-reference)

---

## 1. How the iPod shuffle stores music, and why that matters

When you plug in an iPod shuffle (4th generation), Windows shows it as an ordinary USB drive, for
example `D:`. You can copy MP3 files onto it in File Explorer like onto any USB stick, **but the
iPod will not play them.**

The reason is that the shuffle **does not look at the files**. It only plays the songs listed in its
own database file, `iPod_Control\iTunes\iTunesSD`. iTunes normally writes that file. If you copy or
delete files without updating it, the iPod keeps playing from the old list: new songs are ignored,
and deleted songs leave holes.

Shuffle Manager solves this. **Every time you add or delete songs through the app, it rebuilds
`iTunesSD` automatically** from the audio files that are actually on the iPod. It uses the
open-source database builder from
[nims11/IPod-Shuffle-4g](https://github.com/nims11/IPod-Shuffle-4g), which is bundled inside the app.

Two consequences to keep in mind:

- **The database is rebuilt from the files.** Whatever playable file is on the iPod, in any folder,
  ends up in the database. To remove a song from the iPod, remove the file.
- **Files changed outside the app are not picked up by themselves.** If you copy or delete files in
  File Explorer, press **Rebuild now** afterwards (section 8).

---

## 2. First use: a safe start

Rebuilding the database **replaces** the one iTunes wrote. Your songs are not touched, but
iTunes-only information is lost: iTunes playlists, play counts and the like. Before the first
rebuild:

1. Plug in the iPod and open Shuffle Manager. Check that the iPod's drive letter appears at the top.
2. Open the **Back up** tab and press **Back up to folder…** (section 9). This copies every song to
   your PC with readable names.
3. **Optional but recommended:** in File Explorer, copy the folders `iPod_Control\iTunes` and
   `iPod_Control\Speakable` from the iPod to a safe place. Copying these two folders back to the
   iPod restores the original iTunes database and the built-in voice prompts exactly as they were.

After this, you can add, delete and rebuild freely.

---

## 3. The window at a glance

![Shuffle Manager window](screenshot.png)

From top to bottom:

| Area | What it is for |
|---|---|
| **iPod shuffle** panel | Choose the iPod, see how many songs it holds and how full it is, open it in Explorer |
| **Songs on iPod** tab | Everything on the iPod: search, sort, play, copy to the PC, delete |
| **Add music & options** tab | Queue songs to copy, and choose how the database is built |
| **Back up** tab | Copy all songs off the iPod into tidy folders |
| **Log** | Progress bar and a running record of everything the app did |
| **Status line** (bottom) | One-line summary of the current or last job |

**One job at a time.** While a job runs (copying, deleting, rebuilding, backing up), the buttons
that start other jobs are greyed out. They come back when the job ends. Browsing, searching and
sorting keep working meanwhile.

---

## 4. The iPod shuffle panel: drive, free space, Explorer

### Drive

**What it does:** lists every drive letter that contains an `iPod_Control` folder, which is how an
iPod shuffle is recognised. The first one found is selected automatically.

**Why it matters:** every action in the app works on the drive selected here. With two iPods
plugged in, you choose which one to manage.

**How to use it:** if the list is empty, the message *"No iPod shuffle found. Plug it in and press
Refresh."* appears. Plug the iPod in, wait until Windows shows it in File Explorer, then press
**Refresh**. To switch iPods, pick another letter; the song list reloads at once.

### Refresh

Scans the drive letters again, then reloads the song list and the free space. Use it after plugging
in or swapping an iPod.

### Open in Explorer

Opens the iPod's drive in File Explorer, for when you want to look at the files directly.

### Song count, free space and the bar

**What it shows:** for example `347 songs | 18 MB free of 1,924 MB`, and a bar showing how full the
iPod is.

**Why it matters:** a 2 GB shuffle fills quickly. The app also needs room for its own work: **it
always keeps 16 MB free** for the database and the file system, and it will not copy a song that
would eat into that reserve (section 6).

---

## 5. Tab "Songs on iPod"

### The song list

**What it shows:** every song the iPod will play, with **Title, Artist, Album, Length** and **File on
iPod** (where the file is). Titles, artists and albums come from the songs' own tags. A song without
a title tag is shown by its file name, and one without an artist or album leaves that column blank.

**Why it matters:** the iPod shuffle has no screen. This list is the only way to see what is on it.
It lists exactly what the database builder will index: songs in **any** folder of the iPod, except
the iPod's built-in voice prompts (`iPod_Control\Speakable`), hidden files and folders (names
starting with `.`), and Windows' own `System Volume Information` folder.

Formats listed: `.mp3`, `.m4a`, `.m4b`, `.wav` and `.aa` (Audible). Tags are read once and
remembered, so reloading a large iPod is quick.

### Search

Type in the **Search** box to filter the list as you type. It matches any part of the title,
artist or album, ignoring upper and lower case. The counter changes to *"12 of 347 songs"*. Clear
the box to see everything again.

### Sorting

Click a **column header** to sort by that column, and click it again to reverse the order.

- **Artist** (the default) sorts by artist, then album, then title, which groups albums together.
- **Length** sorts by real duration, not alphabetically.

### Selecting songs

- Click selects one song. **Ctrl+click** adds or removes songs, and **Shift+click** selects a range.
- **Ctrl+A** selects every song shown, so after a search it selects all the matches.

### Play (or double-click)

**What it does:** opens the selected song in your computer's default music player (with several
selected, the first one).

**Why it matters:** to check a song before deleting it or copying it, without hunting for its file.

### Copy selected to PC…

**What it does:** copies the selected songs from the iPod to a folder you choose. Each copy is named
**`Artist - Title`** (or just the title when there is no artist), with characters Windows does not
allow in file names replaced by `_`.

**Why it matters:** an iPod filled by iTunes stores songs under meaningless names such as
`F12\ABCD.mp3`. This gets songs back with names you can read.

**How to use it:** select songs, press the button and choose a folder. Notes:

- **Nothing is overwritten.** If a file with the same name exists, the new copy is called
  `… (2).mp3`, `… (3).mp3`, and so on.
- The app first checks that the folder's drive has enough space, and stops with a message if not.
- Every copy is checked for the right size. A mismatch stops the job with an error in the Log.

To copy **everything** at once with folders per artist and album, use the **Back up** tab instead.

### Delete selected (or the Delete key)

**What it does:** deletes the selected songs **from the iPod**, removes any folders left empty, and
then **rebuilds the database automatically**.

**Why it matters:** deleting files in Explorer leaves the database pointing at songs that no longer
exist. Doing it here keeps both in step. Empty folders are tidied up because the database builder
can stop with an error on an empty folder when folder playlists are used. The iPod's own
`iPod_Control` and `iPod_Control\Music` folders are never removed.

**How to use it:** select songs and press **Delete selected** or the **Delete** key. A confirmation
lists up to ten of the titles. **The deletion cannot be undone**, so copy anything you want to keep
first.

### Reload list

Reads the song list from the iPod again. Use it after changing files in File Explorer. Note that
this refreshes **the list in the window only**; it does not update the iPod's database. For that,
use **Rebuild now** (section 8).

---

## 6. Adding music

There are two ways to add songs. Both copy them into `iPod_Control\Music\<folder name>` on the iPod
and then **rebuild the database automatically**.

### Way 1: drag and drop (fastest)

**How to use it:** select songs and/or folders in File Explorer and drag them onto **any part of the
Shuffle Manager window**. Copying starts immediately.

- **Folders are copied with everything inside them**, including sub-folders, so you can drop a
  whole album or artist folder.
- **Which folder on the iPod?** If you drop **one folder**, the songs go into a folder with **the same
  name** on the iPod, so dropping `Abbey Road` gives `iPod_Control\Music\Abbey Road`. If you drop
  several items, or loose files, they go into the folder named in the **Folder on iPod** box of the
  **Add music & options** tab (default: `Added`).
- **Files that are already on the iPod** are refused, with the message *"Those files are already on
  the iPod."* This stops you from accidentally copying the iPod onto itself.

Drag and drop needs the `tkinterdnd2` component. It is always included in the `.exe`. When running
from source without it, the hint text says to use the **Add music** tab instead.

### Way 2: queue, then copy

Open the **Add music & options** tab. The **Add music** box works like a shopping basket.

| Control | What it does |
|---|---|
| **Add files…** | Pick one or more songs and add them to the queue |
| **Add folder…** | Add a whole folder, sub-folders included. If **Folder on iPod** still says `Added` (or is empty), it is set to the folder's name |
| **Clear list** | Empty the queue without copying anything |
| **Folder on iPod** | The folder inside `iPod_Control\Music` that the songs will go into |
| **Copy to iPod** | Copy everything in the queue, then rebuild |

Below the buttons, a summary such as *"58 songs queued (240 MB); 3 other files will be skipped (not a
format the shuffle plays)"* tells you **before copying** how much space you need and how many files
will be left out.

**Why queue instead of dragging:** to collect songs from several places, check the total size
against the free space, and choose the folder name before anything is copied.

### What happens during a copy (both ways)

- **Only playable formats are copied:** `.mp3`, `.m4a`, `.m4b`, `.wav`, `.aa`. Other files (cover
  images, `.flac`, `.webm`, playlists and so on) are skipped and counted in the Log. Hidden files
  (names starting with `.`) are ignored.
- **Songs already on the iPod are not copied again.** A file with the same name and size in the
  target folder is skipped (*"12 were already there."*). Re-dropping an album after a partial copy
  only adds what is missing.
- **Space is checked song by song.** A song that would leave less than **16 MB free** is skipped,
  but the copy **carries on**, because a smaller song may still fit. At the end, the Log lists the
  songs that did not fit (the first 50 by name).
- **Every copy is checked for the right size.** A mismatch stops the job with an error.
- **Then the database is rebuilt** using the options described in section 7.

Only **add** music through the app or via **Rebuild now**: a song copied in File Explorer is
invisible to the iPod until the database is rebuilt.

---

## 7. Song list options

The lower box of the **Add music & options** tab, *"Song list options (used every time the song list
is rebuilt)"*. These settings apply to **every** rebuild, whether it follows an add, a delete or
**Rebuild now**. They are not saved between sessions: they reset to the defaults when you reopen the
app.

### Playlists

The shuffle 4G can hold several playlists besides "all songs". You switch between them on the
iPod with its VoiceOver button (see Apple's user guide for the shuffle). This setting decides which
playlists the database contains.

| Choice | What you get | When to use it |
|---|---|---|
| **None (all songs)** (default) | Only the main list of all songs | You just shuffle everything |
| **One per folder** | One playlist for each folder inside `iPod_Control\Music`, and for its sub-folders down to the chosen **Folder depth** | Your music on the iPod is organised in folders (for example Artist\Album) |
| **By tag** | One playlist for each distinct value of a tag pattern | Your songs are well tagged, whatever the folders |

**Folder depth** (only for *One per folder*) limits how deep folder playlists go:
`Unlimited` (every folder level), `1` (top-level folders only, for example one per artist), `2`
(two levels, for example artist and album), `3`.

**Tag pattern** (only for *By tag*): pick from the list or type your own using `{artist}`,
`{album}` and `{genre}`:

- `{artist}` gives one playlist per artist.
- `{album}` gives one per album.
- `{genre}` gives one per genre.
- `{artist} - {album}` gives one per artist-and-album pair.

**Why it matters:** with folder or tag playlists, you can choose to listen only to one artist or one
album on the iPod instead of shuffling everything.

⚠️ **On an iPod that iTunes filled, use *By tag*, not *One per folder*.** iTunes stores songs in
folders `F00` to `F49` with scrambled names, so folder playlists would be called `F00`, `F01`, and
so on, and would mix unrelated songs.

Playlist files (`.m3u`, `.pls`) placed inside `iPod_Control\Music` are also read by the database
builder.

### Volume boost (0–99)

**What it does:** stores a volume gain for **all** songs in the database. `0` (default) means no
change.

**Why it matters:** some recordings are quiet, and the shuffle's maximum volume can be too low for
them. Values around 60 are already **very loud** even at the iPod's lowest volume setting, so raise
it in small steps. The audio files themselves are not modified.

### Rename files with characters the iPod can't store (on by default)

**What it does:** the shuffle's database can only store file names written in the **Latin-1**
character set (Western European letters). A file name with other characters, such as a curly
apostrophe `’`, an emoji, or Asian or Cyrillic letters, would break the rebuild or the song would not
play. With this option on, **only those file and folder names are renamed**, each to a short code
of 16 digits and letters, for example `3131373433316331.mp3`. Names that are fine stay as they are.

**Why it matters:** without it, one badly named file can make the whole rebuild fail.

**What you see after renaming:** the song list shows the **title tag**, so a tagged song still looks
normal. A song without a title tag will appear under its new code name. The original name is lost,
so if names matter to you, run a **Back up** first. The backup names files from their tags, not
from their file names.

### Detailed log

**What it does:** makes the database builder print every step of the rebuild in the Log.

**Why it matters:** only for troubleshooting, for example to see which file caused a failed
rebuild. Leave it off normally, because the Log gets long.

---

## 8. Rebuild now: when you need it

**What it does:** rebuilds the iPod's database from the files on it, with the current options.

**Why it matters:** the app rebuilds by itself after adding or deleting songs. You only need this
button when:

- you **copied or deleted files in File Explorer** (or with another program);
- you **changed the Playlists, Volume boost or Rename** options and want them applied now without
  adding or deleting anything;
- an earlier rebuild **failed** and you fixed the cause.

**How to use it:** press **Rebuild now** on the **Add music & options** tab. The Log shows the
command used (for example `> rebuild -i {artist} -u D:\`) and the builder's summary:

```
Writing database. This may take a while...
Database written successfully:
Tracks 347
Albums 41
Artists 44
Playlists 45
```

When it finishes, the status line says *"Song list rebuilt. Eject the iPod in Windows before
unplugging it."*

---

## 9. Tab "Back up"

**What it does:** copies **every song on the iPod** into a new folder on your PC, organised as

```
iPod shuffle backup\
    Artist\
        Album\
            Title.mp3
    song-list.csv
```

- Folder and file names come from the **tags**. Missing tags become `Unknown Artist`,
  `Unknown Album` or `Untitled`.
- If two songs would get the same name, the second becomes `Title (2).mp3`.
- Purchased iTunes songs (`.m4p`) are included in the backup, besides all the playable formats.
- If a folder called `iPod shuffle backup` already exists where you save, the new one is called
  `iPod shuffle backup (2)`, and so on. **An earlier backup is never overwritten.**
- **`song-list.csv`** lists every song (Artist, Album, Title, Length, the backup file, and where
  the original was on the iPod). It opens in Excel, sorted by artist, album and title.

**Why it matters:**

- **Safety:** do it before your first rebuild (section 2) and before big deletions.
- **Getting your music back:** an iPod filled by iTunes hides songs under scrambled names in
  `F00`–`F49`. The backup turns them into a normal, readable music library.
- **A record:** the CSV says what was on the iPod and where each song came from.

**How to use it:** press **Back up to folder…** and choose where to save. The app checks that there
is enough free space before starting. Every copy is size-checked. The iPod itself is **not changed**.

---

## 10. The Log and the status line

- **Progress bar:** moves through copies, deletions and backups.
- **Log:** a running record of what the app did, such as songs copied, skipped, did not fit,
  deleted, and the full output of each rebuild. **Errors also appear here**, starting with `ERROR:`,
  instead of the app closing.
- **Status line** (bottom of the window): what is happening right now, for example
  *"Copying 12/58: Song.mp3"*, or the result of the last job.

If something goes wrong, read the last lines of the Log first: they usually name the file or the
cause.

---

## 11. Unplugging the iPod safely

Windows may keep part of a copy in memory for a moment after the app says it is done. **Always
eject the iPod before unplugging it.** Click the USB icon in the taskbar, choose *Eject iPod*, wait
for *Safe to remove hardware*, then unplug. Unplugging without ejecting can leave the database
half-written, and the iPod may then play nothing until the next rebuild.

---

## 12. Troubleshooting

| What you see | Cause | What to do |
|---|---|---|
| *"No iPod shuffle found. Plug it in and press Refresh."* | The iPod is not mounted yet, or the cable is charge-only | Wait until it shows in File Explorer, then press **Refresh**. Try another cable or USB port |
| Windows says *"Windows protected your PC"* when starting the `.exe` | The exe is not code-signed | **More info → Run anyway** (only the first time) |
| Songs copied in Explorer don't play | The database was not rebuilt | Press **Rebuild now** |
| A song shows as a code like `3131373433316331` | The file was renamed because its name had characters the iPod cannot store, and it has no title tag | It plays normally. To get a readable name, add a title tag with a tag editor, then press **Reload list** |
| *"N songs did not fit"* in the Log | The iPod is full (16 MB is always kept free) | Delete some songs, or choose fewer |
| *"Skipped N files the shuffle can't play"* | Formats such as `.flac`, `.webm` or `.ogg` | Convert them to MP3 or M4A with another program first |
| Drag and drop does nothing | Running from source without `tkinterdnd2`, or the files are already on the iPod | Install the requirements, or use **Add files…** / **Add folder…** |
| *"Rebuild FAILED (exit code …)"* | The builder hit a problem, often an empty folder in `iPod_Control\Music` or an unreadable file | Turn on **Detailed log**, press **Rebuild now**, and read the last lines. Delete empty folders and fix or remove the named file |
| Folder playlists are called `F00`, `F01`… | The music was put there by iTunes | Use **Playlists → By tag** instead |
| The iPod plays nothing after unplugging | It was unplugged without ejecting while the database was being written | Plug it in, press **Rebuild now**, then eject properly |
| You want the original iTunes state back | — | Copy your saved `iTunes` and `Speakable` folders back into `iPod_Control` (section 2) |

---

## 13. Quick reference

| Action | How |
|---|---|
| Add songs | Drag songs or folders onto the window |
| Add songs into a named folder | **Add music & options** → **Add files…** / **Add folder…** → set **Folder on iPod** → **Copy to iPod** |
| Find a song | Type in **Search** |
| Sort | Click a column header (again to reverse) |
| Select all shown | **Ctrl+A** |
| Listen to a song | Double-click it, or **Play** |
| Copy songs to the PC | Select → **Copy selected to PC…** |
| Delete songs | Select → **Delete** key or **Delete selected** |
| Copy everything off the iPod | **Back up** → **Back up to folder…** |
| Apply changed options / Explorer changes | **Add music & options** → **Rebuild now** |
| Refresh the song list display only | **Reload list** |
| Find a newly plugged iPod | **Refresh** |
| Before unplugging | Eject the iPod in Windows |
