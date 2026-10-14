# 07_gerar_pdf_cco.py
# Meu objetivo: gerar um PDF do dashboard com a mesma paleta visual do Streamlit.

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER

ARQ_ANALISES = os.path.join("dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join("dados_tratados", "nao_conformidades_limpas.csv")
ARQ_PDF = os.path.join("dados_tratados", "relatorio_cco.pdf")

# Paleta idêntica ao 05_dashboard_cco.py
BG_PRINCIPAL = HexColor("#0E1117")
BG_CARD = HexColor("#161B22")
BORDA_CARD = HexColor("#21262D")
TEXTO_PRINCIPAL = HexColor("#F0F6FC")
TEXTO_SECUNDARIO = HexColor("#8B949E")
TEXTO_TERCIARIO = HexColor("#6E7681")
VERDE = HexColor("#2E7D32")
VERDE_CLARO = HexColor("#4ADE80")
VERMELHO = HexColor("#C62828")
VERMELHO_CLARO = HexColor("#F85149")
AMARELO = HexColor("#F9A825")
LARANJA = HexColor("#EF6C00")
AZUL = HexColor("#388BFD")

# Cores pro Plotly (em hex string)
PLOTLY_BG = "#0E1117"
PLOTLY_VERDE = "#2E7D32"
PLOTLY_VERDE_CLARO = "#4ADE80"
PLOTLY_VERMELHO = "#C62828"
PLOTLY_AMARELO = "#F9A825"
PLOTLY_LARANJA = "#EF6C00"

TEMPLATE = "plotly_dark"

MAPA_DIAS = {
    "Monday": "Seg", "Tuesday": "Ter", "Wednesday": "Qua",
    "Thursday": "Qui", "Friday": "Sex", "Saturday": "Sáb", "Sunday": "Dom",
}


def carregar_dados():
    df_a = pd.read_csv(ARQ_ANALISES, sep=";", encoding="utf-8", low_memory=False)
    df_a = df_a.assign(
        data_da_avaliacao=pd.to_datetime(df_a["data_da_avaliacao"], errors="coerce")
    )
    df_n = None
    if os.path.exists(ARQ_NCS):
        df_n = pd.read_csv(ARQ_NCS, sep=";", encoding="utf-8", low_memory=False)
    return df_a, df_n


def aplicar_tema(fig, altura=400):
    fig.update_layout(
        template=TEMPLATE,
        height=altura,
        paper_bgcolor=PLOTLY_BG,
        plot_bgcolor=PLOTLY_BG,
        font=dict(color="#C9D1D9", size=13),
        title_font=dict(color="#F0F6FC", size=17),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return fig


def fig_para_imagem(fig, largura_px=1200, altura_px=500):
    return io.BytesIO(fig.to_image(format="png", width=largura_px, height=altura_px, scale=1.5))


def estilos():
    ss = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "titulo", parent=ss["Title"],
            textColor=VERDE_CLARO, fontSize=24, spaceAfter=20,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo", parent=ss["Heading2"],
            textColor=TEXTO_PRINCIPAL, fontSize=16, spaceAfter=10, spaceBefore=20,
        ),
        "texto": ParagraphStyle(
            "texto", parent=ss["Normal"],
            textColor=TEXTO_SECUNDARIO, fontSize=11, spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "caption", parent=ss["Normal"],
            textColor=TEXTO_TERCIARIO, fontSize=9, alignment=TA_CENTER,
        ),
    }


def pintar_fundo(canvas, doc):
    """Pinta o fundo de cada página com a cor do dashboard."""
    canvas.saveState()
    canvas.setFillColor(BG_PRINCIPAL)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.restoreState()


