"""
Backend mínimo de sincronización para 'Mis Gastos'.
- FastAPI + SQLite, un solo usuario, autenticado por token (header X-Token).
- Endpoint /api/sync: el cliente envía sus movimientos; el servidor hace
  merge last-write-wins por 'updated' y devuelve el conjunto completo
  (incluye tombstones para propagar borrados a otros dispositivos).
"""
import os, time, sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

TOKEN = os.environ.get("GASTOS_TOKEN", "cambia-este-token")
DB_PATH = os.environ.get("GASTOS_DB", "/var/lib/gastos/gastos.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")  # evita 'database is locked' con varios dispositivos
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS items(
            id TEXT PRIMARY KEY, amount REAL, type TEXT, cat TEXT, note TEXT,
            ts INTEGER, updated INTEGER, deleted INTEGER DEFAULT 0)""")
        yield con
        con.commit()
    finally:
        con.close()

app = FastAPI(title="Gastos Sync")

class Item(BaseModel):
    id: str
    amount: float
    type: str = "gasto"
    cat: str = "otros"
    note: str = ""
    ts: int
    updated: int
    deleted: bool = False

class SyncIn(BaseModel):
    items: list[Item] = []

def check(token: str | None):
    if not token or token != TOKEN:
        raise HTTPException(status_code=401, detail="token inválido")

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/sync")
def sync(body: SyncIn, x_token: str | None = Header(default=None)):
    check(x_token)
    with db() as con:
        for it in body.items:
            row = con.execute("SELECT updated FROM items WHERE id=?", (it.id,)).fetchone()
            if row is None or it.updated >= row["updated"]:
                con.execute("""INSERT INTO items(id,amount,type,cat,note,ts,updated,deleted)
                    VALUES(?,?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET
                      amount=excluded.amount, type=excluded.type, cat=excluded.cat,
                      note=excluded.note, ts=excluded.ts, updated=excluded.updated,
                      deleted=excluded.deleted""",
                    (it.id, it.amount, it.type, it.cat, it.note, it.ts, it.updated,
                     1 if it.deleted else 0))
        rows = con.execute("SELECT * FROM items").fetchall()
    items = [dict(r) for r in rows]
    for r in items:
        r["deleted"] = bool(r["deleted"])
    return {"items": items, "now": int(time.time() * 1000)}
