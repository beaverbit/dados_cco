# 05_dashboard_cco.py
# Dashboard interativo do CCO com integração de ML.
# Para rodar: streamlit run 05_dashboard_cco.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import joblib

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="CCO - Indicadores Operacionais",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ESTILO VISUAL (dark profissional, sem neon)
st.markdown("""
<style>
    .stApp {
        background: #0E1117;
        color: #E6E6E6;
    }

    [data-testid="stSidebar"] {
        background: #161B22;
        border-right: 1px solid #21262D;
    }
    [data-testid="stSidebar"] * {
        color: #C9D1D9;
    }

    h1 {
        color: #F0F6FC !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    h2, h3 {
        color: #F0F6FC !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
    }

    [data-testid="stMetric"] {
        background: #161B22;
        border-left: 4px solid #388BFD;
        border-radius: 6px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetricLabel"] {
        color: #8B949E !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #F0F6FC !important;
        font-size: 1.9rem !important;
        font-weight: 600 !important;
    }

    hr {
        border-color: #21262D !important;
        margin: 2rem 0 !important;
    }

    [data-testid="stMultiSelect"] label {
        color: #C9D1D9 !important;
        font-weight: 500 !important;
    }

    .stButton > button {
        background: #238636;
        color: #FFFFFF;
        border: none;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        transition: background 0.15s;
    }
    .stButton > button:hover {
        background: #2EA043;
        color: #FFFFFF;
    }

    [data-testid="stForm"] {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 1.5rem;
    }

    [data-testid="stSelectbox"] label {
        color: #C9D1D9 !important;
        font-weight: 500 !important;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6E7681 !important;
        font-size: 0.85rem !important;
    }

    .stAlert {
        background: #161B22 !important;
        border-left: 4px solid #D29922 !important;
        color: #C9D1D9 !important;
    }
</style>
""", unsafe_allow_html=True)

TEMPLATE = "plotly_dark"

ARQ_ANALISES = os.path.join("dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join("dados_tratados", "nao_conformidades_limpas.csv")
ARQ_MODELO = os.path.join("modelo", "modelo_cco.pkl")
ARQ_ENCODERS = os.path.join("modelo", "encoders_cco.pkl")

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
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="#C9D1D9", size=13),
        title_font=dict(color="#F0F6FC", size=17),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return fig


df_a, df_n = carregar_dados()
modelo, encoders = carregar_modelo()


