# How to Connect TradingView to Your Bot

This guide explains essentially **"How to make TradingView press the buttons on your bot."**

You need these 2 things:
1.  **The URL**: Where to send the message (`http://<IP>:5000/webhook`).
2.  **The Message**: What to say (`JSON` payload with buy/sell instructions).

---

## Step 1: Get your URL
If you are running on a VPS, your URL looks like this:
`http://123.45.67.89:5000/webhook`
*(Replace `123.45.67.89` with your actual VPS IP Address)*

If you are running locally (testing):
`http://localhost:5000/webhook` (Requires ngrok to work from outside)

## Step 2: Open TradingView
1.  Go to your chart (e.g., BTCUSDT).
2.  Click **"Alert"** (icon at top) or press `Alt + A`.

## Step 3: Configure the "Webhook" Tab
In the Alert settings window:

1.  Click on the **"Notifications"** tab.
2.  Check the box **[x] Webhook URL**.
3.  **Paste your URL** into the text box below it.
    *   Example: `http://192.168.1.50:5000/webhook`

## Step 4: Configure the "Settings" Tab (The Message)
This is the most critical part. You must tell the bot **what** to do.

1.  Click on the **"Settings"** tab.
2.  Set your **Condition** (e.g., RSI Crossing Up, or your custom indicator).
3.  Look at the **"Message"** box at the bottom.
4.  **Delete everything** in that box.
5.  **Paste one of the JSON templates below**:

### Option A: Simple Buy (Uses Bot Config for Size)
Use this for a standard **Long Entry**:
```json
{
    "signal": "open_long",
    "symbol": "BTCUSDT",
    "product_type": "USDT-FUTURES"
}
```

### Option B: Simple Sell
Use this for a standard **Long Exit** or **Short Entry**:
```json
{
    "signal": "open_short",
    "symbol": "BTCUSDT",
    "product_type": "USDT-FUTURES"
}
```

### Option C: Dynamic (Advanced)
If you want one alert to work for multiple symbols, use TradingView placeholders:
```json
{
    "signal": "buy",
    "symbol": "{{ticker}}", 
    "price": "{{close}}",
    "product_type": "SPOT"
}
```

## Step 5: Save & Test
1.  Click **Create**.
2.  When your condition is met, TradingView will fire the message to your VPS.
3.  Your bot will receive it and execute the trade.

---

### Troubleshooting
*   **401 Unauthorized?** If you set a `WEBHOOK_PASSPHRASE` in your `.env` file, you must add it to the JSON:
    ```json
    {
        "signal": "buy",
        "passphrase": "YOUR_SECRET_PASSWORD"
    }
    ```
