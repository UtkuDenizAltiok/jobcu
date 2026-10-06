# Install and start Jobcu

If you already have the Jobcu folder, go straight to **Start**. You need a Mac or Windows
computer and an internet connection. Your data stays separate from the app's files.

## Download

1. Open [Jobcu on GitHub](https://github.com/UtkuDenizAltiok/jobcu).
2. Choose **Code → Download ZIP**, then unpack it.
3. Put the unpacked `jobcu-main` folder somewhere you can find it, such as Documents.

No GitHub account or invitation is needed. The owner's [license](../../LICENSE) applies.

## Start

| Computer | Action |
|---|---|
| Mac | Double-click **Start Jobcu.command**. If blocked, open **System Settings → Privacy & Security → Open Anyway**. |
| Windows | Double-click **Start Jobcu.bat** (the `.bat` may be hidden). If blocked, choose **More info → Run anyway**. |

If the launcher asks to install **uv**, allow it: Return on Mac, any key on Windows. The first
start may take a few minutes. Jobcu opens in your browser at `http://127.0.0.1:8765`.
Keep the terminal window open while using it.

## Stop and reopen

Close the launcher's terminal window to stop Jobcu. Choose **Terminate** if your Mac asks.
Double-click the same launcher when you want to use it again.

Next: [Set up your keys](getting-your-keys.md), then [Your first search](first-search.md).
Help: [Troubleshooting](troubleshooting.md).

## Update or remove

For a Git checkout such as the owner's Mac project, the launcher checks for updates on clean
main. If it cannot update, it warns and uses the installed version; Codex handles development
updates through the project rules.

For a ZIP download, stop Jobcu, download the new ZIP, and replace the app folder. Your keys,
documents, settings and saved jobs stay in the separate data folder.

To remove the app, delete its code folder. Delete its data folder only if you also want to
permanently erase your inputs and results: `~/Library/Application Support/Jobcu` on Mac,
`%LOCALAPPDATA%/Jobcu` on Windows.
