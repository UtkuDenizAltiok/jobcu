# Install and start Jobcu

You need a Mac or Windows computer and an internet connection. You do not need programming
experience or a Jobcu account. If you already have a Jobcu folder, skip Download and go to
[Start Jobcu](#start-jobcu).

## Download

1. Open [Jobcu on GitHub](https://github.com/UtkuDenizAltiok/jobcu). GitHub is where Jobcu's
   application files are published. You do not need a GitHub account or invitation to download.
2. Click the **Code** button above the list of files, then click **Download ZIP**.
3. Find the downloaded file, usually named `jobcu-main.zip`, in your Downloads folder.
4. Unpack it: on Mac, double-click the ZIP file; on Windows, right-click it, choose
   **Extract All**, and follow the prompts. This creates a normal folder named `jobcu-main`.
5. Move that folder somewhere you can find it again, such as Documents. Open the folder.

If you need more help unpacking, follow [Apple's ZIP instructions](https://support.apple.com/guide/mac-help/zip-and-unzip-files-and-folders-on-mac-mchlp2528/mac)
or [Microsoft's ZIP instructions](https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/zip-and-unzip-files).

The folder contains the app and its guides. Your personal Jobcu data is stored separately.
The owner's [license](../../LICENSE) applies to the application files.

## Start Jobcu

Find the start file inside the unpacked Jobcu folder. Open it from the folder, not from
inside the ZIP download.

### On Mac

1. Double-click **Start Jobcu.command**.
2. If macOS blocks it and you trust this Jobcu download, open **System Settings → Privacy &
   Security** and look for **Open Anyway** for the file you just tried to open. Confirm opening
   it if asked. If this option is unavailable, see [Troubleshooting](troubleshooting.md#jobcu-will-not-open).
3. A Terminal window opens. This is the text window that runs Jobcu. You do not need to type
   commands into it.

Apple explains the security prompt in [Safely open apps on your Mac](https://support.apple.com/en-us/102445).

### On Windows

1. Double-click **Start Jobcu.bat**. Windows may show it as **Start Jobcu** without `.bat`.
2. If Windows shows a protection warning and you trust this Jobcu download, choose **More info**,
   then **Run anyway**, if those options are offered. Otherwise see
   [Troubleshooting](troubleshooting.md#jobcu-will-not-open).
3. A command window opens. This is the text window that runs Jobcu. You do not need to type
   commands into it.

Microsoft describes this prompt in its [SmartScreen guidance for new apps](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app#step-6-handle-smartscreen-for-new-apps).
These operating-system instructions were checked on 2026-10-07; wording can vary by version.

### What happens next

On the first start, the text window may ask to install a free helper called **uv**.
It downloads the software Jobcu needs. Press **Return** on Mac or **any key** on Windows
when the launcher asks. You do not need to install Python yourself.

Wait while Jobcu prepares. The first start can take a few minutes. When it is ready, the
Jobcu page opens in your usual web browser. The address is `http://127.0.0.1:8765`;
this address opens the app on your own computer.

Keep the text window open while using Jobcu. You may minimize it, but closing it stops the
app. If the browser does not open, leave the text window running and type
`http://127.0.0.1:8765` into your browser's address bar.

Next, follow [Set up your keys](getting-your-keys.md), then [How to use Jobcu](first-search.md).

## Stop and reopen

When finished, close the text window that started Jobcu. On Mac, choose **Terminate** if
asked. Close the browser tab too. Closing only the browser tab leaves Jobcu running.

To use it again, open the same Jobcu folder and double-click the same start file. Your saved
keys, documents, settings and marked jobs remain on this computer; you do not need to repeat
setup every time.

## Update Jobcu

If you downloaded a ZIP:

1. Stop Jobcu as described above.
2. Download and unpack a new ZIP from the same GitHub page.
3. Keep the new folder in place of the older app folder and use its start file next time.
   You can remove the older app folder to avoid opening it by mistake.

Your keys, documents, settings and saved jobs are in a separate data folder, so replacing
the app folder keeps them. The ZIP version does not download app updates automatically.

If your copy is managed with Git, such as the owner's Mac development folder, the start file
checks for updates when it is safe to do so. If it cannot update, it shows a warning and starts
the version already installed. Development updates follow the project rules in AGENTS.md.

## Remove Jobcu

Stop Jobcu first. Delete its application folder to remove the app. This keeps your personal
data in case you install Jobcu again.

If you also want to permanently erase your keys, documents and results, delete the separate
data folder. Its location is shown in **Jobcu → Settings → About**. The default location is
`~/Library/Application Support/Jobcu` on Mac or `%LOCALAPPDATA%/Jobcu` on Windows.
Deleting that folder cannot be undone through Jobcu.
