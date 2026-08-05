import streamlit as st
from datetime import datetime, date
import pandas as pd
from openai import OpenAI
from supabase import create_client, Client
import bcrypt
import json
import re
import requests
from bs4 import BeautifulSoup
import unicodedata

st.set_page_config(
    page_title="VitaSalud",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# CONFIGURACIÓN
# ======================
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

WGER_BASE = "https://wger.de/api/v2"

# ======================
# TRADUCCIONES
# ======================
TEXTS = {
    "es": {
        "nav_chat": "💬 Chat con el Coach",
        "nav_food": "🍽️ Registrar Comida",
        "nav_exercise": "💪 Registrar Ejercicio",
        "nav_library": "📚 Biblioteca",
        "nav_progress": "📊 Mi Progreso",
        "nav_profile": "👤 Mi Perfil",
        "edit_profile": "✏️ Editar perfil",
        "logout": "Cerrar sesión",
        "hello": "Hola",
        "sex": "Sexo",
        "goal": "Objetivo",
        "weight": "Peso",
        "experience": "Experiencia",
        "chat_title": "💬 Chat con tu Coach",
        "chat_help": "¿en qué te ayudo hoy?",
        "chat_placeholder": "Escribe tu mensaje aquí...",
        "food_title": "🍽️ Registrar Comida",
        "food_caption": "Escribe lo que comiste, sube una foto o ambas. Puedes estimar las calorías automáticamente.",
        "exercise_title": "💪 Registrar Ejercicio",
        "library_title": "📚 Biblioteca de ejercicios",
        "library_caption": "Explora ejercicios con imágenes e instrucciones. Fuentes: wger.de",
        "progress_title": "📊 Mi Progreso",
        "profile_title": "👤 Mi Perfil",
        "search_exercise": "🔍 Buscar ejercicio",
        "category": "Categoría",
        "register_exercise": "✅ Registrar este ejercicio",
        "save_profile": "Guardar perfil",
        "login": "Iniciar sesión",
        "register": "Crear cuenta",
        "email": "Email",
        "password": "Contraseña",
        "confirm_password": "Confirmar contraseña",
        "no_account": "¿No tienes cuenta? Regístrate aquí",
        "have_account": "¿Ya tienes cuenta? Inicia sesión",
        "complete_profile": "Completa tu perfil",
        "complete_profile_info": "Ve a la sección 👤 Mi Perfil para completar tus datos.",
        "what_ate": "¿Qué comiste?",
        "observations": "Observaciones adicionales (opcional)",
        "estimate_save": "🔍 Estimar calorías y guardar",
        "save_no_estimate": "💾 Guardar sin estimar",
        "how_felt_after": "¿Cómo te sentiste después?",
        "hunger_level": "Nivel de hambre",
        "meal_type": "Tipo de comida",
        "approx_time": "Hora aproximada",
        "date": "Fecha",
        "calories": "Calorías (kcal)",
        "photo_optional": "📷 Subir foto de la comida (opcional)",
        "last_meals": "Últimas comidas registradas",
        "exercise_type": "Tipo de ejercicio",
        "duration": "Duración (minutos)",
        "intensity": "Intensidad",
        "calories_burned": "Calorías quemadas (kcal)",
        "how_felt": "¿Cómo te sentiste?",
        "notes": "Notas (opcional)",
        "last_exercises": "Últimos ejercicios",
        "update_list": "🔄 Actualizar lista",
        "no_exercises": "No se encontraron ejercicios. Intenta otra categoría o escribe otro nombre.",
        "showing": "Mostrando",
        "exercises_word": "ejercicios",
        "current_weight": "Peso actual",
        "meals_today": "Comidas hoy",
        "exercises_today": "Ejercicios hoy",
        "days": "Días",
        "consumed_today": "🔥 Consumidas hoy",
        "burned_today": "💪 Quemadas hoy",
        "balance": "Balance",
        "new_weight": "➕ Registrar nuevo peso",
        "save_weight": "Guardar peso",
        "weight_evolution": "Evolución del peso",
        "weight_hint": "Registra tu peso al menos dos veces para ver la evolución.",
        "library_hint": "💡 Puedes ver imágenes e instrucciones detalladas de los ejercicios en la sección **📚 Biblioteca**.",
        "download_recipe": "📄 Descargar última receta / recomendación",
    },
    "en": {
        "nav_chat": "💬 Chat with Coach",
        "nav_food": "🍽️ Log Meal",
        "nav_exercise": "💪 Log Exercise",
        "nav_library": "📚 Library",
        "nav_progress": "📊 My Progress",
        "nav_profile": "👤 My Profile",
        "edit_profile": "✏️ Edit profile",
        "logout": "Log out",
        "hello": "Hello",
        "sex": "Sex",
        "goal": "Goal",
        "weight": "Weight",
        "experience": "Experience",
        "chat_title": "💬 Chat with your Coach",
        "chat_help": "how can I help you today?",
        "chat_placeholder": "Type your message here...",
        "food_title": "🍽️ Log Meal",
        "food_caption": "Write what you ate, upload a photo, or both. You can estimate calories automatically.",
        "exercise_title": "💪 Log Exercise",
        "library_title": "📚 Exercise Library",
        "library_caption": "Browse exercises with images and instructions. Source: wger.de",
        "progress_title": "📊 My Progress",
        "profile_title": "👤 My Profile",
        "search_exercise": "🔍 Search exercise",
        "category": "Category",
        "register_exercise": "✅ Log this exercise",
        "save_profile": "Save profile",
        "login": "Log in",
        "register": "Create account",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm password",
        "no_account": "Don't have an account? Sign up here",
        "have_account": "Already have an account? Log in",
        "complete_profile": "Complete your profile",
        "complete_profile_info": "Go to 👤 My Profile to complete your details.",
        "what_ate": "What did you eat?",
        "observations": "Additional notes (optional)",
        "estimate_save": "🔍 Estimate calories and save",
        "save_no_estimate": "💾 Save without estimating",
        "how_felt_after": "How did you feel afterwards?",
        "hunger_level": "Hunger level",
        "meal_type": "Meal type",
        "approx_time": "Approximate time",
        "date": "Date",
        "calories": "Calories (kcal)",
        "photo_optional": "📷 Upload meal photo (optional)",
        "last_meals": "Recent meals",
        "exercise_type": "Exercise type",
        "duration": "Duration (minutes)",
        "intensity": "Intensity",
        "calories_burned": "Calories burned (kcal)",
        "how_felt": "How did you feel?",
        "notes": "Notes (optional)",
        "last_exercises": "Recent exercises",
        "update_list": "🔄 Refresh list",
        "no_exercises": "No exercises found. Try another category or different search terms.",
        "showing": "Showing",
        "exercises_word": "exercises",
        "current_weight": "Current weight",
        "meals_today": "Meals today",
        "exercises_today": "Exercises today",
        "days": "Days",
        "consumed_today": "🔥 Consumed today",
        "burned_today": "💪 Burned today",
        "balance": "Balance",
        "new_weight": "➕ Log new weight",
        "save_weight": "Save weight",
        "weight_evolution": "Weight progress",
        "weight_hint": "Log your weight at least twice to see the chart.",
        "library_hint": "💡 You can see images and detailed instructions in the **📚 Library** section.",
        "download_recipe": "📄 Download last recipe / recommendation",
    },
}


def t(key: str) -> str:
    return TEXTS.get(st.session_state.get("lang", "es"), TEXTS["es"]).get(key, key)


# ======================
# FUNCIONES DE DATOS
# ======================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def register_user(email: str, password: str):
    try:
        password_hash = hash_password(password)
        supabase.table("users").insert(
            {"email": email.lower().strip(), "password_hash": password_hash}
        ).execute()
        return True, "Cuenta creada exitosamente"
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, "Este email ya está registrado"
        return False, f"Error al crear cuenta: {str(e)}"


def login_user(email: str, password: str):
    try:
        result = (
            supabase.table("users")
            .select("id, password_hash")
            .eq("email", email.lower().strip())
            .execute()
        )
        if not result.data:
            return False, "Email o contraseña incorrectos", None
        user = result.data[0]
        if check_password(password, user["password_hash"]):
            return True, "Inicio de sesión exitoso", user["id"]
        return False, "Email o contraseña incorrectos", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def get_user_profile(user_id: int):
    try:
        result = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if not result.data:
            return None
        row = result.data[0]
        return {
            "nombre": row.get("nombre"),
            "sexo": row.get("sexo"),
            "edad": row.get("edad"),
            "peso": row.get("peso"),
            "altura": row.get("altura"),
            "objetivo": row.get("objetivo"),
            "nivel_actividad": row.get("nivel_actividad"),
            "experiencia": row.get("experiencia"),
            "lugar_entrenamiento": row.get("lugar_entrenamiento"),
            "restricciones": row.get("restricciones") or [],
            "alergias": row.get("alergias") or "",
            "limitaciones": row.get("limitaciones") or "",
            "fecha_inicio": row.get("fecha_inicio"),
        }
    except Exception:
        return None


def save_user_profile(user_id: int, profile: dict):
    data = {
        "user_id": user_id,
        "nombre": profile.get("nombre"),
        "sexo": profile.get("sexo"),
        "edad": profile.get("edad"),
        "peso": profile.get("peso"),
        "altura": profile.get("altura"),
        "objetivo": profile.get("objetivo"),
        "nivel_actividad": profile.get("nivel_actividad"),
        "experiencia": profile.get("experiencia"),
        "lugar_entrenamiento": profile.get("lugar_entrenamiento"),
        "restricciones": profile.get("restricciones", []),
        "alergias": profile.get("alergias", ""),
        "limitaciones": profile.get("limitaciones", ""),
        "fecha_inicio": profile.get("fecha_inicio"),
    }
    existing = supabase.table("profiles").select("user_id").eq("user_id", user_id).execute()
    if existing.data:
        supabase.table("profiles").update(data).eq("user_id", user_id).execute()
    else:
        supabase.table("profiles").insert(data).execute()


def load_user_meals(user_id: int):
    try:
        result = (
            supabase.table("meals")
            .select("*")
            .eq("user_id", user_id)
            .order("id", desc=True)
            .limit(50)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def save_meal(user_id: int, meal: dict):
    supabase.table("meals").insert(
        {
            "user_id": user_id,
            "fecha": meal["fecha"],
            "tipo": meal["tipo"],
            "hora": meal["hora"],
            "descripcion": meal["descripcion"],
            "calorias": meal.get("calorias"),
            "sensacion": meal.get("sensacion"),
            "hambre": meal.get("hambre"),
            "notas": meal.get("notas", ""),
        }
    ).execute()


def load_user_exercises(user_id: int):
    try:
        result = (
            supabase.table("exercises")
            .select("*")
            .eq("user_id", user_id)
            .order("id", desc=True)
            .limit(50)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def save_exercise(user_id: int, exercise: dict):
    notas = exercise.get("notas", "")
    if exercise.get("calorias_quemadas"):
        notas = f"Calorías quemadas: {exercise['calorias_quemadas']} kcal. {notas}".strip()
    supabase.table("exercises").insert(
        {
            "user_id": user_id,
            "fecha": exercise["fecha"],
            "tipo": exercise["tipo"],
            "duracion": exercise["duracion"],
            "intensidad": exercise["intensidad"],
            "sensacion": exercise.get("sensacion"),
            "notas": notas,
        }
    ).execute()


def load_weight_log(user_id: int):
    try:
        result = (
            supabase.table("weight_log")
            .select("*")
            .eq("user_id", user_id)
            .order("id")
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def save_weight(user_id: int, peso: float, fecha: str = None):
    if fecha is None:
        fecha = str(date.today())
    supabase.table("weight_log").insert(
        {"user_id": user_id, "fecha": fecha, "peso": peso}
    ).execute()


# ======================
# WGER
# ======================
@st.cache_data(ttl=3600)
def get_wger_categories():
    try:
        r = requests.get(f"{WGER_BASE}/exercisecategory/", timeout=10)
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=3600)
def get_wger_exercises(category_id=None, limit=24, offset=0):
    try:
        params = {"limit": limit, "offset": offset}
        if category_id:
            params["category"] = category_id
        r = requests.get(f"{WGER_BASE}/exerciseinfo/", params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"count": 0, "results": []}


def clean_html(text: str) -> str:
    if not text:
        return ""
    try:
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ").strip()
    except Exception:
        return re.sub(r"<[^>]+>", "", text).strip()


def get_exercise_display(ex: dict) -> dict:
    name = "Ejercicio"
    description = ""
    translations = ex.get("translations") or []
    preferred = None
    for tr in translations:
        if tr.get("language") in [4, "4"]:
            preferred = tr
            break
    if not preferred:
        for tr in translations:
            if tr.get("language") in [2, "2"]:
                preferred = tr
                break
    if not preferred and translations:
        preferred = translations[0]
    if preferred:
        name = preferred.get("name") or name
        description = clean_html(
            preferred.get("description") or preferred.get("description_source") or ""
        )
    image_url = None
    images = ex.get("images") or []
    for img in images:
        if img.get("is_main"):
            thumbs = img.get("thumbnails") or {}
            image_url = thumbs.get("medium") or thumbs.get("small") or img.get("image")
            break
    if not image_url and images:
        img = images[0]
        thumbs = img.get("thumbnails") or {}
        image_url = thumbs.get("medium") or thumbs.get("small") or img.get("image")
    category = (ex.get("category") or {}).get("name", "")
    equipment = [e.get("name") for e in (ex.get("equipment") or []) if e.get("name")]
    return {
        "id": ex.get("id"),
        "name": name,
        "description": description[:400] + ("..." if len(description) > 400 else ""),
        "image_url": image_url,
        "category": category,
        "equipment": ", ".join(equipment) if equipment else "Peso corporal",
    }


# ======================
# CALORÍAS
# ======================
def estimar_calorias(descripcion: str) -> int:
    try:
        prompt = f"""Eres un nutricionista experto. Estima de forma realista las calorías totales de esta comida:
"{descripcion}"
Responde ÚNICAMENTE con un número entero (ejemplo: 450).
No escribas texto adicional, solo el número.
Si no puedes estimar, responde 0."""
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=20,
        )
        texto = response.choices[0].message.content.strip()
        numeros = re.findall(r"\d+", texto)
        return int(numeros[0]) if numeros else 0
    except Exception:
        return 0


def estimar_calorias_ejercicio(tipo: str, duracion: int, intensidad: str) -> int:
    try:
        prompt = f"""Estima de forma realista las calorías quemadas en este ejercicio:
Tipo: {tipo}
Duración: {duracion} minutos
Intensidad: {intensidad}
Responde ÚNICAMENTE con un número entero (ejemplo: 180).
Solo el número, nada más."""
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=20,
        )
        texto = response.choices[0].message.content.strip()
        numeros = re.findall(r"\d+", texto)
        return int(numeros[0]) if numeros else 0
    except Exception:
        return 0


# ======================
# ESTADO
# ======================
defaults = {
    "user_id": None,
    "user_email": None,
    "profile": None,
    "messages": [],
    "meals": [],
    "exercises": [],
    "weight_log": [],
    "current_page": "Chat",
    "last_recipe": None,
    "auth_mode": "login",
    "lang": "es",
    "lib_offset": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ======================
# COACH
# ======================
def get_coach_response(user_input: str, profile: dict, chat_history: list, user_id: int) -> str:
    perfil_texto = f"""
Nombre: {profile.get('nombre', 'Usuario')}
Sexo: {profile.get('sexo', 'No especificado')}
Edad: {profile.get('edad', 'No especificada')}
Peso: {profile.get('peso', 'No especificado')} kg
Altura: {profile.get('altura', 'No especificada')} cm
Objetivo: {profile.get('objetivo', 'Mejorar hábitos')}
Nivel de actividad: {profile.get('nivel_actividad', 'No especificado')}
Experiencia con ejercicio: {profile.get('experiencia', 'Principiante')}
Prefiere entrenar en: {profile.get('lugar_entrenamiento', 'Casa')}
Condiciones de salud: {', '.join(profile.get('restricciones', ['Ninguna']))}
Alergias o alimentos que no come: {profile.get('alergias', 'Ninguna')}
Limitaciones físicas: {profile.get('limitaciones', 'Ninguna')}
"""
    if st.session_state.lang == "en":
        lang_instruction = "You speak in clear, natural English."
        role_line = "You are VitaSalud, a professional, friendly, motivating and proactive nutrition and exercise coach."
    else:
        lang_instruction = "Hablas en español latinoamericano de forma clara y cercana."
        role_line = "Eres VitaSalud, un coach de nutrición y ejercicio profesional, amable, motivador y proactivo."

    system_prompt = f"""{role_line}
{lang_instruction}

Tu ÚNICO ámbito de conocimiento es: nutrición, alimentación, ejercicio, hábitos saludables, peso y bienestar físico.
If the user asks about any other topic, politely say you only help with nutrition, exercise and healthy habits.

INFORMACIÓN DEL USUARIO:
{perfil_texto}

### REGLAS IMPORTANTES:
1. Usuarios sedentarios o principiantes: NUNCA empieces con ejercicios de impacto el primer día. La primera semana debe ser muy suave.
2. Al recomendar ejercicios: usa nombres claros, indica series/tiempo y recuerda la Biblioteca de ejercicios.
3. Feedback de ejercicios: pregunta antes y después.
4. Feedback de comidas: pregunta cómo se sintió después de comer.
5. Sé proactivo y prioriza la seguridad.

Responde siempre como el coach de VitaSalud."""

    messages_for_api = [{"role": "system", "content": str(system_prompt)}]
    for msg in chat_history[-10:]:
        role = str(msg.get("role", "user"))
        content = msg.get("content", "")
        if content is None:
            content = ""
        messages_for_api.append({"role": role, "content": str(content)})
    messages_for_api.append({"role": "user", "content": str(user_input or "")})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=1000,
        )
        respuesta = response.choices[0].message.content
        if respuesta is None:
            respuesta = "No pude generar una respuesta. Intenta de nuevo."

        texto = str(user_input or "").lower()
        comida_keywords = [
            "desayuné", "desayune", "almorcé", "almorce", "cené", "cene",
            "comí", "comi", "me comí", "tomé", "tome",
        ]
        if any(k in texto for k in comida_keywords):
            tipo = "Otro"
            if "desayun" in texto:
                tipo = "Desayuno"
            elif "almorz" in texto:
                tipo = "Almuerzo"
            elif "cen" in texto:
                tipo = "Cena"
            calorias_est = estimar_calorias(str(user_input))
            meal = {
                "fecha": str(date.today()),
                "tipo": tipo,
                "hora": datetime.now().strftime("%H:%M"),
                "descripcion": str(user_input),
                "calorias": calorias_est if calorias_est > 0 else None,
                "sensacion": "Bien",
                "hambre": "Normal",
                "notas": "Registrado automáticamente desde el chat",
            }
            save_meal(user_id, meal)
            st.session_state.meals = load_user_meals(user_id)

        ejercicio_keywords = [
            "caminé", "camine", "corrí", "corri", "entrené", "entrene",
            "hice ejercicio", "hice una rutina", "hice yoga", "hice caminata",
        ]
        if any(k in texto for k in ejercicio_keywords):
            exercise = {
                "fecha": str(date.today()),
                "tipo": "Otro",
                "duracion": 20,
                "intensidad": "Suave",
                "sensacion": "Bien",
                "notas": f"Registrado automáticamente: {user_input}",
                "calorias_quemadas": 100,
            }
            save_exercise(user_id, exercise)
            st.session_state.exercises = load_user_exercises(user_id)

        return str(respuesta)
    except Exception as e:
        return f"Lo siento, tuve un problema al conectar con la IA. Error: {str(e)}"


# ======================
# LOGIN
# ======================
if st.session_state.user_id is None:
    st.markdown(
        '<div style="text-align:center; font-size:2.4rem; font-weight:700; color:#2E7D32;">🌱 VitaSalud</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center; color:#555; margin-bottom:1.5rem;">Tu asistente personal de nutrición y ejercicio</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_mode == "login":
            st.subheader(t("login"))
            with st.form("login_form"):
                email = st.text_input(t("email"), placeholder="tu@email.com")
                password = st.text_input(t("password"), type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.error("Por favor completa todos los campos")
                    else:
                        success, msg, user_id = login_user(email, password)
                        if success:
                            st.session_state.user_id = user_id
                            st.session_state.user_email = email.lower().strip()
                            st.session_state.profile = get_user_profile(user_id)
                            st.session_state.meals = load_user_meals(user_id)
                            st.session_state.exercises = load_user_exercises(user_id)
                            st.session_state.weight_log = load_weight_log(user_id)
                            st.session_state.messages = []
                            st.session_state.current_page = "Chat"
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            st.markdown("---")
            if st.button(t("no_account"), use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
        else:
            st.subheader(t("register"))
            with st.form("register_form"):
                email = st.text_input(t("email"), placeholder="tu@email.com")
                password = st.text_input(t("password"), type="password")
                password2 = st.text_input(t("confirm_password"), type="password")
                submitted = st.form_submit_button(t("register"), use_container_width=True)
                if submitted:
                    if not email or not password or not password2:
                        st.error("Por favor completa todos los campos")
                    elif password != password2:
                        st.error("Las contraseñas no coinciden")
                    elif len(password) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                    else:
                        success, msg = register_user(email, password)
                        if success:
                            st.success(msg + ". Ahora puedes iniciar sesión.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(msg)
            st.markdown("---")
            if st.button(t("have_account"), use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
    st.stop()

# ======================
# APP PRINCIPAL
# ======================
user_id = st.session_state.user_id

with st.sidebar:
    st.markdown("## 🌱 VitaSalud")
    st.caption(f"Sesión: {st.session_state.user_email}")
    st.divider()

    lang_choice = st.selectbox(
        "🌐 Idioma / Language",
        options=["Español", "English"],
        index=0 if st.session_state.lang == "es" else 1,
    )
    new_lang = "es" if lang_choice == "Español" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()
    st.divider()

    if st.session_state.profile:
        profile = st.session_state.profile
        st.markdown(f"### {t('hello')}, **{profile.get('nombre', '')}** 👋")
        st.caption(f"{t('goal')}: {profile.get('objetivo', '-')}")
        st.caption(f"{t('weight')}: {profile.get('peso', '-')} kg")
    else:
        st.info(t("complete_profile_info"))

    st.divider()

    pages = {
        "Chat": t("nav_chat"),
        "Comida": t("nav_food"),
        "Ejercicio": t("nav_exercise"),
        "Biblioteca": t("nav_library"),
        "Progreso": t("nav_progress"),
        "Perfil": t("nav_profile"),
    }
    selected = st.radio(
        "Navegación",
        list(pages.keys()),
        format_func=lambda x: pages[x],
        index=list(pages.keys()).index(st.session_state.current_page)
        if st.session_state.current_page in pages
        else 0,
        label_visibility="collapsed",
    )
    st.session_state.current_page = selected

    st.divider()
    if st.button(t("logout"), use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ======================
# CONTENIDO
# ======================
page = st.session_state.current_page
profile = st.session_state.profile

# ----- PERFIL -----
if page == "Perfil":
    st.markdown(f"### {t('profile_title')}")

    p = profile or {}
    with st.form("profile_form"):
        nombre = st.text_input("¿Cómo te llamas?", value=p.get("nombre") or "", placeholder="Ej: Carlos")
        sexo = st.selectbox(
            t("sex"),
            ["Masculino", "Femenino", "Otro"],
            index=["Masculino", "Femenino", "Otro"].index(p["sexo"])
            if p.get("sexo") in ["Masculino", "Femenino", "Otro"]
            else 0,
        )
        edad = st.number_input("Edad", min_value=18, max_value=90, value=int(p.get("edad") or 25))
        peso = st.number_input(
            "Peso actual (kg)",
            min_value=40.0,
            max_value=250.0,
            value=float(p.get("peso") or 85.0),
            step=0.1,
        )
        altura = st.number_input(
            "Altura (cm)", min_value=140, max_value=220, value=int(p.get("altura") or 170)
        )
        objetivo = st.selectbox(
            "Objetivo principal",
            ["Bajar de peso", "Mantener peso", "Ganar músculo", "Mejorar hábitos generales"],
            index=["Bajar de peso", "Mantener peso", "Ganar músculo", "Mejorar hábitos generales"].index(
                p["objetivo"]
            )
            if p.get("objetivo")
            in ["Bajar de peso", "Mantener peso", "Ganar músculo", "Mejorar hábitos generales"]
            else 0,
        )
        nivel_actividad = st.selectbox(
            "Nivel de actividad actual",
            [
                "Sedentario (poco o nada de ejercicio)",
                "Ligero (1-2 días por semana)",
                "Moderado (3-4 días por semana)",
                "Activo (5+ días por semana)",
            ],
            index=[
                "Sedentario (poco o nada de ejercicio)",
                "Ligero (1-2 días por semana)",
                "Moderado (3-4 días por semana)",
                "Activo (5+ días por semana)",
            ].index(p["nivel_actividad"])
            if p.get("nivel_actividad")
            in [
                "Sedentario (poco o nada de ejercicio)",
                "Ligero (1-2 días por semana)",
                "Moderado (3-4 días por semana)",
                "Activo (5+ días por semana)",
            ]
            else 0,
        )
        experiencia = st.selectbox(
            "Experiencia con el ejercicio",
            ["Principiante", "Intermedio", "Avanzado"],
            index=["Principiante", "Intermedio", "Avanzado"].index(p["experiencia"])
            if p.get("experiencia") in ["Principiante", "Intermedio", "Avanzado"]
            else 0,
        )
        lugar_entrenamiento = st.selectbox(
            "¿Dónde prefieres entrenar?",
            ["Casa", "Gimnasio", "Ambos"],
            index=["Casa", "Gimnasio", "Ambos"].index(p["lugar_entrenamiento"])
            if p.get("lugar_entrenamiento") in ["Casa", "Gimnasio", "Ambos"]
            else 0,
        )
        restricciones = st.multiselect(
            "Condiciones de salud / Restricciones",
            [
                "Ninguna",
                "Diabetes / prediabetes",
                "Hipertensión",
                "Sin gluten",
                "Sin lactosa",
                "Vegetariano",
                "Vegano",
            ],
            default=p.get("restricciones") or ["Ninguna"],
        )
        alergias = st.text_area(
            "Alergias o alimentos que NO comes",
            value=p.get("alergias") or "",
            placeholder="Ej: maní, mariscos...",
        )
        limitaciones = st.text_area(
            "Afecciones o limitaciones físicas",
            value=p.get("limitaciones") or "",
            placeholder="Ej: escoliosis...",
        )
        submitted = st.form_submit_button(t("save_profile"), use_container_width=True)
        if submitted:
            if not nombre or not nombre.strip():
                st.error("Por favor escribe tu nombre.")
            elif edad < 18:
                st.error("Debes tener al menos 18 años para usar VitaSalud.")
            else:
                new_profile = {
                    "nombre": nombre.strip(),
                    "sexo": sexo,
                    "edad": edad,
                    "peso": peso,
                    "altura": altura,
                    "objetivo": objetivo,
                    "nivel_actividad": nivel_actividad,
                    "experiencia": experiencia,
                    "lugar_entrenamiento": lugar_entrenamiento,
                    "restricciones": restricciones,
                    "alergias": alergias.strip() if alergias else "",
                    "limitaciones": limitaciones.strip() if limitaciones else "",
                    "fecha_inicio": p.get("fecha_inicio") or str(date.today()),
                }
                save_user_profile(user_id, new_profile)
                save_weight(user_id, peso)
                st.session_state.profile = new_profile
                st.session_state.weight_log = load_weight_log(user_id)
                st.success("¡Perfil guardado!")
                st.rerun()

# Si no hay perfil, solo permitir Perfil
elif profile is None:
    st.markdown(
        '<div style="text-align:center; font-size:2.4rem; font-weight:700; color:#2E7D32;">🌱 VitaSalud</div>',
        unsafe_allow_html=True,
    )
    st.info(t("complete_profile_info"))
    st.session_state.current_page = "Perfil"
    st.rerun()

# ----- CHAT -----
elif page == "Chat":
    st.markdown(f"### {t('chat_title')}")
    st.caption(f"{t('hello')} {profile['nombre']}, {t('chat_help')}")

    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        content = message.get("content")
        if content is None:
            continue
        content = str(content).strip()
        if not content:
            continue
        with st.chat_message(role):
            st.markdown(content)

    prompt = st.chat_input(t("chat_placeholder"))
    if prompt is not None:
        prompt = str(prompt).strip()
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    response = get_coach_response(
                        prompt, profile, st.session_state.messages, user_id
                    )
                    response = str(response) if response is not None else "No pude generar una respuesta."
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

            prompt_text = prompt.lower()
            response_text = response.lower()
            food_keywords = [
                "comida", "comer", "almuerzo", "cena", "desayuno", "receta",
                "ingredientes", "dieta", "recipe", "breakfast", "lunch", "dinner",
            ]
            if any(w in prompt_text for w in food_keywords) or any(
                w in response_text
                for w in ["receta", "desayuno", "almuerzo", "cena", "recipe", "breakfast", "lunch", "dinner"]
            ):
                st.session_state.last_recipe = response
            if any(
                w in response_text
                for w in [
                    "ejercicio", "rutina", "sentadilla", "caminata", "estiramiento",
                    "movilidad", "exercise", "workout", "routine",
                ]
            ):
                st.info(t("library_hint"))
            st.rerun()

    if st.session_state.last_recipe:
        st.divider()
        st.download_button(
            label=t("download_recipe"),
            data=str(st.session_state.last_recipe),
            file_name=f"receta_vitasalud_{date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ----- COMIDA -----
elif page == "Comida":
    st.markdown(f"### {t('food_title')}")
    st.caption(t("food_caption"))

    with st.form("meal_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            meal_type = st.selectbox(
                t("meal_type"), ["Desayuno", "Almuerzo", "Cena", "Snack / Merienda", "Otro"]
            )
            meal_time = st.time_input(t("approx_time"), value=datetime.now().time())
        with col2:
            meal_date = st.date_input(t("date"), value=date.today())
            calorias = st.number_input(t("calories"), min_value=0, max_value=3000, value=0, step=10)
        description = st.text_area(t("what_ate"), placeholder="Ej: 1 pechuga de pollo + ensalada")
        foto = st.file_uploader(t("photo_optional"), type=["jpg", "jpeg", "png"])
        observaciones = st.text_area(t("observations"))
        col3, col4 = st.columns(2)
        with col3:
            feeling = st.select_slider(
                t("how_felt_after"),
                options=["Muy mal", "Mal", "Regular", "Bien", "Muy bien"],
                value="Bien",
            )
        with col4:
            hunger_level = st.select_slider(
                t("hunger_level"),
                options=["Muy lleno", "Satisfecho", "Normal", "Todavía con hambre", "Muy hambriento"],
                value="Satisfecho",
            )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            estimar_y_guardar = st.form_submit_button(t("estimate_save"), use_container_width=True)
        with col_btn2:
            guardar_normal = st.form_submit_button(t("save_no_estimate"), use_container_width=True)

        if estimar_y_guardar or guardar_normal:
            if not description and not foto:
                st.warning("Por favor escribe qué comiste o sube una foto.")
            else:
                texto_completo = description.strip() if description else "Comida con foto"
                if observaciones:
                    texto_completo += f" | {observaciones.strip()}"
                calorias_final = calorias
                if estimar_y_guardar and calorias == 0:
                    with st.spinner("Estimando calorías..."):
                        calorias_final = estimar_calorias(texto_completo)
                meal = {
                    "fecha": str(meal_date),
                    "tipo": meal_type,
                    "hora": str(meal_time)[:5],
                    "descripcion": description.strip() if description else "Comida con foto",
                    "calorias": calorias_final if calorias_final > 0 else None,
                    "sensacion": feeling,
                    "hambre": hunger_level,
                    "notas": observaciones.strip() if observaciones else ("Foto subida" if foto else ""),
                }
                save_meal(user_id, meal)
                st.session_state.meals = load_user_meals(user_id)
                if calorias_final > 0:
                    st.success(f"✅ Comida registrada · **≈ {calorias_final} kcal**")
                else:
                    st.success("✅ Comida registrada")

    if st.session_state.meals:
        st.markdown(f"#### {t('last_meals')}")
        for meal in st.session_state.meals[:10]:
            cal = meal.get("calorias")
            cal_txt = f" · **{cal} kcal**" if cal else ""
            st.markdown(f"**{meal['fecha']} · {meal['tipo']}** ({meal.get('hora', '')}){cal_txt}")
            st.write(meal["descripcion"])
            st.caption(f"Sensación: {meal.get('sensacion')} | Hambre: {meal.get('hambre')}")
            if meal.get("notas"):
                st.caption(f"Notas: {meal['notas']}")
            st.divider()

# ----- EJERCICIO -----
elif page == "Ejercicio":
    st.markdown(f"### {t('exercise_title')}")
    with st.form("exercise_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            exercise_type = st.selectbox(
                t("exercise_type"),
                [
                    "Caminata",
                    "Movilidad / Estiramientos",
                    "Rutina en casa",
                    "Gimnasio",
                    "Cardio suave",
                    "Yoga",
                    "Otro",
                ],
            )
            duration = st.number_input(t("duration"), min_value=5, max_value=180, value=20)
        with col2:
            exercise_date = st.date_input(t("date"), value=date.today(), key="ex_date")
            intensity = st.select_slider(
                t("intensity"),
                options=["Muy suave", "Suave", "Moderada", "Intensa", "Muy intensa"],
                value="Suave",
            )
        calorias_quemadas = st.number_input(
            t("calories_burned"), min_value=0, max_value=1500, value=0, step=10
        )
        how_felt = st.select_slider(
            t("how_felt"),
            options=["Muy mal / dolor", "Incómodo", "Regular", "Bien", "Excelente"],
            value="Bien",
        )
        notes = st.text_area(t("notes"))
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            estimar_ej = st.form_submit_button(t("estimate_save"), use_container_width=True)
        with col_b2:
            guardar_ej = st.form_submit_button(t("save_no_estimate"), use_container_width=True)

        if estimar_ej or guardar_ej:
            calorias_final = calorias_quemadas
            if estimar_ej and calorias_quemadas == 0:
                with st.spinner("Estimando calorías quemadas..."):
                    calorias_final = estimar_calorias_ejercicio(
                        exercise_type, duration, intensity
                    )
            exercise = {
                "fecha": str(exercise_date),
                "tipo": exercise_type,
                "duracion": duration,
                "intensidad": intensity,
                "sensacion": how_felt,
                "notas": notes.strip() if notes else "",
                "calorias_quemadas": calorias_final if calorias_final > 0 else None,
            }
            save_exercise(user_id, exercise)
            st.session_state.exercises = load_user_exercises(user_id)
            if calorias_final > 0:
                st.success(f"✅ Ejercicio registrado · **≈ {calorias_final} kcal quemadas**")
            else:
                st.success("✅ Ejercicio registrado")

    if st.session_state.exercises:
        st.markdown(f"#### {t('last_exercises')}")
        for ex in st.session_state.exercises[:10]:
            st.markdown(f"**{ex['fecha']} · {ex['tipo']}** ({ex['duracion']} min)")
            st.write(f"Intensidad: {ex['intensidad']} | Sensación: {ex.get('sensacion')}")
            if ex.get("notas"):
                st.caption(ex["notas"])
            st.divider()

# ----- BIBLIOTECA -----
elif page == "Biblioteca":
    st.markdown(f"### {t('library_title')}")
    st.caption(t("library_caption"))

    categories = get_wger_categories()
    cat_options = {"Todas": None}
    for c in categories:
        cat_options[c["name"]] = c["id"]

    search_term = st.text_input(t("search_exercise"), placeholder="sentadilla, arm circles...")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        selected_cat_name = st.selectbox(t("category"), list(cat_options.keys()))
    with col_f2:
        if st.button(t("update_list"), use_container_width=True):
            st.cache_data.clear()
            st.session_state.lib_offset = 0
            st.rerun()

    category_id = cat_options[selected_cat_name]
    with st.spinner("Cargando ejercicios..."):
        data = get_wger_exercises(
            category_id=category_id, limit=40, offset=st.session_state.lib_offset
        )

    results = data.get("results", [])
    total = data.get("count", 0)

    if search_term and search_term.strip():
        def normalize(text):
            text = text.lower()
            return "".join(
                c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
            )

        term = normalize(search_term.strip())
        filtered = []
        for ex in results:
            display = get_exercise_display(ex)
            if term in normalize(display["name"]) or term in normalize(display["description"]):
                filtered.append(ex)
        results = filtered

    if not results:
        st.warning(t("no_exercises"))
    else:
        st.caption(f"{t('showing')} {len(results)} {t('exercises_word')}")
        cols = st.columns(2)
        for i, ex in enumerate(results):
            display = get_exercise_display(ex)
            with cols[i % 2]:
                with st.container():
                    if display["image_url"]:
                        st.image(display["image_url"], use_container_width=True)
                    st.markdown(f"**{display['name']}**")
                    st.caption(f"{display['category']} · {display['equipment']}")
                    if display["description"]:
                        st.write(
                            display["description"][:220]
                            + ("..." if len(display["description"]) > 220 else "")
                        )
                    if st.button(
                        t("register_exercise"),
                        key=f"reg_{display['id']}_{i}",
                        use_container_width=True,
                    ):
                        exercise = {
                            "fecha": str(date.today()),
                            "tipo": display["name"][:50],
                            "duracion": 15,
                            "intensidad": "Suave",
                            "sensacion": "Bien",
                            "notas": f"Desde biblioteca. {display['equipment']}",
                            "calorias_quemadas": None,
                        }
                        save_exercise(user_id, exercise)
                        st.session_state.exercises = load_user_exercises(user_id)
                        st.success(f"Registrado: {display['name']}")
                    st.divider()

        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p1:
            if st.session_state.lib_offset > 0 and not (search_term and search_term.strip()):
                if st.button("← Anterior"):
                    st.session_state.lib_offset = max(0, st.session_state.lib_offset - 12)
                    st.rerun()
        with col_p3:
            if st.session_state.lib_offset + 12 < total and not (
                search_term and search_term.strip()
            ):
                if st.button("Siguiente →"):
                    st.session_state.lib_offset += 12
                    st.rerun()

# ----- PROGRESO -----
elif page == "Progreso":
    st.markdown(f"### {t('progress_title')}")
    hoy = str(date.today())
    calorias_consumidas = sum(
        [m.get("calorias") or 0 for m in st.session_state.meals if str(m.get("fecha")) == hoy]
    )
    calorias_quemadas = 0
    for ex in st.session_state.exercises:
        if str(ex.get("fecha")) == hoy and ex.get("notas"):
            match = re.search(r"Calorías quemadas: (\d+)", ex.get("notas", ""))
            if match:
                calorias_quemadas += int(match.group(1))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("current_weight"), f"{profile['peso']} kg")
    with col2:
        st.metric(
            t("meals_today"),
            len([m for m in st.session_state.meals if str(m.get("fecha")) == hoy]),
        )
    with col3:
        st.metric(
            t("exercises_today"),
            len([e for e in st.session_state.exercises if str(e.get("fecha")) == hoy]),
        )
    with col4:
        try:
            inicio = datetime.strptime(str(profile["fecha_inicio"]), "%Y-%m-%d").date()
            dias = (date.today() - inicio).days
            st.metric(t("days"), max(dias, 0))
        except Exception:
            st.metric(t("days"), 0)

    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(t("consumed_today"), f"{calorias_consumidas} kcal")
    with col_b:
        st.metric(t("burned_today"), f"{calorias_quemadas} kcal")
    with col_c:
        st.metric(t("balance"), f"{calorias_consumidas - calorias_quemadas} kcal")

    st.divider()
    with st.expander(t("new_weight")):
        new_weight = st.number_input(
            "Peso (kg)",
            min_value=40.0,
            max_value=250.0,
            value=float(profile["peso"]),
            step=0.1,
        )
        if st.button(t("save_weight")):
            save_weight(user_id, new_weight)
            st.session_state.profile["peso"] = new_weight
            save_user_profile(user_id, st.session_state.profile)
            st.session_state.weight_log = load_weight_log(user_id)
            st.success("Peso actualizado")
            st.rerun()

    if len(st.session_state.weight_log) > 1:
        st.markdown(f"#### {t('weight_evolution')}")
        try:
            df_weight = pd.DataFrame(st.session_state.weight_log)
            df_weight["fecha"] = pd.to_datetime(df_weight["fecha"])
            st.line_chart(df_weight.set_index("fecha")["peso"])
        except Exception:
            st.info("No se pudo generar el gráfico.")
    else:
        st.info(t("weight_hint"))

st.divider()
st.caption("VitaSalud · Versión MVP · DeepSeek AI + Supabase + wger")
st.caption(
    "⚠️ Esta herramienta no sustituye el consejo de un médico o nutricionista profesional. Solo para mayores de 18 años."
)
