from .core import init_db, seed_data
from .config import DB_PATH

if __name__ == "__main__":
    init_db()
    seed_data()
    print(f"Database ready at: {DB_PATH}")