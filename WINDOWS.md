# PROCESSO — Como Alimentar o Pipeline do CCO (Windows)

Guia rápido pra quem vai rodar o pipeline no dia a dia no Windows. Não precisa saber Python — só seguir os passos.

---

## Visão geral

O pipeline funciona em 3 etapas:

```
1. Exportar dados do Google Sheets   (manual, uma vez por mês)
2. Rodar o pipeline Python           (comando único)
3. Abrir o dashboard                 (comando único)
```

Tudo que entra está em `dados_brutos\`. Tudo que sai está em `dados_tratados\`, `imagens\` e no dashboard.

---

## 1. Setup inicial (só uma vez)

Se você acabou de clonar o repositório numa máquina nova, precisa preparar o ambiente. **Esses passos são só uma vez.**

### 1.1. Instalar Python (sem admin)

O Windows da empresa pode não ter Python instalado. Use o Python Install Manager oficial da Microsoft:

1. Baixe o instalador em [python.org](https://www.python.org/downloads/)
2. Execute o instalador (não precisa de admin)
3. Escolha **Python 3.12** (não 3.14 nem 3.15 — versões novas demais dão erro de compilação)
4. Confirme no terminal:

```powershell
py -3.12 --version
```

Deve mostrar `Python 3.12.x`.

### 1.2. Clonar o repositório

```powershell
cd C:\Users\<seu-usuario>
git clone https://github.com/beaverbit/dados_cco.git
cd dados_cco
```

### 1.3. Criar o ambiente virtual

```powershell
py -3.12 -m venv venv
```

### 1.4. Liberar execução de scripts no PowerShell

O PowerShell bloqueia scripts por padrão. Rode uma vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirme com `S` ou `Y`. Isso libera scripts só pra sua conta, sem precisar de admin.

### 1.5. Ativar o ambiente virtual

```powershell
.\venv\Scripts\Activate.ps1
```

Você deve ver `(venv)` no começo da linha:

```
(venv) PS C:\Users\jhonatan.santos\dados_cco>
```

### 1.6. Instalar as dependências

```powershell
pip install -r requirements.txt
```

Isso baixa pandas, plotly, streamlit, scikit-learn, pytest e outras. Leva uns 2-4 minutos. **Só precisa fazer uma vez.**

### 1.7. Confirmar que está tudo certo

```powershell
pytest
```

Deve mostrar `53 passed in ~0.5s`. Se sim, o ambiente está pronto.

---

## 2. Exportar os dados do Google Sheets

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
dados_brutos\
├── 2026-09\
│   ├── registro_analises.csv
│   └── nao_conformidades.csv
└── 2026-10\
    ├── registro_analises.csv
    └── nao_conformidades.csv
```

**Regras:**

- O nome da pasta **precisa** estar no formato `AAAA-MM` (ex: `2026-09`, `2026-10`)
- Você pode salvar os CSVs com **qualquer nome** — o pipeline identifica pelo conteúdo, não pelo nome
- Cada mês fica em sua própria subpasta

**Exemplo prático:** para adicionar outubro de 2026:

```powershell
cd C:\Users\jhonatan.santos\dados_cco
mkdir dados_brutos\2026-10
# Copie os dois CSVs baixados pra dentro dessa pasta
```

---

## 3. Rodar o pipeline

### Antes de rodar

Abra o PowerShell e vá até a raiz do projeto:

```powershell
cd C:\Users\jhonatan.santos\dados_cco
```

Ative o ambiente virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Confirme que `(venv)` aparece na linha.

### Rodar

```powershell
python run_all.py
```

**O que esse comando faz:**

1. Lê todos os CSVs de `dados_brutos\` (todos os meses)
2. Consolida por tipo (análises e NCs)
3. Limpa, explode NCs compostas e padroniza
4. Gera os 13 KPIs
5. Gera os 8 gráficos estáticos em `imagens\`
6. Treina o modelo de ML

**Tempo esperado:** 30-40 segundos no Windows.

### O que olhar na saída

No final do processamento, aparece um bloco de validação:

```
============================================================
VALIDAÇÃO: OK — nenhum problema detectado.
============================================================
```

**Se não aparecer aviso:** tudo certo, pode seguir.

**Se aparecer aviso:**

```
VALIDAÇÃO: 1 aviso(s) encontrado(s)
  ⚠  [categoria] Descrição do problema
```

Leia com calma antes de mostrar o dashboard. Os avisos cobrem:

- **Contagem baixa** — pode indicar que os CSVs não foram salvos corretamente
- **Muitos valores vazios** — a planilha pode estar com colunas faltando
- **Taxa de NC suspeita** — mais de 90% das análises como "Não Conforme"
- **Duplicatas** — linhas repetidas na planilha

Em geral, indicam problema na planilha de origem, não no pipeline.

---

## 4. Abrir o dashboard

```powershell
streamlit run 05_dashboard_cco.py
```

O navegador abre automaticamente em `http://localhost:8501`.

