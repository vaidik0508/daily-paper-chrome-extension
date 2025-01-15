from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel

load_dotenv()

class PaperSummary(BaseModel):
    id: str
    title: str
    summary: str
    by: List[str]
    key_topics: str
    day: str

class PaperDetail(BaseModel):
    title: str
    authors: List[str]
    explanation: str

app = FastAPI(title="Daily AI Papers API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(
        os.getenv("MONGODB_URL"),
        maxPoolSize=10,
        minPoolSize=5
    )
    app.mongodb = app.mongodb_client[os.getenv("MONGODB_DB_NAME")]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

async def get_collection(days_back: int = 0):
    date = datetime.now().date() - timedelta(days=days_back)
    return app.mongodb[str(date)]

@app.get('/api/papers', response_model=List[PaperSummary])
async def get_papers():
    try:
        days_back = 0
        summaries = []
        
        while len(summaries) == 0 and days_back <= 5:
            collection = await get_collection(days_back)
            summaries = await collection.find().to_list(length=None)
            days_back += 1
            
        if not summaries:
            raise HTTPException(status_code=404, detail="No papers found")
            
        return [
            PaperSummary(
                id=paper['paper_id'],
                title=paper['title'],
                summary=paper['summary'],
                by=paper['authors'],
                key_topics=', '.join(paper['key_technologies']),
                day=paper['day']
            ) for paper in summaries
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/paper/{day}/{paper_id}', response_model=PaperDetail)
async def get_paper(day: str, paper_id: str):
    try:
        paper = await app.mongodb[day].find_one({'paper_id': paper_id})
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
            
        explanation = "\n\n".join([f"## {key}\n{value}" for key, value in paper.items() 
                                 if key not in ['_id', 'paper_id', 'day']])
            
        return PaperDetail(
            title=paper['title'],
            authors=paper['authors'],
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)