# Análise de Indicadores Operacionais do CCO

Pipeline de dados aplicado aos registros operacionais do CCO (Centro de Controle Operacional) da Terceirize Mais / Costa Oeste. Processa as análises de conformidade e as não conformidades do Checklist Fácil (CF), gera KPIs operacionais, gráficos estáticos, dashboard interativo e relatório PDF.

- **Fonte dos dados:** planilhas operacionais do CCO (Google Sheets, exportadas em CSV)
- **Escopo:** automação da análise mensal de conformidade
- **Status:** em uso interno

---

## Visão Geral

- **Período analisado:** 2026 (dados de julho a outubro)
- **Total de análises registradas:** 570
- **Análises finalizadas:** 523
- **Não conformidades (após explode):** 224
- **Filial com maior taxa de NC:** Curitiba (76,09%)
- **Item do checklist com maior reincidência:** 1.1 — foto do executante (153 ocorrências)

### Sobre os dois números de NCs

O projeto trabalha com duas métricas diferentes de não conformidade:

- **161 NCs** — soma da coluna `Qtd NC` das análises. Mede quantas NCs o analista registrou **por análise**.
- **224 NCs** — total após explodir as linhas com NCs compostas (`3.2 / 5.3 / 6.1` vira 3 linhas). Mede quantas NCs **individuais** existem no dataset.

As duas são corretas, mas medem coisas diferentes. A primeira é usada nos KPIs de desempenho; a segunda nos KPIs de causa.

---

## Arquitetura do Projeto

```

dados_cco/
│
├── 01_extracao_cco.py          # Lê e consolida CSVs de múltiplos meses
├── 02_limpeza_cco.py           # Limpa, valida e explode NCs compostas
├── 03_analise_cco.py           # Gera 13 KPIs operacionais
├── 04_visualizacao_cco.py      # Gera 8 gráficos estáticos (PNG)
├── 05_dashboard_cco.py         # Dashboard interativo (Streamlit)
├── 06_machine_learning_cco.py  # Modelo experimental de criticidade
├── 07_gerar_pdf_cco.py         # Gera relatório PDF dark (A4)
│
├── run_all.py                  # Executa 01→07 em ordem (~40-80s)
├── tests/                      # 53 testes automatizados
│   ├── conftest.py
│   ├── test_extracao.py
│   ├── test_limpeza.py
│   └── test_analise.py
├── pytest.ini                  # Configuração do pytest
├── requirements.txt
├── README.md
├── PROCESSO.md                 # Guia de uso pra quem vai alimentar o pipeline
├── WINDOWS.md                  # Guia Windows (validado)
└── .gitignore

```

---

## Tecnologias Utilizadas

| Categoria | Tecnologias |
| :--- | :--- |
| **Linguagem** | Python 3.12 |
| **Manipulação de dados** | Pandas, NumPy |
| **Visualização** | Plotly, Kaleido |
| **Dashboard** | Streamlit |
| **Relatório PDF** | ReportLab |
| **Machine Learning** | Scikit-learn (Random Forest) — experimental |
| **Testes** | pytest |
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
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 4. Instale as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Coloque os dados brutos em dados_brutos/

Crie uma subpasta por mês, no formato AAAA-MM:

```
dados_brutos/
├── 2026-09/
│   ├── registro_analises.csv
│   └── nao_conformidades.csv
└── 2026-10/
    ├── registro_analises.csv
    └── nao_conformidades.csv
```

Os arquivos podem ter qualquer nome — o pipeline identifica o tipo pelo conteúdo das colunas.

Para detalhes do processo de exportação do Google Sheets, veja o PROCESSO.md (Linux/Mac) ou WINDOWS.md (Windows).

### 6. Execute o pipeline

```bash
python3 run_all.py
```

Ou etapa por etapa:

```bash
python3 01_extracao_cco.py
python3 02_limpeza_cco.py
python3 03_analise_cco.py
python3 04_visualizacao_cco.py
python3 06_machine_learning_cco.py
python3 07_gerar_pdf_cco.py
```

O `05_dashboard_cco.py` roda separado (é um servidor Streamlit, não um script batch):

```bash
streamlit run 05_dashboard_cco.py
```

### 7. Rode os testes

```bash
pytest
```

Saída esperada: 53 passed in ~0.5s.

### 8. Abra o dashboard

```bash
streamlit run 05_dashboard_cco.py
```

Acesse http://localhost:8501 no navegador.

---

## Saídas Geradas

Depois de rodar o pipeline, os seguintes arquivos existem:

