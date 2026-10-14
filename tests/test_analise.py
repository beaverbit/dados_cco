# tests/test_analise.py
# Testes para o script 03_analise_cco.py

import pandas as pd
import pytest
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from importlib import import_module

analise = import_module("03_analise_cco")


@pytest.fixture
def df_analises_limpo():
    return pd.DataFrame({
        "id_analise": ["J-0001", "J-0002", "J-0003", "J-0004", "J-0005"],
        "filial": ["Cuiabá", "Cuiabá", "Curitiba", "Curitiba", "Curitiba"],
        "analista": ["Jhonatan"] * 5,
        "resultado": [
            "Conforme", "Conforme", "Não Conforme", "Não Conforme", "Conforme",
        ],
        "classificacao": ["Ótimo", "Bom", "Ruim", "Péssimo", "Ótimo"],
        "pct_nota": [1.0, 0.75, 0.25, 0.0, 1.0],
        "qtd_nc": [0, 0, 3, 5, 0],
        "status": ["Finalizado"] * 5,
        "nome_da_unidade": ["Unidade A", "Unidade B", "Unidade C", "Unidade D", "Unidade E"],
    })


@pytest.fixture
def df_ncs_limpo():
    return pd.DataFrame({
        "id_analise": ["J-0003", "J-0003", "J-0003", "J-0004", "J-0004"],
        "codigo_nc": ["3.2", "5.3", "6.1", "1.1", "1.1"],
        "capitulo_nc": ["3", "5", "6", "1", "1"],
        "classificacao": ["Documentação"] * 5,
        "gravidade": ["Crítica", "Crítica", "Alta", "Crítica", "Crítica"],
        "codigo_unidade": [293, 293, 293, 165, 165],
        "filial": ["Curitiba"] * 5,
        "analista": ["Jhonatan"] * 5,
    })


# --- kpi_geral ---

def test_kpi_geral_conta_conformes(df_analises_limpo):
    resultado = analise.kpi_geral(df_analises_limpo)

    assert resultado["total_analises"].iloc[0] == 5
    assert resultado["conformes"].iloc[0] == 3
    assert resultado["nao_conformes"].iloc[0] == 2
    assert resultado["total_nc"].iloc[0] == 8


def test_kpi_geral_taxa_conformidade(df_analises_limpo):
    resultado = analise.kpi_geral(df_analises_limpo)
    assert resultado["taxa_conformidade_pct"].iloc[0] == 60.0


def test_kpi_geral_dataframe_vazio():
    """Não deve quebrar com DataFrame vazio."""
    df = pd.DataFrame({
        "id_analise": [],
        "filial": [],
        "analista": [],
        "resultado": [],
        "classificacao": [],
        "pct_nota": [],
        "qtd_nc": [],
        "status": [],
        "nome_da_unidade": [],
    })
    resultado = analise.kpi_geral(df)
    assert resultado["total_analises"].iloc[0] == 0


# --- kpi_por_filial ---

def test_kpi_por_filial_agrupa_corretamente(df_analises_limpo):
    resultado = analise.kpi_por_filial(df_analises_limpo)

    cuiaba = resultado[resultado["filial"] == "Cuiabá"].iloc[0]
    curitiba = resultado[resultado["filial"] == "Curitiba"].iloc[0]

    assert cuiaba["total_analises"] == 2
    assert cuiaba["nao_conformes"] == 0
    assert cuiaba["taxa_nao_conformidade_pct"] == 0.0

    assert curitiba["total_analises"] == 3
    assert curitiba["nao_conformes"] == 2
    assert abs(curitiba["taxa_nao_conformidade_pct"] - 66.67) < 0.01


def test_kpi_por_filial_ordenado_por_taxa(df_analises_limpo):
    resultado = analise.kpi_por_filial(df_analises_limpo)
    # Curitiba (66%) deve vir antes de Cuiabá (0%)
    assert resultado.iloc[0]["filial"] == "Curitiba"


# --- kpi_por_unidade ---

def test_kpi_por_unidade_retorna_15_max(df_analises_limpo):
    resultado = analise.kpi_por_unidade(df_analises_limpo)
    assert len(resultado) <= 15


# --- kpi_por_analista ---

def test_kpi_por_analista(df_analises_limpo):
    resultado = analise.kpi_por_analista(df_analises_limpo)
    assert len(resultado) == 1
    assert resultado.iloc[0]["analista"] == "Jhonatan"
    assert resultado.iloc[0]["total_analises"] == 5


# --- kpi_por_status ---

