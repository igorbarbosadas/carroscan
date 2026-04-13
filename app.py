import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import zipfile
import io

st.set_page_config(page_title="CarroScan", layout="centered")

st.title("🚗 CarroScan - Renomeador de PDFs")

uploaded_files = st.file_uploader(
    "Envie os PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

# 🔍 Identifica página da placa
def eh_pagina_placa(texto):
    texto = texto.upper()
    return "RELATÓRIO DE CARREGAMENTO" in texto and "PLACA" in texto

# 🔍 Identifica página da data
def eh_pagina_data(texto):
    texto = texto.upper()
    return "MAPA DE CARREGAMENTO" in texto

# 🔎 Extrair placa
def extrair_placa(texto):
    match = re.search(r'PLACA[:\s]*([A-Z0-9]{7})', texto.upper())
    return match.group(1) if match else "SEM_PLACA"

# 📅 Extrair data (IMPRESSO POR)
def extrair_data(texto):
    texto = texto.upper().replace("0", "O")
    
    match = re.search(r'IMPRESSO POR.*?(\d{2})/(\d{2})/\d{4}', texto)
    
    if match:
        dia = match.group(1)
        mes = match.group(2)
        return f"{dia}.{mes}"
    
    return "SEM_DATA"

# 🧠 Processar PDF
def processar_pdf(file_bytes):
    imagens = convert_from_bytes(file_bytes)
    
    placa = "SEM_PLACA"
    data = "SEM_DATA"
    
    for img in imagens:
        texto = pytesseract.image_to_string(img, config='--psm 6')
        
        if placa == "SEM_PLACA" and eh_pagina_placa(texto):
            placa = extrair_placa(texto)
        
        if data == "SEM_DATA" and eh_pagina_data(texto):
            data = extrair_data(texto)
    
    return placa, data

# 🚀 Execução
if uploaded_files:
    resultados = []
    
    for file in uploaded_files:
        placa, data = processar_pdf(file.read())
        novo_nome = f"{placa} - {data}.pdf"
        
        resultados.append((file.name, novo_nome, file))
        
        st.success(f"{file.name} → {novo_nome}")
    
    # 🔹 Se for 1 arquivo → download direto
    if len(resultados) == 1:
        original = resultados[0][2]
        novo_nome = resultados[0][1]
        
        st.download_button(
            "📥 Baixar arquivo renomeado",
            data=original.getvalue(),
            file_name=novo_nome,
            mime="application/pdf"
        )
    
    # 🔹 Se for vários → ZIP
    else:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for _, novo_nome, file in resultados:
                zip_file.writestr(novo_nome, file.getvalue())
        
        st.download_button(
            "📦 Baixar todos em ZIP",
            data=zip_buffer.getvalue(),
            file_name="arquivos_renomeados.zip",
            mime="application/zip"
        )
