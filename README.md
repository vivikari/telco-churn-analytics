# Churn Analytics — IBM Telco

Projeto de análise de churn desenvolvido como portfólio para estágio em dados. A base utilizada é o dataset público **IBM Telco Customer Churn** (Kaggle), com 7.043 clientes e 21 colunas cobrindo perfil, serviços contratados, tipo de contrato, forma de pagamento e se o cliente cancelou.

O objetivo foi responder perguntas reais de negócio sobre cancelamento de clientes, desde a limpeza dos dados até um dashboard executivo no Power BI.

---

## Perguntas de negócio respondidas

1. Qual o perfil do cliente que mais cancela?
2. Contratos mensais têm churn significativamente maior?
3. Clientes com mais serviços ativos cancelam menos?
4. Qual o impacto financeiro do churn em receita mensal?
5. Quanto tempo de permanência reduz o risco de cancelamento?

---

## Principais achados

| Achado | Impacto |
|--------|---------|
| Clientes nos primeiros 6 meses cancelam a ~47% | Alto |
| Contrato mensal gera 42% de churn vs 3% em contratos de 2 anos | Alto |
| Electronic check está associado a 45% de churn | Médio |
| Clientes idosos cancelam ~70% mais que não-idosos | Médio |
| $139K/mês em receita diretamente associada a clientes que cancelaram | Alto |

---

## Stack

- **Python** — ETL, limpeza, feature engineering e score de risco
- **Pandas** — manipulação e transformação dos dados
- **Matplotlib / Seaborn** — visualizações na EDA
- **SQLite** — banco de dados local para análise
- **SQL** — queries de agregação respondendo as perguntas de negócio
- **Databricks** — ambiente cloud para reescrita e execução das queries SQL
- **Power BI** — dashboard executivo com medidas DAX

---

## Estrutura do repositório

```
telco-churn-analytics/
├── data/                          # pasta local — arquivos ignorados pelo .gitignore
│   └── .gitkeep
├── databricks/
│   └── churn_analytics.dbc        # notebook SQL executado no Databricks
├── notebooks/
│   └── eda.ipynb                  # análise exploratória com 8 visualizações
├── powerbi/                       # dashboard .pbix e print do resultado
├── sql/
│   └── business_questions.sql     # 18 queries respondendo as 5 perguntas de negócio
├── src/
│   ├── etl_telco_churn.py         # pipeline ETL completo
│   ├── add_risk_score.py          # cria a coluna de score de risco
│   └── export_to_csv.py           # exporta tabelas SQLite para CSV (Power BI)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Como executar

### Pré-requisitos

```bash
pip install pandas matplotlib seaborn jupyter
```

### 1. Baixar o dataset

Baixe o arquivo `WA_Fn-UseC_-Telco-Customer-Churn.csv` no Kaggle:
[https://www.kaggle.com/datasets/blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)

Salve em `data/Telco_Customer_Churn.csv`.

### 2. Rodar o ETL

```bash
python src/etl_telco_churn.py --csv data/Telco_Customer_Churn.csv
```

O script vai gerar o banco `telco_churn.db` com 3 tabelas e exibir uma validação automática no terminal.

### 3. Adicionar o score de risco

```bash
python src/add_risk_score.py
```

Classifica cada cliente em Baixo, Médio ou Alto risco com base em 4 fatores de negócio identificados na EDA.

### 4. Exportar para CSV (Power BI)

```bash
python src/export_to_csv.py
```

Gera os arquivos `customers_clean.csv`, `dim_services.csv` e `fact_churn.csv` na pasta `data/`.

### 5. EDA

Abra o notebook no Google Colab ou Jupyter:

```bash
jupyter notebook notebooks/eda.ipynb
```

Se usar o Colab, suba o `telco_churn.db` no Google Drive e ajuste o caminho na primeira célula.

---

## Score de risco

O score classifica clientes em 3 grupos com base em fatores de negócio identificados na EDA, sem uso de Machine Learning:

| Fator | Peso |
|-------|------|
| Contrato mensal | +1 |
| Tenure menor que 12 meses | +1 |
| Pagamento via Electronic check | +1 |
| Cliente idoso (SeniorCitizen) | +1 |

**Resultado:**

| Categoria | Clientes | Taxa de churn |
|-----------|----------|---------------|
| Alto risco (3-4 pontos) | 1.314 | 60,7% |
| Médio risco (2 pontos) | 1.824 | 38,1% |
| Baixo risco (0-1 pontos) | 3.905 | 9,6% |

---

## Databricks

As principais queries de agregação foram reescritas e executadas no Databricks (free edition) para praticar o ambiente antes de usar em produção. O notebook cobre churn por tipo de contrato, tempo de permanência, forma de pagamento e tipo de internet.

O arquivo `.dbc` está em `databricks/churn_analytics.dbc` e pode ser importado diretamente em qualquer workspace Databricks.

---

## Dataset

**IBM Telco Customer Churn** — disponível publicamente no Kaggle.

- 7.043 clientes, 21 colunas originais
- Variável alvo: `Churn` (Yes/No) — 26,54% de churn
- Colunas: perfil do cliente, serviços contratados, tipo de contrato, forma de pagamento e valores de cobrança

O dataset é fictício e representa um snapshot estático — não possui dados temporais ou de eventos, o que limita análises de séries temporais mas é suficiente para segmentação e identificação de padrões de risco.

---

## Recomendações de negócio

Com base nos achados da análise:

1. **Programa de onboarding nos primeiros 90 dias** — a janela crítica é o início do relacionamento, onde quase metade dos clientes cancela.
2. **Incentivar migração de contrato mensal para anual** — desconto ou benefício pode reduzir o churn pela metade nesse segmento.
3. **Campanhas para clientes Fiber optic com contrato mensal** — combinação de maior risco identificada na análise.
4. **Facilitar troca do Electronic check para débito automático** — reduz atrito e está associado a maior retenção.

---

## Autor

Desenvolvido por **Vivian** como projeto de portfólio para estágio em dados.
