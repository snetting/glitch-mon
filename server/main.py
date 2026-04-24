from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import time
import uuid
import httpx
import uvicorn
import os
import asyncio

app = FastAPI()

# Database setup
DB_FILE = "anomalies.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (client_id TEXT PRIMARY KEY, last_heartbeat REAL)''')
    try:
        c.execute("ALTER TABLE clients ADD COLUMN ip_address TEXT")
        c.execute("ALTER TABLE clients ADD COLUMN latitude REAL")
        c.execute("ALTER TABLE clients ADD COLUMN longitude REAL")
        c.execute("ALTER TABLE clients ADD COLUMN country TEXT")
    except sqlite3.OperationalError:
        pass # Columns already exist
        
    c.execute('''CREATE TABLE IF NOT EXISTS anomalies 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp REAL, 
                  client_id TEXT, 
                  test_type TEXT, 
                  p_value REAL, 
                  ip_address TEXT, 
                  latitude REAL, 
                  longitude REAL, 
                  country TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Templates & Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class Heartbeat(BaseModel):
    client_id: str

class Report(BaseModel):
    client_id: str
    test_type: str
    p_value: float

async def get_geo_data(ip: str):
    # Free API for IP Geolocation
    if ip == "127.0.0.1": return (0, 0, "Localhost")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://ip-api.com/json/{ip}")
            data = resp.json()
            if data["status"] == "success":
                return (data["lat"], data["lon"], data["country"])
    except:
        pass
    return (0, 0, "Unknown")

async def update_client_geo(client_id: str, ip: str):
    lat, lon, country = await get_geo_data(ip)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Ensure client still exists before updating
    c.execute("UPDATE clients SET latitude=?, longitude=?, country=?, ip_address=? WHERE client_id=?", 
              (lat, lon, country, ip, client_id))
    conn.commit()
    conn.close()

@app.post("/api/heartbeat")
async def heartbeat(hb: Heartbeat, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT ip_address, latitude FROM clients WHERE client_id = ?", (hb.client_id,))
    row = c.fetchone()
    
    if row and row[0] == client_ip and row[1] is not None:
        c.execute("UPDATE clients SET last_heartbeat = ? WHERE client_id = ?", (time.time(), hb.client_id))
    else:
        # Insert/Update heartbeat immediately
        c.execute("INSERT OR REPLACE INTO clients (client_id, last_heartbeat, ip_address, latitude, longitude, country) VALUES (?, ?, ?, COALESCE((SELECT latitude FROM clients WHERE client_id=?), NULL), COALESCE((SELECT longitude FROM clients WHERE client_id=?), NULL), COALESCE((SELECT country FROM clients WHERE client_id=?), NULL))", 
                  (hb.client_id, time.time(), client_ip, hb.client_id, hb.client_id, hb.client_id))
        background_tasks.add_task(update_client_geo, hb.client_id, client_ip)
        
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/report")
async def report(rep: Report, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    timestamp = time.time()
    lat, lon, country = await get_geo_data(client_ip)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO anomalies 
                 (timestamp, client_id, test_type, p_value, ip_address, latitude, longitude, country) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (timestamp, rep.client_id, rep.test_type, rep.p_value, client_ip, lat, lon, country))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get active clients (heartbeat in last 5 minutes)
    five_mins_ago = time.time() - 300
    c.execute("SELECT client_id, latitude, longitude, country FROM clients WHERE last_heartbeat > ?", (five_mins_ago,))
    active_client_rows = c.fetchall()
    clients_data = [dict(r) for r in active_client_rows]
    
    # Get recent anomalies (last 24 hours) - EXCLUDING ip_address for privacy
    one_day_ago = time.time() - 86400
    c.execute("SELECT id, timestamp, client_id, test_type, p_value, latitude, longitude, country FROM anomalies WHERE timestamp > ? ORDER BY timestamp DESC", (one_day_ago,))
    rows = c.fetchall()
    anomalies = [dict(r) for r in rows]
    
    conn.close()
    return {
        "active_clients": len(clients_data) or 1, # default to 1 to prevent /0 in chart
        "clients_data": clients_data,
        "anomalies": anomalies
    }

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
