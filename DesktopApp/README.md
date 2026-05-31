# FitTrack Desktop (PyQt) — PoC

Requirements and quick run:

1. Install dependencies:

```powershell
cd DesktopApp
pip install -r requirements.txt
```

2. Start backend (from project root `Backend`):

```powershell
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Run the desktop app:

```powershell
cd DesktopApp
py main.py
```

This PoC includes a simple API client and a login window. It stores the token in `DesktopApp/token.json`.
