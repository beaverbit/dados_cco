# 01_extracao_cco.py
# Meu objetivo: ler qualquer arquivo em dados_brutos/ e salvar cada aba como CSV padronizado.

import pandas as pd
import os
import glob
import unicodedata

PASTA_BRUTOS = "dados_brutos"
PASTA_SAIDA = os.path.join("dados_tratados", "brutos")

EXTENSOES = ("*.csv", "*.xlsx", "*.xls", "*.tsv", "*.txt")


def sanitizar(nome):
    n = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode("ascii")
    n = n.replace(" ", "_").replace("/", "-").replace(":", "-")
    while "__" in n:
        n = n.replace("__", "_")
    return n.strip("_")


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


def detectar_header_em_lista(linhas, min_celulas=4, max_busca=15):
    limite = min(max_busca, len(linhas))
    for i in range(limite):
        row = linhas[i]
        preenchidas = sum(1 for c in row if str(c).strip() not in ("", "nan"))
        if preenchidas >= min_celulas:
            if i + 1 < len(linhas):
                prox = linhas[i + 1]
                prox_preenchidas = sum(1 for c in prox if str(c).strip() not in ("", "nan"))
                if prox_preenchidas >= min_celulas:
                    return i
    return 0


def classificar_por_conteudo(df):
    """Classifica o DataFrame pelo nome das colunas, não pelo nome do arquivo."""
    if df is None or df.shape[1] < 2:
        return "desconhecido"

    colunas_norm = [normalizar(c) for c in df.columns]

    # Análise: tem ID Checklist ou Data da Avaliação
    if "id_checklist" in colunas_norm or "data_da_avaliacao" in colunas_norm:
        return "analise"

    # NC: tem Pergunta + Gravidade
    if "pergunta" in colunas_norm and "gravidade" in colunas_norm:
        return "nc"

    # Parâmetros: heurística — colunas conhecidas da aba de parâmetros
    if any(c in colunas_norm for c in ["analistas", "filiais", "gravidade"]):
        if "criticidade" in colunas_norm or "classificacao_nc" in colunas_norm:
            return "parametro"

    return "desconhecido"


def ler_csv(arquivo):
    melhor = None
    melhor_cols = 0
    melhor_info = None

    for sep in [";", ",", "\t", "|"]:
        for enc in ["utf-8", "latin-1"]:
            try:
                df = pd.read_csv(
                    arquivo, sep=sep, encoding=enc,
                    low_memory=False, dtype=str, header=None,
                )
                if df.shape[1] > melhor_cols:
                    melhor = df
                    melhor_cols = df.shape[1]
                    melhor_info = (sep, enc)
            except Exception:
                continue

    if melhor is None or melhor_cols < 2:
        return None

    sep, enc = melhor_info
    linhas = melhor.values.tolist()
    idx = detectar_header_em_lista(linhas)

    df = melhor.iloc[idx + 1:].reset_index(drop=True)
    df.columns = [
        str(c).strip() if str(c).strip() not in ("", "nan") else f"col_{i}"
        for i, c in enumerate(melhor.iloc[idx])
    ]
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def ler_excel(arquivo):
    try:
        abas_raw = pd.read_excel(arquivo, sheet_name=None, header=None, dtype=str)
    except Exception as e:
        print(f"  -> Erro excel: {e}")
        return []

    resultado = []
    for nome_aba, df_raw in abas_raw.items():
        if df_raw.empty:
            continue
        linhas = df_raw.values.tolist()
        idx = detectar_header_em_lista(linhas)
        df = df_raw.iloc[idx + 1:].reset_index(drop=True)
        df.columns = [
            str(c).strip() if str(c).strip() not in ("", "nan") else f"col_{i}"
            for i, c in enumerate(df_raw.iloc[idx])
        ]
        df = df.dropna(how="all").reset_index(drop=True)
        resultado.append((nome_aba, df))
    return resultado


def varrer_arquivos():
    arquivos = []
    for ext in EXTENSOES:
        arquivos.extend(glob.glob(os.path.join(PASTA_BRUTOS, ext)))
    return sorted(set(arquivos))


def processar():
    arquivos = varrer_arquivos()
    if not arquivos:
        print(f"Nada em '{PASTA_BRUTOS}/'.")
        return

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    print(f"Encontrei {len(arquivos)} arquivo(s).\n")

    total = 0
    for arquivo in arquivos:
        nome = os.path.basename(arquivo)
        ext = os.path.splitext(nome)[1].lower()
        base = sanitizar(os.path.splitext(nome)[0])

        print(f"Lendo: {nome}")

        if ext in (".xlsx", ".xls"):
            abas = ler_excel(arquivo)
            for nome_aba, df in abas:
                tipo = classificar_por_conteudo(df)
                destino = os.path.join(
                    PASTA_SAIDA,
                    f"{tipo}__{sanitizar(nome_aba)}.csv",
                )
                df.to_csv(destino, index=False, sep=";", encoding="utf-8")
                print(f"  -> aba '{nome_aba}' [{tipo}]: {df.shape[0]} linhas, {df.shape[1]} colunas -> {destino}")
                total += 1
        else:
            df = ler_csv(arquivo)
            if df is None:
                print("  -> não consegui ler")
                continue
            tipo = classificar_por_conteudo(df)
            destino = os.path.join(PASTA_SAIDA, f"{tipo}__{base}.csv")
            df.to_csv(destino, index=False, sep=";", encoding="utf-8")
            print(f"  -> [{tipo}] {df.shape[0]} linhas, {df.shape[1]} colunas -> {destino}")
            total += 1

    print(f"\nTotal de arquivos/abas salvos em '{PASTA_SAIDA}/': {total}")


if __name__ == "__main__":
    processar()