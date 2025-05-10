from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials, firestore

app = FastAPI()

# Inicializar Firebase
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

@app.get("/")
def read_root():
    return {"mensaje": "¡Backend del guante traductor funcionando!"}
