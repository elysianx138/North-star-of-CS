from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message":"Hello,这是我的密钥:123456"}

@app.post("/login")
def login(username:str,password:str):
    return {"username":username,"password":password}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)

#   Bash
# > openssl genrsa -out key.pem 2048
# > openssl req -new -x509 -key key.pem -out cert.pem -day 365 -subj "CN=localhost"

