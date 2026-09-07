import sqlite3
import pandas as pd

DB_FILE = 'budzet_sloiki.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def update_ubrania_podkategoria():
    """Jednorazowa aktualizacja nazwy podkategorii dla słoika Dzieci."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE kategorie 
        SET podkategoria = 'Ubrania Dziecięce' 
        WHERE sloik = 'Dzieci' AND podkategoria = 'Ubrania'
    ''')
    
    cursor.execute('''
        UPDATE transakcje 
        SET podkategoria = 'Ubrania Dziecięce' 
        WHERE zrodlo_lub_sloik = 'Dzieci' AND podkategoria = 'Ubrania'
    ''')
    
    conn.commit()
    conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. TABELA KATEGORII BUDŻETOWYCH
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kategorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sloik TEXT NOT NULL,
        procent REAL NOT NULL,
        podkategoria TEXT NOT NULL
    )''')

    cursor.execute("SELECT COUNT(*) FROM kategorie")
    if cursor.fetchone()[0] == 0:
        default_kategorie = [
            ('Życie', 15.0, 'Jedzenie'),
            ('Życie', 15.0, 'Rachunki'),
            ('Życie', 15.0, 'Apteka / Zdrowie'),
            ('Życie', 15.0, 'Chemia i Dom'),
            ('Dzieci', 50.0, 'Edukacja'),
            ('Dzieci', 50.0, 'Ubrania Dziecięce'),
            ('Dzieci', 50.0, 'Rozrywka i Zajęcia'),
            ('Dzieci', 50.0, 'Alimenty'),
            ('Przyjemności', 8.0, 'Wyjścia i Restauracje'),
            ('Przyjemności', 8.0, 'Hobby'),
            ('Przyjemności', 8.0, 'Kultura / Filmy'),
            ('Nieprzewidziane wydatki', 10.0, 'Lekarz'),
            ('Nieprzewidziane wydatki', 10.0, 'Awarie sprzętu'),
            ('Fundusz Auto', 8.5, 'Paliwo LPG/Pb'),
            ('Fundusz Auto', 8.5, 'Serwis i Części'),
            ('Fundusz Auto', 8.5, 'Ubezpieczenie i Przegląd'),
            ('Oszczędzanie XTB', 7.0, 'Rachunek Maklerski ETF'),
            ('Pomoc innym', 1.5, 'Darowizny'),
            ('Pomoc innym', 1.5, 'Kościół'),
        ]
        cursor.executemany("INSERT INTO kategorie (sloik, procent, podkategoria) VALUES (?, ?, ?)", default_kategorie)

    # 2. TABELA TRANSAKCJI
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transakcje (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        typ TEXT NOT NULL,
        zrodlo_lub_sloik TEXT NOT NULL,
        podkategoria TEXT,
        kwota REAL NOT NULL,
        komentarz TEXT
    )''')

    # 3. TABELE DLA MODUŁU CELE I NAWYKI
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals_def (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        horizon TEXT NOT NULL,
        weight_type TEXT,
        target_frequency INTEGER DEFAULT 1,
        start_date TEXT,
        is_active INTEGER DEFAULT 1
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals_daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER NOT NULL,
        log_date TEXT NOT NULL,
        status INTEGER DEFAULT 0,
        UNIQUE(goal_id, log_date)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals_project_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER NOT NULL,
        progress_pct INTEGER NOT NULL,
        updated_at TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()
    
    update_ubrania_podkategoria()

def get_kategorie_df():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM kategorie", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def get_transakcje_df():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM transakcje ORDER BY data DESC, id DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df