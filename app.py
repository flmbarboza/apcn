import streamlit as st
import io
import re
import subprocess
import sys
from collections import defaultdict

# Tenta instalar o python-docx automaticamente
try:
    import docx
except ImportError:
    st.warning("📦 Instalando a biblioteca python-docx...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    import docx
    st.success("✅ Biblioteca instalada com sucesso!")

# --- CONFIG ---
st.set_page_config(
    page_title="Analisador APCN - Doutorado",
    page_icon="📘",
    layout="centered"
)

st.title("📘 Analisador de Projeto APCN - Doutorado")
st.markdown("""
Envie o **arquivo .docx** do seu projeto de curso de doutorado (modalidade acadêmica ou profissional).
O sistema verificará rapidamente os principais **requisitos quantitativos e estruturais** exigidos pela área 27 (Administração Pública, Contábeis, Turismo) e pelo manual Sucupira.
""")

uploaded_file = st.file_uploader("📎 Escolha o arquivo .docx do projeto", type=["docx"])

# --- FUNÇÕES DE CHEGAGEM ---
def extrair_texto(docx_bytes):
    """Extrai texto de um arquivo .docx"""
    try:
        doc = docx.Document(io.BytesIO(docx_bytes))
        texto_completo = "\n".join([p.text for p in doc.paragraphs])
        return texto_completo
    except Exception as e:
        st.error(f"Erro ao extrair texto: {e}")
        return ""

def checar_docentes(texto):
    """Verifica requisitos do corpo docente"""
    resultados = []
    
    # Docentes permanentes (mínimo 12 para doutorado)
    padrao_permanente = r"(?:permanente[s]?|docente[s]?\s+permanente[s]?)\s*[:]?\s*(\d+)"
    padrao_colaborador = r"(?:colaborador[es]?|docente[s]?\s+colaborador[es]?)\s*[:]?\s*(\d+)"
    
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
        
        total = n_perm + n_colab
        if total > 0:
            perc_colab = n_colab / total
            if perc_colab <= 0.3:
                resultados.append(f"✅ Colaboradores: {n_colab} ({perc_colab*100:.1f}% do total, ≤30%)")
            else:
                resultados.append(f"❌ Colaboradores: {n_colab} ({perc_colab*100:.1f}% do total, >30%)")
    
    # Verifica experiência de orientação (80%)
    if re.search(r"80\s*%", texto, re.IGNORECASE) and re.search(r"orient", texto, re.IGNORECASE):
        resultados.append("✅ Menção a 80% de experiência em orientação identificada.")
    else:
        resultados.append("⚠️ Não foi encontrada menção explícita a 80% de experiência em orientação.")
    
    # Verifica regime de dedicação (50%+1 com ≥20h)
    if re.search(r"(?:50\s*%|20\s*hora)", texto, re.IGNORECASE):
        resultados.append("✅ Menção ao regime de dedicação (≥20h para 50%+1) identificada.")
    else:
        resultados.append("⚠️ Regime de dedicação dos docentes não claramente explicitado.")
    
    return resultados

def checar_vagas(texto):
    """Verifica vagas e orientação"""
    resultados = []
    
    # Busca por número de vagas
    padrao_vagas = r"(?:vagas?|seleção)\s*[:]?\s*(\d+)"
    vagas = re.findall(padrao_vagas, texto, re.IGNORECASE)
    
    if vagas:
        n_vagas = int(vagas[0])
        if 5 <= n_vagas <= 30:
            resultados.append(f"✅ Número de vagas anual: {n_vagas} (faixa típica)")
        else:
            resultados.append(f"⚠️ Número de vagas: {n_vagas} (verificar adequação)")
    else:
        resultados.append("⚠️ Número de vagas não identificado claramente.")
    
    # Verifica relação orientador/orientando
    if re.search(r"[678]\s+orient", texto, re.IGNORECASE):
        resultados.append("✅ Menção a limite de orientandos (6-8) identificada.")
    else:
        resultados.append("⚠️ Limite de orientandos não claramente explicitado.")
    
    return resultados

def checar_carga_horaria(texto):
    """Verifica carga horária e créditos"""
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
            if creditos >= 36:
                resultados.append(f"✅ Créditos em disciplinas: {creditos} (equivale a ≥540h)")
            else:
                resultados.append(f"⚠️ Créditos em disciplinas: {creditos} (verificar equivalência para 540h)")
        else:
            resultados.append("⚠️ Carga horária ou créditos em disciplinas não identificados.")
    
    return resultados

def checar_producao(texto):
    """Verifica produção intelectual"""
    resultados = []
    
    # Verifica estratos de produção
    if re.search(r"MB|B|R|F", texto, re.IGNORECASE):
        resultados.append("✅ Referência a estratos de produção (MB/B/R/F) encontrada.")
    else:
        resultados.append("⚠️ Não foram encontrados estratos de produção (MB/B/R/F).")
    
    # Verifica pontuação média
    if re.search(r"média.*?3", texto, re.IGNORECASE):
        resultados.append("✅ Menção a pontuação média de produção (≥3) identificada.")
    else:
        resultados.append("⚠️ Não foi encontrada menção clara à pontuação média de produção (≥3).")
    
    # Verifica proporção de docentes com produção
    if re.search(r"(?:30%|40%)", texto, re.IGNORECASE):
        resultados.append("✅ Menção à proporção de docentes com produção qualificada identificada.")
    else:
        resultados.append("⚠️ Proporção de docentes com produção não explicitada.")
    
    return resultados

def checar_infraestrutura(texto):
    """Verifica infraestrutura"""
    resultados = []
    itens = [
        ("biblioteca", "Biblioteca"),
        ("laboratório", "Laboratórios"),
        ("internet|acesso", "Acesso à internet"),
        ("salas?.*docentes?", "Salas para docentes"),
        ("salas?.*alunos?", "Salas para alunos"),
        ("coordenação|secretaria", "Sala de coordenação/secretaria"),
    ]
    
    for padrao, label in itens:
        if re.search(padrao, texto, re.IGNORECASE):
            resultados.append(f"✅ {label} mencionada")
        else:
            resultados.append(f"⚠️ {label} não explicitamente mencionada")
    
    return resultados

def checar_autoavaliacao(texto):
    """Verifica política de autoavaliação"""
    resultados = []
    
    if re.search(r"autoavaliação|auto-avaliação", texto, re.IGNORECASE):
        resultados.append("✅ Política de autoavaliação mencionada.")
        if re.search(r"metodologia|procedimento", texto, re.IGNORECASE):
            resultados.append("✅ Metodologia/procedimentos de autoavaliação descritos.")
        else:
            resultados.append("⚠️ Metodologia de autoavaliação não detalhada.")
    else:
        resultados.append("⚠️ Política de autoavaliação não mencionada.")
    
    return resultados

def checar_ead(texto):
    """Verifica requisitos para EaD"""
    resultados = []
    if re.search(r"distância|ead", texto, re.IGNORECASE):
        if re.search(r"30\s*%", texto, re.IGNORECASE) or re.search(r"presencial", texto, re.IGNORECASE):
            resultados.append("✅ Menção a 30% de presencial para EaD identificada.")
        else:
            resultados.append("⚠️ Proposta EaD sem menção a 30% de carga presencial.")
    return resultados

def checar_regimento(texto):
    """Verifica menção ao regimento"""
    resultados = []
    if re.search(r"regimento|regulamento", texto, re.IGNORECASE):
        resultados.append("✅ Regimento/regulamento mencionado.")
    else:
        resultados.append("⚠️ Regimento/regulamento não mencionado.")
    return resultados

def checar_interdisciplinaridade(texto):
    """Verifica abordagem da interdisciplinaridade"""
    resultados = []
    if re.search(r"interdisciplin|multidisciplin", texto, re.IGNORECASE):
        resultados.append("✅ Abordagem interdisciplinar/multidisciplinar mencionada.")
        if re.search(r"área[s]?\s+de\s+concentração", texto, re.IGNORECASE) and re.search(r"linha[s]?\s+de\s+pesquisa", texto, re.IGNORECASE):
            resultados.append("✅ Áreas de concentração e linhas de pesquisa articuladas.")
    else:
        resultados.append("⚠️ Abordagem interdisciplinar não explicitamente mencionada.")
    return resultados

def checar_assimetrias_regionais(texto):
    """Verifica considerações sobre assimetrias regionais"""
    resultados = []
    if re.search(r"regional|assimetria|interiorização", texto, re.IGNORECASE):
        resultados.append("✅ Considerações sobre assimetrias regionais mencionadas.")
    else:
        resultados.append("ℹ️ Assimetrias regionais não mencionadas (opcional, mas valorizado).")
    return resultados

def avaliar_projeto(texto):
    """Avalia todos os aspectos do projeto"""
    avaliacao = {
        "👨‍🏫 Corpo Docente": checar_docentes(texto),
        "🎯 Vagas e Orientação": checar_vagas(texto),
        "📚 Carga Horária": checar_carga_horaria(texto),
        "📝 Produção Intelectual": checar_producao(texto),
        "🏛️ Infraestrutura": checar_infraestrutura(texto),
        "🔄 Autoavaliação": checar_autoavaliacao(texto),
        "📜 Regimento": checar_regimento(texto),
        "🔗 Interdisciplinaridade": checar_interdisciplinaridade(texto),
        "🌎 Assimetrias Regionais": checar_assimetrias_regionais(texto),
    }
    
    # Adiciona EaD se aplicável
    if re.search(r"distância|ead", texto, re.IGNORECASE):
        avaliacao["🌐 Educação a Distância"] = checar_ead(texto)
    
    return avaliacao

# --- INTERFACE PRINCIPAL ---
if uploaded_file:
    try:
        with st.spinner("🔍 Processando o arquivo..."):
            texto = extrair_texto(uploaded_file.getvalue())
        
        if not texto.strip():
            st.warning("⚠️ O arquivo parece estar vazio ou não contém texto legível.")
            st.stop()
        
        # Mostra um preview
        with st.expander("📄 Preview do texto extraído (primeiros 1000 caracteres)"):
            st.text(texto[:1000] + ("..." if len(texto) > 1000 else ""))
        
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
        
        # Resumo de conformidade
        st.subheader("📊 Resumo de Conformidade")
        total_itens = sum(len(itens) for itens in avaliacao.values())
        itens_ok = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("✅"))
        itens_warn = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("⚠️"))
        itens_fail = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("❌"))
        itens_info = sum(1 for itens in avaliacao.values() for item in itens if item.startswith("ℹ️"))
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Atendidos", itens_ok)
        col2.metric("⚠️ Atenção", itens_warn)
        col3.metric("❌ Pendentes", itens_fail)
        col4.metric("ℹ️ Informativos", itens_info)
        
        # Recomendação final
        if itens_fail == 0 and itens_warn <= 2:
            st.success("🎉 O projeto atende aos principais requisitos quantitativos!")
        elif itens_fail == 0 and itens_warn <= 5:
            st.info("📌 O projeto atende aos requisitos críticos, mas recomendamos revisar os itens com ⚠️.")
        else:
            st.warning("📌 Recomenda-se revisar os itens com ⚠️ e ❌ antes da submissão.")
            
        st.caption("""
        **Nota:** Esta é uma análise automatizada baseada em palavras-chave e padrões comuns.
        Não substitui a leitura completa do documento orientador nem a avaliação da CAPES.
        Consulte os documentos oficiais para todos os detalhes.
        """)
        
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("Certifique-se de que o arquivo é um .docx válido e não está corrompido.")

else:
    st.info("👆 Aguardando o upload do arquivo .docx...")
    
    # Mostra requisitos rápidos
    with st.expander("📌 Requisitos rápidos para Doutorado (Área 27)", expanded=False):
        st.markdown("""
        **Principais requisitos:**
        - 👨‍🏫 **Docentes permanentes:** mínimo 12
        - 👥 **Colaboradores:** máximo 30% do total
        - 🎯 **Vagas:** compatível com capacidade de orientação (6-8 orientandos por docente)
        - 📚 **Carga horária:** mínimo 540h em disciplinas
        - 📝 **Produção:** pontuação média ≥3, 40% dos docentes com pontuação ≥9
        - 🏛️ **Infraestrutura:** biblioteca, laboratórios, salas, internet
        - 🔄 **Autoavaliação:** política e metodologia definidas
        - 📜 **Regimento:** anexado à proposta
        """)

# --- RODAPÉ ---
st.markdown("---")
st.markdown("""
**Referências:** 
- [Documento Orientador de APCN - Área 27](https://www.gov.br/capes)
- [Manual do Usuário - APCN Plataforma Sucupira](https://sucupira.capes.gov.br)
""")
