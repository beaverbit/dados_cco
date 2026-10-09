# 02_limpeza_cco.py
# Meu objetivo: ler cada aba salva, separar por tipo, explodir NCs compostas, padronizar.

import pandas as pd
import os
import glob
import re

PASTA_BRUTOS = os.path.join("dados_tratados", "brutos")
ARQ_ANALISES = os.path.join("dados_tratados", "analises_limpas.csv")
ARQ_NCS = os.path.join("dados_tratados", "nao_conformidades_limpas.csv")
ARQ_PARAMS = os.path.join("dados_tratados", "parametros_limpos.csv")


def normalizar(s):
    s = str(s).strip().lower()
    for a, b in [("ç", "c"), ("ã", "a"), ("á", "a"), ("à", "a"),
                 ("é", "e"), ("ê", "e"), ("í", "i"),
                 ("ó", "o"), ("ô", "o"), ("ú", "u")]:
        s = s.replace(a, b)
    s = s.replace(" ", "_").replace("%", "pct").replace("-", "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def classificar_arquivo(nome):
    n = nome.lower()
    if n.startswith("analise__"):
        return "analise"
    if n.startswith("nc__"):
        return "nc"
    if n.startswith("parametro__"):
        return "parametro"
    return "desconhecido"


def achar_coluna(df, *candidatos):
    mapa = {normalizar(c): c for c in df.columns}
    for cand in candidatos:
        n = normalizar(cand)
        if n in mapa:
            return mapa[n]
    return None


def carregar_por_tipo(tipo_alvo):
    arquivos = sorted(glob.glob(os.path.join(PASTA_BRUTOS, "*.csv")))
    selecionados = []
    for arq in arquivos:
        nome = os.path.basename(arq)
        if classificar_arquivo(nome) != tipo_alvo:
            continue
        df = pd.read_csv(arq, sep=";", encoding="utf-8", low_memory=False, dtype=str)
        df.columns = [normalizar(c) for c in df.columns]
        print(f"  [{tipo_alvo}] {nome}: {df.shape[0]} linhas, {df.shape[1]} colunas")
        selecionados.append(df)

    if not selecionados:
        return None
    return pd.concat(selecionados, ignore_index=True, sort=False)


def limpar_analises(df):
    print("\n--- Limpando análises ---")

    mapa = {
        "id_analise": ["id_da_analise", "id_analise"],
        "id_checklist": ["id_checklist"],
        "analista": ["analista"],
        "filial": ["filial"],
        "data_da_avaliacao": ["data_da_avaliacao"],
        "resultado": ["resultado"],
        "classificacao": ["classificacao"],
        "pct_nota": ["pct_nota", "pct"],
        "qtd_nc": ["qtd_nc"],
        "observacoes_gerais": ["observacoes_gerais"],
        "status": ["status"],
        "nome_da_unidade": ["nome_da_unidade"],
    }

    rename = {}
    for canonico, candidatos in mapa.items():
        col = achar_coluna(df, *candidatos)
        if col:
            rename[col] = canonico

    df = df.rename(columns=rename)
    cols = [c for c in mapa.keys() if c in df.columns]
    df = df[cols].copy().drop_duplicates().reset_index(drop=True)

    if "data_da_avaliacao" in df.columns:
        df = df.assign(
            data_da_avaliacao=pd.to_datetime(
                df["data_da_avaliacao"], errors="coerce", dayfirst=True
            )
        )
        df = df.assign(
            ano=df["data_da_avaliacao"].dt.year,
            mes=df["data_da_avaliacao"].dt.month,
            dia_semana=df["data_da_avaliacao"].dt.day_name(),
        )

    if "pct_nota" in df.columns:
        df = df.assign(
            pct_nota=pd.to_numeric(
                df["pct_nota"].astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", ".", regex=False),
                errors="coerce",
            )
        )

    if "qtd_nc" in df.columns:
        df = df.assign(
            qtd_nc=pd.to_numeric(df["qtd_nc"], errors="coerce").fillna(0).astype(int)
        )

    for c in ["filial", "analista", "resultado", "classificacao", "status", "nome_da_unidade"]:
        if c in df.columns:
            df = df.assign(**{c: df[c].astype(str).str.strip()})

    if "id_analise" in df.columns:
        df = df[df["id_analise"].notna() & (df["id_analise"] != "nan")].reset_index(drop=True)

    print(f"Linhas: {len(df)}")
    return df


RE_CODIGO_NC = re.compile(r"^\d+(?:\.\d+)*$")


def limpar_ncs(df):
    print("\n--- Limpando NCs ---")

    mapa = {
        "id_analise": ["id_analise"],
        "pergunta": ["pergunta"],
        "classificacao": ["classificacao"],
        "codigo_unidade": ["departamento"],
        "gravidade": ["gravidade"],
        "observacao": ["observacao"],
        "filial": ["filial"],
        "analista": ["analista"],
        "criticidade": ["criticidade"],
    }

    rename = {}
    for canonico, candidatos in mapa.items():
        col = achar_coluna(df, *candidatos)
        if col:
            rename[col] = canonico

    df = df.rename(columns=rename)
    cols = [c for c in mapa.keys() if c in df.columns]
    df = df[cols].copy().drop_duplicates().reset_index(drop=True)

    if "pergunta" in df.columns:
        df = df.assign(pergunta=df["pergunta"].astype(str).str.strip())

        eh_data = df["pergunta"].str.contains(r"^\d{4}-\d{2}-\d{2}", regex=True, na=False)
        antes = len(df)
        df = df[~eh_data].reset_index(drop=True)
        print(f"Linhas com pergunta=data (removidas): {antes - len(df)}")

        df = df.assign(pergunta=df["pergunta"].str.split("/"))
        df = df.explode("pergunta", ignore_index=True)
        df = df.assign(pergunta=df["pergunta"].astype(str).str.strip())
        df = df[df["pergunta"] != ""].reset_index(drop=True)
        df = df[df["pergunta"].str.lower() != "nan"].reset_index(drop=True)

        antes = len(df)
        df = df[df["pergunta"].str.match(RE_CODIGO_NC, na=False)].reset_index(drop=True)
        print(f"Linhas com pergunta não-código (removidas): {antes - len(df)}")

        df = df.assign(
            codigo_nc=df["pergunta"],
            capitulo_nc=df["pergunta"].str.split(".").str[0],
        )

    for c in ["classificacao", "gravidade", "criticidade"]:
        if c in df.columns:
            df = df.assign(**{c: df[c].astype(str).str.strip()})

    if "codigo_unidade" in df.columns:
        df = df.assign(
            codigo_unidade=pd.to_numeric(df["codigo_unidade"], errors="coerce")
        )

    if "id_analise" in df.columns:
        df = df[df["id_analise"].notna() & (df["id_analise"] != "nan")].reset_index(drop=True)

    print(f"Linhas após explode: {len(df)}")
    return df


def limpar_parametros(df):
    print("\n--- Limpando parâmetros ---")
    df = df.dropna(how="all").drop_duplicates().reset_index(drop=True)
    print(f"Linhas: {len(df)}")
    return df


def main():
    print("Lendo arquivos de:", PASTA_BRUTOS)
    os.makedirs("dados_tratados", exist_ok=True)

    print("\nAnálises:")
    df_a = carregar_por_tipo("analise")
    if df_a is not None:
        df_a = limpar_analises(df_a)
        df_a.to_csv(ARQ_ANALISES, index=False, sep=";", encoding="utf-8")
        print(f"Salvei: {ARQ_ANALISES}")

    print("\nNão Conformidades:")
    df_n = carregar_por_tipo("nc")
    if df_n is not None:
        df_n = limpar_ncs(df_n)
        df_n.to_csv(ARQ_NCS, index=False, sep=";", encoding="utf-8")
        print(f"Salvei: {ARQ_NCS}")

    print("\nParâmetros:")
    df_p = carregar_por_tipo("parametro")
    if df_p is not None:
        df_p = limpar_parametros(df_p)
        df_p.to_csv(ARQ_PARAMS, index=False, sep=";", encoding="utf-8")
        print(f"Salvei: {ARQ_PARAMS}")

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()