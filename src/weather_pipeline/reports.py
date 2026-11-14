import sqlite3
import sys

from weather_pipeline.config import PROJECT_ROOT, load_settings

REPORTS_DIR = PROJECT_ROOT / "sql" / "reports"


def print_table(cursor: sqlite3.Cursor) -> None:
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    widths = [
        max(len(str(v)) for v in [h, *[r[i] for r in rows]])
        for i, h in enumerate(headers)
    ]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(row, widths)))


def main():
    settings = load_settings()
    if not settings.database.exists():
        print(f"Database not found: {settings.database}. Run the pipeline first.")
        sys.exit(1)

    con = sqlite3.connect(settings.database)
    for sql_file in sorted(REPORTS_DIR.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        title = sql.splitlines()[0].lstrip("- ").strip()  # first comment line = title
        print(f"\n{title}\n")
        print_table(con.execute(sql))
    con.close()


if __name__ == "__main__":
    main()
