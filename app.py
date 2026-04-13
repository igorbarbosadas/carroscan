import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import zipfile
import io
import unicodedata
from PIL import ImageEnhance

st.set_page_config(page_title="CarroScan", layout="centered")

st.title("🚗 CarroScan - Renomeador de PDFs")

uploaded_files = st.file_uploader(
    "Envie os PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

# 🔤 Normalizar texto (remove acento e padroniza)
def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

# 🧠 Melhorar imagem pro OCR
def melhorar_imagem(img):
    img = img.convert("L")  # escala de cinza
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    return img

# 🔍 Identifica página da placa
def eh_pagina_placa(texto):
    texto = normalizar(texto.upper())
    return "RELATORIO DE CARREGAMENTO" in texto and "PLACA" in texto

# 🔍 Identifica página da data
def eh_pagina_data(texto):
    texto = normalizar(texto.upper())
    return "MAPA DE CARREGAMENTO" in texto

# 🔎 Extrair placa
def extrair_placa(texto):
    texto = normalizar(texto.upper())
    
    match = re.search(r'PLACA[:\s]*([A-Z0-9]{7})', texto)
    
    if not match:
        # fallback: qualquer padrão de placa
        match = re.search(r'\b[A-Z]{3}[0-9][A-Z0-9][0-9]{2}\b|\b[A-Z]{3}[0-9]{4}\b', texto)
    
    return match.group(1) if match else "SEM_PLACA"

# 📅 Extrair data (IMPRESSO POR)
def extrair_data(texto):
    texto = normalizar(texto.upper()).replace("0", "O")
    
    match = re.search(r'IMPRESSO.*?(\d{2})/(\d{2})/\d{4}', texto)
    
    if match:
        dia = match.group(1)
        mes = match.group(2)
        return f"{dia}.{mes}"
    
    return "SEM_DATA"

# 🚀 Processar PDF
def processar_pdf(file_bytes):
    imagens = convert_from_bytes(file_bytes)
    
    placa = "SEM_PLACA"
    data = "SEM_DATA"
    
    for img in imagens:
        img = melhorar_imagem(img)
        
        texto = pytesseract.image_to_string(img, config='--psm 6')
        
        # DEBUG (se precisar ver o que OCR lê)
        # st.text(texto[:500])
        
        if placa == "SEM_PLACA" and eh_pagina_placa(texto):
            placa = extrair_placa(texto)
        
        if data == "SEM_DATA" and eh_pagina_data(texto):
            data = extrair_data(texto)
    
    return placa, data

# 🧾 Execução
if uploaded_files:
    resultados = []
    
    for file in uploaded_files:
        file_bytes = file.read()
        placa, data = processar_pdf(file_bytes)
        
        novo_nome = f"{placa} - {data}.pdf"
        
        resultados.append((file.name, novo_nome, file_bytes))
        
        st.success(f"{file.name} → {novo_nome}")
    
    # 🔹 Se for 1 arquivo
    if len(resultados) == 1:
        _, novo_nome, file_bytes = resultados[0]
        
        st.download_button(
            "📥 Baixar arquivo renomeado",
            data=file_bytes,
            file_name=novo_nome,
            mime="application/pdf"
        )
    
    # 🔹 Se for vários → ZIP
    else:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for _, novo_nome, file_bytes in resultados:
                zip_file.writestr(novo_nome, file_bytes)
        
        st.download_button(
            "📦 Baixar todos em ZIP",
            data=zip_buffer.getvalue(),
            file_name="arquivos_renomeados.zip",
            mime="application/zip"
        )
