# 04_visualizacao_cco.py
# Meu objetivo: gerar os gráficos estáticos dos KPIs do CCO.

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Raiz do projeto (pasta pai de scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQ_ANALISES = os.path.join(BASE_DIR, "dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join(BASE_DIR, "dados_tratados", "nao_conformidades_limpas.csv")
PASTA_IMAGENS = os.path.join(BASE_DIR, "imagens")

# Cores (Hex Strings)
COR_VERDE_ESCURO = "#2E7D32"
COR_VERDE_CLARO = "#A5D6A7"
COR_AMARELO = "#F9A825"
COR_LARANJA = "#EF6C00"
COR_VERMELHO = "#C62828"
COR_TEXTO = "#2C3E50"
COR_BORDA = "#B0BEC5"


def carregar():
    df_a = pd.read_csv(ARQ_ANALISES, sep=";", encoding="utf-8", low_memory=False)
    df_a = df_a.assign(
        data_da_avaliacao=pd.to_datetime(
            df_a["data_da_avaliacao"], errors="coerce"
        )
    )
    # Filtra igual ao dashboard e PDF
    df_a = df_a[df_a["resultado"].notna()].reset_index(drop=True)
    
    df_n = None
    if os.path.exists(ARQ_NCS):
        df_n = pd.read_csv(ARQ_NCS, sep=";", encoding="utf-8", low_memory=False)
    return df_a, df_n


def salvar(fig, nome):
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    caminho = os.path.join(PASTA_IMAGENS, nome)
    fig.write_image(caminho, width=1200, height=600, scale=1.5)
    print(f"  -> {caminho}")


def aplicar_tema(fig, altura=600):
    fig.update_layout(
        template="plotly_white",
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


def graf_resultados(df_a):
    print("\nGráfico 1: Distribuição de resultados")
    contagem = df_a["resultado"].value_counts().reset_index()
    contagem.columns = ["resultado", "total"]

    cores = []
    for r in contagem["resultado"]:
        rl = r.lower()
        if rl == "conforme":
            cores.append(COR_VERDE_ESCURO)
        elif "observação" in rl:
            cores.append(COR_AMARELO)
        elif "não" in rl:
            cores.append(COR_VERMELHO)
        else:
            cores.append("#95A5A6")

    fig = go.Figure(data=[go.Pie(
        labels=contagem["resultado"],
        values=contagem["total"],
        marker=dict(colors=cores),
        hole=0,
        textinfo="label+percent",
        textfont=dict(color="#FFFFFF", size=13)
    )])
    fig.update_layout(title="Distribuição dos resultados das análises")
    aplicar_tema(fig)
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
        name="Total de análises", marker_color=COR_VERDE_ESCURO,
        text=resumo["total"], textposition="outside", cliponaxis=False
    ))
    fig.add_trace(go.Bar(
        x=resumo["filial"], y=resumo["nc"],
        name="Total de NCs", marker_color=COR_VERMELHO,
        text=resumo["nc"], textposition="outside", cliponaxis=False
    ))
    fig.update_layout(
        title="Análises e NCs por filial",
        barmode="group",
        xaxis_title="Filial",
        yaxis_title="Quantidade",
        xaxis_tickangle=-30,
    )
    aplicar_tema(fig)
    salvar(fig, "02_analises_nc_por_filial.png")


def graf_por_analista(df_a):
    print("\nGráfico 3: Análises por analista")
    resumo = df_a.groupby("analista").agg(
        total=("id_analise", "count"),
    ).reset_index().sort_values("total", ascending=True).tail(15)

    fig = px.bar(
        resumo, x="total", y="analista", orientation="h",
        color="total", color_continuous_scale="Greens",
        labels={"total": "Total de análises", "analista": ""},
        title="Produtividade por analista (top 15)",
    )
    fig.update_traces(
        marker_line_color=COR_BORDA, marker_line_width=1,
        text=resumo["total"], textposition="inside", 
        insidetextanchor="end", textfont=dict(color="#FFFFFF")
    )
    fig.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig)
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
        name="Análises", marker_color=COR_VERDE_ESCURO,
        text=resumo["total"], textposition="outside", cliponaxis=False
    ))
    fig.add_trace(go.Bar(
        x=resumo["periodo"], y=resumo["nc"],
        name="NCs", marker_color=COR_VERMELHO,
        text=resumo["nc"], textposition="outside", cliponaxis=False
    ))
    fig.update_layout(
        title="Análises e NCs por mês",
        barmode="group",
        xaxis_title="Período",
        yaxis_title="Quantidade",
    )
    aplicar_tema(fig)
    salvar(fig, "04_analises_por_mes.png")


