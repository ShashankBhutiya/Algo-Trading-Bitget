# VPS Deployment Guide (Updated)

This guide explains how to deploy your **Bitget Algo Trading Bot** to a Linux VPS (Virtual Private Server) for true 24/7 operation.

## 1. What You Need
*   **A VPS**: Recommended providers: DigitalOcean ($6/mo), Vultr, AWS Lightsail, or Google Cloud.
*   **OS**: Ubuntu 22.04 LTS (Recommended) or Debian.
*   **Files**: Your entire project folder.

## 2. Transfer Files
You need to copy your project files from your PC to the VPS.
**Method A: SCP (Command Line)**
If you are comfortable with terminal:
```bash
scp -r "C:\Users\shash\Music\Algo Trading Bitget" root@<YOUR_VPS_IP>:/root/bitget_bot
```

**Method B: FileZilla (GUI) - EASIEST**
1.  Download [FileZilla Client](https://filezilla-project.org/).
2.  Connect using `SFTP` protocol, your VPS IP, User (`root`), and Password.
3.  Drag and drop your project folder to `/root/`.

## 3. Deployment (One-Click Setup)
I have created a `setup_vps.sh` script that handles everything for you.

1.  **SSH into your VPS**:
    ```bash
    ssh root@<YOUR_VPS_IP>
    ```
2.  **Navigate to the folder**:
    ```bash
    cd bitget_bot
    ```
    *(Or whatever name you gave the folder)*

3.  **Run the Auto-Setup**:
    ```bash
    chmod +x setup_vps.sh
    ./setup_vps.sh
    ```

**What this script does:**
*   Installs Python & Pip.
*   Installs your libraries (`flask`, `pandas`, etc).
*   Configures `systemd` to auto-start your bot on boot.
*   Starts the bot immediately.

## 4. Monitoring & Logs
Once running in the background, you can check on it anytime.

*   **Check Status**:
    ```bash
    systemctl status bitget_bot
    ```
*   **View Real-time Logs**:
    ```bash
    tail -f logs/strategy_bot.log
    # OR
    tail -f logs/webhook_server.log
    ```
*   **Stop Bot**:
    ```bash
    systemctl stop bitget_bot
    ```
*   **Restart Bot**:
    ```bash
    systemctl restart bitget_bot
    ```

## 5. TradingView Webhook
Your Webhook URL for TradingView alerts is now:
`http://<YOUR_VPS_IP>:5000/webhook`

**Firewall Note:**
Ensure your VPS provider allows traffic on Port **5000**.
*   **AWS**: Edit Security Group > Inbound Rules > Add Custom TCP Port 5000 from 0.0.0.0/0.
*   **DigitalOcean/Vultr**: Usually open by default, but check `ufw`:
    ```bash
    ufw allow 5000/tcp
    ```
