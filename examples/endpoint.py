from fastapi import FastAPI
from enum import Enum
app = FastAPI()
@app.get("/hello/{name}")
async def hello(name):
    return f"welcome {name}"
food_items = {'indian': ['samosa','chola'],'italian':['pizza','ravioli']}
@app.get("/get_items/{cuisine}")
async def get_items(cuisine):
    return food_items.get(cuisine)