from fastapi import FastAPI
import hashlib as hsl
import base64 as b64
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class User(BaseModel):
    username: str
    password: str

@app.post("/user/string")
async def root(user: User):
    passwordHash = hsl.sha256(f"{user.username}+{user.password}".encode(), usedforsecurity=True).hexdigest()
    return {'userstring': b64.encodebytes(str(user.username+':'+passwordHash).encode()).strip()}

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8080)