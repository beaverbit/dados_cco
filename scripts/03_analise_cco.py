# 03_analise_cco.py
# Meu objetivo: gerar os KPIs operacionais do CCO.

import pandas as pd
import numpy as np
import os

# Raiz do projeto (pasta pai de scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQ_ANALISES = os.path.join(BASE_DIR, "dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join(BASE_DIR, "dados_tratados", "nao_conformidades_limpas.csv")
ARQ_SAIDA = os.path.join(BASE_DIR, "dados_tratados", "resultados_analise_cco.csv")

GRAVIDADES_ORDEM = ["Baixa", "Média", "Alta", "Crítica"]


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

    print(f"Análises: {len(df_a):,}")
    if df_n is not None:
        print(f"NCs:      {len(df_n):,}")

    return df_a, df_n


def kpi_geral(df_a):
    print("\n" + "=" * 60)
    print("KPI 1: Visão geral")
    print("=" * 60)

    total = len(df_a)
    resultado_lower = df_a["resultado"].astype(str).str.lower()
    conformes = (resultado_lower == "conforme").sum()
    conforme_obs = (resultado_lower == "conforme com observação").sum()
    nao_conformes = (resultado_lower == "não conforme").sum()

    resumo = pd.DataFrame([{
        "total_analises": total,
        "conformes": conformes,
        "conformes_com_observacao": conforme_obs,
        "nao_conformes": nao_conformes,
        "taxa_conformidade_pct": round(conformes / total * 100, 2) if total else 0,
        "taxa_nao_conformidade_pct": round(nao_conformes / total * 100, 2) if total else 0,
        "media_nota_pct": round(df_a["pct_nota"].mean(), 2) if "pct_nota" in df_a and len(df_a) > 0 else None,
        "total_nc": int(df_a["qtd_nc"].sum()) if "qtd_nc" in df_a else None,
    }])
    print(resumo.to_string(index=False))
    return resumo


def kpi_por_filial(df_a):
    print("\n" + "=" * 60)
    print("KPI 2: Desempenho por filial")
    print("=" * 60)

    resumo = df_a.groupby("filial").agg(
        total_analises=("id_analise", "count"),
        media_nota=("pct_nota", "mean"),
        total_nc=("qtd_nc", "sum"),
    ).reset_index()

    nao_conf = df_a[df_a["resultado"].astype(str).str.lower() == "não conforme"] \
    .groupby("filial").size()
    resumo = resumo.assign(
        nao_conformes=resumo["filial"].map(nao_conf).fillna(0).astype(int)
    )
    resumo = resumo.assign(
        taxa_nao_conformidade_pct=(
            resumo["nao_conformes"] / resumo["total_analises"] * 100
        ).round(2),
        media_nota=resumo["media_nota"].round(2),
    )

    resumo = resumo.sort_values("taxa_nao_conformidade_pct", ascending=False)
    print(resumo.to_string(index=False))
    return resumo


def kpi_por_unidade(df_a):
    print("\n" + "=" * 60)
    print("KPI 3: Top 15 unidades com mais NCs")
    print("=" * 60)

    resumo = df_a.groupby("nome_da_unidade").agg(
        total_analises=("id_analise", "count"),
        total_nc=("qtd_nc", "sum"),
    ).reset_index()

    nao_conf = df_a[df_a["resultado"].str.lower() == "não conforme"] \
        .groupby("nome_da_unidade").size()
    resumo = resumo.assign(
        nao_conformes=resumo["nome_da_unidade"].map(nao_conf).fillna(0).astype(int)
    )
    resumo = resumo.assign(
        taxa_nao_conformidade_pct=(
            resumo["nao_conformes"] / resumo["total_analises"] * 100
        ).round(2)
    )

    resumo = resumo.sort_values("total_nc", ascending=False).head(15)
    print(resumo.to_string(index=False))
    return resumo


