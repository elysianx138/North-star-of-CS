import hashlib
import hmac
import base64
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI,Header,HTTPException

SECRET = "my-secret-key"
app = FastAPI()

USERS = {"alice":"password123"}

def create_jwt(username):
    header = base64.urlsafe_b64encode(json.dumps({"alg":"HS256"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": username, "role": "user"}).encode()).rstrip(b"=").decode()
    signature = hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{signature}"

def verify_jwt(token: str):
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid token")
    header, payload, signature = parts
    expected_sig = hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    if signature != expected_sig:
        raise HTTPException(status_code=401, detail="Invalid signature")
    return json.loads(base64.urlsafe_b64decode(payload + "=="))

@app.post("/login")
def login(username:str,password:str):
    if USERS.get(username) != password:
        raise HTTPException(status_code=401,detail="Unauthorized")
    return json.loads(create_jwt(username))
