import streamlit as st
import docx
import io
import re
from collections import defaultdict

# --- CONFIG ---
st.set_page_config(page_title="Checagem APCN Doutorado", layout="centered")

st.title("📘 Analisador de Projeto APCN - Doutorado")
st.markdown("""
Envie o **arquivo .docx** do seu projeto de curso de doutorado (modalidade acadêmica ou profissional).
O sistema verificará rapidamente os principais **requisitos quantitativos e estruturais** exigidos pela área 27 (Administração Pública, Contábeis, Turismo) e pelo manual Sucupira.
""")

uploaded_file = st.file_uploader("📎 Escolha o arquivo .docx do projeto", type=["docx"])

# --- FUNÇÕES DE CHEGAGEM ---
def extrair_texto(docx_bytes):
    doc = docx.Document(io.BytesIO(docx_bytes))
    texto_completo = "\n".join([p.text for p in doc.paragraphs])
    return texto_completo

def checar_docentes(texto):
    resultados = []
    # Busca por indicações de docentes permanentes e colaboradores
    padrao_permanente = r"(?:permanente[s]?|docente[s]?\s+permanente[s]?)\s*[:]?\s*(\d+)"
    padrao_colaborador = r"(?:colaborador[es]?|docente[s]?\s+colaborador[es]?)\s*[:]?\s*(\d+)"
    
    # Tenta encontrar números
    perm = re.search(padrao_permanente, texto, re.IGNORECASE)
    colab = re.search(padrao_colaborador, texto, re.IGNORECASE)
    
    n_perm = int(perm.group(1)) if perm else None
    n_colab = int(colab.group(1)) if colab else 0
    
    if n_perm is None:
        resultados.append("⚠️ Número de docentes permanentes não identificado claramente.")
    else:
        if n_perm >= 12:
            resultados.append(f"✅ Docentes permanentes: {n_perm} (mínimo 12 atendido)")
        else:
            resultados.append(f"❌ Docentes permanentes: {n_perm} (mínimo 12 não atendido)")
        
        # Verifica se há colaboradores (máx 30% do total)
        total = n_perm + n_colab
        if total > 0:
            perc_colab = n_colab / total
            if perc_colab <= 0.3:
                resultados.append(f"✅ Colaboradores: {n_colab} ({perc_colab*100:.1f}% do total, ≤30%)")
            else:
                resultados.append(f"❌ Colaboradores: {n_colab} ({perc_colab*100:.1f}% do total, >30%)")
    
    # Verifica menção a 80% de experiência em orientação
    if "80%" in texto.lower() or "orientação" in texto.lower():
        if re.search(r"80\s*%", texto, re.IGNORECASE):
            resultados.append("✅ Menção a 80% de experiência em orientação identificada.")
        else:
            resultados.append("⚠️ Não foi encontrada menção explícita a 80% de experiência em orientação.")
    else:
        resultados.append("⚠️ Não foi possível verificar a experiência de orientação (80%).")
    
    return resultados

def checar_vagas(texto):
    resultados = []
    # Busca por número de vagas
    padrao_vagas = r"(?:vagas?|seleção)\s*[:]?\s*(\d+)"
    vagas = re.findall(padrao_vagas, texto, re.IGNORECASE)
    
    if vagas:
        n_vagas = int(vagas[0])
        if 10 <= n_vagas <= 30:
            resultados.append(f"✅ Número de vagas anual: {n_vagas} (faixa típica)")
        else:
            resultados.append(f"⚠️ Número de vagas: {n_vagas} (verificar adequação)")
    else:
        resultados.append("⚠️ Número de vagas não identificado claramente.")
    
    # Verifica relação orientador/orientando
    if "orientando" in texto.lower() or "orientador" in texto.lower():
        if re.search(r"[678]\s+orient", texto, re.IGNORECASE):
            resultados.append("✅ Menção a limite de orientandos (6-8) identificada.")
        else:
            resultados.append("⚠️ Limite de orientandos não claramente explicitado.")
    
    return resultados

