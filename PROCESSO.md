# PROCESSO — Como Alimentar o Pipeline do CCO

Guia rápido pra quem vai rodar o pipeline no dia a dia. Não precisa saber Python — só seguir os passos.

---

## Visão geral

O pipeline funciona em 6 etapas:

```
1. Exportar dados do Google Sheets   (manual, uma vez por mês)
2. Rodar o pipeline Python           (comando único)
3. Abrir o dashboard                 (comando único)
```

Tudo que entra está em `dados_brutos/`. Tudo que sai está em `dados_tratados/`, `imagens/` e no dashboard.

---

## 1. Exportar os dados do Google Sheets

### O que exportar

A planilha do CCO tem **duas abas** que interessam:

- **Registro das Análises** — uma linha por análise realizada
- **Não Conformidades** — uma linha por NC registrada

### Como exportar

Para cada aba:

1. Abra a aba no Google Sheets
2. Vá em **Arquivo → Fazer download → Valores separados por vírgula (.csv)**
3. O arquivo vai baixar para a pasta de downloads do navegador

**Importante:** exporte em **CSV**, nunca em **Excel (.xlsx)**. O `.xlsx` do Google Sheets tem um bug conhecido que transforma células vazias em `1900-01-01 00:00:00`, o que quebra o pipeline.

### Onde salvar

Dentro da pasta do projeto, crie uma subpasta com o nome do mês no formato `AAAA-MM`:

```
dados_brutos/
├── 2026-07/
├── 2026-08/
└── 2026-09/          ← mês atual
    ├── registro_analises.csv
    └── nao_conformidades.csv
```

**Regras:**

- O nome da pasta **precisa** estar no formato `AAAA-MM` (ex: `2026-09`, `2026-10`)
- Você pode salvar os CSVs com **qualquer nome** — o pipeline identifica pelo conteúdo, não pelo nome
- Cada mês fica em sua própria subpasta

**Exemplo prático:** para adicionar setembro de 2026:

```bash
mkdir -p dados_brutos/2026-09
# Copie os dois CSVs baixados pra dentro dessa pasta
```

---

## 2. Rodar o pipeline

### Antes de rodar

Confirme que os CSVs do mês estão na subpasta correta:

```bash
ls dados_brutos/2026-09/
# Deve mostrar: registro_analises.csv  nao_conformidades.csv
```

### Rodar

Abra o terminal na pasta do projeto e rode:

```bash
python3 run_all.py
```

**O que esse comando faz:**

1. Lê todos os CSVs de `dados_brutos/` (todos os meses)
2. Consolida por tipo (análises e NCs)
3. Limpa, explode NCs compostas e padroniza
4. Gera os 13 KPIs
5. Gera os 8 gráficos estáticos em `imagens/`
6. Treina o modelo de ML

**Tempo esperado:** 30-40 segundos.

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
- **Taxa de NC suspeita** — mais de 90% das análises como "Não Conforme"
- **Gravidade suspeita** — mais de 90% das NCs como "Crítica"
- **Duplicatas** — linhas repetidas na planilha

Em geral, esses avisos indicam problema na planilha de origem, não no pipeline.

---

## 3. Abrir o dashboard

```bash
streamlit run 05_dashboard_cco.py
```

O navegador abre automaticamente em `http://localhost:8501`.

**Para fechar:** `Ctrl+C` no terminal.

**Se quiser que outras pessoas na rede acessem:** o terminal mostra um "Network URL" tipo `http://192.168.1.11:8501`. Quem estiver na mesma rede pode abrir esse endereço.

---

## Adicionando um mês novo

1. **Baixe os CSVs** do Google Sheets (ver passo 1)
2. **Crie a subpasta** do mês:
   ```bash
   mkdir -p dados_brutos/2026-10
   ```
3. **Salve os CSVs** dentro da pasta
4. **Rode o pipeline:**
   ```bash
   python3 run_all.py
   ```
5. **Pronto.** O dashboard já mostra os dados novos, e os meses antigos continuam no histórico.

**Importante:** os dados de meses anteriores **não são apagados**. Cada vez que você adiciona um mês, o pipeline lê **tudo** (todos os meses) e regenera os CSVs consolidados. Nada se perde.

---

## Problemas comuns

### "O dashboard tá mostrando menos dados do que eu esperava"

Confira:

1. Os CSVs estão na subpasta certa? (`dados_brutos/2026-09/` e não `dados_brutos/`)
2. O nome da pasta está no formato `AAAA-MM`?
3. O pipeline rodou sem erro? Confira a saída do `run_all.py`

### "Apareceu aviso de que muitas NCs são Críticas"

Isso é um **problema na planilha**, não no pipeline. A fórmula que calcula a gravidade no Google Sheets provavelmente está com problema.

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

### "O pipeline rodou, mas o dashboard não abriu"

Feche o terminal e abra de novo. Se o erro persistir, me chama.

---

## Estrutura de pastas (para referência)

```
dados_cco/
│
├── 01_extracao_cco.py         # Lê e consolida os CSVs brutos
├── 02_limpeza_cco.py          # Limpa e valida os dados
├── 03_analise_cco.py          # Gera os 13 KPIs
├── 04_visualizacao_cco.py     # Gera os 8 gráficos estáticos
├── 05_dashboard_cco.py        # Dashboard interativo
├── 06_machine_learning_cco.py # Treina o modelo de ML
├── run_all.py                 # Roda tudo em ordem
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
├── imagens/                   # Gerado automaticamente
├── modelo/                    # Gerado automaticamente
└── README.md
```

**Só a pasta `dados_brutos/` é alimentada manualmente.** Todo o resto é gerado pelo `run_all.py`.

---

## Fluxo resumido (cola no mural)

```
1. Google Sheets → exporta 2 CSVs em CSV
2. Cria pasta dados_brutos/AAAA-MM/
3. Salva os 2 CSVs dentro dela
4. python3 run_all.py
5. streamlit run 05_dashboard_cco.py
```

Tempo total: **menos de 1 minuto**, contando a exportação.

---

## Dúvidas

Se algo der errado ou o comportamento não for o esperado, guarda o print da tela e me manda. O pipeline foi feito pra ser robusto, mas se aparecer um caso novo, abra uma issue que eu resolvo.