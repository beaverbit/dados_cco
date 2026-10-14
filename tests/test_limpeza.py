# tests/test_limpeza.py
# Testes para o script 02_limpeza_cco.py

import pandas as pd
import pytest
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from importlib import import_module

limpeza = import_module("02_limpeza_cco")


# --- normalizar ---

def test_normalizar():
    assert limpeza.normalizar("ID Análise") == "id_analise"
    assert limpeza.normalizar("Não Conformidade") == "nao_conformidade"


# --- classificar_arquivo ---

def test_classificar_arquivo():
    assert limpeza.classificar_arquivo("analise__2026-09.csv") == "analise"
    assert limpeza.classificar_arquivo("nc__2026-09.csv") == "nc"
    assert limpeza.classificar_arquivo("parametro__consolidado.csv") == "parametro"
    assert limpeza.classificar_arquivo("outro.csv") == "desconhecido"


def test_classificar_arquivo_maiusculas():
    assert limpeza.classificar_arquivo("ANALISE__2026-09.csv") == "analise"
    assert limpeza.classificar_arquivo("NC__2026-09.csv") == "nc"


# --- achar_coluna ---

def test_achar_coluna_encontra_por_nome_normalizado():
    df = pd.DataFrame({"ID Análise": [1], "Filial": ["x"]})
    assert limpeza.achar_coluna(df, "id_analise") == "ID Análise"
    assert limpeza.achar_coluna(df, "filial") == "Filial"


def test_achar_coluna_tenta_varios_candidatos():
    df = pd.DataFrame({"ID da Análise": [1]})
    col = limpeza.achar_coluna(df, "id_analise", "id_da_analise")
    assert col == "ID da Análise"


def test_achar_coluna_retorna_none_se_nao_achar():
    df = pd.DataFrame({"a": [1], "b": [2]})
    assert limpeza.achar_coluna(df, "filial") is None


# --- limpar_analises ---

def test_limpar_analises_converte_data(df_analises_bruto):
    df = df_analises_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_analises(df)

    assert "data_da_avaliacao" in resultado.columns
    assert pd.api.types.is_datetime64_any_dtype(resultado["data_da_avaliacao"])
    assert "ano" in resultado.columns
    assert "mes" in resultado.columns


def test_limpar_analises_converte_pct_nota(df_analises_bruto):
    df = df_analises_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_analises(df)

    assert pd.api.types.is_numeric_dtype(resultado["pct_nota"])
    assert resultado["pct_nota"].iloc[0] == 1.0
    assert resultado["pct_nota"].iloc[1] == 0.75


def test_limpar_analises_pct_nota_com_virgula():
    """Testa conversão de % Nota com vírgula decimal (formato BR)."""
    df = pd.DataFrame({
        "ID da Análise": ["J-0001"],
        "Filial": ["Curitiba"],
        "Analista": ["Jhonatan"],
        "Resultado": ["Conforme"],
        "Classificação": ["Ótimo"],
        "% Nota": ["0,75"],
        "Qtd NC": ["0"],
        "Status": ["Finalizado"],
        "Nome da Unidade": ["Unidade X"],
        "Observações Gerais": ["OK"],
    })
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_analises(df)
    assert resultado["pct_nota"].iloc[0] == 0.75


def test_limpar_analises_qtd_nc_e_int(df_analises_bruto):
    df = df_analises_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_analises(df)

    assert pd.api.types.is_integer_dtype(resultado["qtd_nc"])
    assert resultado["qtd_nc"].sum() == 3


def test_limpar_analises_remove_id_nulo():
    df = pd.DataFrame({
        "ID da Análise": ["J-0001", None, "J-0003"],
        "Filial": ["A", "B", "C"],
        "Analista": ["X", "Y", "Z"],
        "Resultado": ["Conforme"] * 3,
        "Classificação": ["Ótimo"] * 3,
        "% Nota": ["1.00"] * 3,
        "Qtd NC": ["0"] * 3,
        "Status": ["Finalizado"] * 3,
        "Nome da Unidade": ["U1", "U2", "U3"],
        "Observações Gerais": ["OK"] * 3,
    })
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_analises(df)
    assert len(resultado) == 2


# --- limpar_ncs ---

def test_limpar_ncs_remove_datas(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert not resultado["pergunta"].str.contains(
        r"^\d{4}-\d{2}-\d{2}", regex=True, na=False
    ).any()


def test_limpar_ncs_explode_compostas(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    j0009 = resultado[resultado["id_analise"] == "J-0009"]
    assert len(j0009) == 4

    j0057 = resultado[resultado["id_analise"] == "J-0057"]
    assert len(j0057) == 2


def test_limpar_ncs_extrai_codigo_e_capitulo(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert "codigo_nc" in resultado.columns
    assert "capitulo_nc" in resultado.columns

    item_32 = resultado[resultado["codigo_nc"] == "3.2"]
    assert item_32["capitulo_nc"].iloc[0] == "3"

    item_11 = resultado[resultado["codigo_nc"] == "1.1"]
    assert item_11["capitulo_nc"].iloc[0] == "1"


def test_limpar_ncs_converte_codigo_unidade(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert pd.api.types.is_numeric_dtype(resultado["codigo_unidade"])
    assert 293 in resultado["codigo_unidade"].values


def test_limpar_ncs_sem_datas_sobra_nada(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df["Pergunta"] = ["2026-01-01"] * 4
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert len(resultado) == 0


def test_limpar_ncs_remove_linha_com_pergunta_vazia():
    """Pergunta vazia após explode deve ser removida."""
    df = pd.DataFrame({
        "ID Análise": ["J-0001", "J-0002"],
        "Pergunta": ["1.1 /  / 2.1", "3.2"],  # primeira tem um item vazio
        "Classificação": ["Documentação", "Limpeza"],
        "Departamento": ["293", "173"],
        "Gravidade": ["Baixa", "Alta"],
        "Observação": ["x", "y"],
        "Filial": ["Cuiabá", "Toledo"],
        "Analista": ["Jhonatan", "Jhonatan"],
        "Criticidade": ["Crítica", "Alta"],
    })
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    # 1.1 e 2.1 da primeira + 3.2 da segunda = 3 linhas
    # (o vazio no meio não conta)
    assert len(resultado) == 3
    assert "" not in resultado["pergunta"].values


def test_limpar_ncs_remove_pergunta_nao_codigo():
    """Linha com pergunta tipo 'abc' deve ser removida."""
    df = pd.DataFrame({
        "ID Análise": ["J-0001", "J-0002"],
        "Pergunta": ["abc", "1.1"],
        "Classificação": ["Documentação", "Documentação"],
        "Departamento": ["293", "293"],
        "Gravidade": ["Baixa", "Baixa"],
        "Observação": ["x", "y"],
        "Filial": ["Cuiabá", "Cuiabá"],
        "Analista": ["Jhonatan", "Jhonatan"],
        "Criticidade": ["Crítica", "Crítica"],
    })
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert len(resultado) == 1
    assert resultado["pergunta"].iloc[0] == "1.1"