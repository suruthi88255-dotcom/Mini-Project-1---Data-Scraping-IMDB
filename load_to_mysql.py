import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text, VARCHAR, Integer, SmallInteger, BigInteger, DECIMAL

# =========================
# CONFIG — EDIT THESE
# =========================
CSV_PATH = r"C:\Users\surut\OneDrive\Desktop\IMDB\outcsv.csv"  # <-- your scraped CSV
DB_USER  = "root"                                              # XAMPP default
DB_PWD   = ""                                                  # XAMPP default (blank)
DB_HOST  = "localhost"
DB_PORT  = 3306
DB_NAME  = "imdbdb"
TABLE    = "imdb_2024"                                         # table name to write
CHUNK    = 10000

# =========================
# 1) Read CSV & keep only desired columns
# =========================
EXPECTED_COLS = ["Rank","Title","Year","Runtime","IMDb Rating","Votes","Votes_Numeric","URL"]

print(f"📂 Reading CSV: {CSV_PATH}")
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# Create any missing expected columns (filled with None)
for c in EXPECTED_COLS:
    if c not in df.columns:
        df[c] = None

# Subset to ONLY the 8 columns in the order you want
df = df[EXPECTED_COLS].copy()

print(f"✅ Rows read: {len(df):,}")
print(f"🧱 Columns used: {list(df.columns)}")

# =========================
# 2) Connect to MySQL (XAMPP)
#    IMPORTANT: Use a SQLAlchemy URL, NOT a phpMyAdmin URL
# =========================
SERVER_URL = f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/"
DB_URL     = f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

server_engine = create_engine(SERVER_URL, pool_recycle=3600)
db_engine     = None

# Create database if missing
print(f"🗃️  Ensuring database exists: {DB_NAME}")
with server_engine.begin() as conn:
    conn.execute(text(f"""
        CREATE DATABASE IF NOT EXISTS {DB_NAME}
        DEFAULT CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;
    """))

# Now connect directly to the target DB
db_engine = create_engine(DB_URL, pool_recycle=3600)

# =========================
# 3) Define desired MySQL column types (for ONLY the 8 columns)
# =========================
dtype_map = {
    "Rank": Integer(),
    "Title": VARCHAR(255),
    "Year": SmallInteger(),
    "Runtime": VARCHAR(20),
    "IMDb Rating": DECIMAL(3,1),
    "Votes": VARCHAR(20),
    "Votes_Numeric": BigInteger(),
    "URL": VARCHAR(255),
}

# =========================
# 4) Write to MySQL
#    - if_exists='replace' recreates the table each run
#      (use 'append' if you want to add rows instead)
# =========================
print(f"📝 Writing to MySQL table: {DB_NAME}.{TABLE}")
df.to_sql(
    TABLE,
    con=db_engine,
    if_exists="replace",      # change to 'append' to keep old rows
    index=False,
    dtype=dtype_map,
    method="multi",
    chunksize=CHUNK
)

# Add a unique index on URL for dedupe/joins (safe to ignore if it already exists)
print("🔑 Ensuring unique index on URL …")
try:
    with db_engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE `{TABLE}` ADD UNIQUE KEY `uniq_url` (URL(191));"))
except Exception as e:
    # likely index already exists; safe to ignore
    pass

print(f"✅ Done! Loaded {len(df):,} rows into `{DB_NAME}.{TABLE}`.")
print("   You can check in phpMyAdmin: Database -> imdbdb -> imdb_2024")
