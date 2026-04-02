import streamlit as st
import json
import os

st.title("🔧 DIAGNÓSTICO - Lexicon")
st.write("Si ves esto, Streamlit está funcionando ✅")

# 1. Verificar que estamos en la carpeta correcta
st.write(f"📁 Carpeta actual: {os.getcwd()}")

# 2. Listar archivos en 'datos/'
st.write("📂 Archivos en datos/:")
try:
    archivos = os.listdir("datos")
    for arch in archivos:
        st.write(f"  - {arch}")
except Exception as e:
    st.error(f"❌ No se pudo listar datos/: {e}")

# 3. Intentar cargar el JSON
st.write("🔍 Intentando cargar: datos/genesis_01_05.json")
try:
    with open("datos/genesis_01_05.json", "r", encoding="utf-8") as f:
        datos = json.load(f)
    st.success(f"✅ JSON cargado: {len(datos)} versículos")
    st.write(f"📖 Primero: {datos[0]['referencia']}")
    st.write(f"📖 Último: {datos[-1]['referencia']}")
except FileNotFoundError:
    st.error("❌ FileNotFoundError: El archivo no existe en esa ruta")
except json.JSONDecodeError as e:
    st.error(f"❌ JSONDecodeError: {e}")
except Exception as e:
    st.error(f"❌ Error inesperado: {type(e).__name__}: {e}")

# 4. Mostrar selector simple
st.sidebar.header("🧪 Prueba de Selector")
libro = st.sidebar.selectbox("Libro", ["Génesis", "Éxodo"])
cap = st.sidebar.selectbox("Capítulos", ["1-5", "6-10"])
st.sidebar.info(f"Seleccionaste: {libro} {cap}")
st.write("✅ Si ves el selector en la barra lateral, Streamlit UI funciona")