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
client = InferenceClient(HF_TOKEN) if HF_TOKEN else None

st.set_page_config(page_title="Lexicon Bíblico", layout="wide")
st.title("📖 Lexicon - Traductor Bíblico Hebreo")
st.markdown("*Herramienta gratuita con análisis morfológico y IA*")
st.markdown("---")

# Inicializar estado
if 'palabra_seleccionada' not in st.session_state:
    st.session_state.palabra_seleccionada = None
if 'libro_seleccionado' not in st.session_state:
    st.session_state.libro_seleccionado = "Génesis"
if 'capitulo_seleccionado' not in st.session_state:
    st.session_state.capitulo_seleccionado = "1-5"

# Cargar datos
@st.cache_data
def cargar_datos(libro, capitulo_rango):
    """Carga los datos bíblicos desde la carpeta datos/"""
    try:
        # Convertir rango "1-5" a "01_05" para el nombre del archivo
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
    """Obtiene sugerencia de traducción desde Hugging Face API"""
    if not HF_TOKEN:
        return "⚠️ Configura tu token en .env"
    
    try:
        API_URL = "https://router.huggingface.co/hf-inference/models/Helsinki-NLP/opus-mt-he-es"
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": texto_hebreo,
            "parameters": {"max_length": 500}
        }
        
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
            
    except requests.exceptions.Timeout:
        return "⏱️ Timeout: La IA está tardando mucho. Intenta de nuevo."
    except requests.exceptions.ConnectionError:
        return "🔌 Error de conexión. Verifica tu internet."
    except Exception as e:
        return f"⚠️ Error: {str(e)[:150]}..."

# Barra lateral - Selector de Libros y Capítulos
st.sidebar.header("📚 Navegación")

# Selector de Libro
libros_disponibles = {
    "Génesis": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40", "41-45", "46-50"],
    "Éxodo": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40"],
    "Levítico": ["1-5", "6-10", "11-15", "16-20", "21-27"],
    "Números": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-36"],
    "Deuteronomio": ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-34"]
}

libro_seleccionado = st.sidebar.selectbox(
    "📖 Libro:",
    options=list(libros_disponibles.keys()),
    index=0
)

capitulos_disponibles = libros_disponibles[libro_seleccionado]
capitulo_seleccionado = st.sidebar.selectbox(
    "📖 Capítulos:",
    options=capitulos_disponibles,
    index=0
)

# Guardar selección en session_state
st.session_state.libro_seleccionado = libro_seleccionado
st.session_state.capitulo_seleccionado = capitulo_seleccionado

st.sidebar.markdown("---")
st.sidebar.info("""
1. **Selecciona** libro y capítulos
2. **Haz clic** en las palabras para analizar
3. **Usa 🤖 IA** para sugerencia de traducción
4. **Escribe** tu traducción
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**🔑 Leyenda de colores:**")
st.sidebar.markdown("- 🔵 Verbo")
st.sidebar.markdown("- 🟢 Sustantivo")
st.sidebar.markdown("- 🟡 Partícula/Preposición")
st.sidebar.markdown("- 🟣 Conjunción")

# Función para determinar color
def get_color(tipo):
    if "Verbo" in tipo:
        return "🔵"
    elif "Sustantivo" in tipo:
        return "🟢"
    elif "Partícula" in tipo or "Preposición" in tipo:
        return "🟡"
    elif "Conjunción" in tipo:
        return "🟣"
    else:
        return "⚪"

# Cargar datos del libro y capítulo seleccionado
datos = cargar_datos(libro_seleccionado, capitulo_seleccionado)

# Mostrar versículos
if datos:
    st.subheader(f"{libro_seleccionado} {capitulo_seleccionado}")
    
    for verso in datos:
        st.markdown(f"### {verso['referencia']}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Mostrar texto hebreo
            st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 25px; 
                        border-radius: 10px; margin: 10px 0;
                        font-size: 32px; direction: rtl; text-align: right;
                        line-height: 2.5; font-family: "SBL Hebrew", serif;'>
                {verso['hebreo']}
            </div>
            """, unsafe_allow_html=True)
            
            # Botones para analizar cada palabra
            st.markdown("**🔍 Haz clic en una palabra para analizar:**")
            cols = st.columns(min(len(verso.get('palabras', [])), 7))
            
            for i, palabra in enumerate(verso.get('palabras', [])):
                with cols[i % 7]:
                    color = get_color(palabra['tipo'])
                    if st.button(f"{color}", key=f"btn_{verso['id']}_{i}", 
                                help=palabra['texto']):
                        st.session_state.palabra_seleccionada = {
                            'verso_id': verso['id'],
                            'palabra_idx': i,
                            'datos': palabra,
                            'referencia': verso['referencia']
                        }
        
        with col2:
            trad_key = f"trad_{verso['id']}"
            if trad_key not in st.session_state:
                st.session_state[trad_key] = verso.get('traduccion', '')
            
            if st.button("🤖 Sugerir con IA", key=f"ia_{verso['id']}", type="primary"):
                with st.spinner("🔄 Traduciendo con IA (10-30 segundos)..."):
                    sugerencia = obtener_sugerencia_ia(verso['hebreo'])
                    st.session_state[trad_key] = sugerencia
                    st.rerun()
            
            st.text_area(
                "Tu traducción al español",
                key=trad_key,
                height=150,
                label_visibility="visible"
            )
            
            st.caption("⚠️ La IA es una sugerencia. Verifica con el análisis morfológico.")
        
        # Panel de análisis
        if st.session_state.palabra_seleccionada:
            sel = st.session_state.palabra_seleccionada
            if sel['verso_id'] == verso['id']:
                st.markdown("---")
                st.markdown(f"### 📊 Análisis: {sel['datos']['texto']} ({sel['referencia']})")
                
                col_basic1, col_basic2, col_basic3 = st.columns(3)
                
                with col_basic1:
                    st.info(f"**📝 Palabra:** {sel['datos']['texto']}")
                with col_basic2:
                    st.success(f"**🌳 Raíz:** {sel['datos']['raiz']}")
                with col_basic3:
                    st.warning(f"**🏷️ Tipo:** {sel['datos']['tipo']}")
                
                st.markdown(f"**📖 Significado:** {sel['datos']['significado']}")
                
                if 'gramatica' in sel['datos']:
                    st.markdown("---")
                    st.markdown("### 🔬 Análisis Gramatical")
                    
                    gram = sel['datos']['gramatica']
                    
                    if "Verbo" in sel['datos']['tipo']:
                        col_v1, col_v2 = st.columns(2)
                        with col_v1:
                            if 'voz' in gram:
                                st.metric("Voz", gram['voz'])
                            if 'aspecto' in gram:
                                st.metric("Aspecto", gram['aspecto'])
                            if 'persona' in gram:
                                st.metric("Persona", gram['persona'])
                        with col_v2:
                            if 'genero' in gram:
                                st.metric("Género", gram['genero'])
                            if 'numero' in gram:
                                st.metric("Número", gram['numero'])
                            if 'nota' in gram:
                                st.caption(f"📌 {gram['nota']}")
                    else:
                        for key, value in gram.items():
                            st.info(f"**{key.title()}:** {value}")
        
        st.markdown("---")
else:
    st.warning("⚠️ No hay datos disponibles para este libro/capítulo. Asegúrate de que el archivo JSON existe en la carpeta datos/")

st.markdown("---")
st.markdown("*Proyecto educativo sin fines de lucro • Texto: WLC • Morfología: ETCBC*")