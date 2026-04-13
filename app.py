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

# 🔤 Normalizar texto
def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

# 🧠 Melhorar imagem
def melhorar_imagem(img):
    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    return img

# 🔍 Identificar página correta
def eh_mapa_carregamento(texto):
    texto = normalizar(texto.upper())
    return "MAPA DE CARREGAMENTO" in texto

# 🔪 Recorte da placa
def recortar_placa(img):
    largura, altura = img.size
    return img.crop((
        0,
        int(altura * 0.15),
        int(largura * 0.6),
        int(altura * 0.35)
    ))

# 🔪 Recorte da data (rodapé)
def recortar_data(img):
    largura, altura = img.size
    return img.crop((
        0,
        int(altura * 0.75),
        largura,
        altura
    ))

# 🔎 Extrair placa
def extrair_placa_mapa(img):
    area = recortar_placa(img)
    area = melhorar_imagem(area)
    
    texto = pytesseract.image_to_string(area, config='--psm 6')
    texto = normalizar(texto.upper())
    
    match = re.search(r'\b[A-Z]{3}[0-9][A-Z0-9][0-9]{2}\b|\b[A-Z]{3}[0-9]{4}\b', texto)
    
    return match.group(0) if match else "SEM_PLACA"

# 📅 Extrair data
def extrair_data_mapa(img):
    area = recortar_data(img)
    area = melhorar_imagem(area)
    
    texto = pytesseract.image_to_string(area, config='--psm 6')
    texto = normalizar(texto.upper()).replace("0", "O")
    
    match = re.search(r'IMPRESSO.*?(\d{2})/(\d{2})/\d{4}', texto)
    
    if match:
        return f"{match.group(1)}.{match.group(2)}"
    
    return "SEM_DATA"

# 🚀 Processamento principal
def processar_pdf(file_bytes):
    imagens = convert_from_bytes(file_bytes)
    
    for img in imagens:
        texto_full = pytesseract.image_to_string(img, config='--psm 6')
        
        if eh_mapa_carregamento(texto_full):
            placa = extrair_placa_mapa(img)
            data = extrair_data_mapa(img)
            return placa, data
    
    return "SEM_PLACA", "SEM_DATA"

# 🧾 Execução
if uploaded_files:
    resultados = []
    
    for file in uploaded_files:
        file_bytes = file.read()
        placa, data = processar_pdf(file_bytes)
        
        novo_nome = f"{placa} - {data}.pdf"
        
        resultados.append((file.name, novo_nome, file_bytes))
        
        st.success(f"{file.name} → {novo_nome}")
    
    # 🔹 1 arquivo
    if len(resultados) == 1:
        _, novo_nome, file_bytes = resultados[0]
        
        st.download_button(
            "📥 Baixar arquivo renomeado",
            data=file_bytes,
            file_name=novo_nome,
            mime="application/pdf"
        )
    
    # 🔹 vários arquivos
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
