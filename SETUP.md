# ORPOSS Setup Guide

## Architecture
```
All laptops
    │
    ├── Aiven MySQL (cloud DB) ── shared by everyone
    ├── Pusher (real-time events)
    └── Cloudinary (image uploads)
```

## 1. Set up Aiven MySQL (one-time, done by team lead)
1. Go to https://aiven.io and create a free account
2. Create a new **MySQL** service (free tier, 1 month trial then ~$19/mo for hobbyist)
3. Once running, go to the service overview and note:
   - **Host**, **Port**, **User**, **Password**
4. Download the **CA Certificate** (`ca.pem`) from the service overview page
5. Open a Query Runner (or connect via DBeaver/TablePlus) and run `db/schema.sql`

## 2. Configure .env (every laptop — fill in once, never touch again)
```
DB_HOST=your-db.aivencloud.com
DB_PORT=3306
DB_USER=avnadmin
DB_PASSWORD=your_aiven_password
DB_NAME=ORPOSS
DB_SSL_CA=ca.pem        ← put ca.pem in the ORPOSS folder, or use full path
```
The rest (Pusher, Cloudinary) is already filled in — leave it as-is.

## 3. Install dependencies
```
pip install -r requirements.txt
```

## 4. Run
```
python main.py
```

## Adding a new laptop
1. Copy the project folder to the new laptop
2. Copy `ca.pem` to the same folder (or wherever `DB_SSL_CA` points)
3. Edit `.env` — fill in the 5 DB_* lines (same values for every machine)
4. `pip install -r requirements.txt`
5. `python main.py`

## Offline mode
If Aiven is unreachable, the app falls back to `data/inventory.py` automatically.
Pusher events are silently dropped if unavailable.

## Login
| Button         | PIN  | Role                      |
|----------------|------|---------------------------|
| KITCHEN PANEL  | k123 | Kitchen order management  |
| ADMIN PANEL    | a123 | Admin (no POS)            |
| ADMIN SETTINGS | a123 | Admin through POS sidebar |
