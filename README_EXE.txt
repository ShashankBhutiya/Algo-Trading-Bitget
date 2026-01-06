
# Bitget Algo Trading Bot - EXE Instructions

This folder contains the standalone executable for the Bitget Trading Bot.

## Setup
1. **API Keys**: The bot requires your Bitget API keys to function. 
   - Ensure the `.env` file is in the SAME folder as the `BitgetBot.exe`.
   - The `.env` file must contain:
     ```
     BITGET_API_KEY=your_key
     BITGET_SECRET=your_secret
     BITGET_PASSPHRASE=your_passphrase
     ```

2. **Dry Run (Simulation)**:
   - To run in simulation mode (no real money), you can run the bot from the command line:
     ```powershell
     .\BitgetBot.exe --dry-run
     ```
   - OR create a shortcut to the EXE, right-click -> Properties, and add ` --dry-run` to the Target field.

## Troubleshooting
- If the window closes immediately, open a terminal (PowerShell or CMD), navigate to this folder, and run `.\BitgetBot.exe`. This will let you see any error messages.
