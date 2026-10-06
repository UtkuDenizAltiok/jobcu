# Install and start Jobcu

## 1. Download

Jobcu's files are on **GitHub**, a website where programs are kept. The code is publicly
readable; the owner's [license](../../LICENSE) still applies to its use.

1. Open the [Jobcu page](https://github.com/UtkuDenizAltiok/jobcu), click the green **Code** button
   → **Download ZIP**.
2. Unpack it: **Mac** double-click the downloaded file · **Windows** right-click it → **Extract
   All** → **Extract**.
3. Move the unpacked `jobcu-main` folder into your **Documents** folder.

You don't need a GitHub account to download it.

You need a Mac or a Windows 10 or 11 computer, and an internet connection.

## 2. Start

### Mac

1. In `jobcu-main`, double-click **Start Jobcu.command**.
2. If your Mac says it "could not verify" the file: click **Done**, open **System Settings** →
   **Privacy & Security**, scroll down and click **Open Anyway**. (Only the first time.)
3. If asked to install the helper program **uv**, press **Return**. The first start takes a few
   minutes.

### Windows

1. In `jobcu-main`, double-click **Start Jobcu**.
2. If you see "Windows protected your PC": click **More info** → **Run anyway**. (Only the first
   time.)
3. If asked to install the helper program **uv**, press any key. The first start takes a few
   minutes.

Jobcu opens in your browser. **Keep Jobcu's small window open while you use it**; close the
terminal window to stop Jobcu, choosing **Terminate** if your Mac asks. Next time, just
double-click **Start Jobcu.command** on Mac or **Start Jobcu** on Windows again.

➡️ Next: [Get your keys](getting-your-keys.md)

---

**Update** (Utku tells you when there's a new version): close Jobcu's window, download the new ZIP
as above and put its `jobcu-main` folder in place of the old one. Your documents, keys, settings
and saved jobs are kept: they live in a separate folder, not in `jobcu-main`. (A Jobcu folder set
up with git updates itself each time you start it.)

**Remove:** delete `jobcu-main`. To also delete your data, delete the `Jobcu` folder in
`~/Library/Application Support` (Mac) or `%LOCALAPPDATA%` (Windows).
