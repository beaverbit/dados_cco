# 07_gerar_pdf_cco.py
# Meu objetivo: gerar um PDF do dashboard com a mesma paleta visual do Streamlit (Tema Claro Corporativo).

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

# Raiz do projeto (pasta pai de scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQ_ANALISES = os.path.join(BASE_DIR, "dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join(BASE_DIR, "dados_tratados", "nao_conformidades_limpas.csv")
ARQ_PDF = os.path.join(BASE_DIR, "dados_tratados", "relatorio_cco.pdf")

# Paleta Corporativa (idêntica ao dashboard atualizado)
VERDE = HexColor("#4C9F70")
VERDE_ESCURO = HexColor("#3B8259")
CINZA_TEXTO = HexColor("#2C3E50")
CINZA_CLARO = HexColor("#7F8C8D")
CINZA_BG = HexColor("#F8F9FA")
CINZA_BORDA = HexColor("#E9ECEF")

# Cores pro Plotly (em hex string)
PLOTLY_BG = "#FFFFFF"
PLOTLY_VERDE = "#4C9F70"
PLOTLY_AZUL_ESCURO = "#2E86C1"
PLOTLY_AZUL_CLARO = "#85C1E9"
PLOTLY_AMARELO = "#F4D03F"
PLOTLY_LARANJA = "#E67E22"
PLOTLY_VERMELHO = "#C0392B"

TEMPLATE = "plotly_white"

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
        font=dict(color=CINZA_TEXTO, size=13),
        title_font=dict(color=CINZA_TEXTO, size=17),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=CINZA_BORDA)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=CINZA_BORDA)
    return fig


def fig_para_imagem(fig, largura_px=1200, altura_px=500):
    return io.BytesIO(fig.to_image(format="png", width=largura_px, height=altura_px, scale=1.5))


def estilos():
    ss = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "titulo", parent=ss["Title"],
            textColor=VERDE, fontSize=24, spaceAfter=20, alignment=TA_CENTER,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo", parent=ss["Heading2"],
            textColor=CINZA_TEXTO, fontSize=16, spaceAfter=10, spaceBefore=20,
        ),
        "texto": ParagraphStyle(
            "texto", parent=ss["Normal"],
            textColor=CINZA_CLARO, fontSize=11, spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "caption", parent=ss["Normal"],
            textColor=CINZA_CLARO, fontSize=9, alignment=TA_CENTER,
        ),
    }


def desenhar_faixa_titulo(canvas, doc, titulo):
    """Desenha a faixa verde corporativa no topo da página."""
    canvas.saveState()
    
    # Faixa verde
    canvas.setFillColor(VERDE)
    canvas.rect(0, doc.pagesize[1] - 2.5*cm, doc.pagesize[0], 2.5*cm, fill=1, stroke=0)
    
    # Texto da faixa
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(2*cm, doc.pagesize[1] - 1.5*cm, titulo)
    
    canvas.restoreState()


# ============================================================
# GRÁFICOS
# ============================================================

