# Análise de Indicadores Operacionais do CCO

Pipeline de Ciência de Dados aplicado aos dados operacionais do CCO (Centro de Controle Operacional) da Terceirize Mais / Costa Oeste. Processa registros de análises de conformidade e não conformidades, gera KPIs, gráficos estáticos e dashboard interativo, além de um modelo de Machine Learning para previsão de criticidade.

---

## Visão Geral

- **Fonte dos dados:** planilhas operacionais do CCO (Google Sheets, exportadas em CSV)
- **Período analisado:** 2026
- **Total de análises:** 570
- **Total de não conformidades:** 224 (após explodir NCs compostas)
- **Total de registros explodidos:** 224
- **Filial com maior taxa de NC:** Curitiba (76,09%)
- **Gravidade predominante:** Crítica (96,88%)

---

## Arquitetura do Projeto

```
dados_cco/
│
├── dados_brutos/              # CSVs originais exportados do Google Sheets (não versionados)
├── dados_tratados/            # Dados limpos e resultados intermediários (não versionados)
├── imagens/                   # Gráficos estáticos gerados (versionados)
├── modelo/                    # Modelo ML treinado (não versionado — gerado pelo script 06)
│
├── 01_extracao_cco.py         # Leitura e consolidação dos CSVs brutos
├── 02_limpeza_cco.py          # Limpeza, explode de NCs e padronização
├── 03_analise_cco.py          # Análises estatísticas descritivas (13 KPIs)
├── 04_visualizacao_cco.py     # Geração dos 8 gráficos estáticos (Plotly + kaleido)
├── 05_dashboard_cco.py        # Dashboard interativo (Streamlit)
├── 06_machine_learning_cco.py # Treinamento do modelo Random Forest
│
├── run_all.py                 # Executa o pipeline todo em ordem
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Tecnologias Utilizadas

| Categoria | Tecnologias |
| :--- | :--- |
| **Linguagem** | Python 3.14 |
| **Manipulação de dados** | Pandas, NumPy |
| **Visualização** | Plotly, Kaleido |
| **Dashboard** | Streamlit |
| **Machine Learning** | Scikit-learn (Random Forest) |
| **Versionamento** | Git, GitHub |

---

## Como Executar

### 1. Clone o repositório

```bash
git clone https://github.com/beaverbit/dados_cco.git
cd dados_cco
```

### 2. Crie as pastas necessárias

```bash
mkdir -p dados_brutos dados_tratados modelo imagens
```

### 3. Crie o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 4. Instale as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Baixe os dados brutos

Acesse a planilha do CCO no Google Sheets e exporte cada aba em CSV separado. Salve em `dados_brutos/` com os nomes:

- `Arquivo1.csv`
- `Arquivo2.csv`

### 6. Execute o pipeline

```bash
python3 01_extracao_cco.py
python3 02_limpeza_cco.py
python3 03_analise_cco.py
python3 04_visualizacao_cco.py
python3 06_machine_learning_cco.py
```

Ou tudo em um comando:

```bash
python3 01_extracao_cco.py && python3 02_limpeza_cco.py && python3 03_analise_cco.py && python3 04_visualizacao_cco.py && python3 06_machine_learning_cco.py
```

### 7. Abra o dashboard

```bash
streamlit run 05_dashboard_cco.py
```

Acesse `http://localhost:8501` no navegador.

---

## Estrutura dos Dados

### Aba "Registro das Análises"

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `ID da Análise` | texto | Identificador único (ex: `J-0001`) |
| `ID Checklist` | número | ID do checklist no sistema |
| `Analista` | texto | Nome do analista responsável |
| `Filial` | texto | Filial (Curitiba, Santa Catarina, etc.) |
| `Data da Avaliação` | data | Data da análise |
| `Resultado` | texto | Conforme / Conforme com Observação / Não Conforme |
| `Classificação` | texto | Ótimo / Bom / Regular / Ruim / Péssimo |
| `% Nota` | número | Nota em decimal (1.00 = 100%) |
| `Qtd NC` | número | Quantidade de NCs identificadas |
| `Status` | texto | Finalizado / Pendente / Em Análise |
| `Nome da Unidade` | texto | Nome da unidade avaliada |

