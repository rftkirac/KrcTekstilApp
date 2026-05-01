import sqlite3
import pandas as pd
from datetime import datetime
from utils import cfg  # Hazırladığımız config objesini import et


DB_NAME = cfg['database']['db_name']


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # 1. Users
        c.execute('''CREATE TABLE IF NOT EXISTS Users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     userName TEXT UNIQUE, 
                     name TEXT, surname TEXT, 
                      isActive INTEGER DEFAULT 1, 
                      password TEXT, 
                      createTime TEXT, 
                      ruleId INTEGER, 
                      createUser TEXT)''')
        # 2. Customer
        c.execute('''CREATE TABLE IF NOT EXISTS Customer
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      code TEXT UNIQUE, 
                      name TEXT, 
                      address TEXT, 
                      phone TEXT, mail TEXT, 
                      contactName TEXT)''')
        # 3. Departmans
        c.execute('''CREATE TABLE IF NOT EXISTS Departmans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT, 
                     name TEXT, 
                     createTime TEXT, 
                     createUser TEXT)''')


        # 4. Model
        execute_db('''
                CREATE TABLE IF NOT EXISTS Model (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    companyId INTEGER,
                    code TEXT UNIQUE,
                    type TEXT,
                    name TEXT,
                    siparisAdet INTEGER,
                    birimFiyat REAL,
                    dövizKodu TEXT DEFAULT 'TRY',
                    siparisTarihi TEXT,
                    baslamaTarihi TEXT,
                    kapamaTarihi TEXT,
                    aktif INTEGER DEFAULT 1,
                    createUser TEXT,
                    createTime TEXT,
                    updateUser TEXT,
                    updateTime TEXT
                )
            ''')
        c.execute('''CREATE TABLE IF NOT EXISTS modelProcess (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          companyId INTEGER,
                          modelId INTEGER,
                          departmanId INTEGER,
                          birimFiyat REAL,
                          dovizKodu TEXT,
                          is_internal INTEGER, -- 1: İç (Kendi bünyemizde), 0: Dış (Fason)
                          createUser TEXT,
                          createTime TEXT,
                          updateUser TEXT,
                          updateTime TEXT,
                          FOREIGN KEY (modelId) REFERENCES Model(id),
                          FOREIGN KEY (departmanId) REFERENCES Departmans(id)
                      )''')
        # 5. Production
        c.execute('''CREATE TABLE IF NOT EXISTS Production
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, modelId INTEGER, 
                     departmentId INTEGER, 
                      date TEXT, quantity INTEGER, createTime TEXT, createUser TEXT,
                      FOREIGN KEY(modelId) REFERENCES Model(id),
                      FOREIGN KEY(departmentId) REFERENCES Departmans(id))''')

        c.execute('''CREATE TABLE IF NOT EXISTS ModelDetay (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            companyId INTEGER,
                            modelId INTEGER,
                            renk TEXT,
                            beden TEXT,
                            adet INTEGER,
                            createUser TEXT,
                            createTime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updateUser TEXT,
                            updateTime DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')

        execute_db("""
            CREATE TABLE IF NOT EXISTS modele_kapama (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                companyId INTEGER,
                modelId INTEGER,
                kapamaTarihi TEXT,
                yuklemeTarihi TEXT,
                beden TEXT,
                renk TEXT,
                adet INTEGER,
                ikinciKaliteAdet INTEGER,
                createUser TEXT,
                createTime TEXT,
                updateUser TEXT,
                updateTime TEXT
            )
        """)

        execute_db("""
                CREATE TABLE IF NOT EXISTS parameter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    groupCode TEXT,
                    code TEXT,
                    value TEXT
                )
            """)
        execute_db("""
                CREATE TABLE IF NOT EXISTS aksesuar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    modelId INTEGER,
                    name TEXT,
                    type TEXT,
                    adet REAL,
                    birim TEXT,
                    birimFiyat REAL,
                    dövizKodu TEXT,
                    creataUser TEXT,
                    CreateTime TEXT,
                    updateUser TEXT,
                    updateTime TEXT
                )
            """)

        # Sayaç Tablosu
        execute_db("""
                CREATE TABLE IF NOT EXISTS sayac (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    prefix TEXT,
                    last_number INTEGER,
                    suffix TEXT
                )
            """)

        # 1. Rollerin tanımlandığı tablo (Örn: Admin, Personel, Kesimhane)
        c.execute('''CREATE TABLE IF NOT EXISTS Roles 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, roleName TEXT UNIQUE)''')

        # 2. Hangi rolün hangi ekranı görebileceğini tutan tablo
        c.execute('''CREATE TABLE IF NOT EXISTS RolePermissions 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, roleId INTEGER, pageName TEXT,
                      FOREIGN KEY(roleId) REFERENCES Roles(id))''')

        # 3. Mevcut Users tablosuna roleId kolonu ekleme (Eğer yoksa)
        try:
            c.execute("ALTER TABLE Users ADD COLUMN roleId INTEGER")
        except:
            pass  # Zaten varsa hata vermez

        # --- BAŞLANGIÇ VERİLERİ (SEED) ---



        # Varsayılan Admin
        # Önce kullanıcıyı ara
        c.execute("SELECT userName FROM Users WHERE userName = ?", ('admin',))
        user_exists = c.fetchone()

        if not user_exists:
            c.execute(
                "INSERT OR IGNORE INTO Users (userName, name, surname, password, createTime, createUser) VALUES (?,?,?,?,?,?)",
                ('admin', 'Sistem', 'Admin', '12345', datetime.now().strftime("%Y-%m-%d %H:%M"), 'System'))
            # --- RENK PARAMETRELERİ ---
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'DGR', 'Diğer'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'BEY', 'Beyaz'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'SIH', 'Siyah'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'MAV', 'Mavi'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'SAR', 'Sarı'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'MOR', 'Mor'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'YES', 'Yeşil'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'KIR', 'Kırmızı'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'KAH', 'Kahve Rengi'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'LAC', 'Lacivert'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'BEJ', 'Bej'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'GRI', 'Gri'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'TUR', 'Turuncu'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('RENK', 'BOR', 'Bordo'))

            # --- BEDEN PARAMETRELERİ ---
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'DGR', 'Diğer'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'XS', 'XS'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'S', 'S'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'M', 'M'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'L', 'L'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'XL', 'XL'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'XXL', 'XXL'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'M', 'M'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'L', 'L'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('BEDEN', 'XL', 'XL'))

            # --- AKSESUAR TİPLERİ ---
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'DGR', 'Diğer'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'KUM', 'Kumaş'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'FER', 'Fermuar'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'DUG', 'Düğme'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'ETI', 'Etiket'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'LAS', 'Lastik'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('AKS_TYPE', 'YTAL', 'Yıkama Talimat'))

            # --- MODEL TİPLERİ ---
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('MODEL_TYPE', 'DIG', 'Diğer'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('MODEL_TYPE', 'ERK', 'Erkek'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('MODEL_TYPE', 'KAD', 'Kadın'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)",('MODEL_TYPE', 'COC', 'Çocuk'))
            c.execute("INSERT OR IGNORE INTO parameter (groupCode, code, value) VALUES (?,?,?)", ('MODEL_TYPE', 'BEB', 'Bebek'))
            # --- SAYAÇ BAŞLANGICI ---
            c.execute("INSERT OR IGNORE INTO sayac (code, prefix, last_number, suffix) VALUES (?,?,?,?)",('MODEL', 'MDL-', 0, ''))
            c.execute("INSERT OR IGNORE INTO sayac (code, prefix, last_number, suffix) VALUES (?,?,?,?)",('FIRMA', 'FRM-', 0, ''))

            c.execute("INSERT OR IGNORE INTO Roles (roleName) VALUES ('Admin')")
            c.execute("INSERT OR IGNORE INTO Roles (roleName) VALUES ('Kesimhane')")
            c.execute("INSERT OR IGNORE INTO Roles (roleName) VALUES ('Dikimhane')")
            c.execute("INSERT OR IGNORE INTO Roles (roleName) VALUES ('UtuPaket')")

        conn.commit()


def get_next_number(table_code):
    """
    Sıradaki numarayı döndürür. Kayıt yoksa otomatik oluşturur.
    """
    import sqlite3

    # Mevcut sayacı kontrol et
    res = run_query("SELECT prefix, last_number, suffix FROM sayac WHERE code = ?", (table_code,))

    if res.empty:
        # KAYIT YOKSA: Otomatik prefix oluştur (İlk 3 harf + tire)
        prefix = f"{table_code[:3].upper()}-"
        last_num = 1
        suffix = ""
        execute_db(
            "INSERT INTO sayac (code, prefix, last_number, suffix) VALUES (?, ?, ?, ?)",
            (table_code, prefix, last_num, suffix)
        )
        return f"{prefix}{last_num}{suffix}"

    else:
        # KAYIT VARSA: Güncelle ve döndür
        prefix = res['prefix'][0]
        last_num = int(res['last_number'][0]) + 1
        suffix = res['suffix'][0]

        execute_db(
            "UPDATE sayac SET last_number = ? WHERE code = ?",
            (last_num, table_code)
        )
        return f"{prefix}{last_num}{suffix}"
def get_next_number2(table_code):
    res = run_query("SELECT prefix, last_number, suffix FROM sayac WHERE code = ?", (table_code,))

    if res.empty:
        # Eğer yoksa varsayılan oluştur
        execute_db("INSERT INTO sayac (code, prefix, last_number, suffix) VALUES (?, 'KRC-', 0, '')", (table_code,))
        res = run_query("SELECT prefix, last_number, suffix FROM sayac WHERE code = ?", (table_code,))

    prefix = res['prefix'][0]
    last_num = int(res['last_number'][0])
    suffix = res['suffix'][0]

    # --- UNIQUE HATASINI ENGELLEYEN DÖNGÜ ---
    exists = True
    while exists:
        last_num += 1
        test_code = f"{prefix}{last_num}{suffix}"

        # Bu kod Model tablosunda var mı?
        check = run_query("SELECT id FROM Model WHERE code = ?", (test_code,))
        if check.empty:
            exists = False  # Eğer yoksa döngüden çık, bu numarayı kullanabiliriz

    # Sayacı en son bulduğumuz boş sayıya güncelle
    execute_db("UPDATE sayac SET last_number = ? WHERE code = ?", (last_num, table_code))

    return f"{prefix}{last_num}{suffix}"

def run_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)


def execute_db(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(query, params)
        conn.commit()

def check_permission(userName, role_id, page_name):
    """Kullanıcının belirtilen sayfaya yetkisi var mı?"""
    res = run_query("SELECT id FROM RolePermissions WHERE roleId = ? AND pageName = ?", (role_id, page_name))
    return not res.empty

