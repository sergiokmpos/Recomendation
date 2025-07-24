import streamlit as st
import pandas as pd
import os
from math import sqrt

ARQUIVO_AVALIACOES = 'avaliacoes.csv'

# Função para carregar base do CSV
def carregar_avaliacoes():
    if not os.path.exists(ARQUIVO_AVALIACOES):
        return pd.DataFrame(columns=["usuario", "carro", "nota"])
    return pd.read_csv(ARQUIVO_AVALIACOES)

# Função para salvar base no CSV
def salvar_avaliacoes(df):
    df.to_csv(ARQUIVO_AVALIACOES, index=False)

# Transforma o DataFrame em dicionário de usuários
def df_para_dict_usuarios(df):
    base = {}
    for _, row in df.iterrows():
        base.setdefault(row["usuario"], {})
        base[row["usuario"]][row["carro"]] = float(row["nota"])
    return base

# Transforma o DataFrame em dicionário de itens
def df_para_dict_itens(df):
    base = {}
    for _, row in df.iterrows():
        base.setdefault(row["carro"], {})
        base[row["carro"]][row["usuario"]] = float(row["nota"])
    return base

# Similaridade Euclidiana
def euclidiana(base, item1, item2):
    si = {usuario for usuario in base[item1] if usuario in base[item2]}
    if not si: return 0
    soma = sum(pow(base[item1][usuario] - base[item2][usuario], 2) for usuario in si)
    return 1 / (1 + sqrt(soma))

# Itens similares (carros parecidos)
def calculaItensSimilares(base):
    result = {}
    for item in base:
        similares = []
        for outro in base:
            if item == outro: continue
            sim = euclidiana(base, item, outro)
            similares.append((sim, outro))
        similares.sort(reverse=True)
        result[item] = similares[:10]
    return result

# Recomendações por itens semelhantes
def getRecomendacoesItens(baseUsuario, similaridadeItens, usuario):
    notasUsuario = baseUsuario.get(usuario, {})
    notas = {}
    totalSimilaridade = {}
    for (item, nota) in notasUsuario.items():
        for (similaridade, item2) in similaridadeItens.get(item, []):
            if item2 in notasUsuario: continue
            notas.setdefault(item2, 0)
            notas[item2] += similaridade * nota
            totalSimilaridade.setdefault(item2, 0)
            totalSimilaridade[item2] += similaridade
    rankings = [(score / totalSimilaridade[item], item) for item, score in notas.items()]
    rankings.sort(reverse=True)
    return rankings

# ========== Streamlit App ==========
st.set_page_config(page_title="🔧 Recomendador de Carros", layout="wide")
st.title("🚗 Sistema de Recomendação de Carros")

# Carrega ou inicializa base
df = carregar_avaliacoes()
usuarios = sorted(df["usuario"].unique()) if not df.empty else []
carros = sorted(df["carro"].unique()) if not df.empty else []

abas = st.tabs(["📊 Recomendar Carros", "📝 Editar Avaliações", "📁 Ver Base de Dados"])

# === ABA 1: Recomendações ===
with abas[0]:
    st.subheader("📊 Recomendação Personalizada")
    if usuarios:
        usuario_selecionado = st.selectbox("Selecione o usuário para recomendação:", usuarios)
        base_usuario = df_para_dict_usuarios(df)
        base_item = df_para_dict_itens(df)
        similaridadeItens = calculaItensSimilares(base_item)
        recomendacoes = getRecomendacoesItens(base_usuario, similaridadeItens, usuario_selecionado)

        if recomendacoes:
            st.markdown("### 🔍 Recomendações para " + usuario_selecionado)
            for nota, carro in recomendacoes[:10]:
                st.write(f"**{carro}** — nota estimada: {nota:.2f}")
        else:
            st.info("Sem recomendações suficientes para este usuário.")
    else:
        st.warning("A base de dados ainda está vazia.")

# === ABA 2: Editar Avaliações ===
with abas[1]:
    st.subheader("📝 Inserir ou Editar Avaliação")
    usuario = st.text_input("Nome do usuário")
    carro = st.text_input("Nome do carro")
    nota = st.slider("Nota (0 a 5)", 0.0, 5.0, 3.0, 0.5)

    if st.button("Salvar Avaliação"):
        if usuario and carro:
            nova = pd.DataFrame([[usuario, carro, nota]], columns=["usuario", "carro", "nota"])
            df = df[~((df["usuario"] == usuario) & (df["carro"] == carro))]  # remove duplicada
            df = pd.concat([df, nova], ignore_index=True)
            salvar_avaliacoes(df)
            st.success(f"Avaliação salva: {usuario} avaliou '{carro}' com nota {nota}")
        else:
            st.error("Preencha todos os campos.")

# === ABA 3: Visualização de Dados ===
with abas[2]:
    st.subheader("📁 Base de Avaliações")
    st.dataframe(df)
    st.download_button("📥 Baixar CSV", data=df.to_csv(index=False), file_name="avaliacoes.csv", mime="text/csv")
