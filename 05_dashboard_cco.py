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

# CONSTANTES
ARQ_ANALISES = os.path.join("dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join("dados_tratados", "nao_conformidades_limpas.csv")
ARQ_MODELO = os.path.join("modelo", "modelo_cco.pkl")
ARQ_ENCODERS = os.path.join("modelo", "encoders_cco.pkl")

FEATURES = ["filial", "classificacao", "codigo_unidade", "capitulo_nc"]
TARGET = "critica_bin"


# CARREGAMENTO DOS DADOS (com cache)
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


# CARREGAMENTO DO MODELO E ENCODERS (com cache)
@st.cache_resource
def carregar_modelo():
    if not os.path.exists(ARQ_MODELO) or not os.path.exists(ARQ_ENCODERS):
        return None, None
    modelo = joblib.load(ARQ_MODELO)
    encoders = joblib.load(ARQ_ENCODERS)
    return modelo, encoders


df_a, df_n = carregar_dados()
modelo, encoders = carregar_modelo()


# CABEÇALHO
st.title("CCO - Indicadores Operacionais")
st.markdown(
    """
    **Análises:** {:,.0f}  
    **Não conformidades:** {:,.0f}  
    """.format(len(df_a), len(df_n) if df_n is not None else 0)
)

st.divider()


# SIDEBAR - FILTROS
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

st.sidebar.markdown(f"**Análises filtradas:** {len(df_a_f):,}")


# KPIs PRINCIPAIS
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


# GRÁFICO 1: Análises e NCs por filial
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
    marker_color="steelblue",
    yaxis="y1",
))
fig1.add_trace(go.Scatter(
    x=resumo_filial["filial"],
    y=resumo_filial["nc"],
    name="Total de NCs",
    mode="lines+markers",
    marker=dict(color="crimson", size=10),
    line=dict(width=3),
    yaxis="y2",
))
fig1.update_layout(
    yaxis=dict(title="Total de análises", side="left"),
    yaxis2=dict(title="NCs", overlaying="y", side="right"),
    hovermode="x unified",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig1, width="stretch")


# GRÁFICO 2: Taxa de Conformidade por Filial
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
fig2.update_layout(height=400, coloraxis_showscale=False)
st.plotly_chart(fig2, width="stretch")


# GRÁFICO 3: Distribuição Mensal
st.subheader("Distribuição Mensal de Análises e NCs")

resumo_mes = df_a_f.groupby("mes").agg(
    total=("id_analise", "count"),
    nc=("qtd_nc", "sum"),
).reset_index()

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=resumo_mes["mes"], y=resumo_mes["total"],
    name="Análises", marker_color="steelblue",
))
fig3.add_trace(go.Bar(
    x=resumo_mes["mes"], y=resumo_mes["nc"],
    name="NCs", marker_color="crimson",
))
fig3.update_layout(
    barmode="group",
    height=400,
    xaxis_title="Mês",
    yaxis_title="Quantidade",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig3, width="stretch")


# GRÁFICO 4: Análises e taxa de NC por dia da semana
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
    marker_color="skyblue",
    yaxis="y1",
))
fig4.add_trace(go.Scatter(
    x=resumo_dia["dia_semana_pt"],
    y=resumo_dia["taxa_nc"],
    name="Taxa de NC (%)",
    mode="lines+markers",
    marker=dict(color="darkred", size=8),
    line=dict(width=3),
    yaxis="y2",
))
fig4.update_layout(
    yaxis=dict(title="Total de análises", side="left"),
    yaxis2=dict(title="Taxa de NC (%)", overlaying="y", side="right"),
    hovermode="x unified",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig4, width="stretch")


# GRÁFICO 5 e 6: Resultado e classificação
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Distribuição por Resultado")
    resumo_resultado = df_a_f.groupby("resultado").agg(
        total=("id_analise", "count"),
    ).reset_index()
    fig5 = px.bar(
        resumo_resultado, x="resultado", y="total",
        color="total", color_continuous_scale="reds",
        labels={"resultado": "Resultado", "total": "Análises"},
        text="total",
    )
    fig5.update_traces(textposition="outside")
    fig5.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig5, width="stretch")

with col_d:
    st.subheader("Distribuição por Classificação")
    resumo_class = df_a_f.groupby("classificacao").agg(total=("id_analise", "count")).reset_index()
    fig6 = px.pie(
        resumo_class, names="classificacao", values="total",
        color_discrete_sequence=px.colors.sequential.Plasma,
        hole=0.4,
    )
    fig6.update_layout(height=400)
    st.plotly_chart(fig6, width="stretch")


