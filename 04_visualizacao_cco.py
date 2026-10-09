# 04_visualizacao_cco.py
# Meu objetivo: gerar os gráficos estáticos dos KPIs do CCO usando Plotly + kaleido.

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

ARQ_ANALISES = os.path.join("dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join("dados_tratados", "nao_conformidades_limpas.csv")
PASTA_IMAGENS = "imagens"

GRAVIDADES_ORDEM = ["Baixa", "Média", "Alta", "Crítica"]
CORES_GRAVIDADE = {
    "Baixa": "#2ecc71",
    "Média": "#f1c40f",
    "Alta": "#e67e22",
    "Crítica": "#c0392b",
}


def carregar():
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


def salvar(fig, nome):
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    caminho = os.path.join(PASTA_IMAGENS, nome)
    fig.write_image(caminho, width=1200, height=600, scale=1.5)
    print(f"  -> {caminho}")


def graf_resultados(df_a):
    print("\nGráfico 1: Distribuição de resultados")
    contagem = df_a["resultado"].value_counts().reset_index()
    contagem.columns = ["resultado", "total"]

    cores = []
    for r in contagem["resultado"]:
        rl = r.lower()
        if rl == "conforme":
            cores.append("#2ecc71")
        elif "observação" in rl:
            cores.append("#f1c40f")
        elif "não" in rl:
            cores.append("#c0392b")
        else:
            cores.append("#95a5a6")

    fig = go.Figure(data=[go.Pie(
        labels=contagem["resultado"],
        values=contagem["total"],
        marker=dict(colors=cores),
        hole=0,
        textinfo="label+percent",
    )])
    fig.update_layout(title="Distribuição dos resultados das análises")
    salvar(fig, "01_distribuicao_resultados.png")


def graf_por_filial(df_a):
    print("\nGráfico 2: Análises e NCs por filial")
    resumo = df_a.groupby("filial").agg(
        total=("id_analise", "count"),
        nc=("qtd_nc", "sum"),
    ).reset_index().sort_values("nc", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["filial"], y=resumo["total"],
        name="Total de análises", marker_color="steelblue",
    ))
    fig.add_trace(go.Bar(
        x=resumo["filial"], y=resumo["nc"],
        name="Total de NCs", marker_color="crimson",
    ))
    fig.update_layout(
        title="Análises e NCs por filial",
        barmode="group",
        xaxis_title="Filial",
        yaxis_title="Quantidade",
        xaxis_tickangle=-30,
    )
    salvar(fig, "02_analises_nc_por_filial.png")


def graf_por_analista(df_a):
    print("\nGráfico 3: Análises por analista")
    resumo = df_a.groupby("analista").agg(
        total=("id_analise", "count"),
    ).reset_index().sort_values("total", ascending=True).tail(15)

    fig = px.bar(
        resumo, x="total", y="analista", orientation="h",
        color="total", color_continuous_scale="Viridis",
        labels={"total": "Total de análises", "analista": ""},
        title="Produtividade por analista (top 15)",
    )
    fig.update_layout(coloraxis_showscale=False)
    salvar(fig, "03_analises_por_analista.png")


def graf_por_mes(df_a):
    print("\nGráfico 4: Análises por mês")
    df_a = df_a.assign(
        periodo=(
            df_a["ano"].astype("Int64").astype(str) + "-"
            + df_a["mes"].astype("Int64").astype(str).str.zfill(2)
        )
    )
    resumo = df_a.groupby("periodo").agg(
        total=("id_analise", "count"),
        nc=("qtd_nc", "sum"),
    ).reset_index().sort_values("periodo")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["periodo"], y=resumo["total"],
        name="Análises", marker_color="steelblue",
    ))
    fig.add_trace(go.Bar(
        x=resumo["periodo"], y=resumo["nc"],
        name="NCs", marker_color="crimson",
    ))
    fig.update_layout(
        title="Análises e NCs por mês",
        barmode="group",
        xaxis_title="Período",
        yaxis_title="Quantidade",
    )
    salvar(fig, "04_analises_por_mes.png")


def graf_nc_gravidade(df_n):
    print("\nGráfico 5: NCs por gravidade")
    resumo = df_n["gravidade"].value_counts().reindex(GRAVIDADES_ORDEM).fillna(0).reset_index()
    resumo.columns = ["gravidade", "total"]

    fig = px.bar(
        resumo, x="gravidade", y="total",
        color="gravidade",
        color_discrete_map=CORES_GRAVIDADE,
        text="total",
        labels={"gravidade": "Gravidade", "total": "Total de NCs"},
        title="Distribuição de NCs por gravidade",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)
    salvar(fig, "05_nc_por_gravidade.png")


def graf_nc_classificacao(df_n):
    print("\nGráfico 6: NCs por classificação")
    resumo = df_n["classificacao"].value_counts().reset_index()
    resumo.columns = ["classificacao", "total"]

    fig = px.bar(
        resumo, x="total", y="classificacao", orientation="h",
        color="total", color_continuous_scale="OrRd",
        text="total",
        labels={"total": "Total", "classificacao": ""},
        title="NCs por classificação",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    salvar(fig, "06_nc_por_classificacao.png")


def graf_nc_capitulo(df_n):
    print("\nGráfico 7: NCs por capítulo")
    resumo = df_n.groupby("capitulo_nc").size().reset_index(name="total")
    resumo = resumo.assign(cap_int=resumo["capitulo_nc"].astype(int))
    resumo = resumo.sort_values("cap_int")

    fig = px.bar(
        resumo, x="capitulo_nc", y="total",
        color="total", color_continuous_scale="Viridis",
        text="total",
        labels={"capitulo_nc": "Capítulo", "total": "Total de NCs"},
        title="NCs por capítulo do checklist",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    salvar(fig, "07_nc_por_capitulo.png")


def graf_filial_x_gravidade(df_n):
    print("\nGráfico 8: Filial x Gravidade")
    pivot = df_n.pivot_table(
        index="filial", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in GRAVIDADES_ORDEM:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[GRAVIDADES_ORDEM]
    pivot = pivot.assign(total=pivot.sum(axis=1))
    pivot = pivot.sort_values("total", ascending=True).drop(columns="total").reset_index()

    fig = go.Figure()
    for g in GRAVIDADES_ORDEM:
        fig.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g, orientation="h",
            marker_color=CORES_GRAVIDADE[g],
        ))
    fig.update_layout(
        title="NCs por filial e gravidade",
        barmode="stack",
        xaxis_title="Total de NCs",
        yaxis_title="",
        legend_title="Gravidade",
    )
    salvar(fig, "08_filial_x_gravidade.png")


if __name__ == "__main__":
    df_a, df_n = carregar()

    graf_resultados(df_a)
    graf_por_filial(df_a)
    graf_por_analista(df_a)
    graf_por_mes(df_a)

    if df_n is not None and len(df_n) > 0:
        graf_nc_gravidade(df_n)
        graf_nc_classificacao(df_n)
        graf_nc_capitulo(df_n)
        graf_filial_x_gravidade(df_n)

    print("\nGráficos gerados.")