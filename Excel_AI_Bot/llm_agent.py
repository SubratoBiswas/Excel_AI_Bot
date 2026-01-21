import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """You are an Excel analytics assistant.
You will be given a catalog of SQL tables (DuckDB) derived from uploaded Excel files.
Your job: produce ONE DuckDB-compatible SQL query that answers the question.

Rules:
- Only use tables/columns from the catalog.
- Prefer joins on clearly matching keys (e.g., CustomerID, Date, Region) when asked to compare across tables.
- If the question is ambiguous, make a reasonable assumption and state it in the explanation.
- Never write destructive SQL (no DROP/UPDATE/DELETE).
- Return JSON matching the schema.
- Do NOT include a trailing semicolon in SQL.
- Return only ONE SELECT statement.
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
        "explanation": {"type": "string"}
    },
    "required": ["sql", "explanation"],
    "additionalProperties": False
}

def generate_sql(question: str, catalog: dict) -> dict:
    # Keep catalog concise but useful: include columns, dtypes, row count, a tiny sample
    catalog_compact = {
        t: {
            "file": m["file"],
            "sheet": m["sheet"],
            "rows": m["rows"],
            "cols": m["cols"],
            "dtypes": m["dtypes"],
            "sample": m["sample"],
        }
        for t, m in catalog.items()
    }

    resp = client.responses.create(
        model="gpt-5.2",  # pick what you have access to
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CATALOG:\n{json.dumps(catalog_compact)[:120000]}"},
            {"role": "user", "content": f"QUESTION:\n{question}"}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "sql_plan",
                "schema": OUTPUT_SCHEMA,
                "strict": True
            }
        }
    )

    # The SDK returns structured text; parse JSON:
    out_text = resp.output_text
    return json.loads(out_text)
