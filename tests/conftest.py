# tests/conftest.py
# Fixtures compartilhadas entre os testes.

import pandas as pd
import pytest
import os
import sys
import tempfile

# Adiciona a raiz do projeto no path pra importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def df_analises_bruto():
    """Simula o CSV bruto de análises, com colunas originais da planilha."""
    return pd.DataFrame({
        "ID da Análise": ["J-0001", "J-0002", "J-0003", "J-0004"],
        "ID Checklist": ["211898669", "211362667", "211172177", "211171971"],
        "Analista": ["Jhonatan", "Jhonatan", "Jhonatan", "Jhonatan"],
        "Filial": ["Cuiabá", "Cuiabá", "Curitiba", "Curitiba"],
        "Data da Avaliação": [
            "31/07/2026", "28/07/2026", "27/07/2026", "27/07/2026",
        ],
        "Resultado": ["Conforme", "Conforme", "Não Conforme", "Conforme"],
        "Classificação": ["Ótimo", "Bom", "Ruim", "Ótimo"],
        "% Nota": ["1.00", "0.75", "0.25", "1.00"],
        "Qtd NC": ["0", "0", "3", "0"],
        "Observações Gerais": ["EM CONFORMIDADE"] * 4,
        "Status": ["Finalizado"] * 4,
        "Nome da Unidade": [
            "314 - COMPLEXO", "194 - SEDUC", "184 - EEB X", "293 - JARDINAGEM",
        ],
    })


@pytest.fixture
def df_ncs_bruto():
    """Simula o CSV bruto de NCs, com NCs compostas."""
    return pd.DataFrame({
        "ID Análise": ["J-0009", "J-0016", "J-0036", "J-0057"],
        "Pergunta": [
            "3.2 / 5.3 / 6.1 / 6.2",  # composta — deve virar 4 linhas
            "2026-01-01 00:00:00",     # data — deve ser removida
            "2026-02-03 00:00:00",     # data — deve ser removida
            "1.1 / 7.1",               # composta — deve virar 2 linhas
        ],
        "Classificação": ["Documentação", "Documentação", "Limpeza", "Documentação"],
        "Departamento": ["293", "273", "173", "262"],
        "Gravidade": ["Baixa", "Média", "Alta", "Crítica"],
        "Observação": ["IMAGENS BORRADAS"] * 4,
        "Filial": ["Cuiabá", "Toledo", "Toledo", "Curitiba"],
        "Analista": ["Jhonatan"] * 4,
        "Criticidade": ["Crítica", "Média", "Média", "Baixa"],
    })


@pytest.fixture
def pasta_temporaria():
    """Cria uma pasta temporária e limpa depois."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir