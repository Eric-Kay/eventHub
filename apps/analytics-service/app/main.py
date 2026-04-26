from fastapi import FastAPI, Depends, HTTPException
from .auth import get_current_user

app = FastAPI(title="analytics-service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service"}

@app.get("/analytics/admin/overview")
def overview(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return {
        "total_revenue": 0,
        "total_bookings": 0,
        "active_events": 0,
        "failed_notifications": 0,
        "top_events": [],
        "notes": "Connect real aggregations in a later phase."
    }

@app.get("/analytics/organizers/{organizer_id}")
def organizer_stats(organizer_id: int, user: dict = Depends(get_current_user)):
    if user["role"] not in ["organizer", "admin"]:
        raise HTTPException(status_code=403, detail="forbidden")
    return {
        "organizer_id": organizer_id,
        "events": 0,
        "tickets_sold": 0,
        "gross_revenue": 0
    }

@app.get("/analytics/admin/sales")
def sales(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return {
        "series": [
            {"label": "Mon", "sales": 0},
            {"label": "Tue", "sales": 0},
            {"label": "Wed", "sales": 0}
        ]
    }
