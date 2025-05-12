from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt

app = FastAPI()

# --- 1) Inicializar Firebase ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- 2) Montar estáticos ---
#    Pon aquí tu carpeta con css/, js/, img/, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- 3) Configurar plantillas ---
#    Pon aquí tu carpeta con index.html, nLog.html, ajustes.html, traductor.html
templates = Jinja2Templates(directory="templates")


# --- 4) Rutas de renderizado de páginas ---

@app.get("/", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/nLog.html", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("nLog.html", {"request": request})

@app.get("/ajustes.html", response_class=HTMLResponse)
async def ajustes_get(request: Request,
                      user_id: str | None = Cookie(default=None)):
    # Podrías validar aquí que exista la cookie `user_id`
    return templates.TemplateResponse("ajustes.html", {"request": request})

@app.get("/traductor.html", response_class=HTMLResponse)
async def traductor_get(request: Request,
                        user_id: str | None = Cookie(default=None)):
    if not user_id:
        # Si no hay sesión, redirige al login
        return RedirectResponse("/", status_code=303)
    # Inyectamos el user_id en la plantilla para usarlo en el cliente
    return templates.TemplateResponse(
        "traductor.html",
        {"request": request, "user_id": user_id}
    )


# --- 5) Lógica de Login y Registro ---

@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    email = email.lower()
    usuarios = db.collection("usuarios").document(email)
    doc = usuarios.get()
    if not doc.exists:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Usuario no registrado"
        })
    user_data = doc.to_dict()

    # Verificar contraseña con bcrypt
    if not bcrypt.checkpw(password.encode("utf-8"),
                          user_data.get("password", "").encode("utf-8")):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Contraseña incorrecta"
        })

    # Login exitoso → redirigir y dejar cookie con user_id
    response = RedirectResponse("/traductor.html", status_code=303)
    response.set_cookie(key="user_id", value=doc.id, httponly=True)
    return response


@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    email = email.lower()
    usuarios_ref = db.collection("usuarios").document(email)
    if usuarios_ref.get().exists:
        return templates.TemplateResponse("nLog.html", {
            "request": request,
            "error": "El correo ya está registrado"
        })

    # Hashear contraseña y guardar nuevo usuario
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    usuarios_ref.set({"correo": email, "nombre": nombre, "password": hashed})

    # Tras registro, redirigir al login
    return RedirectResponse("/", status_code=303)

@app.post("/logout")
async def logout():
    # Creamos la respuesta que redirige al login
    response = RedirectResponse("/", status_code=303)
    # Borramos la cookie de sesión
    response.delete_cookie(key="user_id")
    return response
