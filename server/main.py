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

app = FastAPI()

# Database setup
DB_FILE = "anomalies.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (client_id TEXT PRIMARY KEY, last_heartbeat REAL)''')
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

@app.post("/api/heartbeat")
async def heartbeat(hb: Heartbeat):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO clients (client_id, last_heartbeat) VALUES (?, ?)", 
              (hb.client_id, time.time()))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/report")
async def report(rep: Report, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.client.host
    # If behind a proxy (like many cloud setups), we might need:
    # client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
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
    c.execute("SELECT COUNT(*) as count FROM clients WHERE last_heartbeat > ?", (five_mins_ago,))
    active_clients = c.fetchone()["count"]
    
    # Get recent anomalies (last 24 hours) - EXCLUDING ip_address for privacy
    one_day_ago = time.time() - 86400
    c.execute("SELECT id, timestamp, client_id, test_type, p_value, latitude, longitude, country FROM anomalies WHERE timestamp > ? ORDER BY timestamp DESC", (one_day_ago,))
    rows = c.fetchall()
    anomalies = [dict(r) for r in rows]
    
    conn.close()
    return {
        "active_clients": max(active_clients, 1),
        "anomalies": anomalies
    }

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
