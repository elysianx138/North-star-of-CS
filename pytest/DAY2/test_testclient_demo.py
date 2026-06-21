from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/hello/{name}")
def hello(name:str):
    return {"hello":name}

client = TestClient(app)

def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

def test_hello():
    response = client.get("/hello/alice")
    assert response.status_code == 200
    assert response.json() == {"hello":"alice"}