def kpis(df_a):
    total = len(df_a)
    conformes = (df_a["resultado"].str.lower() == "conforme").sum()
    nao_conf = (df_a["resultado"].str.lower() == "não conforme").sum()
    taxa = (nao_conf / total * 100) if total else 0
    return [
        ("TOTAL DE ANÁLISES", f"{total:,}"),
        ("ANÁLISES CONFORMES", f"{conformes:,}"),
        ("ANÁLISES NÃO CONFORMES", f"{nao_conf:,}"),
        ("TAXA DE NÃO CONFORMIDADE", f"{taxa:.2f}%"),
    ]


def tabela_kpis(dados):
    tabela = Table(
        [[k, v] for k, v in dados],
        colWidths=[8 * cm, 5 * cm],
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXTO_SECUNDARIO),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXTO_PRINCIPAL),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDA_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA_CARD),
    ]))
    return tabela


# ============================================================
# GRÁFICOS
# ============================================================

def g1_analises_filial(df_a):
    """Gráfico 1: Análises (barra) + NCs (linha). Número só na barra."""
    resumo = df_a.groupby("filial").agg(
        total=("id_analise", "count"),
        nc=("qtd_nc", "sum"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["filial"], y=resumo["total"], name="Análises",
        marker_color=PLOTLY_VERDE,
        text=resumo["total"], textposition="outside",
        textfont=dict(color="#F0F6FC", size=12),
        cliponaxis=False,
    ))
    fig.add_trace(go.Scatter(
        x=resumo["filial"], y=resumo["nc"], name="NCs",
        mode="lines+markers",
        marker=dict(color=PLOTLY_VERMELHO, size=10),
        line=dict(width=3), yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Análises", side="left"),
        yaxis2=dict(title="NCs", overlaying="y", side="right"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g2_taxa_conformidade(df_a):
    resumo = df_a.groupby("filial").agg(
        total=("id_analise", "count"),
        conformes=("resultado", lambda s: (s.str.lower() == "conforme").sum()),
    ).reset_index()
    resumo = resumo.assign(taxa=resumo["conformes"] / resumo["total"] * 100)
    resumo = resumo.sort_values("taxa", ascending=False)

    fig = px.bar(
        resumo, x="filial", y="taxa",
        color="taxa", color_continuous_scale="RdYlGn",
        labels={"filial": "Filial", "taxa": "Taxa de Conformidade (%)"},
        text="taxa",
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        textfont=dict(color="#F0F6FC", size=12),
        cliponaxis=False,
    )
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g3_distribuicao_mes(df_a):
    resumo = df_a.groupby("mes").agg(
        total=("id_analise", "count"),
        nc=("qtd_nc", "sum"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["mes"], y=resumo["total"], name="Análises",
        marker_color=PLOTLY_VERDE,
        text=resumo["total"], textposition="outside",
        textfont=dict(color="#F0F6FC", size=12),
        cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        x=resumo["mes"], y=resumo["nc"], name="NCs",
        marker_color=PLOTLY_VERMELHO,
        text=resumo["nc"], textposition="outside",
        textfont=dict(color="#F0F6FC", size=12),
        cliponaxis=False,
    ))
    fig.update_layout(
        barmode="group", xaxis_title="Mês", yaxis_title="Quantidade",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g4_dia_semana(df_a):
    """Gráfico 4: Análises (barra) + taxa NC (linha). Número só na barra."""
    df = df_a.assign(dia=df_a["dia_semana"].map(MAPA_DIAS))
    resumo = df.groupby("dia").agg(
        total=("id_analise", "count"),
        nc=("qtd_nc", "sum"),
    ).reset_index()
    resumo = resumo.assign(
        taxa=resumo["nc"] / resumo["total"] * 100,
        ordem=resumo["dia"].map({v: i for i, v in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"])}),
    ).sort_values("ordem")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["dia"], y=resumo["total"], name="Análises",
        marker_color=PLOTLY_VERDE,
        text=resumo["total"], textposition="outside",
        textfont=dict(color="#F0F6FC", size=12),
        cliponaxis=False,
    ))
    fig.add_trace(go.Scatter(
        x=resumo["dia"], y=resumo["taxa"], name="Taxa NC (%)",
        mode="lines+markers",
        marker=dict(color=PLOTLY_VERMELHO, size=8),
        line=dict(width=3), yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Análises", side="left"),
        yaxis2=dict(title="Taxa NC (%)", overlaying="y", side="right"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g5_resultado(df_a):
    resumo = df_a.groupby("resultado").agg(total=("id_analise", "count")).reset_index()
    cores = {"Conforme": PLOTLY_VERDE, "Conforme com Observação": PLOTLY_AMARELO,
             "Não Conforme": PLOTLY_VERMELHO}
    fig = px.bar(
        resumo, x="resultado", y="total",
        color="resultado", color_discrete_map=cores,
        labels={"resultado": "Resultado", "total": "Análises"}, text="total",
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#F0F6FC", size=13),
        cliponaxis=False,
    )
    fig.update_layout(showlegend=False)
    return aplicar_tema(fig, 400)


def g6_classificacao(df_a):
    resumo = df_a.groupby("classificacao").agg(total=("id_analise", "count")).reset_index()
    ordem = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
    cores = {"Ótimo": PLOTLY_VERDE, "Bom": PLOTLY_VERDE_CLARO,
             "Regular": PLOTLY_AMARELO, "Ruim": PLOTLY_LARANJA,
             "Péssimo": PLOTLY_VERMELHO}
    fig = px.pie(
        resumo, names="classificacao", values="total",
        color="classificacao", color_discrete_map=cores,
        category_orders={"classificacao": ordem}, hole=0.4,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="value+percent",
        textfont=dict(color="#FFFFFF", size=13),
        insidetextorientation="radial",
    )
    return aplicar_tema(fig, 400)


def g7_top_unidades(df_n):
    """Top 10 unidades. No PDF, com números visíveis (decisão: PDF é estático)."""
    resumo = df_n.groupby("codigo_unidade").agg(total=("codigo_nc", "count")).reset_index()
    resumo = resumo.sort_values("total", ascending=False).head(10)
    resumo = resumo.assign(
        codigo_unidade=resumo["codigo_unidade"].apply(
            lambda x: f"Unidade {int(x)}" if pd.notna(x) else "Sem unidade"
        )
    )

    fig = px.bar(
        resumo, x="total", y="codigo_unidade", orientation="h",
        color="total", color_continuous_scale="Reds",
        labels={"total": "NCs", "codigo_unidade": ""}, text="total",
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(color="#F0F6FC", size=11),
        cliponaxis=False,
    )
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 500)


def g8_gravidade(df_n):
    resumo = df_n.groupby("gravidade").agg(total=("codigo_nc", "count")).reset_index()
    resumo = resumo.sort_values("total", ascending=False)
    fig = px.bar(
        resumo, x="gravidade", y="total",
        color="total", color_continuous_scale="Reds",
        labels={"gravidade": "Gravidade", "total": "NCs"}, text="total",
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(color="#F0F6FC", size=13),
        cliponaxis=False,
    )
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g9_top_codigos(df_n):
    """Top 15 códigos. No PDF, com números visíveis."""
    resumo = df_n.groupby("codigo_nc").agg(total=("codigo_nc", "count")).reset_index()
    resumo = resumo.sort_values("total", ascending=False).head(15)
    resumo = resumo.assign(
        codigo_nc=resumo["codigo_nc"].apply(lambda x: f"Item {x}")
    ).sort_values("total", ascending=True)

    fig = px.bar(
        resumo, x="total", y="codigo_nc", orientation="h",
        color="total", color_continuous_scale="Reds",
        labels={"total": "NCs", "codigo_nc": ""}, text="total",
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(color="#F0F6FC", size=10),
        cliponaxis=False,
    )
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 500)


def g10_nc_area(df_n):
    """NCs por Área do Checklist (antes: Capítulo)."""
    resumo = df_n.groupby("capitulo_nc").agg(total=("codigo_nc", "count")).reset_index()
    resumo = resumo.assign(cap_int=resumo["capitulo_nc"].astype(int)).sort_values("cap_int")
    fig = px.bar(
        resumo, x="capitulo_nc", y="total",
        color="total", color_continuous_scale="Greens",
        labels={"capitulo_nc": "Área", "total": "NCs"}, text="total",
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(color="#F0F6FC", size=13),
        cliponaxis=False,
    )
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g11_filial_gravidade(df_n):
    """Filial x Gravidade. Empilhada com número dentro (PDF não tem hover)."""
    ordem = ["Baixa", "Média", "Alta", "Crítica"]
    pivot = df_n.pivot_table(
        index="filial", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in ordem:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[ordem].assign(total=pivot[ordem].sum(axis=1))
    pivot = pivot.sort_values("total", ascending=False).drop(columns="total").reset_index()

    fig = go.Figure()
    cores = {"Baixa": PLOTLY_VERDE, "Média": PLOTLY_AMARELO,
             "Alta": PLOTLY_LARANJA, "Crítica": PLOTLY_VERMELHO}
    for g in ordem:
        fig.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g,
            orientation="h", marker_color=cores[g],
            text=pivot[g], textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#FFFFFF", size=11),
        ))
    fig.update_layout(
        barmode="stack", xaxis_title="NCs", yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g12_nc_dia_semana(df_a, df_n):
    """NCs registradas por dia da semana (novo no PDF)."""
    df_n_dia = df_n.merge(
        df_a[["id_analise", "dia_semana"]], on="id_analise", how="left"
    )
    df_n_dia = df_n_dia.assign(dia=df_n_dia["dia_semana"].map(MAPA_DIAS))

    resumo = df_n_dia.groupby("dia").size().reset_index(name="total")
    resumo = resumo.assign(
        ordem=resumo["dia"].map({v: i for i, v in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"])})
    ).sort_values("ordem")

    fig = px.bar(
        resumo, x="dia", y="total",
        color="total", color_continuous_scale="Reds",
        labels={"dia": "Dia", "total": "NCs"}, text="total",
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(color="#F0F6FC", size=12),
        cliponaxis=False,
    )
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g13_gravidade_area(df_n):
    """Gravidade das NCs por Área. Empilhada com número dentro (PDF não tem hover)."""
    ordem = ["Baixa", "Média", "Alta", "Crítica"]
    pivot = df_n.pivot_table(
        index="capitulo_nc", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in ordem:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[ordem].reset_index().sort_values("capitulo_nc", key=lambda s: s.astype(int))

    fig = go.Figure()
    cores = {"Baixa": PLOTLY_VERDE, "Média": PLOTLY_AMARELO,
             "Alta": PLOTLY_LARANJA, "Crítica": PLOTLY_VERMELHO}
    for g in ordem:
        fig.add_trace(go.Bar(
            x=pivot["capitulo_nc"], y=pivot[g], name=g,
            marker_color=cores[g],
            text=pivot[g], textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#FFFFFF", size=11),
        ))
    fig.update_layout(
        barmode="stack", xaxis_title="Área", yaxis_title="NCs",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


# ============================================================
# MONTAGEM DO PDF
# ============================================================

def gerar_pdf():
    print("Carregando dados...")
    df_a, df_n = carregar_dados()
    est = estilos()

    print("Gerando gráficos...")
    imagens = {
        "g1": fig_para_imagem(g1_analises_filial(df_a), 1200, 450),
        "g2": fig_para_imagem(g2_taxa_conformidade(df_a), 1200, 450),
        "g3": fig_para_imagem(g3_distribuicao_mes(df_a), 1200, 450),
        "g4": fig_para_imagem(g4_dia_semana(df_a), 1200, 450),
        "g5": fig_para_imagem(g5_resultado(df_a), 1200, 450),
        "g6": fig_para_imagem(g6_classificacao(df_a), 1200, 450),
    }
    if df_n is not None:
        imagens["g7"]  = fig_para_imagem(g7_top_unidades(df_n), 1200, 500)
        imagens["g8"]  = fig_para_imagem(g8_gravidade(df_n), 1200, 450)
        imagens["g9"]  = fig_para_imagem(g9_top_codigos(df_n), 1200, 600)
        imagens["g10"] = fig_para_imagem(g10_nc_area(df_n), 1200, 450)
        imagens["g11"] = fig_para_imagem(g11_filial_gravidade(df_n), 1200, 450)
        imagens["g12"] = fig_para_imagem(g12_nc_dia_semana(df_a, df_n), 1200, 450)
        imagens["g13"] = fig_para_imagem(g13_gravidade_area(df_n), 1200, 450)

    print("Montando PDF...")
    doc = SimpleDocTemplate(
        ARQ_PDF, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    historia = []

    # ----- Capa -----
    historia.append(Paragraph("CCO - Indicadores Operacionais", est["titulo"]))
    historia.append(Paragraph(
        f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        est["caption"],
    ))
    historia.append(Spacer(1, 1 * cm))
    historia.append(Paragraph(
        f"Análises: {len(df_a):,} | NCs: {len(df_n) if df_n is not None else 0:,}",
        est["texto"],
    ))
    historia.append(Spacer(1, 0.5 * cm))
    historia.append(tabela_kpis(kpis(df_a)))
    historia.append(PageBreak())

    # ----- Seções -----
    def secao(titulo, img_key):
        """Envolve título + imagem + spacer num KeepTogether pra não cortar entre páginas."""
        bloco = [
            Paragraph(titulo, est["subtitulo"]),
            Image(imagens[img_key], width=17 * cm, height=6.5 * cm),
            Spacer(1, 0.8 * cm),
        ]
        historia.append(KeepTogether(bloco))

    def secao_dupla(titulo1, img1, titulo2, img2):
        """Duas seções na mesma 'unidade' — evita que se separem se uma só não couber."""
        bloco = [
            Paragraph(titulo1, est["subtitulo"]),
            Image(imagens[img1], width=17 * cm, height=6.5 * cm),
            Spacer(1, 0.4 * cm),
            Paragraph(titulo2, est["subtitulo"]),
            Image(imagens[img2], width=17 * cm, height=6.5 * cm),
            Spacer(1, 0.8 * cm),
        ]
        historia.append(KeepTogether(bloco))

    # Página 2: filial
    secao_dupla(
        "Análises e NCs por Filial", "g1",
        "Taxa de Conformidade por Filial", "g2",
    )
    historia.append(PageBreak())

    # Página 3: mensal + dia
    secao_dupla(
        "Distribuição Mensal de Análises e NCs", "g3",
        "Distribuição por Dia da Semana", "g4",
    )
    historia.append(PageBreak())

    # Página 4: resultado + classificação + gravidade
    secao_dupla(
        "Distribuição por Resultado", "g5",
        "Distribuição por Classificação", "g6",
    )
    secao("NCs por Gravidade", "g8")
    historia.append(PageBreak())

    # Página 5: top unidades + top códigos (g9 é alto)
    secao("Unidades com Maior Incidência de NCs", "g7")
    secao("Itens do Checklist com Maior Reincidência", "g9")
    historia.append(PageBreak())

    if df_n is not None:
        # Página 6: área + filial x gravidade
        secao_dupla(
            "NCs por Área do Checklist", "g10",
            "Filial x Gravidade", "g11",
        )
        historia.append(PageBreak())

        # Página 7: NC por dia + gravidade x área
        secao_dupla(
            "NCs Registradas por Dia da Semana", "g12",
            "Gravidade das NCs por Área", "g13",
        )

    doc.build(historia, onFirstPage=pintar_fundo, onLaterPages=pintar_fundo)
    print(f"PDF gerado: {ARQ_PDF}")


if __name__ == "__main__":
    gerar_pdf()