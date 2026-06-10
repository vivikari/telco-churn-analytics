-- Queries de negócio — IBM Telco Customer Churn
-- Banco: telco_churn.db | Tabela principal: customers_clean


-- 1. Qual o perfil do cliente que mais cancela?

-- churn por gênero
SELECT
    gender AS genero,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct
FROM customers_clean
GROUP BY gender
ORDER BY taxa_churn_pct DESC;


-- churn por faixa etária (idoso vs não-idoso)
SELECT
    CASE senior_citizen
        WHEN 'Yes' THEN 'Idoso'
        ELSE 'Não idoso'
    END AS faixa_etaria,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct
FROM customers_clean
GROUP BY senior_citizen
ORDER BY taxa_churn_pct DESC;


-- churn por perfil familiar
SELECT
    partner AS tem_parceiro,
    dependents AS tem_dependentes,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct
FROM customers_clean
GROUP BY partner, dependents
ORDER BY taxa_churn_pct DESC;


-- médias gerais: churned vs retidos
SELECT
    churn AS cancelou,
    ROUND(AVG(tenure), 1) AS media_meses,
    ROUND(AVG(monthly_charges), 2) AS media_cobranca_mensal,
    ROUND(AVG(total_charges), 2) AS media_cobranca_total,
    ROUND(AVG(num_services), 2) AS media_servicos,
    COUNT(*) AS total_clientes
FROM customers_clean
GROUP BY churn;


-- 2. Contratos mensais têm churn significativamente maior?

-- taxa de churn por tipo de contrato
SELECT
    contract AS tipo_contrato,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct,
    ROUND(AVG(monthly_charges), 2) AS media_cobranca_mensal
FROM customers_clean
GROUP BY contract
ORDER BY taxa_churn_pct DESC;


-- distribuição da base por contrato
SELECT
    contract AS tipo_contrato,
    churn AS cancelou,
    COUNT(*) AS qtd_clientes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY contract), 2) AS pct_dentro_contrato,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_base_total
FROM customers_clean
GROUP BY contract, churn
ORDER BY contract, churn;


-- quanto do churn total vem de contratos mensais?
SELECT
    ROUND(
        SUM(CASE WHEN contract = 'Month-to-month' AND churn = 'Yes' THEN 1 ELSE 0 END) * 100.0
        / SUM(churn_binary), 2
    ) AS pct_churn_vindo_de_mensal
FROM customers_clean;


-- 3. Clientes com mais serviços ativos cancelam menos?

-- churn por número de serviços ativos
SELECT
    num_services AS qtd_servicos,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct
FROM customers_clean
GROUP BY num_services
ORDER BY num_services;


-- churn por tipo de internet
SELECT
    internet_service AS tipo_internet,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct,
    ROUND(AVG(monthly_charges), 2) AS media_cobranca_mensal
FROM customers_clean
GROUP BY internet_service
ORDER BY taxa_churn_pct DESC;


-- impacto de ter proteção online (security + backup + device protection)
SELECT
    CASE has_online_protection
        WHEN 1 THEN 'Tem proteção online'
        ELSE 'Sem proteção online'
    END AS protecao_online,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct
FROM customers_clean
GROUP BY has_online_protection
ORDER BY taxa_churn_pct DESC;


-- combinação de maior risco: Fiber optic + contrato mensal
SELECT
    internet_service AS internet,
    contract AS contrato,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct,
    ROUND(AVG(monthly_charges), 2) AS media_mensal
FROM customers_clean
WHERE internet_service = 'Fiber optic'
GROUP BY internet_service, contract
ORDER BY taxa_churn_pct DESC;


-- 4. Qual o impacto financeiro do churn em receita mensal?

-- resumo financeiro geral
SELECT
    ROUND(SUM(monthly_charges), 2) AS receita_mensal_total,
    ROUND(SUM(revenue_at_risk), 2) AS receita_em_risco,
    ROUND(SUM(monthly_charges) - SUM(revenue_at_risk), 2) AS receita_segura,
    ROUND(SUM(revenue_at_risk) * 100.0 / SUM(monthly_charges), 2) AS pct_receita_em_risco,
    ROUND(SUM(revenue_at_risk) * 12, 2) AS projecao_perda_anual
FROM customers_clean;


-- impacto por tipo de contrato
SELECT
    contract AS tipo_contrato,
    ROUND(SUM(monthly_charges), 2) AS receita_total_segmento,
    ROUND(SUM(revenue_at_risk), 2) AS receita_em_risco,
    ROUND(AVG(monthly_charges), 2) AS ticket_medio,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN monthly_charges END), 2) AS ticket_medio_churned
FROM customers_clean
GROUP BY contract
ORDER BY receita_em_risco DESC;


-- top 10 segmentos com maior receita em risco
SELECT
    contract AS contrato,
    internet_service AS internet,
    payment_method AS pagamento,
    COUNT(*) AS clientes_churned,
    ROUND(SUM(revenue_at_risk), 2) AS receita_em_risco,
    ROUND(AVG(monthly_charges), 2) AS ticket_medio
FROM customers_clean
WHERE churn = 'Yes'
GROUP BY contract, internet_service, payment_method
ORDER BY receita_em_risco DESC
LIMIT 10;


-- 5. Quanto tempo de permanência reduz o risco de cancelamento?

-- churn por faixa de tenure
SELECT
    tenure_group AS faixa_permanencia,
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churn,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct,
    ROUND(AVG(monthly_charges), 2) AS media_mensal
FROM customers_clean
GROUP BY tenure_group
ORDER BY
    CASE tenure_group
        WHEN '0-6 m'   THEN 1
        WHEN '7-12 m'  THEN 2
        WHEN '13-24 m' THEN 3
        WHEN '25-36 m' THEN 4
        WHEN '37-48 m' THEN 5
        WHEN '49-72 m' THEN 6
    END;


-- a partir de quantos meses o churn cai abaixo de 20%?
SELECT
    tenure,
    COUNT(*) AS total_clientes,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct
FROM customers_clean
GROUP BY tenure
HAVING COUNT(*) >= 20
ORDER BY tenure;


-- tenure médio por contrato e churn
SELECT
    contract AS contrato,
    churn AS cancelou,
    ROUND(AVG(tenure), 1) AS tenure_medio,
    MIN(tenure) AS tenure_minimo,
    MAX(tenure) AS tenure_maximo,
    COUNT(*) AS total
FROM customers_clean
GROUP BY contract, churn
ORDER BY contract, churn;


-- KPIs para os cartões do Power BI
SELECT
    COUNT(*) AS total_clientes,
    SUM(churn_binary) AS total_churned,
    ROUND(AVG(churn_binary) * 100, 2) AS taxa_churn_pct,
    ROUND(SUM(monthly_charges), 2) AS mrr_total,
    ROUND(SUM(revenue_at_risk), 2) AS mrr_em_risco,
    ROUND(SUM(revenue_at_risk) * 12, 2) AS arr_em_risco,
    ROUND(AVG(tenure), 1) AS tenure_medio_geral,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN tenure END), 1) AS tenure_medio_churned,
    ROUND(AVG(monthly_charges), 2) AS ticket_medio_geral
FROM customers_clean;