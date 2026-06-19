"""
Adiciona uma coluna de score de risco nos CSVs exportados para o Power BI.

A lógica é baseada em 4 fatores de negócio identificados na EDA:
- Contrato mensal         → maior fator de risco (~42% de churn)
- Tenure baixo (< 12m)   → janela crítica de cancelamento
- Electronic check        → método associado a 45% de churn
- Senior citizen          → churn 70% maior que não-idosos

Cada fator vale 1 ponto. Score final:
- 0-1 pontos → Baixo Risco
- 2 pontos   → Médio Risco
- 3-4 pontos → Alto Risco
"""

import pandas as pd


def calculate_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # cada condição vale 1 ponto
    score = (
        (df["contract"] == "Month-to-month").astype(int)
        + (df["tenure"] < 12).astype(int)
        + (df["payment_method"] == "Electronic check").astype(int)
        + (df["senior_citizen"] == "Yes").astype(int)
    )

    df["risk_score"] = score

    # categoria para usar nos visuais do Power BI
    df["risk_category"] = df["risk_score"].map({
        0: "Baixo Risco",
        1: "Baixo Risco",
        2: "Médio Risco",
        3: "Alto Risco",
        4: "Alto Risco",
    })

    # ordem para o Power BI ordenar corretamente nos gráficos
    df["risk_order"] = df["risk_score"].map({
        0: 1,
        1: 1,
        2: 2,
        3: 3,
        4: 3,
    })

    return df


def main():
    print("Adicionando risk_score aos CSVs...\n")

    # carrega o CSV principal
    df = pd.read_csv("data/customers_clean.csv", sep=";", decimal=",")
    print(f"Linhas carregadas: {len(df):,}")

    df = calculate_risk_score(df)

    # distribuição do score
    print("\nDistribuição do risk_score:")
    dist = df.groupby(["risk_category", "risk_score"]).agg(
        total=("customer_id", "count"),
        churn_rate=("churn_binary", lambda x: round(x.mean() * 100, 2))
    ).reset_index()
    print(dist.to_string(index=False))

    # valida se o score faz sentido — alto risco deve ter churn bem maior
    print("\nChurn rate por categoria de risco:")
    validation = df.groupby("risk_category")["churn_binary"].agg(
        total="count",
        churned="sum",
        churn_rate=lambda x: round(x.mean() * 100, 2)
    )
    print(validation)

    # salva de volta com o mesmo formato (ponto e vírgula + vírgula decimal)
    df.to_csv("data/customers_clean.csv", index=False, sep=";", decimal=",")
    print("\n[OK] data/customers_clean.csv atualizado com risk_score e risk_category")


if __name__ == "__main__":
    main()