"""
ETL — IBM Telco Customer Churn

Pipeline completo: extração do CSV → limpeza → feature engineering → carga no SQLite.

Uso:
    python etl_telco_churn.py
    python etl_telco_churn.py --csv outro_caminho.csv
    python etl_telco_churn.py --csv dados.csv --db meu_banco.db

Dependências: pandas, sqlite3 (stdlib)
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd


DEFAULT_CSV = "WA_Fn-UseC_-Telco-Customer-Churn.csv"
DEFAULT_DB  = "telco_churn.db"


def extract(csv_path: str) -> pd.DataFrame:
    """Lê o CSV original e retorna um DataFrame bruto."""
    path = Path(csv_path)
    if not path.exists():
        sys.exit(f"[ERRO] Arquivo não encontrado: {csv_path}\n"
                 "Baixe o dataset em: https://www.kaggle.com/datasets/blastchar/telco-customer-churn")

    df = pd.read_csv(path)
    print(f"[OK] Extraídas {len(df):,} linhas × {len(df.columns)} colunas de '{path.name}'")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Correções aplicadas:
    - Renomeia colunas para snake_case
    - TotalCharges: converte espaços em NaN e depois para float
    - Imputa NaN de TotalCharges com MonthlyCharges (clientes com tenure=0)
    - SeniorCitizen: 0/1 → 'No'/'Yes' para ficar consistente com as demais colunas binárias
    - Remove duplicatas e registros sem customerID
    - Strip em todas as strings para evitar espaços escondidos
    """
    df = df.copy()

    # snake_case nos nomes de coluna
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"(?<=[a-z])(?=[A-Z])", "_", regex=True)
        .str.lower()
    )
    df.rename(columns={"customerid": "customer_id"}, inplace=True)

    print(f"  Colunas renomeadas: {list(df.columns)}")

    # remove duplicatas e linhas sem customer_id
    before = len(df)
    df.drop_duplicates(subset="customer_id", inplace=True)
    df.dropna(subset=["customer_id"], inplace=True)
    removed = before - len(df)
    if removed:
        print(f"  Removidas {removed} linhas duplicadas/sem ID")

    # TotalCharges vem como string com espaços em clientes tenure=0
    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")
    nan_count = df["total_charges"].isna().sum()
    if nan_count:
        mask = df["total_charges"].isna()
        df.loc[mask, "total_charges"] = df.loc[mask, "monthly_charges"]
        print(f"  TotalCharges: {nan_count} NaN imputados com MonthlyCharges (tenure=0)")

    # SeniorCitizen 0/1 → 'No'/'Yes'
    df["senior_citizen"] = df["senior_citizen"].map({0: "No", 1: "Yes"})

    # strip em todas as strings
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    print(f"  Limpeza concluída. Linhas finais: {len(df):,}")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Features criadas:
    - churn_binary          : Churn Yes/No → 1/0
    - num_services          : contagem de serviços ativos (0–9)
    - has_online_protection : 1 se tem ao menos um de security, backup ou device protection
    - tenure_group          : faixas de permanência em 6 grupos
    - monthly_charge_tier   : faixas de valor mensal (Low / Mid / High)
    - revenue_at_risk       : monthly_charges dos clientes que cancelaram, 0 para os demais
    - avg_monthly_from_total: total_charges / tenure (custo médio real por mês)
    """
    df = df.copy()

    df["churn_binary"] = (df["churn"] == "Yes").astype(int)

    # conta serviços ativos — exclui os valores que indicam ausência de serviço
    service_cols = [
        "phone_service", "multiple_lines", "internet_service",
        "online_security", "online_backup", "device_protection",
        "tech_support", "streaming_tv", "streaming_movies",
    ]
    no_values = {"No", "No internet service", "No phone service"}
    df["num_services"] = df[service_cols].apply(
        lambda row: sum(v not in no_values for v in row), axis=1
    )

    # proteção online agrupa 3 serviços de segurança
    protection_cols = ["online_security", "online_backup", "device_protection"]
    df["has_online_protection"] = df[protection_cols].apply(
        lambda row: int(any(v not in no_values for v in row)), axis=1
    )

    # faixas de tenure
    bins   = [0, 6, 12, 24, 36, 48, 72]
    labels = ["0-6 m", "7-12 m", "13-24 m", "25-36 m", "37-48 m", "49-72 m"]
    df["tenure_group"] = pd.cut(
        df["tenure"], bins=bins, labels=labels, include_lowest=True
    ).astype(str)

    # faixas de cobrança mensal
    df["monthly_charge_tier"] = pd.cut(
        df["monthly_charges"],
        bins=[0, 35, 65, 120],
        labels=["Low (<$35)", "Mid ($35-65)", "High (>$65)"],
        include_lowest=True,
    ).astype(str)

    df["revenue_at_risk"] = df["monthly_charges"] * df["churn_binary"]

    # evita divisão por zero para clientes com tenure=0
    df["avg_monthly_from_total"] = df.apply(
        lambda r: round(r["total_charges"] / r["tenure"], 2) if r["tenure"] > 0 else r["monthly_charges"],
        axis=1,
    )

    print("  Features criadas: churn_binary, num_services, has_online_protection, "
          "tenure_group, monthly_charge_tier, revenue_at_risk, avg_monthly_from_total")
    return df


def load_to_sqlite(df: pd.DataFrame, db_path: str) -> None:
    """
    Cria (ou substitui) 3 tabelas no SQLite:
    - customers_clean : todos os dados limpos + features
    - dim_services    : perfil de serviços por cliente
    - fact_churn      : métricas financeiras e churn
    """
    conn = sqlite3.connect(db_path)

    df.to_sql("customers_clean", conn, if_exists="replace", index=False)
    print(f"  Tabela 'customers_clean': {len(df):,} linhas carregadas")

    service_cols = [
        "customer_id", "phone_service", "multiple_lines",
        "internet_service", "online_security", "online_backup",
        "device_protection", "tech_support", "streaming_tv",
        "streaming_movies", "num_services", "has_online_protection",
    ]
    df[service_cols].to_sql("dim_services", conn, if_exists="replace", index=False)
    print(f"  Tabela 'dim_services': {len(df):,} linhas carregadas")

    fact_cols = [
        "customer_id", "tenure", "tenure_group",
        "contract", "payment_method", "paperless_billing",
        "monthly_charges", "total_charges", "avg_monthly_from_total",
        "monthly_charge_tier", "revenue_at_risk",
        "churn", "churn_binary",
    ]
    df[fact_cols].to_sql("fact_churn", conn, if_exists="replace", index=False)
    print(f"  Tabela 'fact_churn': {len(df):,} linhas carregadas")

    # índices para as colunas mais usadas nas queries analíticas
    cursor = conn.cursor()
    indexes = [
        ("idx_clean_churn",    "customers_clean", "churn"),
        ("idx_clean_contract", "customers_clean", "contract"),
        ("idx_clean_tenure",   "customers_clean", "tenure_group"),
        ("idx_fact_churn",     "fact_churn",      "churn_binary"),
        ("idx_fact_contract",  "fact_churn",      "contract"),
    ]
    for idx_name, table, col in indexes:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({col})")
    conn.commit()
    print(f"  Índices criados: {[i[0] for i in indexes]}")

    conn.close()
    print(f"[OK] Banco '{db_path}' pronto.")


def validate(db_path: str) -> None:
    """Queries de sanidade para confirmar que a carga foi correta."""
    conn = sqlite3.connect(db_path)
    checks = {
        "Total de clientes":        "SELECT COUNT(*) FROM customers_clean",
        "Clientes com churn=Yes":   "SELECT COUNT(*) FROM customers_clean WHERE churn='Yes'",
        "Taxa de churn (%)":        "SELECT ROUND(AVG(churn_binary)*100, 2) FROM customers_clean",
        "NaN em total_charges":     "SELECT COUNT(*) FROM customers_clean WHERE total_charges IS NULL",
        "Receita mensal total ($)": "SELECT ROUND(SUM(monthly_charges), 2) FROM customers_clean",
        "Receita em risco ($)":     "SELECT ROUND(SUM(revenue_at_risk), 2) FROM customers_clean",
        "Avg serviços (churned)":   "SELECT ROUND(AVG(num_services), 2) FROM customers_clean WHERE churn='Yes'",
        "Avg serviços (retidos)":   "SELECT ROUND(AVG(num_services), 2) FROM customers_clean WHERE churn='No'",
    }
    print("\nValidação pós-carga")
    print("-" * 42)
    for label, query in checks.items():
        result = conn.execute(query).fetchone()[0]
        print(f"  {label:<30} {result}")
    conn.close()
    print()


def main():
    parser = argparse.ArgumentParser(description="ETL — Telco Customer Churn")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Caminho para o CSV do Kaggle")
    parser.add_argument("--db",  default=DEFAULT_DB,  help="Caminho para o banco SQLite de saída")
    args = parser.parse_args()

    print("\nETL · IBM Telco Customer Churn\n")

    print("[1/4] Extraindo dados...")
    df_raw = extract(args.csv)

    print("\n[2/4] Limpando dados...")
    df_clean = clean(df_raw)

    print("\n[3/4] Engenharia de features...")
    df_final = engineer_features(df_clean)

    print("\n[4/4] Carregando no SQLite...")
    load_to_sqlite(df_final, args.db)

    validate(args.db)

    print("Pipeline concluído.\n")


if __name__ == "__main__":
    main()