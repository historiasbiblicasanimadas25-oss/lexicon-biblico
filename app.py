import streamlit as st
import json
import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import requests

# Cargar variables de entorno
load_dotenv()

# Configurar cliente de IA
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

st.set_page_config(page_title="Lexicon Bíblico", layout="wide")
st.title("📖 Lexicon - Traductor Bíblico Hebreo")
st.markdown("*Herramienta gratuita con análisis morfológico y IA*")
st.markdown("---")

# Inicializar estado
if 'palabra_seleccionada' not in st.session_state:
    st.session_state.palabra_seleccionada = None

# Cargar datos
@st.cache_data
def cargar_datos(libro, capitulo_rango):
    """Carga los datos bíblicos desde la carpeta datos/"""
    try:
        partes = capitulo_rango.split('-')
        cap_inicio = partes[0].zfill(2)
        cap_fin = partes[1].zfill(2)
        nombre_archivo = f"datos/{libro.lower()}_{cap_inicio}_{cap_fin}.json"
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        return []

# Función de IA
def obtener_sugerencia_ia(texto_hebreo):
    if not HF_TOKEN:
        return "⚠️ Configura tu token en .env"
    try:
        API_URL = "https://router.huggingface.co/hf-inference/models/Helsinki-NLP/opus-mt-he-es"
        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
        payload = {"inputs": texto_hebreo, "parameters": {"max_length": 500}}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('translation_text', 'Traducción no disponible')
            elif isinstance(result, dict):
                return result.get('translation_text', result.get('generated_text', 'Traducción no disponible'))
            else:
                return "Formato de respuesta inesperado"
        elif response.status_code == 503:
            return "⏳ El modelo está cargando. Intenta de nuevo en 30 segundos."
        elif response.status_code == 429:
            return "⚠️ Límite de peticiones excedido. Espera 1 hora."
        else:
            return f"⚠️ Error HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return f"⚠️ Error: {str(e)[:150]}..."

# Barra lateral
st.sidebar.header("📚 Navegación")
libros_disponibles = {
    "Génesis": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40", "41-45", "46-50"],
    "Éxodo": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40"],
    "Levítico": ["1-5", "6-10", "11-15", "16-20", "21-27"],
    "Números": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-36"],
    "Deuteronomio": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-34"]
}

libro_seleccionado = st.sidebar.selectbox("📖 Libro:", options=list(libros_disponibles.keys()), index=0)
capitulos_disponibles = libros_disponibles[libro_seleccionado]
capitulo_seleccionado = st.sidebar.selectbox("📖 Capítulos:", options=capitulos_disponibles, index=0)

st.sidebar.markdown("---")
st.sidebar.info("1. Selecciona libro y capítulos\n2. Haz clic en palabras para analizar\n3. Usa 🤖 IA para sugerencia\n4. Escribe tu traducción")
st.sidebar.markdown("**🔑 Leyenda:** 🔵 Verbo | 🟢 Sustantivo | 🟡 Partícula | 🟣 Conjunción")

def get_color(tipo):
    if "Verbo" in tipo: return "🔵"
    elif "Sustantivo" in tipo: return "🟢"
    elif "Partícula" in tipo or "Preposición" in tipo: return "🟡"
    elif "Conjunción" in tipo: return "🟣"
    else: return "⚪"

# === LÍNEA CRÍTICA: Cargar los datos ===
datos = cargar_datos(libro_seleccionado, capitulo_seleccionado)

# Mostrar versículos
if datos:
    st.subheader(f"{libro_seleccionado} {capitulo_seleccionado}")
    for verso in datos:
        st.markdown(f"### {verso['referencia']}")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"<div style='background:#f0f2f6;padding:25px;border-radius:10px;font-size:32px;direction:rtl;text-align:right;line-height:2.5'>{verso['hebreo']}</div>", unsafe_allow_html=True)
            st.markdown("**🔍 Haz clic en una palabra:**")
            cols = st.columns(min(len(verso.get('palabras',[])), 7))
            for i, palabra in enumerate(verso.get('palabras', [])):
                with cols[i % 7]:
                    color = get_color(palabra['tipo'])
                    if st.button(f"{color}", key=f"btn_{verso['id']}_{i}", help=palabra['texto']):
                        st.session_state.palabra_seleccionada = {'verso_id': verso['id'], 'palabra_idx': i, 'datos': palabra, 'referencia': verso['referencia']}
        with col2:
            trad_key = f"trad_{verso['id']}"
            if trad_key not in st.session_state:
                st.session_state[trad_key] = verso.get('traduccion', '')
            if st.button("🤖 Sugerir con IA", key=f"ia_{verso['id']}", type="primary"):
                with st.spinner("🔄 Traduciendo..."):
                    st.session_state[trad_key] = obtener_sugerencia_ia(verso['hebreo'])
                    st.rerun()
            st.text_area("Tu traducción", key=trad_key, height=120, label_visibility="visible")
        # Panel de análisis
        if st.session_state.palabra_seleccionada and st.session_state.palabra_seleccionada['verso_id'] == verso['id']:
            sel = st.session_state.palabra_seleccionada
            st.markdown(f"### 📊 Análisis: {sel['datos']['texto']}")
            c1,c2,c3 = st.columns(3)
            with c1: st.info(f"📝 {sel['datos']['texto']}")
            with c2: st.success(f"🌳 {sel['datos']['raiz']}")
            with c3: st.warning(f"🏷️ {sel['datos']['tipo']}")
            st.markdown(f"**📖 Significado:** {sel['datos']['significado']}")
            if 'gramatica' in sel['datos']:
                st.markdown("---\n### 🔬 Gramática")
                for k,v in sel['datos']['gramatica'].items():
                    st.info(f"**{k.title()}:** {v}")
        st.markdown("---")
else:
    st.warning(f"⚠️ No hay datos para {libro_seleccionado} {capitulo_seleccionado}. Verifica que existe: `datos/{libro_seleccionado.lower()}_{capitulo_seleccionado.split('-')[0].zfill(2)}_{capitulo_seleccionado.split('-')[1].zfill(2)}.json`")

st.markdown("---\n*Proyecto educativo • Texto: WLC • Morfología: ETCBC*")