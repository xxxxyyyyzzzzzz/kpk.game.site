import sqlite3
import os

print("--- Створення та ініціалізація бази даних ---")

# Шлях до файлу бази даних (такий самий, як в app.py)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kpk_game.db')

# Видаляємо старий файл, щоб гарантовано почати з нуля
if os.path.exists(DB_FILE):
    print(f"Знайдено існуючий файл: {DB_FILE}. Видалення...")
    os.remove(DB_FILE)
    print("Старий файл бази даних видалено.")

conn = None
try:
    # Створюємо новий файл бази даних і встановлюємо з'єднання
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("Створено новий файл бази даних і встановлено з'єднання.")

    # Створюємо всі таблиці з правильною структурою
    
    # Table: users
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY, nickname TEXT UNIQUE, faction TEXT, 
            score INTEGER DEFAULT 0, level1_score REAL DEFAULT 0, 
            level2_score REAL DEFAULT 0, level3_score REAL DEFAULT 0, 
            registration_time TEXT, 
            active_points INTEGER DEFAULT 7, 
            attack_points INTEGER DEFAULT 5, 
            build_points INTEGER DEFAULT 4,
            spent_active_points INTEGER DEFAULT 0,
            spent_attack_points INTEGER DEFAULT 0,
            spent_build_points INTEGER DEFAULT 0,
            mission_replacements_by_level TEXT DEFAULT '{"1": 1, "2": 1, "3": 1}',
            currency_earned_this_turn INTEGER DEFAULT 0
        )
    ''')
    print("Таблицю 'users' створено успішно.")

    # Table: user_mission_slots
    cursor.execute('''
        CREATE TABLE user_mission_slots (
            id INTEGER PRIMARY KEY, user_id INTEGER, slot_index INTEGER, mission_id INTEGER, 
            current_progress INTEGER DEFAULT 0, UNIQUE(user_id, slot_index))
    ''')
    print("Таблицю 'user_mission_slots' створено успішно.")

    # Table: user_class_progress
    cursor.execute('''
        CREATE TABLE user_class_progress (
            id INTEGER PRIMARY KEY, user_id INTEGER, mission_class TEXT,
            unlocked_tier INTEGER DEFAULT 1, UNIQUE(user_id, mission_class))
    ''')
    print("Таблицю 'user_class_progress' створено успішно.")

    # Table: score_history
    cursor.execute('''
        CREATE TABLE score_history (
            id INTEGER PRIMARY KEY, user_id INTEGER, reason TEXT, 
            score_change INTEGER, timestamp TEXT, nickname TEXT, 
            level_score_change REAL, level INTEGER, 
            currency_change INTEGER DEFAULT 0, 
            FOREIGN KEY (user_id) REFERENCES users (id))
    ''')
    print("Таблицю 'score_history' створено успішно.")

    # Table: news_state
    cursor.execute('''
        CREATE TABLE news_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            round_number INTEGER DEFAULT 0,
            news_content TEXT
        )
    ''')
    cursor.execute('INSERT INTO news_state (id, round_number, news_content) VALUES (1, 0, NULL)')
    print("Таблицю 'news_state' створено та ініціалізовано.")

    # Table: user_upgrades
    cursor.execute('''
        CREATE TABLE user_upgrades (
            id INTEGER PRIMARY KEY, user_id INTEGER, upgrade_id TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id), UNIQUE(user_id, upgrade_id)
        )
    ''')
    print("Таблицю 'user_upgrades' створено успішно.")
    
    # Table: game_state
    cursor.execute('''
        CREATE TABLE game_state (
            id INTEGER PRIMARY KEY CHECK (id = 1), 
            base_turn_order_json TEXT,
            turn_order_json TEXT,
            current_turn_index INTEGER DEFAULT 0, 
            news_round_number INTEGER DEFAULT 0,
            turn_in_news_round INTEGER DEFAULT 0,
            is_session_running BOOLEAN DEFAULT FALSE, session_start_time TEXT,
            total_paused_duration REAL DEFAULT 0, last_pause_time TEXT,
            is_turn_active BOOLEAN DEFAULT FALSE, current_turn_start_time TEXT,
            current_turn_seconds_left REAL DEFAULT 420,
            previous_initiative_player TEXT,
            needs_new_initiative BOOLEAN DEFAULT FALSE,
            is_game_over BOOLEAN DEFAULT FALSE
        )
    ''')
    cursor.execute('INSERT INTO game_state (id) VALUES (1)')
    print("Таблицю 'game_state' створено та ініціалізовано.")

    # Table: completed_missions (таблиця, що викликала помилку)
    cursor.execute('''
        CREATE TABLE completed_missions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            mission_id INTEGER,
            UNIQUE(user_id, mission_id)
        )
    ''')
    print("Таблицю 'completed_missions' створено успішно.")

    conn.commit()
    print("\n✅ Базу даних успішно створено та налаштовано!")

except Exception as e:
    print(f"\n❌ Виникла помилка: {e}")
finally:
    if conn:
        conn.close()
        print("З'єднання з базою даних закрито.")