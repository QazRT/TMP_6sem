from fastapi import FastAPI
from random import randint
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {'massage': str(randint(1, 1000))}    

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)