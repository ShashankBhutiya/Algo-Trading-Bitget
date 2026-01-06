# How to Upload Files to VPS

Since you are already using a terminal to SSH, the fastest way is using the `scp` command (Secure Copy).

**Open a new terminal window** on your PC (do not use the one where you are already logged into the VPS).

## 1. Upload a Single File
To upload just `run_bot.py`:

```powershell
scp "run_bot.py" root@135.181.32.220:/root/bitget_bot/
```

*   **Syntax**: `scp [LocalFile] [User]@[IP]:[RemoteFolderPath]`
*   Make sure you run this from inside your project folder (`c:\Users\shash\Music\Algo Trading Bitget`).

## 2. Upload a Folder (e.g. 'core')
To upload the updated `core` folder (with the new logic):

```powershell
scp -r "core" root@135.181.32.220:/root/bitget_bot/
```

*   **`-r`**: Means "Recursive" (copy whole folder).

## 3. Alternative: VS Code Drag & Drop
If you are using VS Code:
1.  Install the **"Remote - SSH"** extension.
2.  Click the Green Icon (bottom left) -> "Connect to Host" -> Enter `root@135.181.32.220`.
3.  Once connected, you can see the VPS files in the sidebar.
4.  Just **drag and drop** files from your PC into that sidebar.
