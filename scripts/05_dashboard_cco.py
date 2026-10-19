# 05_dashboard_cco.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import joblib

# Raiz do projeto (pasta pai de scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="CCO - Indicadores Operacionais",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ESTILO VISUAL - TEMA CLARO CORPORATIVO
st.markdown("""
<style>
    /* Fundo Geral */
    .stApp {
        background: #FFFFFF;
        color: #2C3E50;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #F8F9FA;
        border-right: 1px solid #E9ECEF;
    }
    [data-testid="stSidebar"] * {
        color: #2C3E50;
    }

    /* Títulos */
    h1 {
        color: #4C9F70 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    h2, h3 {
        color: #2C3E50 !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
    }

    /* Cards de Métricas (KPIs) */
    [data-testid="stMetric"] {
        background: #F8F9FA;
        border-left: 4px solid #4C9F70;
        border-radius: 6px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricLabel"] {
        color: #7F8C8D !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #2C3E50 !important;
        font-size: 1.9rem !important;
        font-weight: 700 !important;
    }

    hr {
        border-color: #E9ECEF !important;
        margin: 2rem 0 !important;
    }

    /* Inputs e Selects */
    [data-testid="stMultiSelect"] label {
        color: #2C3E50 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSelectbox"] label {
        color: #2C3E50 !important;
        font-weight: 600 !important;
    }

    /* Botões */
    .stButton > button {
        background: #4C9F70;
        color: #FFFFFF;
        border: none;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        transition: background 0.15s;
    }
    .stButton > button:hover {
        background: #3B8259;
        color: #FFFFFF;
    }

    /* Formulários */
    [data-testid="stForm"] {
        background: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 1.5rem;
    }

    /* Textos de Legenda/Caption */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #7F8C8D !important;
        font-size: 0.85rem !important;
    }

    /* Alertas */
    .stAlert {
        background: #F8F9FA !important;
        border-left: 4px solid #F39C12 !important;
        color: #2C3E50 !important;
    }
</style>
""", unsafe_allow_html=True)

TEMPLATE = "plotly_white"

ARQ_ANALISES = os.path.join(BASE_DIR, "dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join(BASE_DIR, "dados_tratados", "nao_conformidades_limpas.csv")
ARQ_MODELO = os.path.join(BASE_DIR, "modelo", "modelo_cco.pkl")
ARQ_ENCODERS = os.path.join(BASE_DIR, "modelo", "encoders_cco.pkl")

# Cores unificadas (iguais às do PDF)
COR_VERDE_ESCURO = "#2E7D32"
COR_VERDE_CLARO = "#A5D6A7"
COR_AMARELO = "#F9A825"
COR_LARANJA = "#EF6C00"
COR_VERMELHO = "#C62828"
COR_TEXTO = "#2C3E50"
COR_BORDA = "#B0BEC5" # Contorno das barras brancas

FEATURES = ["filial", "classificacao", "codigo_unidade", "capitulo_nc"]
TARGET = "critica_bin"


@st.cache_data
def carregar_dados():
    df_a = pd.read_csv(ARQ_ANALISES, sep=";", encoding="utf-8", low_memory=False)
    df_a = df_a.assign(
        data_da_avaliacao=pd.to_datetime(
            df_a["data_da_avaliacao"], errors="coerce"
        )
    )
    df_n = None
    if os.path.exists(ARQ_NCS):
        df_n = pd.read_csv(ARQ_NCS, sep=";", encoding="utf-8", low_memory=False)
    return df_a, df_n


@st.cache_resource
def carregar_modelo():
    if not os.path.exists(ARQ_MODELO) or not os.path.exists(ARQ_ENCODERS):
        return None, None
    modelo = joblib.load(ARQ_MODELO)
    encoders = joblib.load(ARQ_ENCODERS)
    return modelo, encoders


def aplicar_tema(fig, altura=400):
    fig.update_layout(
        template=TEMPLATE,
        height=altura,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=COR_TEXTO, size=13),
        title_font=dict(color=COR_TEXTO, size=17),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E9ECEF')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E9ECEF')
    return fig


df_a, df_n = carregar_dados()
modelo, encoders = carregar_modelo()