# GRÁFICO 7: Top unidades com mais NCs
st.subheader("Top 10 Unidades com Mais NCs")

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
        color="total", color_continuous_scale="orrd",
        labels={"total": "Total de NCs", "codigo_unidade": "Unidade"},
        text="total",
    )
    fig7.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig7.update_layout(height=500, coloraxis_showscale=False)
    st.plotly_chart(fig7, width="stretch")


# GRÁFICO 8: NCs por gravidade
st.subheader("NCs por Gravidade")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_grav = df_n_f.groupby("gravidade").agg(
        total=("codigo_nc", "count"),
    ).reset_index().sort_values("total", ascending=False)

    fig8 = px.bar(
        resumo_grav, x="gravidade", y="total",
        color="total", color_continuous_scale="reds",
        labels={"gravidade": "Gravidade", "total": "NCs"},
        text="total",
    )
    fig8.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig8.update_layout(height=400, coloraxis_showscale=False)
    st.plotly_chart(fig8, width="stretch")


# GRÁFICO 9: Top 15 Códigos de NC mais recorrentes
st.subheader("Top 15 Códigos de NC Mais Recorrentes")

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
        color="total", color_continuous_scale="reds",
        labels={"total": "Total de NCs", "codigo_nc": "Código"},
        text="total",
    )
    fig9.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig9.update_layout(
        height=900,
        coloraxis_showscale=False,
        margin=dict(l=120, r=80, t=60, b=60),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
    )
    st.plotly_chart(fig9, width="stretch")


# GRÁFICO 10: NCs por capítulo do checklist
st.subheader("NCs por Capítulo do Checklist")

if df_n_f is not None and len(df_n_f) > 0:
    resumo_cap = df_n_f.groupby("capitulo_nc").agg(
        total=("codigo_nc", "count"),
    ).reset_index()
    resumo_cap = resumo_cap.assign(cap_int=resumo_cap["capitulo_nc"].astype(int))
    resumo_cap = resumo_cap.sort_values("cap_int")

    fig10 = px.bar(
        resumo_cap, x="capitulo_nc", y="total",
        color="total", color_continuous_scale="Viridis",
        labels={"capitulo_nc": "Capítulo", "total": "NCs"},
        text="total",
    )
    fig10.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig10.update_layout(height=400, coloraxis_showscale=False)
    st.plotly_chart(fig10, width="stretch")


# GRÁFICO 11: Filial x Gravidade
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
        "Baixa": "#2ecc71", "Média": "#f1c40f",
        "Alta": "#e67e22", "Crítica": "#c0392b",
    }
    for g in ordem_grav:
        fig11.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g, orientation="h",
            marker_color=cores_grav[g],
        ))
    fig11.update_layout(
        barmode="stack",
        height=500,
        xaxis_title="NCs",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig11, width="stretch")


# GRÁFICO 12: NCs por dia da semana (só NCs)
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
        color="total", color_continuous_scale="reds",
        labels={"dia_semana_pt": "Dia", "total": "NCs"},
        text="total",
    )
    fig12.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig12.update_layout(height=400, coloraxis_showscale=False)
    st.plotly_chart(fig12, width="stretch")


# GRÁFICO 13: Distribuição de Gravidade por Capítulo
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
        "Baixa": "#2ecc71", "Média": "#f1c40f",
        "Alta": "#e67e22", "Crítica": "#c0392b",
    }
    for g in ordem_grav:
        fig13.add_trace(go.Bar(
            x=pivot_cap["capitulo_nc"], y=pivot_cap[g], name=g,
            marker_color=cores_grav[g],
        ))
    fig13.update_layout(
        barmode="stack",
        height=400,
        xaxis_title="Capítulo",
        yaxis_title="NCs",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig13, width="stretch")


# SEÇÃO DE MACHINE LEARNING - PREVISÃO DE CRITICIDADE
st.divider()
st.header("Previsão de Criticidade com Machine Learning")
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
                "Crítica": "#c0392b",
                "Outra": "#2ecc71",
            }

            cor = cores.get(classe_prevista, "#888")

            st.markdown(
                f"""
                <div style="
                    background-color: {cor}20;
                    border-left: 8px solid {cor};
                    padding: 20px;
                    border-radius: 8px;
                    margin: 10px 0;
                ">
                    <h2 style="color: {cor}; margin: 0;">
                        Classificação prevista: {classe_prevista}
                    </h2>
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
                color_continuous_scale="reds",
                text="Probabilidade (%)",
            )
            fig_pred.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_pred.update_layout(
                height=300,
                showlegend=False,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_pred, width="stretch")

            st.caption(
                "Esta previsão é baseada em padrões estatísticos históricos e "
                "não deve ser utilizada como única fonte para decisões operacionais."
            )

        except Exception as e:
            st.error(f"Erro ao fazer a previsão: {e}")


# RODAPÉ
st.divider()
st.caption(
    "Dashboard de indicadores operacionais do CCO."
)