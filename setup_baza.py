import sqlite3

def init_db():
    conn = sqlite3.connect('budzet_sloiki.db')
    cursor = conn.cursor()

    # 1. Tabela Słoików i Podkategorii
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kategorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sloik TEXT NOT NULL,
        procent REAL NOT NULL,
        podkategoria TEXT NOT NULL
    )
    ''')

    # 2. Tabela Transakcji (Wpływy i Wydatki)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transakcje (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        typ TEXT NOT NULL,
        zrodlo_lub_sloik TEXT NOT NULL,
        podkategoria TEXT,
        kwota REAL NOT NULL,
        komentarz TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('DELETE FROM kategorie')

    struktura_sloikow = [
        # Dzieci - 50%
        ('Dzieci', 50.0, 'Alimenty'),
        ('Dzieci', 50.0, 'Przyszłość Oskar'),
        ('Dzieci', 50.0, 'Przyszłość Konstanty'),
        ('Dzieci', 50.0, 'Zabawki'),
        ('Dzieci', 50.0, 'Ubrania'),
        ('Dzieci', 50.0, 'Apteka'),
        ('Dzieci', 50.0, 'Artykuły higieniczne'),
        ('Dzieci', 50.0, 'Atrakcje'),

        # Życie - 15%
        ('Życie', 15.0, 'Wyżywienie'),
        ('Życie', 15.0, 'Chemia i artykuły higieniczne'),
        ('Życie', 15.0, 'Telefon'),
        ('Życie', 15.0, 'Płatne narzędzia'),

        # Przyjemności - 8%
        ('Przyjemności', 8.0, 'Fryzjer'),
        ('Przyjemności', 8.0, 'Wyjścia na miasto'),
        ('Przyjemności', 8.0, 'Hobby'),
        ('Przyjemności', 8.0, 'Perfumy'),
        ('Przyjemności', 8.0, 'Sport'),
        ('Przyjemności', 8.0, 'Subskrypcje'),

        # Nieprzewidziane wydatki - 10%
        ('Nieprzewidziane wydatki', 10.0, 'Opieka lekarska'),
        ('Nieprzewidziane wydatki', 10.0, 'Ubrania'),
        ('Nieprzewidziane wydatki', 10.0, 'Naprawy domowe/narzędzia'),

        # Fundusz Auto - 8,5%
        ('Fundusz Auto', 8.5, 'Naprawy'),
        ('Fundusz Auto', 8.5, 'Paliwo PB'),
        ('Fundusz Auto', 8.5, 'Paliwo LPG'),
        ('Fundusz Auto', 8.5, 'Opłaty parkingowe/ubezpieczenie'),
        ('Fundusz Auto', 8.5, 'Myjnia'),

        # Oszczędzanie XTB - 7%
        ('Oszczędzanie XTB', 7.0, 'Inwestycje XTB'),

        # Pomoc innym - 1,5%
        ('Pomoc innym', 1.5, 'Kościół'),
        ('Pomoc innym', 1.5, 'Akcje charytatywne')
    ]

    cursor.executemany('''
    INSERT INTO kategorie (sloik, procent, podkategoria) 
    VALUES (?, ?, ?)
    ''', struktura_sloikow)

    conn.commit()
    conn.close()
    print("Baza danych zoptymalizowana i poprawnie utworzona!")

if __name__ == '__main__':
    init_db()