st.title("CCO - Indicadores Operacionais")
st.markdown(
    f"""
    <div style="color:#7F8C8D; font-size:0.95rem; margin-bottom:1rem;">
        <b style="color:#2C3E50;">Análises:</b> {len(df_a):,} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b style="color:#2C3E50;">Não conformidades:</b> {len(df_n) if df_n is not None else 0:,}
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


st.sidebar.header("Filtros")

filiais_disponiveis = sorted(df_a["filial"].dropna().unique().tolist())
filiais_selecionadas = st.sidebar.multiselect(
    "Filial",
    options=filiais_disponiveis,
    default=filiais_disponiveis,
)

analistas_disponiveis = sorted(df_a["analista"].dropna().unique().tolist())
analistas_selecionados = st.sidebar.multiselect(
    "Analista",
    options=analistas_disponiveis,
    default=analistas_disponiveis,
)

resultados_disponiveis = sorted(df_a["resultado"].dropna().unique().tolist())
resultados_selecionados = st.sidebar.multiselect(
    "Resultado",
    options=resultados_disponiveis,
    default=resultados_disponiveis,
)

df_a_f = df_a[
    (df_a["filial"].isin(filiais_selecionadas))
    & (df_a["analista"].isin(analistas_selecionados))
    & (df_a["resultado"].isin(resultados_selecionados))
].copy()

df_n_f = None
if df_n is not None:
    df_n_f = df_n[df_n["id_analise"].isin(df_a_f["id_analise"])].copy()

st.sidebar.markdown(
    f"<div style='color:#7F8C8D; margin-top:1rem;'>Análises filtradas: "
    f"<b style='color:#2C3E50;'>{len(df_a_f):,}</b></div>",
    unsafe_allow_html=True,
)


col1, col2, col3, col4 = st.columns(4)

total_analises = len(df_a_f)
total_nc = int(df_a_f["qtd_nc"].sum())
nao_conformes = int((df_a_f["resultado"].str.lower() == "não conforme").sum())
taxa_nc = (nao_conformes / total_analises * 100) if total_analises > 0 else 0

col1.metric("Total de Análises", f"{total_analises:,}")
col2.metric("Total de NCs", f"{total_nc:,}")
col3.metric("Análises Não Conformes", f"{nao_conformes:,}")
col4.metric("Taxa de Não Conformidade", f"{taxa_nc:.2f}%")

st.divider()


# ---------- Gráfico 1: Análises e NCs por Filial ----------
st.subheader("Análises e NCs por Filial")

resumo_filial = df_a_f.groupby("filial").agg(
    total=("id_analise", "count"),
    nc=("qtd_nc", "sum"),
).reset_index()

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=resumo_filial["filial"],
    y=resumo_filial["total"],
    name="Total de análises",
    marker_color=COR_VERDE_ESCURO,
    yaxis="y1",
    text=resumo_filial["total"],
    textposition="outside",
    textfont=dict(color=COR_TEXTO, size=12),
    cliponaxis=False,
))
fig1.add_trace(go.Scatter(
    x=resumo_filial["filial"],
    y=resumo_filial["nc"],
    name="Total de NCs",
    mode="lines+markers",
    marker=dict(color=COR_VERMELHO, size=10),
    line=dict(width=3),
    yaxis="y2",
    hovertemplate="%{x}<br>NCs: %{y}<extra></extra>",
))
fig1.update_layout(
    yaxis=dict(title="Total de análises", side="left"),
    yaxis2=dict(title="NCs", overlaying="y", side="right"),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
aplicar_tema(fig1, 400)
st.plotly_chart(fig1, width="stretch", theme=None)


# ---------- Gráfico 2: Taxa de Conformidade por Filial ----------
st.subheader("Taxa de Conformidade por Filial")

resumo_conf = df_a_f.groupby("filial").agg(
    total=("id_analise", "count"),
    conformes=("resultado", lambda s: (s.str.lower() == "conforme").sum()),
).reset_index()
resumo_conf = resumo_conf.assign(
    taxa_conformidade=resumo_conf["conformes"] / resumo_conf["total"] * 100
)
resumo_conf = resumo_conf.sort_values("taxa_conformidade", ascending=False)

fig2 = px.bar(
    resumo_conf, x="filial", y="taxa_conformidade",
    color="taxa_conformidade", color_continuous_scale="Greens",
    labels={"filial": "Filial", "taxa_conformidade": "Taxa de Conformidade (%)"},
    text="taxa_conformidade",
)
fig2.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside",
    textfont=dict(color=COR_TEXTO, size=12),
    cliponaxis=False,
    marker_line_color=COR_BORDA, marker_line_width=1
)
fig2.update_layout(coloraxis_showscale=False)
aplicar_tema(fig2, 400)
st.plotly_chart(fig2, width="stretch", theme=None)


# ---------- Gráfico 3: Distribuição Mensal ----------
st.subheader("Distribuição Mensal de Análises e NCs")

resumo_mes = df_a_f.groupby("mes").agg(
    total=("id_analise", "count"),
    nc=("qtd_nc", "sum"),
).reset_index()

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=resumo_mes["mes"], y=resumo_mes["total"],
    name="Análises", marker_color=COR_VERDE_ESCURO,
    text=resumo_mes["total"],
    textposition="outside",
    textfont=dict(color=COR_TEXTO, size=12),
    cliponaxis=False,
))
fig3.add_trace(go.Bar(
    x=resumo_mes["mes"], y=resumo_mes["nc"],
    name="NCs", marker_color=COR_VERMELHO,
    text=resumo_mes["nc"],
    textposition="outside",
    textfont=dict(color=COR_TEXTO, size=12),
    cliponaxis=False,
))
fig3.update_layout(
    barmode="group",
    xaxis_title="Mês",
    yaxis_title="Quantidade",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
aplicar_tema(fig3, 400)
st.plotly_chart(fig3, width="stretch", theme=None)


# ---------- Gráfico 4: Dia da Semana ----------
st.subheader("Distribuição por Dia da Semana e Taxa de Não Conformidade")

mapa_dias = {
    "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta",
    "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo",
}

df_a_f = df_a_f.assign(dia_semana_pt=df_a_f["dia_semana"].map(mapa_dias))

resumo_dia = df_a_f.groupby("dia_semana_pt").agg(
    total=("id_analise", "count"),
    nc=("qtd_nc", "sum"),
).reset_index()
resumo_dia = resumo_dia.assign(
    taxa_nc=resumo_dia["nc"] / resumo_dia["total"] * 100,
    ordem=resumo_dia["dia_semana_pt"].map(
        {v: i for i, v in enumerate(["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])}
    ),
)
resumo_dia = resumo_dia.sort_values("ordem")

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=resumo_dia["dia_semana_pt"],
    y=resumo_dia["total"],
    name="Total de análises",
    marker_color=COR_VERDE_ESCURO,
    yaxis="y1",
    text=resumo_dia["total"],
    textposition="outside",
    textfont=dict(color=COR_TEXTO, size=12),
    cliponaxis=False,
))
fig4.add_trace(go.Scatter(
    x=resumo_dia["dia_semana_pt"],
    y=resumo_dia["taxa_nc"],
    name="Taxa de NC (%)",
    mode="lines+markers",
    marker=dict(color=COR_VERMELHO, size=8),
    line=dict(width=3),
    yaxis="y2",
    hovertemplate="%{x}<br>Taxa NC: %{y:.1f}%<extra></extra>",
))
fig4.update_layout(
    yaxis=dict(title="Total de análises", side="left"),
    yaxis2=dict(title="Taxa de NC (%)", overlaying="y", side="right"),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
aplicar_tema(fig4, 400)
st.plotly_chart(fig4, width="stretch", theme=None)


# ---------- Gráficos 5 e 6: Resultado e Classificação (lado a lado) ----------
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Distribuição por Resultado")
    resumo_resultado = df_a_f.groupby("resultado").agg(
        total=("id_analise", "count"),
    ).reset_index()

    cores_resultado = {
        "Conforme": COR_VERDE_ESCURO,
        "Conforme com Observação": COR_AMARELO,
        "Não Conforme": COR_VERMELHO,
    }

    fig5 = px.bar(
        resumo_resultado, x="resultado", y="total",
        color="resultado",
        color_discrete_map=cores_resultado,
        labels={"resultado": "Resultado", "total": "Análises"},
        text="total",
    )
    fig5.update_traces(
        textposition="outside",
        textfont=dict(color=COR_TEXTO, size=13),
        cliponaxis=False,
    )
    fig5.update_layout(showlegend=False)
    aplicar_tema(fig5, 400)
    st.plotly_chart(fig5, width="stretch", theme=None)

with col_d:
    st.subheader("Distribuição por Classificação")
    resumo_class = df_a_f.groupby("classificacao").agg(total=("id_analise", "count")).reset_index()

    ordem_class = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
    
    cores_class = {
        "Ótimo": COR_VERDE_ESCURO,
        "Bom": COR_VERDE_CLARO,
        "Regular": COR_AMARELO,
        "Ruim": COR_LARANJA,
        "Péssimo": COR_VERMELHO,
    }

    fig6 = px.pie(
        resumo_class, names="classificacao", values="total",
        color="classificacao",
        color_discrete_map=cores_class,
        category_orders={"classificacao": ordem_class},
        hole=0.4,
    )
    fig6.update_traces(
        textposition="inside",
        textinfo="value+percent",
        textfont=dict(color="#FFFFFF", size=13),
        insidetextorientation="radial",
    )
    aplicar_tema(fig6, 400)
    st.plotly_chart(fig6, width="stretch", theme=None)


# ---------- Gráfico 7: Unidades com Maior Incidência ----------
st.subheader("Unidades com Maior Incidência de NCs")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_unidade = df_n_f.groupby("codigo_unidade").agg(
        total=("codigo_nc", "count"),
    ).reset_index().sort_values("total", ascending=False).head(10)
    resumo_unidade = resumo_unidade.assign(
        codigo_unidade=resumo_unidade["codigo_unidade"].apply(
            lambda x: f"Unidade {int(x)}" if pd.notna(x) else "Sem unidade"
        )
    )

    fig7 = px.bar(
        resumo_unidade, x="total", y="codigo_unidade",
        orientation="h",
        color="total", color_continuous_scale="Greens",
        labels={"total": "Total de NCs", "codigo_unidade": "Unidade"},
    )
    # Adiciona contorno nas barras
    fig7.update_traces(marker_line_color=COR_BORDA, marker_line_width=1)
    fig7.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig7, 500)
    st.plotly_chart(fig7, width="stretch", theme=None)


# ---------- Gráfico 8: NCs por Gravidade ----------
st.subheader("NCs por Gravidade")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_grav = df_n_f.groupby("gravidade").agg(
        total=("codigo_nc", "count"),
    ).reset_index().sort_values("total", ascending=False)

    cores_grav_bar = {
        "Baixa": COR_VERDE_ESCURO,
        "Média": COR_AMARELO,
        "Alta": COR_LARANJA,
        "Crítica": COR_VERMELHO,
    }

    fig8 = px.bar(
        resumo_grav, x="gravidade", y="total",
        color="gravidade", color_discrete_map=cores_grav_bar,
        labels={"gravidade": "Gravidade", "total": "NCs"},
        text="total",
    )
    fig8.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        textfont=dict(color=COR_TEXTO, size=13),
        cliponaxis=False,
    )
    fig8.update_layout(showlegend=False)
    aplicar_tema(fig8, 400)
    st.plotly_chart(fig8, width="stretch", theme=None)


# ---------- Gráfico 9: Itens com Maior Reincidência ----------
st.subheader("Itens do Checklist com Maior Reincidência")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_cod = df_n_f.groupby("codigo_nc").agg(
        total=("codigo_nc", "count"),
    ).reset_index().sort_values("total", ascending=False).head(15)
    resumo_cod = resumo_cod.assign(
        codigo_nc=resumo_cod["codigo_nc"].apply(lambda x: f"Item {x}")
    )
    resumo_cod = resumo_cod.sort_values("total", ascending=True)

    fig9 = px.bar(
        resumo_cod, x="total", y="codigo_nc",
        orientation="h",
        color="total", color_continuous_scale="Greens",
        labels={"total": "Total de NCs", "codigo_nc": "Código"},
    )
    fig9.update_traces(marker_line_color=COR_BORDA, marker_line_width=1)
    fig9.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig9, 900)
    st.plotly_chart(fig9, width="stretch", theme=None)


# ---------- Gráfico 10: NCs por Área ----------
st.subheader("NCs por Área do Checklist")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_cap = df_n_f.groupby("capitulo_nc").agg(
        total=("codigo_nc", "count"),
    ).reset_index()
    resumo_cap = resumo_cap.assign(cap_int=resumo_cap["capitulo_nc"].astype(int))
    resumo_cap = resumo_cap.sort_values("cap_int")

    fig10 = px.bar(
        resumo_cap, x="capitulo_nc", y="total",
        color="total", color_continuous_scale="Greens",
        labels={"capitulo_nc": "Área", "total": "NCs"},
        text="total",
    )
    fig10.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        textfont=dict(color=COR_TEXTO, size=13),
        cliponaxis=False,
        marker_line_color=COR_BORDA, marker_line_width=1
    )
    fig10.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig10, 400)
    st.plotly_chart(fig10, width="stretch", theme=None)


# ---------- Gráfico 11: Filial x Gravidade ----------
st.subheader("Filial x Gravidade")

if df_n_f is not None and len(df_n_f) > 0:
    ordem_grav = ["Baixa", "Média", "Alta", "Crítica"]
    pivot = df_n_f.pivot_table(
        index="filial", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in ordem_grav:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[ordem_grav]
    pivot = pivot.assign(total=pivot.sum(axis=1))
    pivot = pivot.sort_values("total", ascending=False).drop(columns="total").reset_index()

    fig11 = go.Figure()
    
    cores_grav = {
        "Baixa": COR_VERDE_ESCURO,
        "Média": COR_AMARELO,
        "Alta": COR_LARANJA,
        "Crítica": COR_VERMELHO,
    }
    
    for g in ordem_grav:
        fig11.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g, orientation="h",
            marker_color=cores_grav[g],
            hovertemplate="%{y}<br>" + g + ": %{x}<extra></extra>",
        ))
    fig11.update_layout(
        barmode="stack",
        xaxis_title="NCs",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    aplicar_tema(fig11, 500)
    st.plotly_chart(fig11, width="stretch", theme=None)


# ---------- Gráfico 12: NCs por Dia da Semana ----------
st.subheader("NCs Registradas por Dia da Semana")

if df_n_f is not None and len(df_n_f) > 0 and "dia_semana" in df_a_f.columns:
    df_n_dia = df_n_f.merge(
        df_a_f[["id_analise", "dia_semana"]], on="id_analise", how="left"
    )
    df_n_dia = df_n_dia.assign(dia_semana_pt=df_n_dia["dia_semana"].map(mapa_dias))

    resumo_nc_dia = df_n_dia.groupby("dia_semana_pt").size().reset_index(name="total")
    resumo_nc_dia = resumo_nc_dia.assign(
        ordem=resumo_nc_dia["dia_semana_pt"].map(
            {v: i for i, v in enumerate(["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])}
        )
    )
    resumo_nc_dia = resumo_nc_dia.sort_values("ordem")

    fig12 = px.bar(
        resumo_nc_dia, x="dia_semana_pt", y="total",
        color="total", color_continuous_scale="Greens",
        labels={"dia_semana_pt": "Dia", "total": "NCs"},
        text="total",
    )
    fig12.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        textfont=dict(color=COR_TEXTO, size=12),
        cliponaxis=False,
        marker_line_color=COR_BORDA, marker_line_width=1
    )
    fig12.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig12, 400)
    st.plotly_chart(fig12, width="stretch", theme=None)


# ---------- Gráfico 13: Gravidade das NCs por Área ----------
st.subheader("Gravidade das NCs por Área")

if df_n_f is not None and len(df_n_f) > 0:
    ordem_grav = ["Baixa", "Média", "Alta", "Crítica"]
    pivot_cap = df_n_f.pivot_table(
        index="capitulo_nc", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in ordem_grav:
        if g not in pivot_cap.columns:
            pivot_cap[g] = 0
    pivot_cap = pivot_cap[ordem_grav]
    pivot_cap = pivot_cap.reset_index().sort_values("capitulo_nc", key=lambda s: s.astype(int))

    fig13 = go.Figure()
    
    cores_grav = {
        "Baixa": COR_VERDE_ESCURO,
        "Média": COR_AMARELO,
        "Alta": COR_LARANJA,
        "Crítica": COR_VERMELHO,
    }
    
    for g in ordem_grav:
        fig13.add_trace(go.Bar(
            x=pivot_cap["capitulo_nc"], y=pivot_cap[g], name=g,
            marker_color=cores_grav[g],
            hovertemplate="Área %{x}<br>" + g + ": %{y}<extra></extra>",
        ))
    fig13.update_layout(
        barmode="stack",
        xaxis_title="Área",
        yaxis_title="NCs",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    aplicar_tema(fig13, 400)
    st.plotly_chart(fig13, width="stretch", theme=None)


st.divider()
st.header("Previsão de Criticidade")
st.markdown(
    """
    Utilize o formulário abaixo para simular as condições de uma não conformidade.
    O modelo **Random Forest** irá prever se ela será crítica ou não,
    com base nas variáveis selecionadas.
    """
)

if modelo is None or encoders is None:
    st.warning(
        "Modelo não encontrado. Rode `python3 scripts/06_machine_learning_cco.py` "
        "para gerar os arquivos `modelo/modelo_cco.pkl` e `modelo/encoders_cco.pkl`."
    )
else:
    with st.form("form_previsao"):
        col_e, col_f = st.columns(2)

        with col_e:
            filial_input = st.selectbox(
                "Filial",
                options=sorted(df_a["filial"].dropna().unique().tolist()),
            )
            classificacao_input = st.selectbox(
                "Classificação",
                options=sorted(df_n["classificacao"].dropna().unique().tolist()),
            )

        with col_f:
            unidade_input = st.selectbox(
                "Código da unidade",
                options=sorted(df_n["codigo_unidade"].dropna().unique().tolist()),
            )
            capitulo_input = st.selectbox(
                "Área do checklist",
                options=sorted(df_n["capitulo_nc"].dropna().unique().tolist()),
            )

        submit = st.form_submit_button("Prever Criticidade", use_container_width=True)

    if submit:
        try:
            entrada = {
                "filial": filial_input,
                "classificacao": classificacao_input,
                "codigo_unidade": unidade_input,
                "capitulo_nc": capitulo_input,
            }

            linha_codificada = {}
            for feat in FEATURES:
                valor = str(entrada[feat])
                le = encoders[feat]
                if valor in le.classes_:
                    linha_codificada[feat] = int(le.transform([valor])[0])
                else:
                    linha_codificada[feat] = 0
                    st.warning(
                        f"Valor '{valor}' não visto no treino para '{feat}'. "
                        f"Usando valor padrão."
                    )

            X_input = pd.DataFrame([linha_codificada])[FEATURES].astype(float)

            pred = modelo.predict(X_input)[0]
            proba = modelo.predict_proba(X_input)[0]

            le_target = encoders[TARGET]
            classe_prevista = le_target.inverse_transform([pred])[0]

            st.markdown("### Resultado da Previsão")

            cores_pred = {
                "Crítica": COR_VERMELHO,
                "Outra": COR_VERDE_ESCURO,
            }

            cor = cores_pred.get(classe_prevista, "#7F8C8D")

            st.markdown(
                f"""
                <div style="
                    background-color: #F8F9FA;
                    border-left: 6px solid {cor};
                    padding: 20px;
                    border-radius: 6px;
                    margin: 10px 0;
                ">
                    <div style="color: #7F8C8D; font-size: 0.85rem;
                                text-transform: uppercase; letter-spacing: 0.5px;
                                margin-bottom: 4px;">
                        Classificação prevista
                    </div>
                    <div style="color: {cor}; font-size: 1.8rem; font-weight: 600;">
                        {classe_prevista}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### Probabilidade por Classe")
            classes_originais = list(le_target.classes_)
            df_proba = pd.DataFrame({
                "Classe": classes_originais,
                "Probabilidade (%)": [round(p * 100, 2) for p in proba],
            }).sort_values("Probabilidade (%)", ascending=True)

            fig_pred = px.bar(
                df_proba,
                x="Probabilidade (%)",
                y="Classe",
                orientation="h",
                color="Probabilidade (%)",
                color_continuous_scale="Greens",
                text="Probabilidade (%)",
            )
            fig_pred.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
                textfont=dict(color=COR_TEXTO, size=12),
                cliponaxis=False,
            )
            fig_pred.update_layout(showlegend=False, coloraxis_showscale=False)
            aplicar_tema(fig_pred, 300)
            st.plotly_chart(fig_pred, width="stretch", theme=None)

            st.caption(
                "Esta previsão é baseada em padrões estatísticos históricos e "
                "não deve ser utilizada como única fonte para decisões operacionais."
            )

        except Exception as e:
            st.error(f"Erro ao fazer a previsão: {e}")


st.divider()
st.caption(
    "Desenvolvido por Jhonatan L. Santos para Terceirize Mais / Costa Oeste © 2026. Todos os direitos reservados."
)