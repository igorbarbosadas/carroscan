import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
from PIL import Image

st.set_page_config(page_title="Leitor de Placas", layout="centered")

st.title("📄 Leitor de Placas de PDF")

uploaded_files = st.file_uploader(
    "Envie os PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

def extrair_placa(texto):
    match = re.search(r'Placa[:\s]*([A-Z0-9]{7})', texto)
    return match.group(1) if match else "SEM_PLACA"

def extrair_data(texto):
    match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
    return match.group(0).replace("/", "-") if match else "SEM_DATA"

def recortar_area_placa(imagem):
    largura, altura = imagem.size
    
    # 🔥 AJUSTADO PARA SEU MODELO
    # topo esquerdo onde fica "Placa"
    crop = imagem.crop((
        0,                 # esquerda
        int(altura * 0.15),  # topo
        int(largura * 0.6),  # direita
        int(altura * 0.35)   # baixo
    ))
    
    return crop

if uploaded_files:
    for file in uploaded_files:
        st.write(f"Processando: {file.name}")
        
        imagens = convert_from_bytes(file.read(), first_page=1, last_page=1)
        imagem = imagens[0]
        
        # 📍 recorta só a área da placa (muito mais preciso)
        area_placa = recortar_area_placa(imagem)
        
        texto = pytesseract.image_to_string(area_placa, lang='por')
        
        placa = extrair_placa(texto)
        
        # também pode pegar data do documento inteiro
        texto_completo = pytesseract.image_to_string(imagem, lang='por')
        data = extrair_data(texto_completo)
        
        novo_nome = f"{placa}_{data}.pdf"
        
        st.image(area_placa, caption="Área analisada (placa)", use_column_width=True)
        st.success(f"📌 Placa: {placa}")
        st.info(f"📅 Data: {data}")
        st.warning(f"📁 Novo nome: {novo_nome}")