st.title("CCO - Indicadores Operacionais")
st.markdown(
    f"""
    <div style="color:#8B949E; font-size:0.95rem; margin-bottom:1rem;">
        <b style="color:#C9D1D9;">Análises:</b> {len(df_a):,} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b style="color:#C9D1D9;">Não conformidades:</b> {len(df_n) if df_n is not None else 0:,}
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
    f"<div style='color:#8B949E; margin-top:1rem;'>Análises filtradas: "
    f"<b style='color:#C9D1D9;'>{len(df_a_f):,}</b></div>",
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
    marker_color="#388BFD",
    yaxis="y1",
))
fig1.add_trace(go.Scatter(
    x=resumo_filial["filial"],
    y=resumo_filial["nc"],
    name="Total de NCs",
    mode="lines+markers",
    marker=dict(color="#F85149", size=10),
    line=dict(width=3),
    yaxis="y2",
))
fig1.update_layout(
    yaxis=dict(title="Total de análises", side="left"),
    yaxis2=dict(title="NCs", overlaying="y", side="right"),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
aplicar_tema(fig1, 400)
st.plotly_chart(fig1, width="stretch", theme=None)


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
    color="taxa_conformidade", color_continuous_scale="RdYlGn",
    labels={"filial": "Filial", "taxa_conformidade": "Taxa de Conformidade (%)"},
    text="taxa_conformidade",
)
fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig2.update_layout(coloraxis_showscale=False)
aplicar_tema(fig2, 400)
st.plotly_chart(fig2, width="stretch", theme=None)


st.subheader("Distribuição Mensal de Análises e NCs")

resumo_mes = df_a_f.groupby("mes").agg(
    total=("id_analise", "count"),
    nc=("qtd_nc", "sum"),
).reset_index()

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=resumo_mes["mes"], y=resumo_mes["total"],
    name="Análises", marker_color="#388BFD",
))
fig3.add_trace(go.Bar(
    x=resumo_mes["mes"], y=resumo_mes["nc"],
    name="NCs", marker_color="#F85149",
))
fig3.update_layout(
    barmode="group",
    xaxis_title="Mês",
    yaxis_title="Quantidade",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
aplicar_tema(fig3, 400)
st.plotly_chart(fig3, width="stretch", theme=None)


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
    marker_color="#388BFD",
    yaxis="y1",
))
fig4.add_trace(go.Scatter(
    x=resumo_dia["dia_semana_pt"],
    y=resumo_dia["taxa_nc"],
    name="Taxa de NC (%)",
    mode="lines+markers",
    marker=dict(color="#F85149", size=8),
    line=dict(width=3),
    yaxis="y2",
))
fig4.update_layout(
    yaxis=dict(title="Total de análises", side="left"),
    yaxis2=dict(title="Taxa de NC (%)", overlaying="y", side="right"),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
aplicar_tema(fig4, 400)
st.plotly_chart(fig4, width="stretch", theme=None)


col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Distribuição por Resultado")
    resumo_resultado = df_a_f.groupby("resultado").agg(
        total=("id_analise", "count"),
    ).reset_index()

    cores_resultado = {
        "Conforme": "#3FB950",
        "Conforme com Observação": "#D29922",
        "Não Conforme": "#F85149",
    }

    fig5 = px.bar(
        resumo_resultado, x="resultado", y="total",
        color="resultado",
        color_discrete_map=cores_resultado,
        labels={"resultado": "Resultado", "total": "Análises"},
        text="total",
    )
    fig5.update_traces(textposition="outside")
    fig5.update_layout(showlegend=False)
    aplicar_tema(fig5, 400)
    st.plotly_chart(fig5, width="stretch", theme=None)

with col_d:
    st.subheader("Distribuição por Classificação")
    resumo_class = df_a_f.groupby("classificacao").agg(total=("id_analise", "count")).reset_index()

    ordem_class = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
    cores_class = {
        "Ótimo": "#3FB950",
        "Bom": "#388BFD",
        "Regular": "#D29922",
        "Ruim": "#F0883E",
        "Péssimo": "#F85149",
    }

    fig6 = px.pie(
        resumo_class, names="classificacao", values="total",
        color="classificacao",
        color_discrete_map=cores_class,
        category_orders={"classificacao": ordem_class},
        hole=0.4,
    )
    aplicar_tema(fig6, 400)
    st.plotly_chart(fig6, width="stretch", theme=None)


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
        color="total", color_continuous_scale="Reds",
        labels={"total": "Total de NCs", "codigo_unidade": "Unidade"},
        text="total",
    )
    fig7.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig7.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig7, 500)
    st.plotly_chart(fig7, width="stretch", theme=None)


st.subheader("NCs por Gravidade")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_grav = df_n_f.groupby("gravidade").agg(
        total=("codigo_nc", "count"),
    ).reset_index().sort_values("total", ascending=False)

    fig8 = px.bar(
        resumo_grav, x="gravidade", y="total",
        color="total", color_continuous_scale="Reds",
        labels={"gravidade": "Gravidade", "total": "NCs"},
        text="total",
    )
    fig8.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig8.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig8, 400)
    st.plotly_chart(fig8, width="stretch", theme=None)


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
        color="total", color_continuous_scale="Reds",
        labels={"total": "Total de NCs", "codigo_nc": "Código"},
        text="total",
    )
    fig9.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig9.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig9, 900)
    st.plotly_chart(fig9, width="stretch", theme=None)


st.subheader("NCs por Capítulo do Checklist")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_cap = df_n_f.groupby("capitulo_nc").agg(
        total=("codigo_nc", "count"),
    ).reset_index()
    resumo_cap = resumo_cap.assign(cap_int=resumo_cap["capitulo_nc"].astype(int))
    resumo_cap = resumo_cap.sort_values("cap_int")

    fig10 = px.bar(
        resumo_cap, x="capitulo_nc", y="total",
        color="total", color_continuous_scale="Blues_r",
        labels={"capitulo_nc": "Capítulo", "total": "NCs"},
        text="total",
    )
    fig10.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig10.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig10, 400)
    st.plotly_chart(fig10, width="stretch", theme=None)


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
        "Baixa": "#3FB950",
        "Média": "#D29922",
        "Alta": "#F0883E",
        "Crítica": "#F85149",
    }
    for g in ordem_grav:
        fig11.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g, orientation="h",
            marker_color=cores_grav[g],
        ))
    fig11.update_layout(
        barmode="stack",
        xaxis_title="NCs",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    aplicar_tema(fig11, 500)
    st.plotly_chart(fig11, width="stretch", theme=None)


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
        color="total", color_continuous_scale="Reds",
        labels={"dia_semana_pt": "Dia", "total": "NCs"},
        text="total",
    )
    fig12.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig12.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig12, 400)
    st.plotly_chart(fig12, width="stretch", theme=None)


st.subheader("Gravidade das NCs por Capítulo")

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
        "Baixa": "#3FB950",
        "Média": "#D29922",
        "Alta": "#F0883E",
        "Crítica": "#F85149",
    }
    for g in ordem_grav:
        fig13.add_trace(go.Bar(
            x=pivot_cap["capitulo_nc"], y=pivot_cap[g], name=g,
            marker_color=cores_grav[g],
        ))
    fig13.update_layout(
        barmode="stack",
        xaxis_title="Capítulo",
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
        "Modelo não encontrado. Rode `python3 06_machine_learning_cco.py` "
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
                "Capítulo do checklist",
                options=sorted(df_n["capitulo_nc"].dropna().unique().tolist()),
            )

        submit = st.form_submit_button("Prever Criticidade", width="stretch")

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

            cores = {
                "Crítica": "#F85149",
                "Outra": "#3FB950",
            }

            cor = cores.get(classe_prevista, "#8B949E")

            st.markdown(
                f"""
                <div style="
                    background-color: #161B22;
                    border-left: 6px solid {cor};
                    padding: 20px;
                    border-radius: 6px;
                    margin: 10px 0;
                ">
                    <div style="color: #8B949E; font-size: 0.85rem;
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
                color_continuous_scale="Reds",
                text="Probabilidade (%)",
            )
            fig_pred.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
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