import io
import re
import pandas as pd
import duckdb

def safe_name(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", s.strip())
    s = re.sub(r"_{2,}", "_", s).strip("_")
    return s[:80] if s else "table"

class ExcelStore:
    """
    Loads many Excel files and sheets.
    Registers each (file,sheet) as a DuckDB table.
    """
    def __init__(self):
        self.con = duckdb.connect(database=":memory:")
        self.tables = {}  # table_name -> metadata

    def add_excel_file(self, file_name: str, file_bytes: bytes):
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        base = safe_name(file_name.rsplit(".", 1)[0])

        for sheet in xls.sheet_names:
            df = xls.parse(sheet_name=sheet)
            # Optional: normalize column names
            df.columns = [safe_name(str(c)) for c in df.columns]

            tname = safe_name(f"{base}__{sheet}")
            # Ensure uniqueness
            original = tname
            i = 2
            while tname in self.tables:
                tname = f"{original}_{i}"
                i += 1

            self.con.register(tname, df)

            self.tables[tname] = {
                "file": file_name,
                "sheet": sheet,
                "rows": int(len(df)),
                "cols": list(df.columns),
                "dtypes": {c: str(df[c].dtype) for c in df.columns},
                "sample": df.head(5).to_dict(orient="records"),
            }

    def catalog(self) -> dict:
        return self.tables

    def run_sql(self, sql: str, limit: int = 200):
    # Remove trailing semicolons (DuckDB-safe)
        sql = sql.strip().rstrip(";")

        wrapped = f"SELECT * FROM ({sql}) q LIMIT {int(limit)}"
        return self.con.execute(wrapped).fetchdf()