def checar_carga_horaria(texto):
    resultados = []
    # Busca por carga horária em disciplinas
    padrao_ch = r"(\d+)\s*hora[s]?\s*(?:em|de)?\s*disciplinas?"
    ch = re.search(padrao_ch, texto, re.IGNORECASE)
    
    if ch:
        horas = int(ch.group(1))
        if horas >= 540:
            resultados.append(f"✅ Carga horária em disciplinas: {horas}h (mínimo 540h para doutorado)")
        else:
            resultados.append(f"❌ Carga horária em disciplinas: {horas}h (abaixo de 540h)")
    else:
        # Tenta encontrar menção a créditos
        padrao_cred = r"(\d+)\s*créditos?\s*(?:em)?\s*disciplinas?"
        cred = re.search(padrao_cred, texto, re.IGNORECASE)
        if cred:
            creditos = int(cred.group(1))
            if creditos >= 36:  # 540h / 15h por crédito (padrão)
                resultados.append(f"✅ Créditos em disciplinas: {creditos} (equivale a ≥540h)")
            else:
                resultados.append(f"⚠️ Créditos em disciplinas: {creditos} (verificar equivalência para 540h)")
        else:
            resultados.append("⚠️ Carga horária ou créditos em disciplinas não identificados.")
    
    return resultados

def checar_producao(texto):
    resultados = []
    # Busca por indicadores de produção qualificada
    if "produção" in texto.lower() or "artigos" in texto.lower():
        if re.search(r"MB|B|R|F", texto, re.IGNORECASE):
            resultados.append("✅ Referência a estratos de produção (MB/B/R/F) encontrada.")
        else:
            resultados.append("⚠️ Não foram encontrados estratos de produção (MB/B/R/F).")
    else:
        resultados.append("⚠️ Seção de produção não identificada.")
    
    # Verifica menção a pontuação média
    if "média" in texto.lower() and "3" in texto:
        resultados.append("✅ Menção a pontuação média de produção (≥3) identificada.")
    else:
        resultados.append("⚠️ Não foi encontrada menção clara à pontuação média de produção (≥3).")
    
    return resultados

def checar_infraestrutura(texto):
    resultados = []
    itens = [
        ("biblioteca", "biblioteca"),
        ("laboratório", "laboratório"),
        ("internet", "internet/acesso"),
        ("salas", "salas para docentes/alunos"),
        ("coordenação", "sala de coordenação/secretaria"),
    ]
    
    for padrao, label in itens:
        if re.search(padrao, texto, re.IGNORECASE):
            resultados.append(f"✅ {label.capitalize()} mencionada")
        else:
            resultados.append(f"⚠️ {label.capitalize()} não explicitamente mencionada")
    
    return resultados

def checar_ead(texto):
    resultados = []
    if "distância" in texto.lower() or "ead" in texto.lower():
        if "30%" in texto.lower() or "presencial" in texto.lower():
            resultados.append("✅ Menção a 30% de presencial para EaD identificada.")
        else:
            resultados.append("⚠️ Proposta EaD sem menção a 30% de carga presencial.")
    return resultados

def avaliar_projeto(texto):
    avaliacao = {}
    
    # Seções principais
    avaliacao["Docentes"] = checar_docentes(texto)
    avaliacao["Vagas"] = checar_vagas(texto)
    avaliacao["Carga Horária"] = checar_carga_horaria(texto)
    avaliacao["Produção"] = checar_producao(texto)
    avaliacao["Infraestrutura"] = checar_infraestrutura(texto)
    avaliacao["EaD"] = checar_ead(texto)
    
    return avaliacao

# --- PROCESSAMENTO ---
if uploaded_file:
    try:
        texto = extrair_texto(uploaded_file.getvalue())
        
        # Mostra um preview
        with st.expander("📄 Preview do texto extraído (primeiros 1000 caracteres)"):
            st.text(texto[:1000] + "...")
        
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
                    else:
                        st.warning(item)
        
        # Resumo de conformidade
        st.subheader("📊 Resumo de Conformidade")
        total_itens = sum(len(itens) for itens in avaliacao.values())
        itens_ok = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("✅"))
        itens_warn = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("⚠️"))
        itens_fail = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("❌"))
        
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Atendidos", itens_ok)
        col2.metric("⚠️ Atenção", itens_warn)
        col3.metric("❌ Pendentes", itens_fail)
        
        if itens_fail == 0 and itens_warn <= 2:
            st.success("🎉 O projeto atende aos principais requisitos quantitativos!")
        else:
            st.info("📌 Recomenda-se revisar os itens com ⚠️ e ❌ antes da submissão.")
            
        st.caption("""
        **Nota:** Esta é uma análise automatizada baseada em palavras-chave e padrões comuns.
        Não substitui a leitura completa do documento orientador nem a avaliação da CAPES.
        Consulte os documentos oficiais para todos os detalhes.
        """)
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        st.info("Certifique-se de que o arquivo é um .docx válido.")
else:
    st.info("Aguardando o upload do arquivo .docx...")

# --- RODAPÉ ---
st.markdown("---")
st.markdown("""
**Referências:** 
- Documento Orientador de APCN - Área 27 (Administração Pública, Contábeis, Turismo)
- Manual do Usuário - APCN Plataforma Sucupira
""")
