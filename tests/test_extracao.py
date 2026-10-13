# tests/test_extracao.py
# Testes para o script 01_extracao_cco.py

import pandas as pd
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importlib import import_module

extracao = import_module("01_extracao_cco")


# --- normalizar ---

def test_normalizar_remove_acentos():
    assert extracao.normalizar("Classificação") == "classificacao"
    assert extracao.normalizar("ID Análise") == "id_analise"
    assert extracao.normalizar("Não Conformidade") == "nao_conformidade"


def test_normalizar_remove_espacos_e_hifens():
    assert extracao.normalizar("ID da Análise") == "id_da_analise"
    assert extracao.normalizar("Data-Avaliação") == "data_avaliacao"
    assert extracao.normalizar("  Filial  ") == "filial"


def test_normalizar_colapsa_underscores_repetidos():
    assert extracao.normalizar("ID___Análise") == "id_analise"
    assert extracao.normalizar("a  b") == "a_b"


def test_normalizar_string_vazia():
    assert extracao.normalizar("") == ""
    assert extracao.normalizar("   ") == ""


# --- sanitizar ---

def test_sanitizar_nome_arquivo():
    assert extracao.sanitizar("Não Conformidades") == "Nao_Conformidades"
    assert extracao.sanitizar("Registro das Análises") == "Registro_das_Analises"


def test_sanitizar_remove_barras_e_dois_pontos():
    assert extracao.sanitizar("a/b:c") == "a-b-c"


# --- classificar_por_conteudo ---

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


def test_classificar_por_conteudo_dataframe_vazio():
    assert extracao.classificar_por_conteudo(None) == "desconhecido"
    assert extracao.classificar_por_conteudo(pd.DataFrame()) == "desconhecido"


def test_classificar_por_conteudo_uma_coluna():
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert extracao.classificar_por_conteudo(df) == "desconhecido"


def test_classificar_por_conteudo_analise_so_com_id_checklist():
    """Data frame que só tem id_checklist deve ser classificado como análise."""
    df = pd.DataFrame({
        "id_checklist": ["1", "2"],
        "outra_coluna": ["a", "b"],
    })
    assert extracao.classificar_por_conteudo(df) == "analise"


def test_classificar_por_conteudo_nc_so_com_pergunta_e_gravidade():
    """Data frame com pergunta + gravidade deve ser NC."""
    df = pd.DataFrame({
        "pergunta": ["1.1", "2.1"],
        "gravidade": ["Alta", "Baixa"],
    })
    assert extracao.classificar_por_conteudo(df) == "nc"


# --- detectar_header_em_lista ---

def test_detectar_header_em_lista():
    linhas = [
        ["Título da planilha", None, None, None, None],
        [None, None, None, None, None],
        ["ID", "Nome", "Data", "Valor", "Status"],
        ["J-001", "Teste", "2026-01-01", "100", "OK"],
    ]
    idx = extracao.detectar_header_em_lista(linhas, min_celulas=4)
    assert idx == 2


def test_detectar_header_em_lista_none_nao_conta():
    """None não deve contar como célula preenchida."""
    linhas = [
        [None, None, None, None, None],
        ["ID", "Nome", "Data", "Valor", "Status"],
        ["J-001", "Teste", "2026-01-01", "100", "OK"],
    ]
    idx = extracao.detectar_header_em_lista(linhas, min_celulas=4)
    assert idx == 1


def test_detectar_header_em_lista_sem_header():
    """Se não achar header, retorna 0."""
    linhas = [
        ["a", "b"],
        ["c", "d"],
    ]
    idx = extracao.detectar_header_em_lista(linhas, min_celulas=4)
    assert idx == 0


def test_detectar_header_em_lista_so_uma_linha_preenchida():
    """Se só tem uma linha preenchida, não pode ser header válido."""
    linhas = [
        ["ID", "Nome", "Data", "Valor", "Status"],
    ]
    idx = extracao.detectar_header_em_lista(linhas, min_celulas=4)
    assert idx == 0