**Para fechar:** `Ctrl+C` no terminal.

**Se quiser que outras pessoas na rede acessem:** o terminal mostra um "Network URL" tipo `http://192.168.10.246:8501`. Quem estiver na mesma rede pode abrir esse endereço.

---

## 5. Adicionando um mês novo

1. **Baixe os CSVs** do Google Sheets (ver passo 2)
2. **Crie a subpasta** do mês:
   ```powershell
   mkdir dados_brutos\2026-10
   ```
3. **Salve os CSVs** dentro da pasta
4. **Rode o pipeline:**
   ```powershell
   python run_all.py
   ```
5. **Pronto.** O dashboard já mostra os dados novos, e os meses antigos continuam no histórico.

**Importante:** os dados de meses anteriores **não são apagados**. Cada vez que você adiciona um mês, o pipeline lê **tudo** (todos os meses) e regenera os CSVs consolidados. Nada se perde.

---

## Problemas comuns (Windows)

### "O termo '.\venv\Scripts\Activate.ps1' não é reconhecido"

Você não está na raiz do projeto, ou o ambiente virtual não foi criado. Verifique:

```powershell
pwd
```

Se não estiver em `C:\Users\<usuario>\dados_cco`, navegue até lá com `cd`.

### "A execução de scripts foi desabilitada neste sistema"

Rode novamente:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "python não é reconhecido"

O Python não está no PATH, ou você não está no ambiente virtual. Tenta:

```powershell
py --version
```

Se funcionar, use `py` no lugar de `python`:

```powershell
py run_all.py
```

### "pip não é reconhecido"

O ambiente virtual não está ativado. Confirme que aparece `(venv)` na linha. Se não aparecer, rode:

```powershell
.\venv\Scripts\Activate.ps1
```

### "mkdir não aceita o parâmetro -p"

No Windows, o comando é diferente:

```powershell
# Linux/Mac
mkdir -p dados_brutos dados_tratados modelo imagens

# Windows
mkdir dados_brutos, dados_tratados, modelo, imagens
```

### Erro do pandas na instalação (`error: metadata-generation-failed`)

Você está usando Python 3.14 ou 3.15. Essas versões são novas demais e algumas bibliotecas não têm binário pronto. Use o Python 3.12:

```powershell
# Remove o venv antigo
Remove-Item -Recurse -Force venv

# Cria com Python 3.12
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "O pipeline rodou, mas o dashboard não abriu"

1. Feche o terminal e rode novamente:
   ```powershell
   streamlit run 05_dashboard_cco.py
   ```

2. Se o erro persistir, tente outra porta:
   ```powershell
   streamlit run 05_dashboard_cco.py --server.port 8502
   ```

### "Porta 8501 já está em uso"

Outra instância do Streamlit está rodando. Ou feche ela, ou use outra porta:

```powershell
streamlit run 05_dashboard_cco.py --server.port 8502
```

---

## Estrutura de pastas (para referência)

```
dados_cco\
│
├── 01_extracao_cco.py         # Lê e consolida os CSVs brutos
├── 02_limpeza_cco.py          # Limpa e valida os dados
├── 03_analise_cco.py          # Gera os 13 KPIs
├── 04_visualizacao_cco.py     # Gera os 8 gráficos estáticos
├── 05_dashboard_cco.py        # Dashboard interativo
├── 06_machine_learning_cco.py # Treina o modelo de ML
├── run_all.py                 # Roda tudo em ordem
│
├── dados_brutos\              # ← VOCÊ ALIMENTA AQUI
│   ├── 2026-09\
│   │   ├── registro_analises.csv
│   │   └── nao_conformidades.csv
│   └── 2026-10\
│       ├── registro_analises.csv
│       └── nao_conformidades.csv
│
├── dados_tratados\            # Gerado automaticamente
├── imagens\                   # Gerado automaticamente
├── modelo\                    # Gerado automaticamente
├── tests\                     # Testes automatizados
└── venv\                      # Ambiente virtual (não versionar)
```

**Só a pasta `dados_brutos\` é alimentada manualmente.** Todo o resto é gerado pelo `run_all.py`.

---

## Fluxo resumido (cola no mural)

```
1. Google Sheets → exporta 2 CSVs em CSV
2. Cria pasta dados_brutos\AAAA-MM\
3. Salva os 2 CSVs dentro dela
4. cd C:\Users\<usuario>\dados_cco
5. .\venv\Scripts\Activate.ps1
6. python run_all.py
7. streamlit run 05_dashboard_cco.py
```

Tempo total: **menos de 1 minuto**, contando a exportação.

---

## Dúvidas

Se algo der errado:

1. Salve o print da tela e a saída completa do terminal
2. Identifique qual script falhou (`01` a `06`)
3. Abra o script correspondente e confira o trecho que processa o dado em questão
4. Se for um caso novo (coluna com nome diferente, tipo de dado novo), ajuste o mapeamento no `02_limpeza_cco.py` e registre a mudança
