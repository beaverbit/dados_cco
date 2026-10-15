# PROCESSO — Como Alimentar o Pipeline

Guia rápido pra quem vai rodar o pipeline no dia a dia. Não precisa saber Python — só seguir os passos.

---

## Visão geral

O pipeline funciona em 3 etapas:

```
1. Exportar dados da fonte    (manual, uma vez por ciclo)
2. Rodar o pipeline Python    (comando único)
3. Abrir o dashboard          (comando único)
```

Tudo que entra está em `dados_brutos/`. Tudo que sai está em `dados_tratados/`, `imagens/` e no dashboard.

O `run_all.py` executa 7 scripts em sequência:

1. Extração — consolida os CSVs brutos
2. Limpeza — valida, expande NCs compostas, padroniza
3. Análise — gera os 13 KPIs
4. Visualização — gera os 8 gráficos estáticos em `imagens/`
5. Machine Learning — treina o modelo (experimental)
6. Relatório PDF — gera `dados_tratados/relatorio_cco.pdf`

---

## 1. Exportar os dados da fonte

### O que exportar

O pipeline trabalha com **duas categorias de registros**:

- **Registro das Análises** — uma linha por análise realizada
- **Não Conformidades** — uma linha por NC registrada

### Como exportar

A forma de exportar depende da fonte. O pipeline espera **CSV** como formato de entrada.

**Importante:** exporte sempre em **CSV**, nunca em **Excel (.xlsx)**. Algumas ferramentas (como o Google Sheets) geram `.xlsx` com células vazias viradas em `1900-01-01 00:00:00` quando lidas com Pandas, o que quebra o pipeline.

### Onde salvar

Dentro da pasta do projeto, crie uma subpasta com o período de referência no formato `AAAA-MM`:

```
dados_brutos/
├── 2026-07/
├── 2026-08/
└── 2026-09/          ← período atual
    ├── registro_analises.csv
    └── nao_conformidades.csv
```

**Regras:**

- O nome da pasta **precisa** estar no formato `AAAA-MM` (ex: `2026-09`, `2026-10`)
- Você pode salvar os CSVs com **qualquer nome** — o pipeline identifica pelo conteúdo, não pelo nome
- Cada período fica em sua própria subpasta

**Exemplo prático:** para adicionar um novo período:

```bash
mkdir -p dados_brutos/AAAA-MM
# Copie os dois CSVs exportados pra dentro dessa pasta
```

---

## 2. Rodar o pipeline

### Antes de rodar

Confirme que os CSVs do período estão na subpasta correta:

```bash
ls dados_brutos/AAAA-MM/
# Deve mostrar os dois CSVs exportados
```

### Rodar

Abra o terminal na pasta do projeto e rode:

```bash
python3 run_all.py
```

**O que esse comando faz:**

1. Lê todos os CSVs de `dados_brutos/` (todos os períodos)
2. Consolida por tipo (análises e NCs)
3. Limpa, expande NCs compostas e padroniza
4. Gera os 13 KPIs
5. Gera os 8 gráficos estáticos em `imagens/`
6. Treina o modelo de ML
7. Gera o relatório PDF em `dados_tratados/relatorio_cco.pdf`

**Tempo esperado:** 30-40 segundos no Linux, 60-80 segundos no Windows (a etapa 07 é a mais lenta).

### O que olhar na saída

No final do processamento, aparece um bloco de validação:

```
============================================================
VALIDAÇÃO: X aviso(s) encontrado(s)
============================================================
  ⚠  [categoria] Descrição do problema
  ...
============================================================
```

**Se não aparecer aviso:** tudo certo, pode seguir.

**Se aparecer aviso:** leia com calma antes de mostrar o dashboard pra alguém. Os avisos cobrem:

- **Contagem baixa** — pode indicar que os CSVs não foram salvos corretamente
- **Muitos valores vazios** — a planilha pode estar com colunas faltando
- **Taxa de NC suspeita** — mais de 90% dos registros como "Não Conforme"
- **Gravidade suspeita** — mais de 90% das NCs como "Crítica"
- **Duplicatas** — linhas repetidas na planilha

Em geral, esses avisos indicam problema na fonte dos dados, não no pipeline.

### Onde está o PDF

Depois que o pipeline terminar, o relatório PDF está em:

```
dados_tratados/relatorio_cco.pdf
```

É um PDF de 7 páginas, com a mesma identidade visual do dashboard (fundo escuro, cards de KPI, 13 gráficos). Pode ser impresso ou enviado por e-mail pra quem não tem acesso ao Streamlit.

---

## 3. Abrir o dashboard

```bash
streamlit run scripts/05_dashboard_cco.py
```

O navegador abre automaticamente em `http://localhost:8501`.

**Para fechar:** `Ctrl+C` no terminal.

