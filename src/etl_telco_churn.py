"""
ETL — IBM Telco Customer Churn
==============================
Pipeline completo: extração do CSV → limpeza → feature engineering → carga no SQLite.

Uso:
    python etl_telco_churn.py                        # CSV no mesmo diretório
    python etl_telco_churn.py --csv outro_caminho.csv
    python etl_telco_churn.py --csv dados.csv --db meu_banco.db

Dependências: pandas, sqlite3 (stdlib)
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd


# ─────────────────────────────────────────────
# Configurações padrão
# ─────────────────────────────────────────────
DEFAULT_CSV = "WA_Fn-UseC_-Telco-Customer-Churn.csv"
DEFAULT_DB  = "telco_churn.db"


# ══════════════════════════════════════════════
# 1. EXTRAÇÃO
# ══════════════════════════════════════════════
def extract(csv_path: str) -> pd.DataFrame:
    """Lê o CSV original e retorna um DataFrame bruto."""
    path = Path(csv_path)
    if not path.exists():
        sys.exit(f"[ERRO] Arquivo não encontrado: {csv_path}\n"
                 "Baixe o dataset em: https://www.kaggle.com/datasets/blastchar/telco-customer-churn")

    df = pd.read_csv(path)
    print(f"[OK] Extraídas {len(df):,} linhas × {len(df.columns)} colunas de '{path.name}'")
    return df


# ══════════════════════════════════════════════
# 2. LIMPEZA
# ══════════════════════════════════════════════
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Correções aplicadas:
    - Renomeia colunas para snake_case
    - TotalCharges: converte ' ' (espaço) → NaN, depois float
    - Imputa NaN de TotalCharges com MonthlyCharges (clientes novos, tenure=0)
    - SeniorCitizen: 0/1 → 'No'/'Yes' (consistência com demais binárias)
    - Remove duplicatas e registros sem customerID
    - Padroniza strings (strip + title case)
    """
    df = df.copy()

    # ── 2.1 Snake_case nos nomes de coluna
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"(?<=[a-z])(?=[A-Z])", "_", regex=True)
        .str.lower()
    )
    # Garante que o campo-chave fique exatamente como 'customer_id'
    df.rename(columns={"customerid": "customer_id"}, inplace=True)

    print(f"  Colunas renomeadas: {list(df.columns)}")

    # ── 2.2 Remove duplicatas e linhas sem customer_id
    before = len(df)
    df.drop_duplicates(subset="customer_id", inplace=True)
    df.dropna(subset=["customer_id"], inplace=True)
    removed = before - len(df)
    if removed:
        print(f"  Removidas {removed} linhas duplicadas/sem ID")

    # ── 2.3 TotalCharges: espaços viram NaN, converte para float
    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")

    nan_count = df["total_charges"].isna().sum()
    if nan_count:
        # Clientes com tenure=0 ainda não tiveram cobrança — imputa com monthly_charges
        mask = df["total_charges"].isna()
        df.loc[mask, "total_charges"] = df.loc[mask, "monthly_charges"]
        print(f"  TotalCharges: {nan_count} NaN imputados com MonthlyCharges (tenure=0)")

    # ── 2.4 SeniorCitizen 0/1 → 'No'/'Yes'
    df["senior_citizen"] = df["senior_citizen"].map({0: "No", 1: "Yes"})

    # ── 2.5 Strip em strings para evitar espaços escondidos
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    print(f"  Limpeza concluída. Linhas finais: {len(df):,}")
    return df


