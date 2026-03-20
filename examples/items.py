from fastapi import FastAPI
app = FastAPI()
items = []
@app.get('/')
async def root():
    return "Hello World"
@app.post('/items')
async def create_item(item:str):
    items.append(item)
    return items
@app.get('/items')
async def list_items():
    return items