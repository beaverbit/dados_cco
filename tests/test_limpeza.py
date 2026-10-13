# tests/test_limpeza.py
# Testes para o script 02_limpeza_cco.py

import pandas as pd
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importlib import import_module

limpeza = import_module("02_limpeza_cco")


def test_normalizar():
    assert limpeza.normalizar("ID Análise") == "id_analise"
    assert limpeza.normalizar("Não Conformidade") == "nao_conformidade"


def test_classificar_arquivo():
    assert limpeza.classificar_arquivo("analise__2026-09.csv") == "analise"
    assert limpeza.classificar_arquivo("nc__2026-09.csv") == "nc"
    assert limpeza.classificar_arquivo("parametro__consolidado.csv") == "parametro"
    assert limpeza.classificar_arquivo("outro.csv") == "desconhecido"


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


def test_limpar_analises_qtd_nc_e_int(df_analises_bruto):
    df = df_analises_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_analises(df)

    assert pd.api.types.is_integer_dtype(resultado["qtd_nc"])
    assert resultado["qtd_nc"].sum() == 3


def test_limpar_ncs_remove_datas(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    # Nenhuma linha deve ter pergunta começando com data
    assert not resultado["pergunta"].str.contains(
        r"^\d{4}-\d{2}-\d{2}", regex=True, na=False
    ).any()


def test_limpar_ncs_explode_compostas(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    # J-0009 tinha 4 NCs (3.2, 5.3, 6.1, 6.2) → 4 linhas
    j0009 = resultado[resultado["id_analise"] == "J-0009"]
    assert len(j0009) == 4

    # J-0057 tinha 2 NCs (1.1, 7.1) → 2 linhas
    j0057 = resultado[resultado["id_analise"] == "J-0057"]
    assert len(j0057) == 2


def test_limpar_ncs_extrai_codigo_e_capitulo(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert "codigo_nc" in resultado.columns
    assert "capitulo_nc" in resultado.columns

    # Item 3.2 → capítulo 3
    item_32 = resultado[resultado["codigo_nc"] == "3.2"]
    assert item_32["capitulo_nc"].iloc[0] == "3"

    # Item 1.1 → capítulo 1
    item_11 = resultado[resultado["codigo_nc"] == "1.1"]
    assert item_11["capitulo_nc"].iloc[0] == "1"


def test_limpar_ncs_converte_codigo_unidade(df_ncs_bruto):
    df = df_ncs_bruto.copy()
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert pd.api.types.is_numeric_dtype(resultado["codigo_unidade"])
    assert 293 in resultado["codigo_unidade"].values


def test_limpar_ncs_sem_datas_sobra_nada(df_ncs_bruto):
    """Testa com um df que só tem datas — deve retornar vazio."""
    df = df_ncs_bruto.copy()
    df["Pergunta"] = ["2026-01-01"] * 4
    df.columns = [limpeza.normalizar(c) for c in df.columns]
    resultado = limpeza.limpar_ncs(df)

    assert len(resultado) == 0