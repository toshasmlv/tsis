import sys
sys.path.insert(0, "C:\\pylibs")
import psycopg2
from config import DB_CONFIG

def get_conn():
    cfg = DB_CONFIG
    dsn = (
        f"host={cfg['host']} "
        f"port={cfg['port']} "
        f"dbname={cfg['database']} "
        f"user={cfg['user']} "
        f"password={cfg['password']}"
    )
    return psycopg2.connect(dsn)