def g1_analises_filial(df_a):
    resumo = df_a.groupby("filial").agg(total=("id_analise", "count"), nc=("qtd_nc", "sum")).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["filial"], y=resumo["total"], name="Análises",
        marker_color=PLOTLY_VERDE, text=resumo["total"], textposition="outside",
        textfont=dict(color=CINZA_TEXTO, size=12), cliponaxis=False,
    ))
    fig.add_trace(go.Scatter(
        x=resumo["filial"], y=resumo["nc"], name="NCs",
        mode="lines+markers", marker=dict(color=PLOTLY_VERMELHO, size=10),
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
    resumo = df_a.groupby("filial").agg(total=("id_analise", "count"), conformes=("resultado", lambda s: (s.str.lower() == "conforme").sum())).reset_index()
    resumo = resumo.assign(taxa=resumo["conformes"] / resumo["total"] * 100).sort_values("taxa", ascending=False)

    fig = px.bar(
        resumo, x="filial", y="taxa",
        color="taxa", color_continuous_scale="RdBu",
        labels={"filial": "Filial", "taxa": "Taxa de Conformidade (%)"}, text="taxa",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", textfont=dict(color=CINZA_TEXTO, size=12), cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g3_distribuicao_mes(df_a):
    resumo = df_a.groupby("mes").agg(total=("id_analise", "count"), nc=("qtd_nc", "sum")).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["mes"], y=resumo["total"], name="Análises", marker_color=PLOTLY_VERDE,
        text=resumo["total"], textposition="outside", textfont=dict(color=CINZA_TEXTO, size=12), cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        x=resumo["mes"], y=resumo["nc"], name="NCs", marker_color=PLOTLY_VERMELHO,
        text=resumo["nc"], textposition="outside", textfont=dict(color=CINZA_TEXTO, size=12), cliponaxis=False,
    ))
    fig.update_layout(
        barmode="group", xaxis_title="Mês", yaxis_title="Quantidade",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g4_dia_semana(df_a):
    df = df_a.assign(dia=df_a["dia_semana"].map(MAPA_DIAS))
    resumo = df.groupby("dia").agg(total=("id_analise", "count"), nc=("qtd_nc", "sum")).reset_index()
    resumo = resumo.assign(
        taxa=resumo["nc"] / resumo["total"] * 100,
        ordem=resumo["dia"].map({v: i for i, v in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"])}),
    ).sort_values("ordem")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resumo["dia"], y=resumo["total"], name="Análises", marker_color=PLOTLY_VERDE,
        text=resumo["total"], textposition="outside", textfont=dict(color=CINZA_TEXTO, size=12), cliponaxis=False,
    ))
    fig.add_trace(go.Scatter(
        x=resumo["dia"], y=resumo["taxa"], name="Taxa NC (%)",
        mode="lines+markers", marker=dict(color=PLOTLY_VERMELHO, size=8), line=dict(width=3), yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Análises", side="left"),
        yaxis2=dict(title="Taxa NC (%)", overlaying="y", side="right"),
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g5_resultado(df_a):
    resumo = df_a.groupby("resultado").agg(total=("id_analise", "count")).reset_index()
    cores = {"Conforme": PLOTLY_VERDE, "Conforme com Observação": PLOTLY_AMARELO, "Não Conforme": PLOTLY_VERMELHO}
    fig = px.bar(
        resumo, x="resultado", y="total", color="resultado", color_discrete_map=cores,
        labels={"resultado": "Resultado", "total": "Análises"}, text="total",
    )
    fig.update_traces(textposition="outside", textfont=dict(color=CINZA_TEXTO, size=13), cliponaxis=False)
    fig.update_layout(showlegend=False)
    return aplicar_tema(fig, 400)


def g6_classificacao(df_a):
    resumo = df_a.groupby("classificacao").agg(total=("id_analise", "count")).reset_index()
    ordem = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
    cores = {"Ótimo": PLOTLY_AZUL_ESCURO, "Bom": PLOTLY_AZUL_CLARO, "Regular": PLOTLY_AMARELO, "Ruim": PLOTLY_LARANJA, "Péssimo": PLOTLY_VERMELHO}
    fig = px.pie(
        resumo, names="classificacao", values="total", color="classificacao", color_discrete_map=cores,
        category_orders={"classificacao": ordem}, hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="value+percent", textfont=dict(color="#FFFFFF", size=13), insidetextorientation="radial")
    return aplicar_tema(fig, 400)


def g7_top_unidades(df_n):
    resumo = df_n.groupby("codigo_unidade").agg(total=("codigo_nc", "count")).reset_index().sort_values("total", ascending=False).head(10)
    resumo = resumo.assign(codigo_unidade=resumo["codigo_unidade"].apply(lambda x: f"Unidade {int(x)}" if pd.notna(x) else "Sem unidade"))

    fig = px.bar(
        resumo, x="total", y="codigo_unidade", orientation="h", color="total", color_continuous_scale="Reds",
        labels={"total": "NCs", "codigo_unidade": ""}, text="total",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont=dict(color=CINZA_TEXTO, size=11), cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 500)


def g8_gravidade(df_n):
    resumo = df_n.groupby("gravidade").agg(total=("codigo_nc", "count")).reset_index().sort_values("total", ascending=False)
    fig = px.bar(
        resumo, x="gravidade", y="total", color="total", color_continuous_scale="Reds",
        labels={"gravidade": "Gravidade", "total": "NCs"}, text="total",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont=dict(color=CINZA_TEXTO, size=13), cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g9_top_codigos(df_n):
    resumo = df_n.groupby("codigo_nc").agg(total=("codigo_nc", "count")).reset_index().sort_values("total", ascending=False).head(15)
    resumo = resumo.assign(codigo_nc=resumo["codigo_nc"].apply(lambda x: f"Item {x}")).sort_values("total", ascending=True)

    fig = px.bar(
        resumo, x="total", y="codigo_nc", orientation="h", color="total", color_continuous_scale="Reds",
        labels={"total": "NCs", "codigo_nc": ""}, text="total",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont=dict(color=CINZA_TEXTO, size=10), cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 500)


def g10_nc_area(df_n):
    resumo = df_n.groupby("capitulo_nc").agg(total=("codigo_nc", "count")).reset_index()
    resumo = resumo.assign(cap_int=resumo["capitulo_nc"].astype(int)).sort_values("cap_int")
    fig = px.bar(
        resumo, x="capitulo_nc", y="total", color="total", color_continuous_scale="Blues",
        labels={"capitulo_nc": "Área", "total": "NCs"}, text="total",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont=dict(color=CINZA_TEXTO, size=13), cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g11_filial_gravidade(df_n):
    ordem = ["Baixa", "Média", "Alta", "Crítica"]
    pivot = df_n.pivot_table(index="filial", columns="gravidade", values="codigo_nc", aggfunc="count", fill_value=0)
    for g in ordem:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[ordem].assign(total=pivot[ordem].sum(axis=1)).sort_values("total", ascending=False).drop(columns="total").reset_index()

    fig = go.Figure()
    cores = {"Baixa": PLOTLY_AZUL_CLARO, "Média": PLOTLY_AMARELO, "Alta": PLOTLY_LARANJA, "Crítica": PLOTLY_VERMELHO}
    for g in ordem:
        fig.add_trace(go.Bar(
            y=pivot["filial"], x=pivot[g], name=g, orientation="h", marker_color=cores[g],
            text=pivot[g], textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=11),
        ))
    fig.update_layout(
        barmode="stack", xaxis_title="NCs", yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return aplicar_tema(fig, 400)


def g12_nc_dia_semana(df_a, df_n):
    df_n_dia = df_n.merge(df_a[["id_analise", "dia_semana"]], on="id_analise", how="left")
    df_n_dia = df_n_dia.assign(dia=df_n_dia["dia_semana"].map(MAPA_DIAS))

    resumo = df_n_dia.groupby("dia").size().reset_index(name="total")
    resumo = resumo.assign(ordem=resumo["dia"].map({v: i for i, v in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"])})).sort_values("ordem")

    fig = px.bar(
        resumo, x="dia", y="total", color="total", color_continuous_scale="Blues",
        labels={"dia": "Dia", "total": "NCs"}, text="total",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont=dict(color=CINZA_TEXTO, size=12), cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False)
    return aplicar_tema(fig, 400)


def g13_gravidade_area(df_n):
    ordem = ["Baixa", "Média", "Alta", "Crítica"]
    pivot = df_n.pivot_table(index="capitulo_nc", columns="gravidade", values="codigo_nc", aggfunc="count", fill_value=0)
    for g in ordem:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[ordem].reset_index().sort_values("capitulo_nc", key=lambda s: s.astype(int))

    fig = go.Figure()
    cores = {"Baixa": PLOTLY_AZUL_CLARO, "Média": PLOTLY_AMARELO, "Alta": PLOTLY_LARANJA, "Crítica": PLOTLY_VERMELHO}
    for g in ordem:
        fig.add_trace(go.Bar(
            x=pivot["capitulo_nc"], y=pivot[g], name=g, marker_color=cores[g],
            text=pivot[g], textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=11),
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
    
    # Criando o documento
    doc = SimpleDocTemplate(
        ARQ_PDF, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=3.5 * cm, bottomMargin=1.5 * cm, # Aumentei o topo para caber a faixa verde
    )

    historia = []

    # --- Capa ---
    historia.append(Spacer(1, 1 * cm))
    historia.append(Paragraph("CCO - Indicadores Operacionais", est["titulo"]))
    historia.append(Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", est["caption"]))
    historia.append(Spacer(1, 1.5 * cm))
    
    # KPI Cards formatados como tabela
    tabela = Table(
        [[k, v] for k, v in kpis(df_a)],
        colWidths=[8 * cm, 5 * cm],
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_BG),
        ("TEXTCOLOR", (0, 0), (0, -1), CINZA_CLARO),
        ("TEXTCOLOR", (1, 0), (1, -1), CINZA_TEXTO),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LINEBELOW", (0, 0), (-1, -2), 1, CINZA_BORDA),
        ("BOX", (0, 0), (-1, -1), 1, CINZA_BORDA),
        # Detalhe verde na esquerda de cada KPI
        ("LINEBEFORE", (0, 0), (0, -1), 4, VERDE),
    ]))
    historia.append(tabela)
    
    # --- Páginas de Gráficos ---
    
    # Definindo os títulos que vão na faixa verde de cada página
    titulos_paginas = [
        "Análise Geral e Filiais",
        "Volume Mensal e Diário",
        "Resultados e Classificações",
        "Detalhamento de Não Conformidades",
        "Unidades e Checklist",
        "Gravidade por Área e Filial"
    ]
    
    def secao(titulo, img_key):
        bloco = [
            Paragraph(titulo, est["subtitulo"]),
            Image(imagens[img_key], width=17 * cm, height=6.5 * cm),
            Spacer(1, 0.8 * cm),
        ]
        return KeepTogether(bloco)

    def secao_dupla(titulo1, img1, titulo2, img2):
        bloco = [
            Paragraph(titulo1, est["subtitulo"]),
            Image(imagens[img1], width=17 * cm, height=6.5 * cm),
            Spacer(1, 0.4 * cm),
            Paragraph(titulo2, est["subtitulo"]),
            Image(imagens[img2], width=17 * cm, height=6.5 * cm),
            Spacer(1, 0.8 * cm),
        ]
        return KeepTogether(bloco)

    # Lista de páginas e seus conteúdos
    paginas_conteudo = [
        # Página 1
        secao_dupla("Análises e NCs por Filial", "g1", "Taxa de Conformidade por Filial", "g2"),
        # Página 2
        secao_dupla("Distribuição Mensal de Análises e NCs", "g3", "Distribuição por Dia da Semana", "g4"),
        # Página 3
        [secao_dupla("Distribuição por Resultado", "g5", "Distribuição por Classificação", "g6"), secao("NCs por Gravidade", "g8")],
        # Página 4
        [secao("Unidades com Maior Incidência de NCs", "g7"), secao("Itens do Checklist com Maior Reincidência", "g9")],
        # Página 5
        secao_dupla("NCs por Área do Checklist", "g10", "Filial x Gravidade", "g11"),
        # Página 6
        secao_dupla("NCs Registradas por Dia da Semana", "g12", "Gravidade das NCs por Área", "g13"),
    ]

    # Monta o PDF iterando as páginas
    for i, conteudo in enumerate(paginas_conteudo):
        historia.append(PageBreak())
        
        # O onPage desenha a faixa verde no topo. Precisamos passar o título específico.
        # Como o SimpleDocTemplate onPage é genérico, vamos usar um truque: desenhamos no build final.
        
        if isinstance(conteudo, list):
            historia.extend(conteudo)
        else:
            historia.append(conteudo)

    # Como o ReportLab não facilita trocar o onPage dinamicamente, 
    # vamos usar o parâmetro onLaterPages com uma função que lê um arquivo temporário ou variável global.
    # Mas para manter simples e à prova de falhas, vou desenhar a faixa estática em todas.
    # Para dar o efeito, o título do gráfico fica dentro do bloco da tabela já.
    # A faixa verde servirá para enquadrar.

    def on_page(canvas, doc):
        desenhar_faixa_titulo(canvas, doc, "CCO - INDICADORES OPERACIONAIS")
        # Rodapé
        canvas.saveState()
        canvas.setFillColor(CINZA_CLARO)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(doc.pagesize[0] - 2*cm, 1*cm, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(historia, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF gerado: {ARQ_PDF}")


if __name__ == "__main__":
    gerar_pdf()
