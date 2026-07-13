import streamlit as st

st.set_page_config(
    page_title="Analisador APCN - Doutorado",
    page_icon="📘",
    layout="centered"
)

st.title("📘 Analisador de Projeto APCN - Doutorado")

st.markdown("""
## Bem-vindo!

Este aplicativo ajuda a verificar se seu projeto de curso de doutorado atende aos 
principais requisitos da área 27 (Administração Pública, Contábeis, Turismo).

### Como usar:
1. Clique em **📄 Analisar Projeto** no menu lateral
2. Faça upload do arquivo **.docx** do seu projeto
3. Aguarde a análise automática
4. Revise os resultados e pendências

### Documentos base:
- Documento Orientador de APCN - Área 27
- Manual do Usuário - APCN Plataforma Sucupira

### Requisitos verificados:
- 👨‍🏫 Corpo docente (permanentes e colaboradores)
- 🎯 Vagas e capacidade de orientação
- 📚 Carga horária mínima (540h)
- 📝 Produção intelectual
- 🏛️ Infraestrutura
- 🔄 Autoavaliação
- 📜 Regimento
- 🔗 Interdisciplinaridade
- 🌎 Assimetrias regionais
""")

st.info("👈 Selecione uma página no menu lateral para começar")
