import os
import sys
from typing import Dict




# 1. ОЧИСТКА ОКРУЖЕНИЯ

safe_env: Dict[str, str] = {}
for key in ['PATH', 'SYSTEMROOT', 'WINDIR', 'PROGRAMFILES', 'USERPROFILE', 'APPDATA']:
    if key in os.environ:
        val: str = os.environ[key]
        safe_env[key] = val.encode('ascii', 'ignore').decode('ascii')
os.environ.clear()
for key, val in safe_env.items():
    os.environ[key] = val
os.environ['USERNAME'] = 'user'
os.environ['COMPUTERNAME'] = 'PC'
os.environ['LANG'] = 'C'
os.environ['LC_ALL'] = 'C'


# 2. ИМПОРТЫ

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from modules import run_cycle
from modules.database import create_tables, init_db
from modules.seed.products import init_products

if __name__ == "__main__":
    init_db()
    create_tables()
    init_products()
    run_cycle()