def kpi_por_analista(df_a):
    print("\n" + "=" * 60)
    print("KPI 4: Produtividade por analista")
    print("=" * 60)

    resumo = df_a.groupby("analista").agg(
        total_analises=("id_analise", "count"),
        media_nota=("pct_nota", "mean"),
        total_nc=("qtd_nc", "sum"),
    ).reset_index()
    resumo = resumo.assign(media_nota=resumo["media_nota"].round(2))
    resumo = resumo.sort_values("total_analises", ascending=False)
    print(resumo.to_string(index=False))
    return resumo


def kpi_por_status(df_a):
    print("\n" + "=" * 60)
    print("KPI 5: Análises por status")
    print("=" * 60)

    resumo = df_a["status"].value_counts().reset_index()
    resumo.columns = ["status", "total"]
    resumo = resumo.assign(
        percentual_pct=(resumo["total"] / resumo["total"].sum() * 100).round(2)
    )
    print(resumo.to_string(index=False))
    return resumo


def kpi_por_mes(df_a):
    print("\n" + "=" * 60)
    print("KPI 6: Análises por mês")
    print("=" * 60)

    resumo = df_a.groupby(["ano", "mes"]).agg(
        total=("id_analise", "count"),
        media_nota=("pct_nota", "mean"),
        total_nc=("qtd_nc", "sum"),
    ).reset_index()
    resumo = resumo.assign(media_nota=resumo["media_nota"].round(2))
    resumo = resumo.sort_values(["ano", "mes"])
    print(resumo.to_string(index=False))
    return resumo


def kpi_nc_por_gravidade(df_n):
    print("\n" + "=" * 60)
    print("KPI 7: NCs por gravidade")
    print("=" * 60)

    resumo = df_n["gravidade"].value_counts().reindex(GRAVIDADES_ORDEM).fillna(0).reset_index()
    resumo.columns = ["gravidade", "total"]
    resumo = resumo.assign(
        percentual_pct=(resumo["total"] / resumo["total"].sum() * 100).round(2)
    )
    print(resumo.to_string(index=False))
    return resumo


def kpi_nc_por_classificacao(df_n):
    print("\n" + "=" * 60)
    print("KPI 8: NCs por classificação")
    print("=" * 60)

    resumo = df_n.groupby("classificacao").agg(
        total=("codigo_nc", "count"),
        criticas=("gravidade", lambda s: (s == "Crítica").sum()),
    ).reset_index()
    resumo = resumo.assign(
        percentual_pct=(resumo["total"] / resumo["total"].sum() * 100).round(2)
    )
    resumo = resumo.sort_values("total", ascending=False)
    print(resumo.to_string(index=False))
    return resumo


def kpi_nc_por_capitulo(df_n):
    print("\n" + "=" * 60)
    print("KPI 9: NCs por capítulo do checklist")
    print("=" * 60)

    resumo = df_n.groupby("capitulo_nc").agg(
        total=("codigo_nc", "count"),
        criticas=("gravidade", lambda s: (s == "Crítica").sum()),
    ).reset_index()
    resumo = resumo.assign(
        taxa_criticidade_pct=(resumo["criticas"] / resumo["total"] * 100).round(2)
    )
    resumo = resumo.sort_values("capitulo_nc", key=lambda s: s.astype(int))
    print(resumo.to_string(index=False))
    return resumo


def kpi_top_ncs(df_n):
    print("\n" + "=" * 60)
    print("KPI 10: Top 15 códigos de NC mais recorrentes")
    print("=" * 60)

    resumo = df_n.groupby("codigo_nc").agg(
        total=("codigo_nc", "count"),
        criticas=("gravidade", lambda s: (s == "Crítica").sum()),
    ).reset_index().sort_values("total", ascending=False).head(15)
    print(resumo.to_string(index=False))
    return resumo


