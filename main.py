import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from database import db, create_document, get_documents
from schemas import Bet

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Wingo Admin Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

class BetIn(BaseModel):
    period_id: str
    bet_type: str
    selection: str
    amount: float
    source: Optional[str] = None

@app.post("/api/bets")
def add_bet(bet: BetIn):
    try:
        bet_doc = Bet(**bet.model_dump())
        inserted_id = create_document("bet", bet_doc)
        return {"id": inserted_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/periods/{period_id}/totals")
def get_period_totals(period_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    pipeline = [
        {"$match": {"period_id": period_id}},
        {"$group": {
            "_id": {
                "bet_type": "$bet_type",
                "selection": {"$toLower": "$selection"}
            },
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    try:
        results = list(db["bet"].aggregate(pipeline))
        totals: Dict[str, Any] = {
            "big_small": {"big": 0.0, "small": 0.0, "total": 0.0},
            "number": {str(i): 0.0 for i in range(10)},
            "color": {"red": 0.0, "green": 0.0, "violet": 0.0}
        }
        for r in results:
            t = r["_id"]["bet_type"]
            s = r["_id"]["selection"]
            amt = float(r["total_amount"]) if r.get("total_amount") is not None else 0.0
            if t == "big_small":
                if s in ("big", "small"):
                    totals["big_small"][s] = totals["big_small"].get(s, 0.0) + amt
                    totals["big_small"]["total"] += amt
            elif t == "number":
                if s in totals["number"]:
                    totals["number"][s] = totals["number"].get(s, 0.0) + amt
            elif t == "color":
                if s in totals["color"]:
                    totals["color"][s] = totals["color"].get(s, 0.0) + amt
        return {"period_id": period_id, "totals": totals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/periods")
def list_periods(limit: int = Query(20, ge=1, le=200)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    try:
        docs = db["bet"].find({}, {"period_id": 1}).sort("_id", -1).limit(limit)
        seen = set()
        periods: List[str] = []
        for d in docs:
            pid = d.get("period_id")
            if pid and pid not in seen:
                seen.add(pid)
                periods.append(pid)
        return {"periods": periods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
