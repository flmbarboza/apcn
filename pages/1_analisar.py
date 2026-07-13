import streamlit as st
import io
import re
import zipfile
import xml.etree.ElementTree as ET

# Importa funções de utils
import sys
sys.path.append('.')
from utils.extractor import extrair_texto_docx, avaliar_projeto

st.set_page_config(
    page_title="Analisar Projeto",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Analisar Projeto")

st.markdown("""
Faça upload do arquivo **.docx** do seu projeto de doutorado para análise automática.
""")

uploaded_file = st.file_uploader("📎 Escolha o arquivo .docx", type=["docx"])

if uploaded_file:
    try:
        with st.spinner("🔍 Processando o arquivo..."):
            texto = extrair_texto_docx(uploaded_file.getvalue())
        
        if not texto.strip():
            st.warning("⚠️ O arquivo parece estar vazio ou não contém texto legível.")
            st.stop()
        
        # Preview
        with st.expander("📄 Preview do texto extraído"):
            st.text(texto[:1500] + ("..." if len(texto) > 1500 else ""))
        
        st.subheader("📋 Análise do Projeto")
        
        avaliacao = avaliar_projeto(texto)
        
        # Exibe resultados por seção
        for secao, itens in avaliacao.items():
            with st.expander(f"🔍 {secao}", expanded=True):
                for item in itens:
                    if item.startswith("✅"):
                        st.success(item)
                    elif item.startswith("❌"):
                        st.error(item)
                    elif item.startswith("ℹ️"):
                        st.info(item)
                    else:
                        st.warning(item)
        
        # Resumo
        st.subheader("📊 Resumo de Conformidade")
        
        itens_ok = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("✅"))
        itens_warn = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("⚠️"))
        itens_fail = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("❌"))
        itens_info = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("ℹ️"))
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Atendidos", itens_ok)
        col2.metric("⚠️ Atenção", itens_warn)
        col3.metric("❌ Pendentes", itens_fail)
        col4.metric("ℹ️ Informativos", itens_info)
        
        # Recomendação
        if itens_fail == 0 and itens_warn <= 2:
            st.success("🎉 O projeto atende aos principais requisitos quantitativos!")
        elif itens_fail == 0 and itens_warn <= 5:
            st.info("📌 O projeto atende aos requisitos críticos, mas revise os itens com ⚠️.")
        else:
            st.warning("📌 Revise os itens com ⚠️ e ❌ antes da submissão.")
            
    except Exception as e:
        st.error(f"❌ Erro ao processar: {str(e)}")
        st.info("Certifique-se de que o arquivo é um .docx válido.")

else:
    st.info("👆 Aguardando o upload do arquivo...")