### Aba "Não Conformidades"

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `ID Análise` | texto | FK para `Registro das Análises` |
| `Pergunta` | texto | Código da NC no checklist (ex: `3.2 / 5.3 / 6.1`) |
| `Classificação` | texto | Documentação / Procedimento / Limpeza / Segurança / Organização / Equipamentos / EPI / Operacional / Administrativo / Outro |
| `Departamento` | número | Código da unidade (renomeado para `codigo_unidade`) |
| `Gravidade` | texto | Baixa / Média / Alta / Crítica |
| `Observação` | texto | Descrição da NC |
| `Filial` | texto | Filial |
| `Analista` | texto | Analista |
| `Criticidade` | texto | Criticidade atribuída |

**Observação importante:** a coluna `Pergunta` pode conter múltiplas NCs separadas por `/`. O script `02_limpeza_cco.py` explode essas linhas, transformando `3.2 / 5.3 / 6.1` em 3 linhas distintas.

---

## KPIs Gerados (script 03)

1. **Visão geral** — total de análises, conformes, NCs, taxa de conformidade, nota média
2. **Desempenho por filial** — taxa de NC por filial
3. **Top 15 unidades com mais NCs**
4. **Produtividade por analista**
5. **Análises por status**
6. **Análises por mês**
7. **NCs por gravidade**
8. **NCs por classificação**
9. **NCs por capítulo do checklist**
10. **Top 15 códigos de NC mais recorrentes**
11. **NCs por filial**
12. **Filial x Gravidade** (cruzamento)
13. **NCs registradas por analista**

Resultados salvos em `dados_tratados/resultados_analise_cco.csv`.

---

## Machine Learning (script 06)

Modelo **Random Forest** treinado para prever se uma NC é **Crítica** ou **Outra**.

- **Acurácia:** 100% (com apenas 162 amostras — modelo ainda não tem volume suficiente para ser confiável)
- **Variáveis de entrada:** filial, classificação, código da unidade, capítulo do checklist
- **Variável alvo:** crítico/não crítico (binário)
- **Arquivos gerados:** `modelo/modelo_cco.pkl`, `modelo/encoders_cco.pkl`

**Limitação atual:** com apenas 7 amostras de `Crítica` no dataset, o modelo não tem variabilidade suficiente para generalizar. Recomenda-se rodar novamente após acumular mais 3-6 meses de análises.

---

## Decisões Técnicas

### Por que CSV e não XLSX?

O Google Sheets exporta `.xlsx` com as células vazias viradas em `1900-01-01 00:00:00` quando lê com Pandas. Isso fazia 87% das NCs do arquivo bruto virarem linhas com data em vez de código. A solução foi exportar em CSV, que preserva os valores como texto.

### Por que Plotly + Kaleido e não Matplotlib?

O Matplotlib 3.9.2 estoura a pilha (`RecursionError`) no Python 3.14 ao tentar fazer `deepcopy` dos markers. Plotly + Kaleido não tem esse problema e gera os PNGs sem erro.

### Por que explodir as NCs?

Uma linha da aba "Não Conformidades" pode conter várias NCs separadas por `/` (ex: `3.2 / 5.3 / 6.1`). Se não forem explodidas, os KPIs ficam imprecisos — uma única linha poderia contar como 1 NC ou como 3, dependendo da lógica. O explode garante que cada NC seja contada individualmente.

---

## Limitações

- **Volume de dados:** o dataset atual é pequeno (~570 análises, ~224 NCs). Os KPIs são representativos mas os modelos de ML ainda não.
- **Dados de agosto incompletos:** o CSV do mês está com valores estranhos na coluna `Pergunta` (a fórmula do Sheets não resolveu). Vale investigar na planilha original.
- **Gravidade concentrada em Crítica:** 217 de 224 NCs estão como `Crítica`. Isso pode indicar que a fórmula de gravidade na planilha está com problema, ou que a maioria das NCs realmente é crítica. Requer validação.

---

## Próximos Passos

- [ ] Coletar mais meses de dados para o modelo de ML (previsto para dez/2026)
- [ ] Levar o achado do Item 1.1 (153 NCs em foto de executante) para a gestão — indica necessidade de orientação sobre uso do CF
- [ ] Avaliar notificações automáticas caso o volume de dados justifique

---

## Referências

- PEDREGOSA, F. et al. **Scikit-learn: Machine Learning in Python**. JMLR, 2011.
- MCKINNEY, W. **Python for Data Analysis**. O'Reilly Media, 2022.