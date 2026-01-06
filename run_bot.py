import subprocess
import time
import sys
import os
from datetime import datetime

def log_message(name, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{name}] {message}")

def run_process(script_name, log_file):
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Open log file in append mode
    f = open(log_file, "a")
    
    try:
        # Prepare command
        if isinstance(script_name, list):
             cmd = [sys.executable] + script_name
        else:
             cmd = [sys.executable, "-u", script_name]

        # Start the process
        proc = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            cwd=os.getcwd(),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0 
            # On Windows, CREATE_NEW_CONSOLE might pop up new windows. 
            # Let's avoid that to keep it in background/same window?
            # Actually, keeping it in same window but piping to file is better.
            # So I will remove creationflags to keep it hidden/embedded.
        )
        return proc, f
    except Exception as e:
        log_message("System", f"Failed to start {script_name}: {e}")
        f.close()
        return None, None

def main():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Define the scripts to run
    # Format: "DisplayName": {"file": "filename.py", "log": "path/to/log", "process": None, "file_handle": None}
    scripts = {
        # "StrategyBot": {
        #     "file": "bot.py", 
        #     "log": "logs/strategy_bot.log", 
        #     "process": None,
        #     "file_handle": None
        # },
        "WebhookServer": {
            # Use Gunicorn as a module to run production server
            # -w 1: One worker (sufficient for webhook)
            # -b 0.0.0.0:5000: Bind all IPs on port 5000
            # --access-logfile -: Log to stdout (captured by our logger)
            "file": ["-m", "gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--access-logfile", "-", "webhook_bot:app"], 
            "log": "logs/webhook_server.log", 
            "process": None,
            "file_handle": None
        }
    }

    log_message("System", "Starting 24/7 Watchdog...")
    log_message("System", "Logs will be written to 'logs/' directory.")
    log_message("System", "Press Ctrl+C to stop all services.")

    try:
        while True:
            for name, info in scripts.items():
                proc = info["process"]
                
                # If process is not started or has exited
                if proc is None or proc.poll() is not None:
                    
                    # If it was running and died, close the file handle and log
                    if proc is not None:
                        return_code = proc.poll()
                        log_message(name, f"Process exited with code {return_code}. Restarting in 5 seconds...")
                        if info["file_handle"]:
                            info["file_handle"].close()
                            info["file_handle"] = None
                        time.sleep(5) # Delay before restart
                    
                    # Start/Restart
                    log_message(name, f"Starting {info['file']}...")
                    p, f = run_process(info["file"], info["log"])
                    
                    if p:
                        info["process"] = p
                        info["file_handle"] = f
                        log_message(name, f"Started with PID {p.pid}")
            
            # Check every 2 seconds
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n")
        log_message("System", "Stopping all processes...")
        for name, info in scripts.items():
            if info["process"]:
                log_message(name, "Terminating...")
                info["process"].terminate()
                try:
                    info["process"].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    info["process"].kill()
                
                if info["file_handle"]:
                    info["file_handle"].close()
        log_message("System", "Shutdown complete.")

if __name__ == "__main__":
    main()