**Se quiser que outras pessoas na rede acessem:** o terminal mostra um "Network URL" tipo `http://192.168.1.11:8501`. Quem estiver na mesma rede pode abrir esse endereço.

---

## Adicionando um período novo

1. **Exporte os CSVs** da fonte (ver passo 1)
2. **Crie a subpasta** do período:
   ```bash
   mkdir -p dados_brutos/AAAA-MM
   ```
3. **Salve os CSVs** dentro da pasta
4. **Rode o pipeline:**
   ```bash
   python3 run_all.py
   ```
5. **Pronto.** O dashboard já mostra os dados novos, o PDF é regenerado, e os períodos antigos continuam no histórico.

**Importante:** os dados de períodos anteriores **não são apagados**. Cada vez que você adiciona um período, o pipeline lê **tudo** (todos os períodos) e regenera os CSVs consolidados. Nada se perde.

---

## Problemas comuns

### "O dashboard tá mostrando menos dados do que eu esperava"

Confira:

1. Os CSVs estão na subpasta certa? (`dados_brutos/AAAA-MM/` e não `dados_brutos/`)
2. O nome da pasta está no formato `AAAA-MM`?
3. O pipeline rodou sem erro? Confira a saída do `run_all.py`

### "Apareceu aviso de que muitas NCs são Críticas"

Isso é um **problema na fonte**, não no pipeline. A fórmula que calcula a gravidade na planilha de origem provavelmente está com problema.

**O que fazer:**

- Abra a planilha original
- Confira se a coluna `Gravidade` está sendo calculada corretamente
- Se muitas linhas têm `Crítica` como valor fixo, provavelmente a fórmula está quebrada

Até isso ser corrigido, os KPIs de gravidade vão ficar distorcidos.

### "Apareceu aviso de contagem baixa"

Pode ser:

1. O CSV está incompleto (a exportação falhou ou baixou só parte)
2. O arquivo foi salvo no lugar errado
3. A planilha realmente tem menos linhas que o esperado

Abra o CSV no Excel ou Google Sheets e confira se tem as linhas esperadas.

### "O PDF não foi gerado"

Verifique:

1. A pasta `dados_tratados/` existe? Se não, rode `mkdir -p dados_tratados`
2. O `reportlab` está instalado? Confirme com `pip list | grep reportlab`. Se não estiver, rode `pip install -r requirements.txt`
3. A saída do terminal mostra erro na etapa 07? Salve o print e mande

### "O pipeline rodou, mas o dashboard não abriu"

Feche o terminal e abra de novo. Se o erro persistir, me chama.

---

## Estrutura de pastas (para referência)

```
dados_cco/
│
├── scripts/                   # Todos os scripts executáveis
│   ├── 01_extracao_cco.py     # Lê e consolida os CSVs brutos
│   ├── 02_limpeza_cco.py      # Limpa e valida os dados
│   ├── 03_analise_cco.py      # Gera os 13 KPIs
│   ├── 04_visualizacao_cco.py # Gera os 8 gráficos estáticos
│   ├── 05_dashboard_cco.py    # Dashboard interativo
│   ├── 06_machine_learning_cco.py  # Treina o modelo de ML
│   └── 07_gerar_pdf_cco.py    # Gera o relatório PDF dark
│
├── run_all.py                 # Roda tudo em ordem (01→07)
│
├── dados_brutos/              # ← VOCÊ ALIMENTA AQUI
│   ├── 2026-09/
│   │   ├── registro_analises.csv
│   │   └── nao_conformidades.csv
│   └── 2026-10/
│       ├── registro_analises.csv
│       └── nao_conformidades.csv
│
├── dados_tratados/            # Gerado automaticamente
│   ├── analises_limpas.csv
│   ├── nao_conformidades_limpas.csv
│   ├── resultados_analise_cco.csv
│   └── relatorio_cco.pdf      ← O PDF sai aqui
│
├── imagens/                   # Gerado automaticamente
├── modelo/                    # Gerado automaticamente
├── tests/                     # Testes automatizados
└── README.md
```

**Só a pasta `dados_brutos/` é alimentada manualmente.** Todo o resto é gerado pelo `run_all.py`.

---

## Fluxo resumido (cola no mural)

```
1. Exporta 2 CSVs em CSV
2. Cria pasta dados_brutos/AAAA-MM/
3. Salva os 2 CSVs dentro dela
4. python3 run_all.py
5. streamlit run scripts/05_dashboard_cco.py
```

Tempo total: **menos de 2 minutos**, contando a exportação.

---

## Registro de problemas

Se o comportamento não for o esperado:

1. Salve o print da tela e a saída completa do terminal
2. Identifique qual script falhou (`01` a `07`)
3. Abra o script correspondente e confira o trecho que processa o dado em questão
4. Se for um caso novo (coluna com nome diferente, tipo de dado novo), ajuste o mapeamento no `scripts/02_limpeza_cco.py` e registre a mudança
