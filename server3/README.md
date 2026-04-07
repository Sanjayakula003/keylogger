## Consent-based monitoring demo (exam-safe)

This is **not** a stealth keylogger. It is a **visible, consent-based** classroom demo that shows the same *networking concepts* safely:

- **Client (second device)**: sends **only text typed into the client app** (not global keystrokes) + **full-screen screenshots every 10 seconds** with a visible "CAPTURING: ON" indicator.
- **Server (main device)**: receives events and shows them on a simple dashboard.

### Setup

Install Python 3.10+ on both devices.

On both devices (or once, then copy the folder):

```bash
cd e:\keylogger3
python -m pip install -r requirements.txt
```

### Run the server (main device)

```bash
cd e:\keylogger3
python server.py
```

Then open the dashboard in a browser:

- `http://127.0.0.1:5000/dashboard`

To accept connections from another device on your LAN, run with your LAN IP:

```bash
set MONITOR_DEMO_HOST=0.0.0.0
set MONITOR_DEMO_PORT=5000
python server.py
```

Allow inbound TCP `8080` in Windows Firewall.

### Run the client (second device)

```bash
cd e:\keylogger3
python client.py
```

In the UI:

- Set **Server URL** to your main device, e.g. `http://192.168.1.50:8080`
- Set **Server URL** to your main device, e.g. `http://192.168.1.50:5000`
- Click **Start (I consent)** (indicator turns red)
- Type into the app textbox, and screenshots will upload every \(N\) seconds.

### Where data is stored

Server writes received data under:

- `data/keystrokes.log`
- `data/screenshots/*.png`

