# Churn Analytics — IBM Telco

Projeto de análise de churn desenvolvido como portfólio para estágio em dados. A base utilizada é o dataset público **IBM Telco Customer Churn** (Kaggle), com 7.043 clientes e 21 colunas cobrindo perfil, serviços contratados, tipo de contrato, forma de pagamento e status de cancelamento.

O projeto cobre o fluxo de preparação, análise e visualização dos dados, utilizando **Python/Pandas** no tratamento e transformação, **Databricks** para armazenamento em Delta Tables e execução das análises SQL, e **Power BI** para visualização dos resultados.

O objetivo é responder perguntas de negócio relacionadas ao cancelamento de clientes, identificando padrões de churn, segmentos de maior risco e possíveis oportunidades de retenção.

---

## Arquitetura

```
┌─────────────────┐
│   CSV / Dataset │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Python + Pandas │
│ ETL + Features  │
└────────┬────────┘
         ↓
┌─────────────────┐
│    Databricks   │
│   Delta Tables  │
└────────┬────────┘
         ↓
┌─────────────────┐
│   SQL Analytics │
│ Business Queries│
└────────┬────────┘
         ↓
┌─────────────────┐
│    Power BI     │
│    Dashboard    │
└─────────────────┘
```

---

## Perguntas de negócio respondidas

1. Qual o perfil do cliente que mais cancela?
2. Clientes com contrato mensal apresentam maior taxa de churn?
3. Clientes com mais serviços ativos cancelam menos?
4. Qual o impacto financeiro do churn em receita mensal?
5. Quanto tempo de permanência reduz o risco de cancelamento?

---

## Principais achados

| Achado | Impacto |
|---|---|
| Clientes com até 6 meses de permanência apresentam taxa de churn próxima de 47%, a maior entre os períodos analisados | Alto |
| Clientes com contrato mensal apresentam taxa de churn de 42%, contra 3% em contratos de 2 anos | Alto |
| Clientes que utilizam Electronic check apresentam taxa de churn de 45% | Médio |
| Clientes idosos apresentam taxa de churn ~70% maior que não-idosos | Médio |
| $139K/mês em receita diretamente associada a clientes que cancelaram | Alto |

---

## Stack

- **Python** — ETL, limpeza, feature engineering e heuristic churn risk score
- **Pandas** — manipulação e transformação dos dados
- **Matplotlib / Seaborn** — visualizações na EDA
- **Databricks** — armazenamento em Delta Tables e execução das queries SQL analíticas
- **SQL** — 18 queries respondendo as perguntas de negócio, executadas sobre Delta Tables
- **Power BI** — dashboard executivo com medidas DAX

---

## Estrutura do repositório

```
telco-churn-analytics/
├── data/                          # pasta local — arquivos ignorados pelo .gitignore
│   └── .gitkeep
├── databricks/
│   └── churn_analytics.dbc        # notebook com Delta Tables e 18 queries SQL
├── notebooks/
│   └── eda.ipynb                  # análise exploratória com 8 visualizações
├── powerbi/                       # dashboard .pbix e print do resultado
├── sql/
│   └── business_questions.sql     # versão local das queries analíticas
├── src/
│   ├── etl_telco_churn.py         # pipeline ETL completo
│   ├── add_risk_score.py          # cria a coluna de heuristic churn risk score
│   └── export_to_csv.py           # exporta tabelas para CSV
├── .gitignore
├── LICENSE
└── README.md
```

---

## Como executar

O pipeline local em Python/SQLite é utilizado para reproduzir o tratamento e preparação dos dados. As análises SQL apresentadas no projeto são executadas no Databricks sobre Delta Tables.

### Pré-requisitos

```bash
pip install pandas matplotlib seaborn jupyter
```

### 1. Baixar o dataset

Baixe o arquivo `WA_Fn-UseC_-Telco-Customer-Churn.csv` no Kaggle:
[IBM Telco Customer Churn — Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)

Salve em `data/Telco_Customer_Churn.csv`.

