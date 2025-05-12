from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from dotenv import load_dotenv
import os

# Carga variables de entorno
load_dotenv()

# Variables de configuración de Firebase JS SDK (para front-end)
firebase_api_key         = os.getenv("FIREBASE_API_KEY")
firebase_auth_domain     = os.getenv("FIREBASE_AUTH_DOMAIN")
firebase_project_id      = os.getenv("FIREBASE_PROJECT_ID")
firebase_storage_bucket  = os.getenv("FIREBASE_STORAGE_BUCKET")
firebase_messaging_sender_id = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
firebase_app_id          = os.getenv("FIREBASE_APP_ID")
firebase_measurement_id  = os.getenv("FIREBASE_MEASUREMENT_ID")

app = FastAPI()

# --- Endpoint para servir configuración de Firebase al front-end ---
@app.get("/config")
def firebase_config():
    return JSONResponse({
        "apiKey": firebase_api_key,
        "authDomain": firebase_auth_domain,
        "projectId": firebase_project_id,
        "storageBucket": firebase_storage_bucket,
        "messagingSenderId": firebase_messaging_sender_id,
        "appId": firebase_app_id,
        "measurementId": firebase_measurement_id,
    })

# --- Inicializar Firebase Admin (servidor) ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Montar recursos estáticos y plantillas ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Rutas de páginas ---
@app.get("/", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/nLog.html", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("nLog.html", {"request": request})

@app.get("/ajustes.html", response_class=HTMLResponse)
async def ajustes_get(request: Request, user_id: str | None = Cookie(default=None)):
    return templates.TemplateResponse("ajustes.html", {"request": request})

@app.get("/traductor.html", response_class=HTMLResponse)
async def traductor_get(request: Request, user_id: str | None = Cookie(default=None)):
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "traductor.html",
        {"request": request, "user_id": user_id}
    )

# --- Lógica de autenticación ---
@app.post("/login", response_class=RedirectResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    email = email.lower()
    user_ref = db.collection("usuarios").document(email)
    doc = user_ref.get()
    if not doc.exists:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Usuario no registrado"})
    data = doc.to_dict()
    if not bcrypt.checkpw(password.encode(), data.get("password", "").encode()):
        return templates.TemplateResponse("index.html", {"request": request, "error": "Contraseña incorrecta"})
    response = RedirectResponse(url="/traductor.html", status_code=303)
    response.set_cookie(key="user_id", value=doc.id, httponly=True)
    return response

@app.post("/register", response_class=RedirectResponse)
async def register_post(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    email = email.lower()
    user_ref = db.collection("usuarios").document(email)
    if user_ref.get().exists:
        return templates.TemplateResponse("nLog.html", {"request": request, "error": "El correo ya está registrado"})
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_ref.set({"correo": email, "nombre": nombre, "password": hashed})
    return RedirectResponse(url="/", status_code=303)

@app.post("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user_id")
    return response