def graf_nc_gravidade(df_n):
    print("\nGráfico 5: NCs por gravidade")
    resumo = df_n["gravidade"].value_counts().reindex(["Baixa", "Média", "Alta", "Crítica"]).fillna(0).reset_index()
    resumo.columns = ["gravidade", "total"]

    cores_grav = {
        "Baixa": COR_VERDE_ESCURO,
        "Média": COR_AMARELO,
        "Alta": COR_LARANJA,
        "Crítica": COR_VERMELHO,
    }

    fig = px.bar(
        resumo, x="gravidade", y="total",
        color="gravidade",
        color_discrete_map=cores_grav,
        text="total",
        labels={"gravidade": "Gravidade", "total": "Total de NCs"},
        title="Distribuição de NCs por gravidade",
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        marker_line_color=COR_BORDA, marker_line_width=1
    )
    fig.update_layout(showlegend=False)
    aplicar_tema(fig)
    salvar(fig, "05_nc_por_gravidade.png")


def graf_nc_classificacao(df_n):
    print("\nGráfico 6: NCs por classificação")
    resumo = df_n["classificacao"].value_counts().reset_index()
    resumo.columns = ["classificacao", "total"]

    fig = px.bar(
        resumo, x="total", y="classificacao", orientation="h",
        color="total", color_continuous_scale="Greens",
        text="total",
        labels={"total": "Total", "classificacao": ""},
        title="NCs por classificação",
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        marker_line_color=COR_BORDA, marker_line_width=1
    )
    fig.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig)
    salvar(fig, "06_nc_por_classificacao.png")


def graf_nc_area(df_n):
    print("\nGráfico 7: NCs por área")
    # CORRIGIDO AQUI: Voltou a ser capitulo_nc
    resumo = df_n.groupby("capitulo_nc").size().reset_index(name="total")
    resumo = resumo.assign(cap_int=resumo["capitulo_nc"].astype(int))
    resumo = resumo.sort_values("cap_int")

    fig = px.bar(
        resumo, x="capitulo_nc", y="total",
        color="total", color_continuous_scale="Greens",
        text="total",
        labels={"capitulo_nc": "Área", "total": "Total de NCs"},
        title="NCs por área do checklist",
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        marker_line_color=COR_BORDA, marker_line_width=1
    )
    fig.update_layout(coloraxis_showscale=False)
    aplicar_tema(fig)
    salvar(fig, "07_nc_por_area.png")


def graf_filial_x_gravidade(df_n):
    print("\nGráfico 8: Filial x Gravidade")
    pivot = df_n.pivot_table(
        index="filial", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in ["Baixa", "Média", "Alta", "Crítica"]:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[["Baixa", "Média", "Alta", "Crítica"]]
    pivot = pivot.assign(total=pivot.sum(axis=1))
    pivot = pivot.sort_values("total", ascending=True).drop(columns="total").reset_index()

    cores_grav = {
        "Baixa": COR_VERDE_ESCURO,
        "Média": COR_AMARELO,
        "Alta": COR_LARANJA,
        "Crítica": COR_VERMELHO,
    }

    fig = go.Figure()
    for g in ["Baixa", "Média", "Alta", "Crítica"]:
        fig.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g, orientation="h",
            marker_color=cores_grav[g],
            marker_line_color=COR_BORDA, marker_line_width=1,
        ))
    fig.update_layout(
        title="NCs por filial e gravidade",
        barmode="stack",
        xaxis_title="Total de NCs",
        yaxis_title="",
        legend_title="Gravidade",
    )
    aplicar_tema(fig)
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
        graf_nc_area(df_n)
        graf_filial_x_gravidade(df_n)

    print("\nGráficos gerados.")