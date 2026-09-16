# Telco Churn Analytics
Análise de churn de clientes com Python, SQL, Power BI | dataset IBM Telco

> ⚠️ Projeto em andamento. Este README é provisório e será atualizado conforme as etapas forem concluídas, especialmente a parte de Power BI.

Análise de churn de clientes de uma operadora de telecom, usando o dataset público **IBM Telco Customer Churn**. O objetivo é identificar os principais fatores que levam um cliente a cancelar o serviço e apontar oportunidades de retenção.

## Objetivo

Responder três perguntas principais:

- Qual o perfil de cliente com maior propensão a churn?
- Quais fatores (contrato, forma de pagamento, tempo de casa, serviços contratados) mais se relacionam com o cancelamento?
- Quais segmentos de clientes deveriam ser prioridade em uma estratégia de retenção?

## Dataset

**IBM Telco Customer Churn** (dataset público, amplamente usado em projetos de análise de churn), contendo dados demográficos, de contrato e de uso de aproximadamente 7.000 clientes de uma operadora fictícia.

## Estrutura do repositório

```
telco-churn-analytics/
├── data/          # Dados brutos e/ou tratados
├── notebooks/     # Notebooks de EDA e análise exploratória em Python
├── sql/           # Queries SQL usadas para tratamento e agregação dos dados
├── src/           # Scripts auxiliares de processamento
└── README.md
```

## Ferramentas utilizadas

- **Python** (Pandas, Matplotlib/Seaborn) para limpeza e análise exploratória (EDA)
- **SQL** para consultas e agregações
- **Power BI** para o dashboard final *(em desenvolvimento)*

## Etapas do projeto

- [x] Coleta e entendimento do dataset
- [x] Limpeza e tratamento dos dados
- [x] Análise exploratória (EDA) em Python
- [x] Queries SQL para agregações e métricas de negócio
- [ ] Construção do dashboard em Power BI
- [ ] Documentação final dos insights e recomendações

## Próximos passos

O foco atual é finalizar a camada de visualização no Power BI, conectando as métricas já validadas em Python e SQL a um dashboard interativo com os principais indicadores de churn.

## Autora

Vivian Kaori Umaki
[LinkedIn](https://linkedin.com/in/vivianumaki/) · [GitHub](https://github.com/vivikari)