# ══════════════════════════════════════════════
# 3. FEATURE ENGINEERING
# ══════════════════════════════════════════════
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Features criadas:
    - churn_binary         : Churn Yes/No → 1/0
    - num_services         : contagem de serviços ativos (0–7)
    - has_online_protection: agrupa online_security + online_backup + device_protection
    - tenure_group         : faixas de tempo de permanência (6 grupos)
    - monthly_charge_tier  : faixas de valor mensal (Low / Mid / High)
    - revenue_at_risk      : monthly_charges de clientes que cancelaram (senão 0)
    - avg_monthly_from_total: total_charges / tenure (custo médio real por mês)
    """
    df = df.copy()

    # ── 3.1 Alvo binário
    df["churn_binary"] = (df["churn"] == "Yes").astype(int)

    # ── 3.2 Contagem de serviços ativos
    service_cols = [
        "phone_service", "multiple_lines",
        "internet_service",          # 'No' = sem serviço
        "online_security", "online_backup",
        "device_protection", "tech_support",
        "streaming_tv", "streaming_movies",
    ]
    # Conta colunas onde o cliente TEM o serviço (não é 'No' nem 'No internet service')
    no_values = {"No", "No internet service", "No phone service"}
    df["num_services"] = df[service_cols].apply(
        lambda row: sum(v not in no_values for v in row), axis=1
    )

    # ── 3.3 Proteção online (1 se tem ao menos 1 dos 3 serviços)
    protection_cols = ["online_security", "online_backup", "device_protection"]
    df["has_online_protection"] = df[protection_cols].apply(
        lambda row: int(any(v not in no_values for v in row)), axis=1
    )

    # ── 3.4 Faixas de tenure (meses)
    bins   = [0, 6, 12, 24, 36, 48, 72]
    labels = ["0-6 m", "7-12 m", "13-24 m", "25-36 m", "37-48 m", "49-72 m"]
    df["tenure_group"] = pd.cut(
        df["tenure"], bins=bins, labels=labels, include_lowest=True
    ).astype(str)

    # ── 3.5 Faixa de cobrança mensal
    df["monthly_charge_tier"] = pd.cut(
        df["monthly_charges"],
        bins=[0, 35, 65, 120],
        labels=["Low (<$35)", "Mid ($35-65)", "High (>$65)"],
        include_lowest=True,
    ).astype(str)

    # ── 3.6 Receita em risco (churn=1 → monthly_charges, senão 0)
    df["revenue_at_risk"] = df["monthly_charges"] * df["churn_binary"]

    # ── 3.7 Custo médio real por mês (evita divisão por zero para tenure=0)
    df["avg_monthly_from_total"] = df.apply(
        lambda r: round(r["total_charges"] / r["tenure"], 2) if r["tenure"] > 0 else r["monthly_charges"],
        axis=1,
    )

    print(f"  Features criadas: churn_binary, num_services, has_online_protection, "
          f"tenure_group, monthly_charge_tier, revenue_at_risk, avg_monthly_from_total")
    return df


# ══════════════════════════════════════════════
# 4. CARGA NO SQLite
# ══════════════════════════════════════════════
def load_to_sqlite(df: pd.DataFrame, db_path: str) -> None:
    """
    Cria (ou substitui) 3 tabelas no SQLite:
    - customers_clean   : todos os dados limpos + features
    - dim_services      : dimensão com perfil de serviços por cliente
    - fact_churn        : tabela fato com métricas financeiras e churn
    """
    conn = sqlite3.connect(db_path)

    # ── 4.1 Tabela principal (staging / raw analítico)
    df.to_sql("customers_clean", conn, if_exists="replace", index=False)
    print(f"  Tabela 'customers_clean': {len(df):,} linhas carregadas")

    # ── 4.2 Dimensão de serviços
    service_cols = [
        "customer_id", "phone_service", "multiple_lines",
        "internet_service", "online_security", "online_backup",
        "device_protection", "tech_support", "streaming_tv",
        "streaming_movies", "num_services", "has_online_protection",
    ]
    dim_services = df[service_cols].copy()
    dim_services.to_sql("dim_services", conn, if_exists="replace", index=False)
    print(f"  Tabela 'dim_services': {len(dim_services):,} linhas carregadas")

    # ── 4.3 Fato churn (métricas financeiras + comportamento)
    fact_cols = [
        "customer_id", "tenure", "tenure_group",
        "contract", "payment_method", "paperless_billing",
        "monthly_charges", "total_charges", "avg_monthly_from_total",
        "monthly_charge_tier", "revenue_at_risk",
        "churn", "churn_binary",
    ]
    fact_churn = df[fact_cols].copy()
    fact_churn.to_sql("fact_churn", conn, if_exists="replace", index=False)
    print(f"  Tabela 'fact_churn': {len(fact_churn):,} linhas carregadas")

    # ── 4.4 Índices para performance nas queries analíticas
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


# ══════════════════════════════════════════════
# 5. VALIDAÇÃO PÓS-CARGA
# ══════════════════════════════════════════════
def validate(db_path: str) -> None:
    """Queries de sanidade para confirmar que a carga foi correta."""
    conn = sqlite3.connect(db_path)
    checks = {
        "Total de clientes":         "SELECT COUNT(*) FROM customers_clean",
        "Clientes com churn=Yes":    "SELECT COUNT(*) FROM customers_clean WHERE churn='Yes'",
        "Taxa de churn (%)":         "SELECT ROUND(AVG(churn_binary)*100, 2) FROM customers_clean",
        "NaN em total_charges":      "SELECT COUNT(*) FROM customers_clean WHERE total_charges IS NULL",
        "Receita mensal total ($)":  "SELECT ROUND(SUM(monthly_charges), 2) FROM customers_clean",
        "Receita em risco ($)":      "SELECT ROUND(SUM(revenue_at_risk), 2) FROM customers_clean",
        "Avg serviços (churned)":    "SELECT ROUND(AVG(num_services), 2) FROM customers_clean WHERE churn='Yes'",
        "Avg serviços (retidos)":    "SELECT ROUND(AVG(num_services), 2) FROM customers_clean WHERE churn='No'",
    }
    print("\n── Validação pós-carga ──────────────────")
    for label, query in checks.items():
        result = conn.execute(query).fetchone()[0]
        print(f"  {label:<30} {result}")
    conn.close()
    print("─────────────────────────────────────────\n")


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="ETL — Telco Customer Churn")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Caminho para o CSV do Kaggle")
    parser.add_argument("--db",  default=DEFAULT_DB,  help="Caminho para o banco SQLite de saída")
    args = parser.parse_args()

    print("\n══════════════════════════════════════")
    print("  ETL · IBM Telco Customer Churn")
    print("══════════════════════════════════════\n")

    print("[1/4] Extraindo dados...")
    df_raw = extract(args.csv)

    print("\n[2/4] Limpando dados...")
    df_clean = clean(df_raw)

    print("\n[3/4] Engenharia de features...")
    df_final = engineer_features(df_clean)

    print("\n[4/4] Carregando no SQLite...")
    load_to_sqlite(df_final, args.db)

    validate(args.db)

    print(f"Pipeline concluído. Próximo passo: abra o notebook de EDA.\n")


if __name__ == "__main__":
    main()