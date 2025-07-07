from fastapi import FastAPI, Request
from pydantic import BaseModel
import json

app = FastAPI()

with open("movie_db.json", "r") as f:
    MOVIES = json.load(f)

class MovieQuery(BaseModel):
    query: str

@app.post("/search")
async def search_movie(data: MovieQuery):
    query = data.query.lower()
    for m in MOVIES:
        if query in m["title"].lower():
            return m
    return {"message": "Movie not found"}