### 2. Rodar o ETL

```bash
python src/etl_telco_churn.py --csv data/Telco_Customer_Churn.csv
```

O script gera o banco `telco_churn.db` com 3 tabelas e exibe uma validação automática no terminal.

### 3. Adicionar o heuristic churn risk score

```bash
python src/add_risk_score.py
```

Segmenta cada cliente em três grupos de risco de churn com base em 4 fatores de negócio identificados na EDA.

### 4. Exportar para CSV

```bash
python src/export_to_csv.py
```

Gera os arquivos `customers_clean.csv`, `dim_services.csv` e `fact_churn.csv` na pasta `data/`.

### 5. EDA

Abra o notebook no Google Colab ou Jupyter:

```bash
jupyter notebook notebooks/eda.ipynb
```

Se usar o Colab, suba o `telco_churn.db` no Google Drive e ajuste o caminho na primeira célula para `/content/drive/MyDrive/telco_churn.db`.

### 6. Databricks

Importe `databricks/churn_analytics.dbc` em um workspace Databricks e execute o notebook para criar as Delta Tables e reproduzir as 18 queries analíticas.

---

## Databricks

Como parte do estudo de ferramentas utilizadas em ambientes de Analytics, o dataset tratado pelo pipeline em Python foi disponibilizado no Databricks em Delta Tables. As 18 queries SQL utilizadas para responder às perguntas de negócio foram executadas diretamente no ambiente Databricks.

O uso do Databricks neste projeto teve como objetivo praticar a plataforma, Delta Tables e execução de análises SQL em um ambiente cloud. O notebook `.dbc` pode ser importado diretamente em um workspace Databricks.

---

## Heuristic Churn Risk Score

Segmenta clientes em três grupos de risco de churn com base em fatores de negócio identificados na EDA. Não é um modelo preditivo — é uma segmentação baseada em regras, o que permite interpretar facilmente os fatores associados a cada nível de risco e utilizá-los como apoio à priorização de ações de retenção.

| Fator | Peso |
|---|---|
| Contrato mensal | +1 |
| Tenure menor que 12 meses | +1 |
| Pagamento via Electronic check | +1 |
| Cliente idoso (SeniorCitizen) | +1 |

**Resultado:**

| Categoria | Clientes | Taxa de churn |
|---|---|---|
| Alto risco (3-4 pontos) | 1.314 | 60,7% |
| Médio risco (2 pontos) | 1.824 | 38,1% |
| Baixo risco (0-1 pontos) | 3.905 | 9,6% |

---

## Recomendações de negócio

1. **Ações de engajamento nos primeiros 90 dias** — clientes com até 6 meses de permanência apresentam taxa de churn próxima de 47%. Avaliar programas de onboarding e medir seu impacto na retenção por meio de testes controlados.

2. **Avaliar estratégias de migração para contratos de maior duração** — clientes com contrato mensal apresentam taxa de churn maior. Investigar incentivos para migração e medir seu efeito sobre a retenção.

3. **Investigar a relação entre Electronic check e churn** — clientes com esse método apresentam a maior taxa de evasão. Verificar se há atrito no processo de pagamento ou se é um indicador de perfil de menor engajamento.

4. **Segmentação por risco para ações preventivas** — utilizar o heuristic churn risk score como uma regra exploratória para priorizar clientes de maior risco em ações de retenção.

---

## Dataset

**IBM Telco Customer Churn** — disponível publicamente no Kaggle.

- 7.043 clientes, 21 colunas originais
- Variável alvo: `Churn` (Yes/No) — 26,54% de churn
- Colunas: perfil do cliente, serviços contratados, tipo de contrato, forma de pagamento e valores de cobrança

O dataset é fictício e representa um snapshot estático — não possui dados temporais ou de eventos, o que limita análises de séries temporais mas é adequado para segmentação e identificação de padrões de risco.

---

## Autor

Desenvolvido por Vivian · [GitHub](https://github.com/vivikari)