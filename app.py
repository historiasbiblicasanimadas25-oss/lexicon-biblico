import streamlit as st
import json
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
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

# Cargar datos
@st.cache_data
def cargar_datos():
    try:
        with open('genesis1.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        return []

datos = cargar_datos()

# 🔥 FUNCIÓN DE IA CORREGIDA CON NUEVO ENDPOINT 🔥
def obtener_sugerencia_ia(texto_hebreo):
    """Traducción con fallback entre múltiples modelos de Hugging Face"""
    if not HF_TOKEN:
        return "⚠️ Configura tu token en .env"
    
    # Lista de modelos a intentar (en orden de preferencia)
    modelos = [
        {
            "id": "facebook/nllb-200-distilled-600M",
            "tipo": "nllb",
            "url": "https://router.huggingface.co/hf-inference/models/facebook/nllb-200-distilled-600M"
        },
        {
            "id": "Helsinki-NLP/opus-mt-he-es",
            "tipo": "helsinki",
            "url": "https://router.huggingface.co/hf-inference/models/Helsinki-NLP/opus-mt-he-es"
        }
    ]
    
    for modelo in modelos:
        try:
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }
            
            if modelo["tipo"] == "nllb":
                # NLLB requiere formato especial con códigos de idioma
                payload = {
                    "inputs": texto_hebreo,
                    "parameters": {
                        "max_new_tokens": 250,
                        "src_lang": "heb_Hebr",
                        "tgt_lang": "spa_Latn"
                    }
                }
            else:
                # Helsinki-NLP formato estándar
                payload = {
                    "inputs": texto_hebreo,
                    "parameters": {"max_length": 500}
                }
            
            response = requests.post(
                modelo["url"], 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parsear respuesta según formato
                if isinstance(result, list) and len(result) > 0:
                    texto = result[0].get('translation_text') or result[0].get('generated_text')
                    if texto:
                        return texto
                elif isinstance(result, dict):
                    texto = result.get('translation_text') or result.get('generated_text')
                    if texto:
                        return texto
                # Si es string directo (algunos modelos)
                elif isinstance(result, str):
                    return result
                    
            elif response.status_code == 404:
                # Este modelo no está disponible, intentar el siguiente
                continue
            elif response.status_code == 503:
                return "⏳ El modelo está cargando. Intenta de nuevo en 30 segundos."
            elif response.status_code == 429:
                return "⚠️ Límite de peticiones excedido. Espera 1 hora."
            else:
                continue  # Intentar siguiente modelo
                
        except Exception:
            continue  # Intentar siguiente modelo
    
    # Si ningún modelo funcionó
    return "⚠️ Ningún modelo de IA disponible ahora. Intenta más tarde o traduce manualmente."

# Barra lateral
st.sidebar.header("📚 Instrucciones")
st.sidebar.info("""
1. **Lee** el texto hebreo
2. **Haz clic** en las palabras para analizar
3. **Usa 🤖 IA** para sugerencia de traducción
4. **Edita** manualmente la traducción
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

# Mostrar versículos
if datos:
    for verso in datos:
        st.subheader(verso['referencia'])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 25px; 
                        border-radius: 10px; margin: 10px 0;
                        font-size: 32px; direction: rtl; text-align: right;
                        line-height: 2.5; font-family: "SBL Hebrew", serif;'>
                {verso['hebreo']}
            </div>
            """, unsafe_allow_html=True)
            
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
                            'datos': palabra
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
                st.markdown(f"### 📊 Análisis: {sel['datos']['texto']}")
                
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
    st.warning("⚠️ No se cargaron datos. Verifica genesis1.json")

st.markdown("---")
st.markdown("*Proyecto educativo sin fines de lucro*")