def kpi_nc_por_filial(df_n):
    print("\n" + "=" * 60)
    print("KPI 11: NCs por filial")
    print("=" * 60)

    resumo = df_n.groupby("filial").agg(
        total_nc=("codigo_nc", "count"),
        criticas=("gravidade", lambda s: (s == "Crítica").sum()),
    ).reset_index().sort_values("total_nc", ascending=False)
    resumo = resumo.assign(
        taxa_criticidade_pct=(resumo["criticas"] / resumo["total_nc"] * 100).round(2)
    )
    print(resumo.to_string(index=False))
    return resumo


def kpi_filial_x_gravidade(df_n):
    print("\n" + "=" * 60)
    print("KPI 12: Filial x Gravidade")
    print("=" * 60)

    pivot = df_n.pivot_table(
        index="filial", columns="gravidade", values="codigo_nc",
        aggfunc="count", fill_value=0,
    )
    for g in GRAVIDADES_ORDEM:
        if g not in pivot.columns:
            pivot[g] = 0
    pivot = pivot[GRAVIDADES_ORDEM]
    pivot = pivot.assign(total=pivot.sum(axis=1))
    pivot = pivot.sort_values("total", ascending=False).reset_index()
    print(pivot.to_string(index=False))
    return pivot


def kpi_nc_por_analista(df_n):
    print("\n" + "=" * 60)
    print("KPI 13: NCs registradas por analista")
    print("=" * 60)

    resumo = df_n.groupby("analista").agg(
        total_nc=("codigo_nc", "count"),
        criticas=("gravidade", lambda s: (s == "Crítica").sum()),
    ).reset_index().sort_values("total_nc", ascending=False)
    print(resumo.to_string(index=False))
    return resumo


def salvar(resultados):
    # Cria uma pasta só para os KPIs, para não misturar com os dados limpos
    pasta_kpis = os.path.join(BASE_DIR, "dados_tratados", "kpis")
    os.makedirs(pasta_kpis, exist_ok=True)
    
    print("\nSalvando KPIs individuais...")
    for nome, tabela in resultados.items():
        if tabela is None:
            continue
        
        # Limpa o nome do arquivo (ex: "KPI 1 - Visao geral" vira "kpi_01_visao_geral.csv")
        nome_arquivo = nome.lower().replace(" - ", "_").replace(" ", "_").replace("__", "_") + ".csv"
        caminho = os.path.join(pasta_kpis, nome_arquivo)
        
        # Salva no formato CSV correto (separado por ;)
        tabela.to_csv(caminho, index=False, sep=";", encoding="utf-8")
        print(f"  -> {nome_arquivo}")
        
    print(f"\nTodos os KPIs foram salvos em: {pasta_kpis}")


if __name__ == "__main__":
    df_a, df_n = carregar()

    resultados = {}
    resultados["KPI 1 - Visao geral"] = kpi_geral(df_a)
    resultados["KPI 2 - Por filial"] = kpi_por_filial(df_a)
    resultados["KPI 3 - Por unidade"] = kpi_por_unidade(df_a)
    resultados["KPI 4 - Por analista"] = kpi_por_analista(df_a)
    resultados["KPI 5 - Por status"] = kpi_por_status(df_a)
    resultados["KPI 6 - Por mes"] = kpi_por_mes(df_a)

    if df_n is not None:
        resultados["KPI 7 - NC por gravidade"] = kpi_nc_por_gravidade(df_n)
        resultados["KPI 8 - NC por classificacao"] = kpi_nc_por_classificacao(df_n)
        resultados["KPI 9 - NC por capitulo"] = kpi_nc_por_capitulo(df_n)
        resultados["KPI 10 - Top codigos NC"] = kpi_top_ncs(df_n)
        resultados["KPI 11 - NC por filial"] = kpi_nc_por_filial(df_n)
        resultados["KPI 12 - Filial x Gravidade"] = kpi_filial_x_gravidade(df_n)
        resultados["KPI 13 - NC por analista"] = kpi_nc_por_analista(df_n)

    salvar(resultados)
    print("\nAnálise concluída.")