```
dados_tratados/
├── brutos/                                # Consolidados por tipo (etapa 01)
│   ├── analise__consolidado.csv
│   └── nc__consolidado.csv
├── analises_limpas.csv                    # Análises limpas (etapa 02)
├── nao_conformidades_limpas.csv           # NCs explodidas (etapa 02)
├── parametros_limpos.csv                  # Se houver aba de parâmetros
├── resultados_analise_cco.csv             # 13 KPIs em texto (etapa 03)
└── relatorio_cco.pdf                      # Relatório PDF dark (etapa 07)

imagens/                                   # 8 PNGs estáticos (etapa 04)
├── 01_distribuicao_resultados.png
├── 02_analises_nc_por_filial.png
├── 03_analises_por_analista.png
├── 04_analises_por_mes.png
├── 05_nc_por_gravidade.png
├── 06_nc_por_classificacao.png
├── 07_nc_por_capitulo.png
├── 08_filial_x_gravidade.png
├── 09_matriz_confusao_cco.png             # Gerados pelo ML (etapa 06)
└── 10_importancia_features_cco.png

modelo/                                    # Modelo treinado (etapa 06)
├── modelo_cco.pkl
└── encoders_cco.pkl
```

---

## KPIs Gerados (script 03)

```
- 1. Visão geral — total de análises, conformes, NCs, taxa de conformidade, nota média
- 2. Desempenho por filial — taxa de NC por filial
- 3. Top 15 unidades com mais NCs
- 4. Produtividade por analista
- 5. Análises por status
- 6. Análises por mês
- 7. NCs por gravidade
- 8. NCs por classificação
- 9. NCs por área do checklist
- 10. Top 15 códigos de NC mais recorrentes
- 11. NCs por filial
- 12. Filial x Gravidade (cruzamento)
- 13. NCs registradas por analista
```

Resultados salvos em `dados_tratados/resultados_analise_cco.csv`.

---

## Machine Learning (script 06) — Experimental

O modelo de ML foi desenvolvido como experimento pessoal, não como parte do escopo operacional do projeto. Ele está no repositório como demonstração técnica, mas não deve ser usado para decisões operacionais.

### Por que ainda não é confiável:

- A classe "Crítica" representa 96,88% das amostras (217 de 224 NCs)
- Um classificador trivial que sempre prevê "Crítica" já acertaria 96,88%
- A classe "Outra" tem apenas 7 amostras no dataset atual
- Com esse desbalanceamento, não há padrão estatístico que o modelo possa aprender

### O que o modelo faz:

- Alvo: prever se uma NC é Crítica ou Outra
- Features: filial, classificação, código da unidade, área do checklist
- Algoritmo: Random Forest
- Arquivos gerados: `modelo/modelo_cco.pkl`, `modelo/encoders_cco.pkl`

### Quando fará sentido usar:

Quando houver 6+ meses de dados acumulados, com distribuição mais equilibrada entre as classes. Nesse cenário, é possível retreinar, adicionar `stratify=y`, comparar com `DummyClassifier` como baseline e avaliar precision/recall por classe em vez de só acurácia global.

---

## Testes Automatizados

53 testes cobrindo as etapas de extração, limpeza e análise.

```bash
pytest
```

### O que é testado:

- Extração: normalização de nomes de coluna, classificação por conteúdo, detecção de header
- Limpeza: conversão de tipos, explode de NCs compostas, tratamento de valores nulos, formato BR de decimais
- Análise: cálculo de KPIs, agrupamentos, ordenação, tratamento de DataFrame vazio

Casos-limite cobertos: DataFrame vazio, None em coluna de texto, % Nota com vírgula decimal, pergunta vazia após explode, pergunta que não é código.

---

## Decisões Técnicas

### Por que CSV e não XLSX?

O Google Sheets exporta .xlsx com as células vazias viradas em 1900-01-01 00:00:00 quando lê com Pandas. Isso fazia 87% das NCs do arquivo bruto virarem linhas com data em vez de código. A solução foi exportar em CSV, que preserva os valores como texto.

### Por que classificar arquivos por conteúdo e não por nome?

O usuário pode salvar os CSVs com qualquer nome. Se o pipeline dependesse do nome, quebraria quando alguém renomeasse um arquivo. A classificação por conteúdo (nome das colunas) é robusta a essa variação.

### Por que Plotly + Kaleido e não Matplotlib?

O Matplotlib 3.9.2 estoura a pilha (RecursionError) no Python 3.14 ao tentar fazer deepcopy dos markers. Plotly + Kaleido não tem esse problema e gera os PNGs sem erro.

### Por que explodir as NCs?

Uma linha da aba "Não Conformidades" pode conter várias NCs separadas por / (ex: 3.2 / 5.3 / 6.1). Sem explode, uma linha poderia contar como 1 NC ou como 3. O explode garante que cada NC seja contada individualmente.

### Por que ReportLab pro PDF e não gerar HTML?

ReportLab gera PDF nativo, com paginação real, e permite pintar o fundo de cada página via `onFirstPage`/`onLaterPages`. A alternativa (HTML + wkhtmltopdf) exigiria dependência externa e não roda sem admin no Windows.

---

## Referências

- PEDREGOSA, F. et al. Scikit-learn: Machine Learning in Python. JMLR, 2011.
- MCKINNEY, W. Python for Data Analysis. O'Reilly Media, 2022.
