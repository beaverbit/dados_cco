# 01_extracao_cco.py
# Meu objetivo: ler todos os meses em dados_brutos/ e consolidar cada tipo
# em um único CSV em dados_tratados/brutos/.

import pandas as pd
import os
import glob
import unicodedata
import re

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
    """Acha a primeira linha com >= min_celulas preenchidas seguidas por uma linha com dados."""
    def contar_preenchidas(row):
        return sum(
            1 for c in row
            if c is not None
            and str(c).strip() not in ("", "nan", "None")
        )

    limite = min(max_busca, len(linhas))
    for i in range(limite):
        if contar_preenchidas(linhas[i]) >= min_celulas:
            if i + 1 < len(linhas):
                if contar_preenchidas(linhas[i + 1]) >= min_celulas:
                    return i
    return 0


def classificar_por_conteudo(df):
    """Classifica o DataFrame pelo nome das colunas, não pelo nome do arquivo."""
    if df is None or df.shape[1] < 2:
        return "desconhecido"

    colunas_norm = [normalizar(c) for c in df.columns]

    if "id_checklist" in colunas_norm or "data_da_avaliacao" in colunas_norm:
        return "analise"

    if "pergunta" in colunas_norm and "gravidade" in colunas_norm:
        return "nc"

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
    """Varre dados_brutos/ recursivamente, retornando (arquivo, mes_referencia)."""
    arquivos = []

    # 1. Arquivos soltos na raiz (modo antigo, mes_referencia = "sem_mes")
    for ext in EXTENSOES:
        for arq in glob.glob(os.path.join(PASTA_BRUTOS, ext)):
            arquivos.append((arq, "sem_mes"))

    # 2. Arquivos em subpastas (modo novo, subpasta = mes_referencia)
    for item in sorted(os.listdir(PASTA_BRUTOS)):
        caminho = os.path.join(PASTA_BRUTOS, item)
        if not os.path.isdir(caminho):
            continue
        for ext in EXTENSOES:
            for arq in glob.glob(os.path.join(caminho, ext)):
                arquivos.append((arq, item))

    return arquivos


def detectar_mes_referencia(df, mes_pasta):
    """Se a pasta tem nome de mês, usa. Senão tenta extrair da data."""
    if mes_pasta != "sem_mes":
        return mes_pasta

    colunas_norm = [normalizar(c) for c in df.columns]
    for cand in ["data_da_avaliacao", "data"]:
        if cand in colunas_norm:
            col_real = df.columns[colunas_norm.index(cand)]
            try:
                datas = pd.to_datetime(df[col_real], errors="coerce", dayfirst=True)
                if datas.notna().any():
                    ano = int(datas.dt.year.mode()[0])
                    mes = int(datas.dt.month.mode()[0])
                    return f"{ano}-{mes:02d}"
            except Exception:
                pass
    return "sem_mes"


def consolidar_por_tipo():
    arquivos = varrer_arquivos()
    if not arquivos:
        print(f"Nada em '{PASTA_BRUTOS}/'.")
        return

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    print(f"Encontrei {len(arquivos)} arquivo(s).\n")

    # Acumula por tipo
    acumulado = {"analise": [], "nc": [], "parametro": [], "desconhecido": []}

    for arquivo, mes_pasta in arquivos:
        nome = os.path.basename(arquivo)
        rel = os.path.relpath(arquivo, PASTA_BRUTOS)
        ext = os.path.splitext(nome)[1].lower()

        print(f"Lendo: {rel} (mês da pasta: {mes_pasta})")

        if ext in (".xlsx", ".xls"):
            abas = ler_excel(arquivo)
            for nome_aba, df in abas:
                tipo = classificar_por_conteudo(df)
                mes_ref = detectar_mes_referencia(df, mes_pasta)
                df = df.assign(mes_referencia=mes_ref, arquivo_origem=rel, aba_origem=nome_aba)
                acumulado[tipo].append(df)
                print(f"  -> aba '{nome_aba}' [{tipo}] mes={mes_ref}: "
                      f"{df.shape[0]} linhas")
        else:
            df = ler_csv(arquivo)
            if df is None:
                print("  -> não consegui ler")
                continue
            tipo = classificar_por_conteudo(df)
            mes_ref = detectar_mes_referencia(df, mes_pasta)
            df = df.assign(mes_referencia=mes_ref, arquivo_origem=rel, aba_origem="")
            acumulado[tipo].append(df)
            print(f"  -> [{tipo}] mes={mes_ref}: {df.shape[0]} linhas")

    print("\n" + "=" * 60)
    print("CONSOLIDAÇÃO")
    print("=" * 60)

    for tipo, lista in acumulado.items():
        if not lista:
            continue
        df_final = pd.concat(lista, ignore_index=True, sort=False)
        destino = os.path.join(PASTA_SAIDA, f"{tipo}__consolidado.csv")
        df_final.to_csv(destino, index=False, sep=";", encoding="utf-8")
        print(f"  {tipo}: {df_final.shape[0]} linhas, "
              f"{df_final.shape[1]} colunas -> {destino}")

        if "mes_referencia" in df_final.columns:
            contagem = df_final["mes_referencia"].value_counts().sort_index()
            print(f"    Meses: {dict(contagem)}")


if __name__ == "__main__":
    consolidar_por_tipo()