def test_kpi_por_status(df_analises_limpo):
    resultado = analise.kpi_por_status(df_analises_limpo)
    assert "Finalizado" in resultado["status"].values
    assert resultado["percentual_pct"].iloc[0] == 100.0


# --- kpi_por_mes ---

def test_kpi_por_mes_ordena_por_ano_mes():
    df = pd.DataFrame({
        "id_analise": ["J-1", "J-2", "J-3"],
        "filial": ["A", "A", "A"],
        "analista": ["X"] * 3,
        "resultado": ["Conforme"] * 3,
        "classificacao": ["Ótimo"] * 3,
        "pct_nota": [1.0] * 3,
        "qtd_nc": [0] * 3,
        "status": ["Finalizado"] * 3,
        "nome_da_unidade": ["U"] * 3,
        "ano": [2026, 2025, 2026],
        "mes": [9, 12, 8],
    })
    resultado = analise.kpi_por_mes(df)
    # 2025-12, 2026-08, 2026-09
    assert resultado.iloc[0]["ano"] == 2025
    assert resultado.iloc[-1]["mes"] == 9


# --- kpi_nc_por_gravidade ---

def test_kpi_nc_por_gravidade_ordena_corretamente(df_ncs_limpo):
    resultado = analise.kpi_nc_por_gravidade(df_ncs_limpo)
    assert set(resultado["gravidade"]) == {"Baixa", "Média", "Alta", "Crítica"}

    critica = resultado[resultado["gravidade"] == "Crítica"].iloc[0]
    assert critica["total"] == 4


def test_kpi_nc_por_gravidade_dataframe_vazio():
    """Deve retornar 4 linhas com total 0."""
    df = pd.DataFrame({"gravidade": [], "codigo_nc": []})
    resultado = analise.kpi_nc_por_gravidade(df)
    # 4 gravidades, todas 0
    assert len(resultado) == 4
    assert resultado["total"].sum() == 0


# --- kpi_nc_por_classificacao ---

def test_kpi_nc_por_classificacao(df_ncs_limpo):
    resultado = analise.kpi_nc_por_classificacao(df_ncs_limpo)
    assert len(resultado) == 1
    assert resultado.iloc[0]["classificacao"] == "Documentação"
    assert resultado.iloc[0]["total"] == 5


# --- kpi_nc_por_capitulo ---

def test_kpi_nc_por_capitulo_agrupa(df_ncs_limpo):
    resultado = analise.kpi_nc_por_capitulo(df_ncs_limpo)

    cap_1 = resultado[resultado["capitulo_nc"] == "1"].iloc[0]
    cap_3 = resultado[resultado["capitulo_nc"] == "3"].iloc[0]

    assert cap_1["total"] == 2
    assert cap_3["total"] == 1


def test_kpi_nc_por_capitulo_ordena_numericamente(df_ncs_limpo):
    resultado = analise.kpi_nc_por_capitulo(df_ncs_limpo)
    capitulos = resultado["capitulo_nc"].tolist()
    # 1, 3, 5, 6 (ordem numérica crescente)
    assert capitulos == ["1", "3", "5", "6"]


# --- kpi_top_ncs ---

def test_kpi_top_ncs_retorna_top_15(df_ncs_limpo):
    resultado = analise.kpi_top_ncs(df_ncs_limpo)
    assert len(resultado) <= 15
    assert resultado.iloc[0]["codigo_nc"] == "1.1"
    assert resultado.iloc[0]["total"] == 2


def test_kpi_top_ncs_ordena_por_total(df_ncs_limpo):
    resultado = analise.kpi_top_ncs(df_ncs_limpo)
    totais = resultado["total"].tolist()
    assert totais == sorted(totais, reverse=True)


# --- kpi_nc_por_filial ---

def test_kpi_nc_por_filial(df_ncs_limpo):
    resultado = analise.kpi_nc_por_filial(df_ncs_limpo)
    curitiba = resultado[resultado["filial"] == "Curitiba"].iloc[0]
    assert curitiba["total_nc"] == 5
    assert curitiba["criticas"] == 4


# --- kpi_filial_x_gravidade ---

def test_kpi_filial_x_gravidade(df_ncs_limpo):
    resultado = analise.kpi_filial_x_gravidade(df_ncs_limpo)
    assert "filial" in resultado.columns
    assert "Crítica" in resultado.columns
    # Curitiba tem 4 críticas
    curitiba = resultado[resultado["filial"] == "Curitiba"].iloc[0]
    assert curitiba["Crítica"] == 4