import sqlite3
import pandas as pd

conn = sqlite3.connect("telco_churn.db")

tabelas = ["customers_clean", "dim_services", "fact_churn"]

for tabela in tabelas:
    df = pd.read_sql(f"SELECT * FROM {tabela}", conn)
    df.to_csv(f"data/{tabela}.csv", index=False, decimal=",", sep=";")
    print(f"Exportado: data/{tabela}.csv ({len(df):,} linhas)")

conn.close()