# tests/test_extracao.py
# Testes para o script 01_extracao_cco.py

import pandas as pd
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importlib import import_module

extracao = import_module("01_extracao_cco")


def test_normalizar_remove_acentos():
    assert extracao.normalizar("Classificação") == "classificacao"
    assert extracao.normalizar("ID Análise") == "id_analise"
    assert extracao.normalizar("Não Conformidade") == "nao_conformidade"


def test_normalizar_remove_espacos_e_hifens():
    assert extracao.normalizar("ID da Análise") == "id_da_analise"
    assert extracao.normalizar("Data-Avaliação") == "data_avaliacao"
    assert extracao.normalizar("  Filial  ") == "filial"


def test_classificar_por_conteudo_analise(df_analises_bruto):
    tipo = extracao.classificar_por_conteudo(df_analises_bruto)
    assert tipo == "analise"


def test_classificar_por_conteudo_nc(df_ncs_bruto):
    tipo = extracao.classificar_por_conteudo(df_ncs_bruto)
    assert tipo == "nc"


def test_classificar_por_conteudo_desconhecido():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    tipo = extracao.classificar_por_conteudo(df)
    assert tipo == "desconhecido"


def test_detectar_header_em_lista():
    linhas = [
        ["Título da planilha", None, None, None, None],
        [None, None, None, None, None],
        ["ID", "Nome", "Data", "Valor", "Status"],
        ["J-001", "Teste", "2026-01-01", "100", "OK"],
    ]
    idx = extracao.detectar_header_em_lista(linhas, min_celulas=4)
    assert idx == 2  # deve achar a linha 3 (índice 2)


def test_sanitizar_nome_arquivo():
    assert extracao.sanitizar("Não Conformidades") == "Nao_Conformidades"
    assert extracao.sanitizar("Registro das Análises") == "Registro_das_Analises"