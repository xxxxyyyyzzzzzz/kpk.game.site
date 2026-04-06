import sqlite3
import os
import sys
import random
import re
import json
from flask import Flask, request, jsonify, render_template, session
from datetime import datetime
from flask_socketio import SocketIO, emit
from functools import wraps

# --- Ініціалізація додатку ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'e57724220b3b4f63c87895e7c80529d4791054b1f618d3600f6074127c525f0a1c6298e874558509'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Налаштування баз даних ---
USER_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kpk_game.db')
print(f"!!! ШЛЯХ ДО БАЗИ ДАНИХ: {USER_DB} !!!") #
MISSIONS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'missions.db')
MISSION_CLASSES = ['Атака', 'Захист', 'Лут', 'Економіка']
TURN_DURATION_SECONDS = 420  # 7 minutes
TOTAL_NEWS_ROUNDS = 4
TURNS_PER_NEWS_ROUND = 4

# --- Початкові значення балів дій ---
DEFAULT_ACTION_POINTS = {
    'active': 7,
    'attack': 5,
    'build': 4
}

# --- Угрупування та їх кольори ---
FACTIONS = {
    'Скаєри': '#66ADFF', 'Авантюристи': '#A0A0A0', 'Військові': '#FF8282',
    'Цикади': '#A9FFAF', 'Глодекс': '#F9FF9E', 'Розсвіт': '#7EF2FF'
}

# --- Дерево прокачок (ВИПРАВЛЕННЯ: Використано потрійні лапки для 'name') ---
UPGRADES = {
    "zakhyst_1_1": {"id": "zakhyst_1_1", "name": """-1 крок, -1 дальність атаки на підконтрольних секторах""", "category": "Захист", "tier": 1, "cost": 1},
    "zakhyst_1_2": {"id": "zakhyst_1_2", "name": """+1 шкода на підконтрольних секторах всім типам атак""", "category": "Захист", "tier": 1, "cost": 1},
    "zakhyst_2_1": {"id": "zakhyst_2_1", "name": """Будівництво турелей на підконтрольних секторах""", "category": "Захист", "tier": 2, "cost": 1},
    "zakhyst_2_2": {"id": "zakhyst_2_2", "name": """+2 броні всьому (техніка лише угрупування)""", "category": "Захист", "tier": 2, "cost": 1},
    "zakhyst_3_1": {"id": "zakhyst_3_1", "name": """Захист від 'кровинок'""", "category": "Захист", "tier": 3, "cost": 1},
    "zakhyst_3_2": {"id": "zakhyst_3_2", "name": """Овервотч всім стрільцям""", "category": "Захист", "tier": 3, "cost": 1},
    "ataka_1_1": {"id": "ataka_1_1", "name": """+2 шкоди тільки для персонажів""", "category": "Атака", "tier": 1, "cost": 1},
    "ataka_1_2": {"id": "ataka_1_2", "name": """+1 дальність тільки для персонажів""", "category": "Атака", "tier": 1, "cost": 1},
    "ataka_2_1": {"id": "ataka_2_1", "name": """+2 ліміт техніки""", "category": "Атака", "tier": 2, "cost": 1},
    "ataka_2_2": {"id": "ataka_2_2", "name": """'Кровинка' всім 🗡️""", "category": "Атака", "tier": 2, "cost": 1},
    "ataka_3_1": {"id": "ataka_3_1", "name": """Додаткова атака для персонажів ⌛1""", "category": "Атака", "tier": 3, "cost": 1},
    "ataka_3_2": {"id": "ataka_3_2", "name": """Бронелом для стрільців""", "category": "Атака", "tier": 3, "cost": 1},
    "lut_1_1": {"id": "lut_1_1", "name": """+3 шкоди по мутантах""", "category": "Лут", "tier": 1, "cost": 1},
    "lut_1_2": {"id": "lut_1_2", "name": """На підконтрольних секторах +1 крок""", "category": "Лут", "tier": 1, "cost": 1},
    "lut_2_1": {"id": "lut_2_1", "name": """Збільшений крок та карман""", "category": "Лут", "tier": 2, "cost": 1},
    "lut_2_2": {"id": "lut_2_2", "name": """Маскування 3""", "category": "Лут", "tier": 2, "cost": 1},
    "lut_3_1": {"id": "lut_3_1", "name": """Лут не згорає та одразу з підконтрольних секторів ТП на склад""", "category": "Лут", "tier": 3, "cost": 1},
    "lut_3_2": {"id": "lut_3_2", "name": """+1 лут з усього""", "category": "Лут", "tier": 3, "cost": 1},
    "ekonomika_1_1": {"id": "ekonomika_1_1", "name": """Нескінченна конвертація заліза""", "category": "Економіка", "tier": 1, "cost": 1},
    "ekonomika_1_2": {"id": "ekonomika_1_2", "name": """Збільшені ліміти 40 валюти 15 металу""", "category": "Економіка", "tier": 1, "cost": 1},
    "ekonomika_2_1": {"id": "ekonomika_2_1", "name": """+1 монета за підконтрольний сектор""", "category": "Економіка", "tier": 2, "cost": 1},
    "ekonomika_2_2": {"id": "ekonomika_2_2", "name": """Оплата: 3 монети за 1 рівень Мутана та для персонажа (➕+🛡️=💲)""", "category": "Економіка", "tier": 2, "cost": 1},
    "ekonomika_3_1": {"id": "ekonomika_3_1", "name": """Конвертація грошей в бали 1:1""", "category": "Економіка", "tier": 3, "cost": 1},
    "ekonomika_3_2": {"id": "ekonomika_3_2", "name": """Покупка поінтів на місії*""", "category": "Економіка", "tier": 3, "cost": 1},
    "komanduvannya_1_1": {"id": "komanduvannya_1_1", "name": """2 рероли колоди*""", "category": "Командування", "tier": 1, "cost": 0},
    "komanduvannya_1_2": {"id": "komanduvannya_1_2", "name": """-Оплата найманців""", "category": "Командування", "tier": 1, "cost": 0},
    "komanduvannya_2_1": {"id": "komanduvannya_2_1", "name": """Додаткова атакуюча дія""", "category": "Командування", "tier": 2, "cost": 0},
    "komanduvannya_2_2": {"id": "komanduvannya_2_2", "name": """Додатковий командний поінт""", "category": "Командування", "tier": 2, "cost": 0},
    "komanduvannya_2_3": {"id": "komanduvannya_2_3", "name": """Додатковий бал дій""", "category": "Командування", "tier": 2, "cost": 0},
    "komanduvannya_3_1": {"id": "komanduvannya_3_1", "name": """Артилерійський обстріл за раунд""", "category": "Командування", "tier": 3, "cost": 0},
    "komanduvannya_3_2": {"id": "komanduvannya_3_2", "name": """3 атаки (всім окрім 1⌛, 2⌛)""", "category": "Командування", "tier": 3, "cost": 0},
}

class CoordinateGenerator:
    def __init__(self):
        self.GRID_WIDTH = 25
        self.GRID_HEIGHT = 25
        self.all_coords = self._generate_all_coords()
        excluded_zones = self._parse_zones(['A1:E5', 'U1:Y5', 'A21:E25', 'U21:Y25'])
        zones_5x5 = self._parse_zones(['F1:T5', 'U6:Y20', 'F21:T25', 'A6:E20'])
        zones_3x3 = self._parse_zones(['F6:O10', 'P6:T15', 'K16:T20', 'F11:J20'])
        zones_1x1 = self._parse_zones(['K11:O15'])
        self.valid_coords_general = self.all_coords - excluded_zones
        self.valid_coords_5x5 = zones_5x5.intersection(self.valid_coords_general)
        self.valid_coords_3x3 = zones_3x3.intersection(self.valid_coords_general)
        self.valid_coords_1x1 = zones_1x1.intersection(self.valid_coords_general)
        self.NEWS_RULES = {
            1: {"Мутанти 1": ("8-16", "5x5", "100%"),"Мутанти 2": ("4-8", "3x3", "100%"),"Мутанти 3": ("1-2", "1x1", "66%"),"Нанокс": ("2-4", "any", "25%"),"Воля": ("3-5", "50%", "50%"),"Обовʼязок": ("3-5", "any", "50%"),"Псі-випромінювач": ("1", "3x3", "33%"),"Аномалії": ("1-3", "any", "100%"),"Викид": ("50%",),"Транспорт нанокс": ("0", "any", "0%"),},
            2: {"Мутанти 1": ("4-12", "5x5", "100%"),"Мутанти 2": ("8-12", "5x5", "100%"),"Мутанти 3": ("1-4", "3x3", "100%"),"Нанокс": ("2-8", "any", "50%"),"Воля": ("3-5", "any", "75%"),"Обовʼязок": ("3-5", "any", "75%"),"Псі-випромінювач": ("1", "3x3", "50%"),"Аномалії": ("2-4", "any", "100%"),"Викид": ("50%",),"Транспорт нанокс": ("1-3", "any", "33%"),},
            3: {"Мутанти 1": ("4-12", "5x5", "100%"),"Мутанти 2": ("8-12", "5x5", "100%"),"Мутанти 3": ("1-4", "3x3", "100%"),"Нанокс": ("2-8", "any", "50%"),"Воля": ("3-5", "any", "75%"),"Обовʼязок": ("3-5", "any", "75%"),"Псі-випромінювач": ("2", "3x3", "50%"),"Аномалії": ("2-4", "any", "100%"),"Викид": ("50%",),"Транспорт нанокс": ("1-3", "any", "33%"),},
            4: {"Мутанти 1": ("0", "5x5", "0%"),"Мутанти 2": ("8-16", "5x5", "100%"),"Мутанти 3": ("4-8", "3x3", "100%"),"Нанокс": ("4-6", "any", "100%"),"Воля": ("2-5", "any", "40%"),"Обовʼязок": ("2-4", "any", "40%"),"Псі-випромінювач": ("1", "3x3", "50%"),"Аномалії": ("3-6", "any", "100%"),"Викид": ("50%",),"Транспорт нанокс": ("1-3", "any", "66%"),},
        }
    def _to_xy(self, a1_coord):
        match = re.match(r"([A-Y])(\d+)", a1_coord.upper())
        if not match: raise ValueError(f"Неправильний формат координати: {a1_coord}")
        col, row = match.groups()
        return ord(col) - ord('A'), int(row) - 1
    def _to_a1(self, xy_coord):
        x, y = xy_coord
        return f"{chr(ord('A') + x)}{y + 1}"
    def _generate_all_coords(self):
        return {(x, y) for x in range(self.GRID_WIDTH) for y in range(self.GRID_HEIGHT)}
    def _parse_zones(self, zone_list):
        coords = set()
        for zone in zone_list:
            start_a1, end_a1 = zone.split(':')
            start_x, start_y = self._to_xy(start_a1)
            end_x, end_y = self._to_xy(end_a1)
            for x in range(start_x, end_x + 1):
                for y in range(start_y, end_y + 1):
                    coords.add((x, y))
        return coords
    def _get_spawn_params(self, rule):
        quantity_str = rule[0]
        if '-' in quantity_str: quantity = random.randint(*map(int, quantity_str.split('-')))
        else: quantity = int(quantity_str)
        zone_type, chance = "any", 100
        if len(rule) == 3: zone_type, chance = rule[1], int(rule[2].replace('%', ''))
        elif len(rule) == 2: chance = int(rule[1].replace('%', ''))
        elif len(rule) == 1: chance = int(rule[0].replace('%', ''))
        return quantity, zone_type, chance
    def _get_valid_spawn_pool(self, zone_type, occupied_coords):
        if zone_type == '5x5': pool = self.valid_coords_5x5
        elif zone_type == '3x3': pool = self.valid_coords_3x3
        elif zone_type == '1x1': pool = self.valid_coords_1x1
        else: pool = self.valid_coords_general
        return list(pool - occupied_coords)
    def _generate_mirrored(self, quantity, zone_type, occupied_coords):
        generated_coords, spawn_pool = set(), self._get_valid_spawn_pool(zone_type, occupied_coords)
        center_x, center_y = 12, 12
        attempts, max_attempts = 0, 1000

        while len(generated_coords) < quantity and attempts < max_attempts:
            attempts += 1
            if not spawn_pool: break
            
            p1 = random.choice(spawn_pool)
            mirror_group = {p1, (2 * center_x - p1[0], p1[1]), (p1[0], 2 * center_y - p1[1]), (2 * center_x - p1[0], 2 * center_y - p1[1])}
            
            # Перевірка, чи всі точки дзеркальної групи знаходяться у допустимому пулі
            if not all(p in spawn_pool for p in mirror_group):
                continue

            # Перевірка відстані між точками всередині самої дзеркальної групи
            points_list = list(mirror_group)
            is_group_internally_valid = True
            for i in range(len(points_list)):
                for j in range(i + 1, len(points_list)):
                    p_i, p_j = points_list[i], points_list[j]
                    if max(abs(p_i[0] - p_j[0]), abs(p_i[1] - p_j[1])) <= 2:
                        is_group_internally_valid = False
                        break
                if not is_group_internally_valid:
                    break
            
            if not is_group_internally_valid:
                continue

            # Якщо всі перевірки пройдено, додаємо групу і видаляємо зони навколо неї
            generated_coords.update(mirror_group)
            
            full_exclusion_zone = set()
            for p in mirror_group:
                full_exclusion_zone.update(self._get_exclusion_zone(p, 2))
                
            spawn_pool = [c for c in spawn_pool if c not in full_exclusion_zone]
            
        return list(generated_coords)
    def generate_for_news(self, news_id):
        if news_id not in self.NEWS_RULES: return {"error": f"Новина з ID {news_id} не знайдена."}
        rules, results, occupied_coords = self.NEWS_RULES[news_id], {}, set()

        for entity, rule in rules.items():
            if entity == "Викид":
                results["Подія: Викид"] = "Стався" if random.randint(1, 100) <= int(rule[0].replace('%', '')) else "Не стався"
                continue

            quantity, zone_type, chance = self._get_spawn_params(rule)
            if random.randint(1, 100) > chance or quantity == 0:
                results[entity] = []
                continue
            
            # Отримуємо доступний пул координат, враховуючи вже зайняті точки
            spawn_pool = self._get_valid_spawn_pool(zone_type, occupied_coords)
            
            new_coords_xy = []
            
            if entity in ["Мутанти 1", "Мутанти 2"]:
                # Дзеркальна генерація вже враховує відстань всередині себе
                new_coords_xy = self._generate_mirrored(quantity, zone_type, occupied_coords)
            else:
                # Ітеративна генерація для інших сутностей з перевіркою відстані
                random.shuffle(spawn_pool)
                
                while len(new_coords_xy) < quantity and spawn_pool:
                    new_coord = spawn_pool.pop(0)
                    new_coords_xy.append(new_coord)
                    
                    # Видаляємо зону навколо нової точки з пулу
                    exclusion_zone = self._get_exclusion_zone(new_coord, 2)
                    spawn_pool = [c for c in spawn_pool if c not in exclusion_zone]

            occupied_coords.update(new_coords_xy)
            results[entity] = [self._to_a1(xy) for xy in new_coords_xy]
            
        return results
    def _get_exclusion_zone(self, center_coord, radius):
        """Створює набір координат у квадратному радіусі навколо центральної точки."""
        cx, cy = center_coord
        zone = set()
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                if 0 <= x < self.GRID_WIDTH and 0 <= y < self.GRID_HEIGHT:
                    zone.add((x, y))
        return zone

news_generator = CoordinateGenerator()

def check_missions_db():
    if not os.path.exists(MISSIONS_DB):
        print("ПОМИЛКА: Файл missions.db не знайдено!", file=sys.stderr)
        sys.exit(1)

def get_user_db_connection():
    conn = sqlite3.connect(USER_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def get_missions_db_connection():
    conn = sqlite3.connect(MISSIONS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db(conn):
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, nickname TEXT UNIQUE, faction TEXT, 
        score INTEGER DEFAULT 0, level1_score REAL DEFAULT 0, 
        level2_score REAL DEFAULT 0, level3_score REAL DEFAULT 0, 
        registration_time TEXT, 
        active_points INTEGER DEFAULT {DEFAULT_ACTION_POINTS['active']}, 
        attack_points INTEGER DEFAULT {DEFAULT_ACTION_POINTS['attack']}, 
        build_points INTEGER DEFAULT {DEFAULT_ACTION_POINTS['build']},
        spent_active_points INTEGER DEFAULT 0,
        spent_attack_points INTEGER DEFAULT 0,
        spent_build_points INTEGER DEFAULT 0
    )''')
    
    def add_column_if_not_exists(table, column, definition):
        try:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
            print(f"INFO: Added column '{column}' to table '{table}'.")
        except sqlite3.OperationalError as e:
            if f"duplicate column name: {column}" not in str(e).lower():
                raise e

    # Додано нову колонку для відстеження замін місій
    add_column_if_not_exists('users', 'mission_replacement_points', 'INTEGER DEFAULT 3')
    add_column_if_not_exists('users', 'active_points', f"INTEGER DEFAULT {DEFAULT_ACTION_POINTS['active']}")
    add_column_if_not_exists('users', 'attack_points', f"INTEGER DEFAULT {DEFAULT_ACTION_POINTS['attack']}")
    add_column_if_not_exists('users', 'build_points', f"INTEGER DEFAULT {DEFAULT_ACTION_POINTS['build']}")
    add_column_if_not_exists('users', 'spent_active_points', 'INTEGER DEFAULT 0')
    add_column_if_not_exists('users', 'spent_attack_points', 'INTEGER DEFAULT 0')
    add_column_if_not_exists('users', 'spent_build_points', 'INTEGER DEFAULT 0')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_mission_slots (
            id INTEGER PRIMARY KEY, user_id INTEGER, slot_index INTEGER, mission_id INTEGER, 
            current_progress INTEGER DEFAULT 0, UNIQUE(user_id, slot_index))''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_class_progress (
            id INTEGER PRIMARY KEY, user_id INTEGER, mission_class TEXT,
            unlocked_tier INTEGER DEFAULT 1, UNIQUE(user_id, mission_class))''')
    cursor.execute('CREATE TABLE IF NOT EXISTS score_history (id INTEGER PRIMARY KEY, user_id INTEGER, reason TEXT, score_change INTEGER, timestamp TEXT, nickname TEXT, level_score_change REAL, level INTEGER, FOREIGN KEY (user_id) REFERENCES users (id))')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            round_number INTEGER DEFAULT 0,
            news_content TEXT
        )''')
    cursor.execute('INSERT OR IGNORE INTO news_state (id, round_number, news_content) VALUES (1, 0, NULL)')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_upgrades (
            id INTEGER PRIMARY KEY, user_id INTEGER, upgrade_id TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id), UNIQUE(user_id, upgrade_id)
        )''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY CHECK (id = 1), 
            base_turn_order_json TEXT,
            turn_order_json TEXT,
            current_turn_index INTEGER DEFAULT 0, 
            news_round_number INTEGER DEFAULT 0,
            turn_in_news_round INTEGER DEFAULT 0,
            is_session_running BOOLEAN DEFAULT FALSE, session_start_time TEXT,
            total_paused_duration REAL DEFAULT 0, last_pause_time TEXT,
            is_turn_active BOOLEAN DEFAULT FALSE, current_turn_start_time TEXT,
            current_turn_seconds_left REAL DEFAULT 720,
            previous_initiative_player TEXT,
            needs_new_initiative BOOLEAN DEFAULT FALSE,
            is_game_over BOOLEAN DEFAULT FALSE
        )''')
    
    add_column_if_not_exists('game_state', 'base_turn_order_json', 'TEXT')
    add_column_if_not_exists('game_state', 'news_round_number', 'INTEGER DEFAULT 0')
    add_column_if_not_exists('game_state', 'turn_in_news_round', 'INTEGER DEFAULT 0')
    add_column_if_not_exists('game_state', 'current_turn_seconds_left', f"REAL DEFAULT {TURN_DURATION_SECONDS}")
    add_column_if_not_exists('game_state', 'previous_initiative_player', 'TEXT')
    add_column_if_not_exists('game_state', 'needs_new_initiative', 'BOOLEAN DEFAULT FALSE')
    add_column_if_not_exists('game_state', 'is_game_over', 'BOOLEAN DEFAULT FALSE')
        
    cursor.execute(f'INSERT OR IGNORE INTO game_state (id) VALUES (1)')
    
    conn.commit()

check_missions_db()
with app.app_context():
    init_user_db(get_user_db_connection())

def get_player(conn, nickname):
    player = conn.execute('SELECT * FROM users WHERE nickname = ?', (nickname,)).fetchone()
    return dict(player) if player else None

def get_game_state(conn=None):
    close_conn = False
    if conn is None:
        conn = get_user_db_connection()
        close_conn = True
    
    state = conn.execute('SELECT * FROM game_state WHERE id = 1').fetchone()
    
    if close_conn:
        conn.close()
        
    return dict(state) if state else None

def get_current_turn_player_nickname(conn):
    state = get_game_state(conn)
    if not state or not state.get('turn_order_json'):
        return None
    
    turn_order = json.loads(state['turn_order_json'])
    index = state.get('current_turn_index', 0)

    if index >= len(turn_order):
        return "bots"

    if 0 <= index < len(turn_order):
        return turn_order[index]
    
    return None

def turn_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        nickname = session.get('nickname')
        if not nickname:
            return jsonify({"error": "Необхідна авторизація"}), 401
        
        conn = get_user_db_connection()
        state = get_game_state(conn)
        turn_order = json.loads(state['turn_order_json']) if state.get('turn_order_json') else []
        conn.close()

        if not turn_order:
            return jsonify({"error": "Порядок ходу ще не визначено"}), 403

        current_index = state.get('current_turn_index', 0)
        
        if current_index >= len(turn_order):
            last_player = turn_order[-1]
            if nickname == last_player:
                 return f(*args, **kwargs)
            else:
                 return jsonify({"error": "Тільки останній гравець може завершити хід ботів"}), 403
        
        current_player = turn_order[current_index]
        if current_player != nickname:
            return jsonify({"error": "Зараз не ваш хід"}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def assign_initial_state(conn, user_id):
    for i in range(6):
        conn.execute('INSERT OR IGNORE INTO user_mission_slots (user_id, slot_index) VALUES (?, ?)', (user_id, i))
    for m_class in MISSION_CLASSES:
        conn.execute('INSERT OR IGNORE INTO user_class_progress (user_id, mission_class, unlocked_tier) VALUES (?, ?, 1)', (user_id, m_class))

def create_player(conn, nickname, faction):
    try:
        cursor = conn.cursor()
        cursor.execute(f'''INSERT INTO users (nickname, faction, registration_time, active_points, attack_points, build_points, spent_active_points, spent_attack_points, spent_build_points) 
                            VALUES (?, ?, ?, {DEFAULT_ACTION_POINTS['active']}, {DEFAULT_ACTION_POINTS['attack']}, {DEFAULT_ACTION_POINTS['build']}, 0, 0, 0)''', 
                         (nickname, faction, datetime.now().isoformat()))
        user_id = cursor.lastrowid
        assign_initial_state(conn, user_id)
        conn.commit()
        socketio.emit('update_required', {'reason': 'new_player'})
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False

def get_active_player_nicknames(conn):
    cursor = conn.execute('SELECT nickname FROM users ORDER BY registration_time ASC').fetchall()
    return [row['nickname'] for row in cursor]

def get_player_data(conn, player):
    if not player: return None
    is_active = player['nickname'] in get_active_player_nicknames(conn)
    
    replacements_str = player.get('mission_replacements_by_level', '{"1": 1, "2": 1, "3": 1}')
    try:
        replacements_json = json.loads(replacements_str)
    except (json.JSONDecodeError, TypeError):
        replacements_json = {"1": 1, "2": 1, "3": 1}

    data = { 
        "nickname": player['nickname'], "score": player['score'], 
        "level1_score": player['level1_score'], "level2_score": player['level2_score'], 
        "level3_score": player['level3_score'], "is_active": is_active,
        "faction": player.get('faction'), "faction_color": FACTIONS.get(player.get('faction')),
        "mission_replacements_by_level": replacements_json,
        "currency_earned_this_turn": player.get('currency_earned_this_turn', 0) # <-- ДОДАНО
    }
    if 'active_points' in player:
        data['action_points'] = {
            'active': player['active_points'],
            'attack': player['attack_points'],
            'build': player['build_points'],
            'spent_active': player.get('spent_active_points', 0),
            'spent_attack': player.get('spent_attack_points', 0),
            'spent_build': player.get('spent_build_points', 0),
        }
    return data

def handle_api_error(e, message="Internal Server Error"):
    print(f"API Error: {e}", file=sys.stderr)
    return jsonify({"error": message, "details": str(e)}), 500

# --- Маршрути (Routes) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/check_session', methods=['GET'])
def check_session():
    conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"logged_in": False}), 200
        
        conn = get_user_db_connection()
        player = get_player(conn, nickname)
        if not player:
            session.pop('nickname', None)
            return jsonify({"logged_in": False})
        
        player_data = get_player_data(conn, player)
        return jsonify({"logged_in": True, "user": player_data})
    except Exception as e:
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    conn = get_user_db_connection()
    try:
        data = request.json
        nickname = data.get('nickname')
        faction = data.get('faction')

        if not nickname or not faction: return jsonify({"error": "Нікнейм та угрупування є обов'язковими"}), 400

        taken_factions_rows = conn.execute('SELECT faction FROM users WHERE faction IS NOT NULL').fetchall()
        taken_factions = {row['faction'] for row in taken_factions_rows}

        player = get_player(conn, nickname)

        if player and player.get('faction'):
                 session['nickname'] = nickname
                 return jsonify(get_player_data(conn, player))

        if faction == 'random':
            available_factions = list(set(FACTIONS.keys()) - taken_factions)
            if not available_factions:
                return jsonify({"error": "Всі угрупування вже зайняті"}), 400
            chosen_faction = random.choice(available_factions)
        else:
            if faction not in FACTIONS: return jsonify({"error": "Невідоме угрупування"}), 400
            if faction in taken_factions: return jsonify({"error": f"Угрупування '{faction}' вже зайняте"}), 400
            chosen_faction = faction
        
        if not player:
            if not create_player(conn, nickname, chosen_faction): 
                return jsonify({"error": "Нікнейм вже існує"}), 409
        else:
            conn.execute('UPDATE users SET faction = ? WHERE nickname = ?', (chosen_faction, nickname))
            conn.commit()

        session['nickname'] = nickname
        updated_player = get_player(conn, nickname)
        return jsonify(get_player_data(conn, updated_player))
    except Exception as e:
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('nickname', None)
    return jsonify({"success": True})

@app.route('/api/reset_game', methods=['POST'])
def reset_game():
    conn = get_user_db_connection()
    try:
        conn.execute('BEGIN')
        conn.execute('DELETE FROM users')
        conn.execute('DELETE FROM user_mission_slots')
        conn.execute('DELETE FROM user_class_progress')
        conn.execute('DELETE FROM score_history')
        conn.execute('DELETE FROM user_upgrades')
        conn.execute('UPDATE news_state SET round_number = 0, news_content = NULL WHERE id = 1')
        conn.execute(f'''UPDATE game_state SET 
                        base_turn_order_json = NULL, turn_order_json = NULL, 
                        current_turn_index = 0, news_round_number = 0, turn_in_news_round = 0,
                        is_session_running = FALSE, session_start_time = NULL, 
                        total_paused_duration = 0, last_pause_time = NULL, 
                        is_turn_active = FALSE, current_turn_start_time = NULL, 
                        current_turn_seconds_left = {TURN_DURATION_SECONDS},
                        previous_initiative_player = NULL,
                        needs_new_initiative = FALSE,
                        is_game_over = FALSE
                        WHERE id = 1''')
        
        try:
            conn.execute("DELETE FROM sqlite_sequence")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        session.pop('nickname', None)
        socketio.emit('update_required', {'reason': 'game_reset'})
        socketio.emit('game_state_updated')
        return jsonify({"success": True, "message": "Гра успішно скинута."})
    except Exception as e:
        conn.rollback()
        return handle_api_error(e)
    finally:
        conn.close()

@app.route('/api/factions', methods=['GET'])
def get_factions():
    # Ця версія повністю від'єднана від бази даних, щоб гарантувати
    # завантаження екрану входу в будь-якому випадку.
    # Вона повертає *всі* угрупування як доступні.
    # Перевірка на те, чи угрупування вже зайняте,
    # виконується на стороні сервера під час спроби логіну в /api/login.
    print("INFO: /api/factions called. Returning static list to allow login.")
    return jsonify({"factions": FACTIONS, "taken": []})
        
@app.route('/api/get_news')
def get_news():
    try:
        conn = get_user_db_connection()
        news_state = conn.execute('SELECT round_number, news_content FROM news_state WHERE id = 1').fetchone()
        conn.close()
        if not news_state:
            return jsonify({"round_number": 0, "news": []})
        
        news_content = json.loads(news_state['news_content']) if news_state['news_content'] else []
        
        return jsonify({
            "round_number": news_state['round_number'],
            "news": news_content
        })
    except Exception as e:
        return handle_api_error(e)

@app.route('/api/reset_news', methods=['POST'])
def reset_news():
    try:
        conn = get_user_db_connection()
        conn.execute('UPDATE news_state SET round_number = 0, news_content = NULL WHERE id = 1')
        conn.commit()
        conn.close()
        socketio.emit('update_required', {'reason': 'news_updated'})
        return jsonify({"success": True})
    except Exception as e:
        return handle_api_error(e)
        
@app.route('/api/game_state')
def api_get_game_state():
    conn = None
    try:
        nickname = session.get('nickname')
        if not nickname:
            return jsonify({"error": "Необхідна авторизація"}), 401

        conn = get_user_db_connection()
        game_state = conn.execute('SELECT * FROM game_state WHERE id = 1').fetchone()
        my_player_data_row = conn.execute('SELECT * FROM users WHERE nickname = ?', (nickname,)).fetchone()

        if not game_state:
            return jsonify({"error": "Стан гри не ініціалізовано"}), 500

        state_dict = dict(game_state)
        turn_order = json.loads(state_dict['turn_order_json']) if state_dict['turn_order_json'] else []

        current_turn_index = state_dict.get('current_turn_index', 0)
        current_player_nickname = None
        is_bot_turn = False

        if turn_order:
            if 0 <= current_turn_index < len(turn_order):
                current_player_nickname = turn_order[current_turn_index]
            else:
                current_player_nickname = "bots"
                is_bot_turn = True

        is_my_turn = (nickname == current_player_nickname)

        # --- НОВИЙ КОД: Отримуємо дані про бали активного гравця ---
        current_player_action_points = None
        if current_player_nickname and not is_bot_turn:
            current_player_row = conn.execute('SELECT * FROM users WHERE nickname = ?', (current_player_nickname,)).fetchone()
            if current_player_row:
                current_player_action_points = get_player_data(conn, dict(current_player_row)).get('action_points')
        # --- КІНЕЦЬ НОВОГО КОДУ ---

        total_session_time = state_dict.get('total_paused_duration', 0)
        if state_dict['is_session_running'] and state_dict['session_start_time']:
            start_time = datetime.fromisoformat(state_dict['session_start_time'])
            session_run_duration = (datetime.now() - start_time).total_seconds()
            total_session_time += session_run_duration

        turn_time_left = state_dict.get('current_turn_seconds_left', TURN_DURATION_SECONDS)
        if state_dict['is_turn_active'] and state_dict['current_turn_start_time']:
            turn_start_time = datetime.fromisoformat(state_dict['current_turn_start_time'])
            elapsed_turn_time = (datetime.now() - turn_start_time).total_seconds()
            turn_time_left = max(0, state_dict['current_turn_seconds_left'] - elapsed_turn_time)

        response_data = {
            "is_setup_complete": bool(state_dict.get('base_turn_order_json')),
            "turn_order": turn_order,
            "news_round_number": state_dict['news_round_number'],
            "turn_in_news_round": state_dict['turn_in_news_round'],
            "current_player_nickname": current_player_nickname,
            "current_turn_index": current_turn_index,
            "is_my_turn": is_my_turn,
            "is_bot_turn": is_bot_turn,
            "needs_new_initiative": state_dict.get('needs_new_initiative', False),
            "previous_initiative_player": state_dict.get('previous_initiative_player'),
            "is_game_over": state_dict.get('is_game_over', False),
            "session_timer": {
                "is_running": state_dict['is_session_running'],
                "elapsed_seconds": total_session_time,
            },
            "player_turn_timer": {
                "is_active": state_dict['is_turn_active'],
                "seconds_left": turn_time_left
            },
            "my_action_points": get_player_data(conn, dict(my_player_data_row) if my_player_data_row else {}).get('action_points'),
            "current_player_action_points": current_player_action_points, # Додано нове поле
            "bot_turn_order": ['Мутанти', 'Зомбі', 'Воля', 'Обовʼязок', 'Нанокс', 'Транспорт нанокс']
        }

        return jsonify(response_data)

    except Exception as e:
        return handle_api_error(e, "Помилка при отриманні стану гри")
    finally:
        if conn: conn.close()

@app.route('/api/set_turn_order', methods=['POST'])
def set_turn_order():
    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({"error": "Відсутні дані 'order'"}), 400
    
    order = data.get('order')
    if not isinstance(order, list) or not order:
        return jsonify({"error": "Неправильний формат даних для 'order'"}), 400

    conn = get_user_db_connection()
    conn.execute(
        'UPDATE game_state SET base_turn_order_json = ?, is_session_running = ?, session_start_time = ?, needs_new_initiative = ? WHERE id = 1',
        (json.dumps(order), True, datetime.now().isoformat(), True)
    )
    conn.commit()
    conn.close()
    
    socketio.emit('game_state_updated')
    return jsonify({"success": True})

@app.route('/api/toggle_session_timer', methods=['POST'])
def toggle_session_timer():
    conn = get_user_db_connection()
    state = conn.execute('SELECT is_session_running, session_start_time, total_paused_duration FROM game_state WHERE id = 1').fetchone()
    
    if state['is_session_running']:
        run_duration = (datetime.now() - datetime.fromisoformat(state['session_start_time'])).total_seconds()
        new_total_duration = state['total_paused_duration'] + run_duration
        conn.execute(
            'UPDATE game_state SET is_session_running = ?, total_paused_duration = ? WHERE id = 1',
            (False, new_total_duration)
        )
    else:
        conn.execute(
            'UPDATE game_state SET is_session_running = ?, session_start_time = ? WHERE id = 1',
            (True, datetime.now().isoformat())
        )

    conn.commit()
    conn.close()
    socketio.emit('game_state_updated')
    return jsonify({"success": True})

@app.route('/api/toggle_turn_timer', methods=['POST'])
def toggle_player_turn_timer():
    conn = get_user_db_connection()
    try:
        state = conn.execute('SELECT * FROM game_state WHERE id = 1').fetchone()
        
        if state['is_turn_active']:
            turn_start_time = datetime.fromisoformat(state['current_turn_start_time'])
            elapsed_time = (datetime.now() - turn_start_time).total_seconds()
            seconds_left = max(0, state['current_turn_seconds_left'] - elapsed_time)
            
            conn.execute(
                'UPDATE game_state SET is_turn_active = ?, current_turn_start_time = NULL, current_turn_seconds_left = ? WHERE id = 1',
                (False, seconds_left)
            )
        else:
            if state['current_turn_seconds_left'] <= 0:
                return jsonify({"error": "Час на хід вийшов"}), 400

            conn.execute(
                'UPDATE game_state SET is_turn_active = ?, current_turn_start_time = ? WHERE id = 1',
                (True, datetime.now().isoformat())
            )
        
        conn.commit()
        socketio.emit('game_state_updated')
        return jsonify({"success": True})
    except Exception as e:
        return handle_api_error(e)
    finally:
        if conn: conn.close()

def reset_player_action_points(conn, user_id):
    upgrades = conn.execute('SELECT upgrade_id FROM user_upgrades WHERE user_id = ?', (user_id,)).fetchall()
    purchased_ids = {row['upgrade_id'] for row in upgrades}

    active_bonus = 1 if "komanduvannya_2_3" in purchased_ids else 0
    attack_bonus = 1 if "komanduvannya_2_1" in purchased_ids else 0

    conn.execute(f'''UPDATE users SET 
        active_points = {DEFAULT_ACTION_POINTS['active']} + ?,
        attack_points = {DEFAULT_ACTION_POINTS['attack']} + ?,
        build_points = {DEFAULT_ACTION_POINTS['build']},
        spent_active_points = 0,
        spent_attack_points = 0,
        spent_build_points = 0
        WHERE id = ?
    ''', (active_bonus, attack_bonus, user_id))


# ЗАМІНИТИ ЦЮ ФУНКЦІЮ ПОВНІСТЮ
# ЗАМІНИТИ ЦЮ ФУНКЦІЮ ПОВНІСТЮ
# ЗАМІНИТИ ЦЮ ФУНКЦІЮ ПОВНІСТЮ
@app.route('/api/next_turn', methods=['POST'])
@turn_required
def next_turn():
    conn = get_user_db_connection()
    try:
        state = conn.execute('SELECT * FROM game_state WHERE id = 1').fetchone()
        
        turn_order = json.loads(state['turn_order_json'])
        current_index = state['current_turn_index']
        
        conn.execute('BEGIN')

        if current_index < len(turn_order):
            player_nickname_to_reset = turn_order[current_index]
            player_to_reset = conn.execute('SELECT id FROM users WHERE nickname = ?', (player_nickname_to_reset,)).fetchone()
            if player_to_reset:
                default_replacements = json.dumps({"1": 1, "2": 1, "3": 1})
                conn.execute('UPDATE users SET mission_replacements_by_level = ?, currency_earned_this_turn = 0 WHERE id = ?', (default_replacements, player_to_reset['id']))            

        # Якщо зараз хід ботів (останній гравець натиснув кнопку)
        if current_index >= len(turn_order):
            new_turn_in_round = state['turn_in_news_round'] + 1
            
            # Перевіряємо, чи завершився великий раунд (новина)
            if new_turn_in_round >= TURNS_PER_NEWS_ROUND:
                # Перевіряємо, чи не закінчилася вся гра
                if state['news_round_number'] >= TOTAL_NEWS_ROUNDS:
                    conn.execute('UPDATE game_state SET is_game_over = ?, is_turn_active = ? WHERE id = 1', (True, False))
                else:
                    # Потрібна нова ініціатива для наступного великого раунду
                    conn.execute('UPDATE game_state SET needs_new_initiative = ?, is_turn_active = ? WHERE id = 1', (True, False))
            else:
                # Починається новий малий раунд в межах тієї ж новини
                conn.execute(
                    f'''UPDATE game_state SET 
                       current_turn_index = 0, turn_in_news_round = ?, is_turn_active = ?, 
                       current_turn_start_time = NULL, current_turn_seconds_left = {TURN_DURATION_SECONDS}
                       WHERE id = 1''',
                    (new_turn_in_round, False)
                )
                # Скидаємо бали першому гравцю нового малого раунду
                first_player_row = conn.execute('SELECT id FROM users WHERE nickname = ?', (turn_order[0],)).fetchone()
                if first_player_row:
                    reset_player_action_points(conn, first_player_row['id'])
        else:
            # Перехід до наступного гравця або до ботів
            new_index = current_index + 1
            conn.execute(
                f'''UPDATE game_state SET 
                   current_turn_index = ?, is_turn_active = ?, 
                   current_turn_start_time = NULL, current_turn_seconds_left = {TURN_DURATION_SECONDS}
                   WHERE id = 1''',
                (new_index, False)
            )
            # Якщо наступний - гравець, скидаємо його бали
            if new_index < len(turn_order):
                next_player_nickname = turn_order[new_index]
                next_player_row = conn.execute('SELECT id FROM users WHERE nickname = ?', (next_player_nickname,)).fetchone()
                if next_player_row:
                    reset_player_action_points(conn, next_player_row['id'])

        conn.commit()
    except Exception as e:
        conn.rollback()
        return handle_api_error(e)
    finally:
        conn.close()

    socketio.emit('game_state_updated')
    return jsonify({"success": True})

@app.route('/api/spend_action_point', methods=['POST'])
@turn_required
def spend_action_point():
    data = request.get_json()
    point_type = data.get('type')
    amount = data.get('amount', 1)
    
    valid_types = {'active': 'spent_active_points', 'attack': 'spent_attack_points', 'build': 'spent_build_points'}
    if point_type not in valid_types:
        return jsonify({"error": "Неправильний тип балів"}), 400

    column_name = valid_types[point_type]
    limit_column_name = f"{point_type}_points"
    nickname = session['nickname']
    
    conn = get_user_db_connection()
    player = conn.execute(f'SELECT {column_name}, {limit_column_name} FROM users WHERE nickname = ?', (nickname,)).fetchone()
    
    current_spent = player[column_name]
    limit = player[limit_column_name]

    new_spent = current_spent + amount

    if not (0 <= new_spent <= limit):
        conn.close()
        return jsonify({"error": "Неприпустима кількість балів"}), 400

    conn.execute(
        f'UPDATE users SET {column_name} = ? WHERE nickname = ?',
        (new_spent, nickname)
    )
    conn.commit()
    conn.close()
    
    socketio.emit('game_state_updated')
    return jsonify({"success": True})

# ЗАМІНИТИ ЦЮ ФУНКЦІЮ ПОВНІСТЮ
# ЗАМІНИТИ ЦЮ ФУНКЦІЮ ПОВНІСТЮ
@app.route('/api/determine_new_initiative', methods=['POST'])
def determine_new_initiative():
    conn = get_user_db_connection()
    try:
        game_state = conn.execute('SELECT base_turn_order_json, previous_initiative_player, news_round_number FROM game_state WHERE id = 1').fetchone()
        
        base_order = json.loads(game_state['base_turn_order_json'])
        if not base_order:
            return jsonify({"error": "Базовий порядок ходу не встановлено"}), 400

        previous_player = game_state['previous_initiative_player']
        eligible_players = [p for p in base_order if p != previous_player]
        if not eligible_players:
            eligible_players = base_order
        new_initiative_player = random.choice(eligible_players)
        
        start_index = base_order.index(new_initiative_player)
        new_turn_order = base_order[start_index:] + base_order[:start_index]

        new_news_round_number = game_state['news_round_number'] + 1
        if new_news_round_number > TOTAL_NEWS_ROUNDS:
             return jsonify({"error": "Гра вже закінчилась"}), 400

        generated_data = news_generator.generate_for_news(new_news_round_number)
        news_list = []
        for entity, coords in generated_data.items():
            if isinstance(coords, list):
                news_list.append(f"{entity} ({len(coords)}): {', '.join(coords) if coords else 'немає'}")
            else:
                news_list.append(f"{entity}: {coords}")

        conn.execute('BEGIN')

        
        conn.execute(
            '''UPDATE game_state 
               SET turn_order_json = ?, current_turn_index = 0, previous_initiative_player = ?, 
                   needs_new_initiative = ?, news_round_number = ?, turn_in_news_round = 0,
                   is_turn_active = FALSE, current_turn_start_time = NULL, current_turn_seconds_left = ?
               WHERE id = 1''',
            (json.dumps(new_turn_order), new_initiative_player, False, new_news_round_number, TURN_DURATION_SECONDS)
        )
        conn.execute('UPDATE news_state SET round_number = ?, news_content = ? WHERE id = 1', 
                     (new_news_round_number, json.dumps(news_list)))
        
        first_player_row = conn.execute('SELECT id FROM users WHERE nickname = ?', (new_initiative_player,)).fetchone()
        if first_player_row:
            reset_player_action_points(conn, first_player_row['id'])
        
        conn.commit()
        
        socketio.emit('game_state_updated')
        socketio.emit('update_required', {'reason': 'news_updated'})
        return jsonify({"success": True, "new_initiative_player": new_initiative_player})

    except Exception as e:
        if conn: conn.rollback()
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/get_upgrades_state')
def get_upgrades_state():
    conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401
        
        conn = get_user_db_connection()
        player = get_player(conn, nickname)
        if not player: return jsonify({"error": "Player not found"}), 404

        purchased_upgrades_rows = conn.execute('SELECT upgrade_id FROM user_upgrades WHERE user_id = ?', (player['id'],)).fetchall()
        news_state = conn.execute('SELECT round_number FROM news_state WHERE id = 1').fetchone()
        
        purchased_ids = [row['upgrade_id'] for row in purchased_upgrades_rows]
        
        return jsonify({
            "tree": UPGRADES,
            "purchased": purchased_ids,
            "round_number": news_state['round_number']
        })
    except Exception as e:
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/get_upgrades_ownership')
def get_upgrades_ownership():
    try:
        conn = get_user_db_connection()
        ownership_rows = conn.execute('''
            SELECT u.nickname, u.faction, uu.upgrade_id 
            FROM user_upgrades uu
            JOIN users u ON uu.user_id = u.id
        ''').fetchall()
        conn.close()

        ownership_data = {}
        for row in ownership_rows:
            upgrade_id = row['upgrade_id']
            if upgrade_id not in ownership_data:
                ownership_data[upgrade_id] = []
            
            ownership_data[upgrade_id].append({
                "nickname": row['nickname'],
                "faction_color": FACTIONS.get(row['faction'])
            })
        
        return jsonify(ownership_data)
    except Exception as e:
        return handle_api_error(e)

@app.route('/api/purchase_upgrade', methods=['POST'])
@turn_required
def purchase_upgrade():
    conn = None
    try:
        nickname = session.get('nickname')
        conn = get_user_db_connection()
        player = get_player(conn, nickname)
        data = request.get_json()
        upgrade_id = data.get('upgrade_id')
        upgrade = UPGRADES.get(upgrade_id)
        if not upgrade: return jsonify({"error": "Невірна прокачка"}), 400
        
        purchased_upgrades_rows = conn.execute('SELECT upgrade_id FROM user_upgrades WHERE user_id = ?', (player['id'],)).fetchall()
        purchased_ids = [row['upgrade_id'] for row in purchased_upgrades_rows]

        if upgrade_id in purchased_ids:
            return jsonify({"error": "Прокачку вже куплено"}), 400

        purchased_by_tier = {1: 0, 2: 0, 3: 0}
        for pid in purchased_ids:
            if UPGRADES[pid]['tier'] in purchased_by_tier:
                purchased_by_tier[UPGRADES[pid]['tier']] += 1
        
        limits = {1: 4, 2: 3, 3: 2}
        if purchased_by_tier[upgrade['tier']] >= limits[upgrade['tier']]:
            return jsonify({"error": f"Досягнуто ліміту прокачок {upgrade['tier']}-го рівня"}), 400

        is_branch_occupied = any(UPGRADES[pid]['category'] == upgrade['category'] and UPGRADES[pid]['tier'] == upgrade['tier'] for pid in purchased_ids)
        if is_branch_occupied:
            return jsonify({"error": f"Ви вже взяли прокачку {upgrade['tier']}-го рівня в цій гілці"}), 400

        if upgrade['category'] == "Командування":
            news_state = conn.execute('SELECT round_number FROM news_state WHERE id = 1').fetchone()
            if news_state['round_number'] < upgrade['tier']:
                return jsonify({"error": f"Доступно з {upgrade['tier']}-го раунду новин"}), 400

            has_other_tier_upgrade = any(UPGRADES[pid]['tier'] == upgrade['tier'] and UPGRADES[pid]['category'] != "Командування" for pid in purchased_ids)
            if not has_other_tier_upgrade:
                return jsonify({"error": f"Потрібна будь-яка інша прокачка {upgrade['tier']}-го рівня"}), 400
        else:
            points_field = f"level{upgrade['tier']}_score"
            if player[points_field] < upgrade['cost']:
                return jsonify({"error": f"Недостатньо балів {upgrade['tier']}-го рівня"}), 400
        
        if upgrade['tier'] > 1:
            has_prerequisite = any(UPGRADES[pid]['category'] == upgrade['category'] and UPGRADES[pid]['tier'] == upgrade['tier'] - 1 for pid in purchased_ids)
            if not has_prerequisite:
                return jsonify({"error": f"Спочатку купіть прокачку {upgrade['tier']-1}-го рівня"}), 400

        conn.execute('BEGIN')
        if upgrade['category'] != "Командування":
            points_field = f"level{upgrade['tier']}_score"
            conn.execute(f'UPDATE users SET {points_field} = {points_field} - ? WHERE id = ?', (upgrade['cost'], player['id']))
        
        if upgrade_id == "komanduvannya_2_3":
            conn.execute('UPDATE users SET active_points = active_points + 1 WHERE id = ?', (player['id'],))
        elif upgrade_id == "komanduvannya_2_1":
            conn.execute('UPDATE users SET attack_points = attack_points + 1 WHERE id = ?', (player['id'],))
        
        conn.execute('INSERT INTO user_upgrades (user_id, upgrade_id) VALUES (?, ?)', (player['id'], upgrade_id))
        conn.commit()
        
        socketio.emit('update_required', {'reason': 'upgrades_updated', 'nickname': nickname})
        return jsonify({"success": True})
    except Exception as e:
        if conn: conn.rollback()
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/rollback_upgrade', methods=['POST'])
@turn_required
def rollback_upgrade():
    conn = None
    try:
        nickname = session.get('nickname')
        upgrade_id_to_rollback = request.json.get('upgrade_id')
        
        conn = get_user_db_connection()
        player = get_player(conn, nickname)
        purchased_upgrades_rows = conn.execute('SELECT upgrade_id FROM user_upgrades WHERE user_id = ?', (player['id'],)).fetchall()
        purchased_ids = {row['upgrade_id'] for row in purchased_upgrades_rows}

        if upgrade_id_to_rollback not in purchased_ids:
            return jsonify({"error": "Цю прокачку не було куплено"}), 400

        upgrades_to_remove = {upgrade_id_to_rollback}
        
        while True:
            newly_removed_count = 0
            for pid in list(purchased_ids):
                if pid in upgrades_to_remove:
                    continue

                upgrade = UPGRADES[pid]
                valid_prereqs_exist = True
                
                if upgrade['tier'] > 1:
                    has_category_prereq = any(
                        UPGRADES[pre_id]['category'] == upgrade['category'] and 
                        UPGRADES[pre_id]['tier'] == upgrade['tier'] - 1
                        for pre_id in (purchased_ids - upgrades_to_remove)
                    )
                    if not has_category_prereq:
                        valid_prereqs_exist = False

                if valid_prereqs_exist and upgrade['category'] == "Командування":
                    has_command_prereq = any(
                        UPGRADES[pre_id]['tier'] == upgrade['tier'] and 
                        UPGRADES[pre_id]['category'] != "Командування"
                        for pre_id in (purchased_ids - upgrades_to_remove)
                    )
                    if not has_command_prereq:
                        valid_prereqs_exist = False

                if not valid_prereqs_exist:
                    if pid not in upgrades_to_remove:
                        upgrades_to_remove.add(pid)
                        newly_removed_count += 1
            
            if newly_removed_count == 0:
                break

        conn.execute('BEGIN')
        total_refunds = {1: 0.0, 2: 0.0, 3: 0.0}

        for uid in upgrades_to_remove:
            removed_upgrade = UPGRADES[uid]
            
            if removed_upgrade['category'] != "Командування":
                total_refunds[removed_upgrade['tier']] += removed_upgrade['cost']

            if uid == "komanduvannya_2_3":
                conn.execute('UPDATE users SET active_points = active_points - 1 WHERE id = ?', (player['id'],))
            elif uid == "komanduvannya_2_1":
                conn.execute('UPDATE users SET attack_points = attack_points - 1 WHERE id = ?', (player['id'],))
            
            conn.execute('DELETE FROM user_upgrades WHERE user_id = ? AND upgrade_id = ?', (player['id'], uid))

        for tier, amount in total_refunds.items():
            if amount > 0:
                points_field = f"level{tier}_score"
                conn.execute(f'UPDATE users SET {points_field} = {points_field} + ? WHERE id = ?', (amount, player['id']))

        conn.commit()
        
        socketio.emit('update_required', {'reason': 'upgrades_updated', 'nickname': nickname})
        return jsonify({"success": True, "removed": list(upgrades_to_remove)})
    except Exception as e:
        if conn: conn.rollback()
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/get_all_players_missions')
def get_all_players_missions():
    conn = None
    missions_conn = None
    try:
        conn = get_user_db_connection()
        players = conn.execute('SELECT id, nickname, faction FROM users').fetchall()
        all_missions = {}
        missions_conn = get_missions_db_connection()

        for player in players:
            player_missions_data = []
            slots_data = conn.execute('SELECT * FROM user_mission_slots WHERE user_id = ? ORDER BY slot_index', (player['id'],)).fetchall()
            for slot in slots_data:
                slot_dict = dict(slot)
                if slot['mission_id']:
                    mission = missions_conn.execute('SELECT * FROM missions WHERE id = ?', (slot['mission_id'],)).fetchone()
                    if mission:
                        mission_data = dict(mission)
                        del mission_data['id']
                        slot_dict.update(mission_data)
                player_missions_data.append(slot_dict)
            
            all_missions[player['nickname']] = {
                "missions": player_missions_data,
                "faction": player['faction'],
                "faction_color": FACTIONS.get(player['faction'])
            }
        
        return jsonify(all_missions)
    except Exception as e:
        return handle_api_error(e)
    finally:
        if conn: conn.close()
        if missions_conn: missions_conn.close()

@app.route('/api/get_user_missions')
def get_user_missions():
    user_conn = None
    missions_conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401
        
        user_conn = get_user_db_connection()
        player = get_player(user_conn, nickname)
        if not player: return jsonify({"error": "Player not found"}), 404
        
        slots_data = user_conn.execute('SELECT * FROM user_mission_slots WHERE user_id = ? ORDER BY slot_index', (player['id'],)).fetchall()
        
        mission_details = []
        missions_conn = get_missions_db_connection()
        for slot in slots_data:
            slot_dict = dict(slot)
            if slot['mission_id']:
                mission = missions_conn.execute('SELECT * FROM missions WHERE id = ?', (slot['mission_id'],)).fetchone()
                if mission:
                    mission_data = dict(mission)
                    del mission_data['id']
                    slot_dict.update(mission_data)
            mission_details.append(slot_dict)
        
        return jsonify(mission_details)
    except Exception as e:
        return handle_api_error(e)
    finally:
        if user_conn: user_conn.close()
        if missions_conn: missions_conn.close()

@app.route('/api/get_mission_selection_data')
def get_mission_selection_data():
    conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401
        
        conn = get_user_db_connection()
        player = get_player(conn, nickname)
        if not player: return jsonify({"error": "Player not found"}), 404
        
        progress = conn.execute('SELECT mission_class, unlocked_tier FROM user_class_progress WHERE user_id = ?', (player['id'],)).fetchall()
        
        progress_dict = {row['mission_class']: row['unlocked_tier'] for row in progress}
        
        return jsonify({
            "unlocked_tiers": progress_dict
        })
    except Exception as e:
        return handle_api_error(e)
    finally:
        if conn: conn.close()

@app.route('/api/get_mission_choices', methods=['POST'])
def get_mission_choices():
    user_conn = None
    missions_conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401
        
        user_conn = get_user_db_connection()
        player = get_player(user_conn, nickname)
        if not player: return jsonify({"error": "Player not found"}), 404

        current_turn_player = get_current_turn_player_nickname(user_conn)
        if current_turn_player == nickname:
            return jsonify({"error": "Обирати місії можна лише поза своїм ходом."}), 403

        data = request.get_json()
        slot_index = data.get('slot_index')
        mission_class = data.get('mission_class')

        target_slot = user_conn.execute('SELECT mission_id FROM user_mission_slots WHERE user_id = ? AND slot_index = ?', (player['id'], slot_index)).fetchone()
        is_replacement = target_slot and target_slot['mission_id'] is not None
        
        mission_level = str((slot_index % 3) + 1)

        if is_replacement:
            # ВИПРАВЛЕНО: Додано розбір JSON-рядка
            replacements_str = player.get('mission_replacements_by_level', '{}')
            replacements = json.loads(replacements_str)
            if replacements.get(mission_level, 0) <= 0:
                return jsonify({"error": f"Закінчилися заміни для місій {mission_level}-го рівня."}), 403
        
        active_missions = user_conn.execute('SELECT mission_id FROM user_mission_slots WHERE user_id = ? AND mission_id IS NOT NULL', (player['id'],)).fetchall()
        completed_missions = user_conn.execute('SELECT mission_id FROM completed_missions WHERE user_id = ?', (player['id'],)).fetchall()
        excluded_ids = {row['mission_id'] for row in active_missions} | {row['mission_id'] for row in completed_missions}

        missions_conn = get_missions_db_connection()
        query = 'SELECT * FROM missions WHERE m_class = ? AND level = ?'
        params = [mission_class, mission_level]
        if excluded_ids:
            placeholders = ', '.join('?' for _ in excluded_ids)
            query += f' AND id NOT IN ({placeholders})'
            params.extend(list(excluded_ids))
        
        query += ' ORDER BY RANDOM() LIMIT 4'
        
        mission_choices = missions_conn.execute(query, tuple(params)).fetchall()
        
        if not mission_choices:
            return jsonify({"error": "Не знайдено доступних місій для цього вибору."}), 404

        return jsonify([dict(row) for row in mission_choices])

    except Exception as e:
        return handle_api_error(e, "Помилка при отриманні варіантів місій")
    finally:
        if user_conn: user_conn.close()
        if missions_conn: missions_conn.close()


@app.route('/api/select_mission_choice', methods=['POST'])
def select_mission_choice():
    user_conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401

        data = request.get_json()
        slot_index = data.get('slot_index')
        mission_id = data.get('mission_id')
        is_replacement = data.get('is_replacement', False)

        user_conn = get_user_db_connection()
        player_row = user_conn.execute('SELECT * FROM users WHERE nickname = ?', (nickname,)).fetchone()
        player = dict(player_row) if player_row else None
        if not player: return jsonify({"error": "Player not found"}), 404

        if is_replacement:
            mission_level = str((slot_index % 3) + 1)
            # ВИПРАВЛЕНО: Додано розбір JSON-рядка
            replacements_str = player.get('mission_replacements_by_level', '{}')
            replacements = json.loads(replacements_str)
            
            if replacements.get(mission_level, 0) > 0:
                replacements[mission_level] -= 1
                user_conn.execute('UPDATE users SET mission_replacements_by_level = ? WHERE id = ?', (json.dumps(replacements), player['id']))
            else:
                 return jsonify({"error": "Недостатньо очок заміни."}), 403
        
        user_conn.execute('UPDATE user_mission_slots SET mission_id = ?, current_progress = 0 WHERE user_id = ? AND slot_index = ?', (mission_id, player['id'], slot_index))
        user_conn.commit()

        socketio.emit('update_required', {'reason': 'mission_changed', 'nickname': nickname})
        return jsonify({"success": True})
    except Exception as e:
        return handle_api_error(e, "Помилка при виборі місії")
    finally:
        if user_conn: user_conn.close()

@app.route('/api/update_mission_progress', methods=['POST'])
def update_mission_progress():
    user_conn = None
    missions_conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401
        
        data = request.get_json()
        slot_id = data.get('slot_id')
        delta = data.get('delta')
        
        user_conn = get_user_db_connection()
        player = get_player(user_conn, nickname)
        if not player or not slot_id or delta not in [-1, 1]: return jsonify({"error": "Invalid request"}), 400
        
        slot_info = user_conn.execute('SELECT mission_id, current_progress FROM user_mission_slots WHERE id = ? AND user_id = ?', (slot_id, player['id'])).fetchone()
        
        if not slot_info:
            return jsonify({"error": "Місія не знайдена"}), 400
        
        missions_conn = get_missions_db_connection()
        mission_def = missions_conn.execute('SELECT target_progress FROM missions WHERE id = ?', (slot_info['mission_id'],)).fetchone()
        if not mission_def: 
            return jsonify({"error": "Місія не призначена цьому слоту або не знайдена в базі даних місій."}), 400
            
        new_progress = max(0, min(slot_info['current_progress'] + delta, mission_def['target_progress']))
        user_conn.execute('UPDATE user_mission_slots SET current_progress = ? WHERE id = ?', (new_progress, slot_id))
        user_conn.commit()
        
        socketio.emit('update_required', {'reason': 'progress_updated', 'nickname': nickname})
        return jsonify({"success": True, "new_progress": new_progress})
    except Exception as e:
        return handle_api_error(e)
    finally:
        if user_conn: user_conn.close()
        if missions_conn: missions_conn.close()

@app.route('/api/complete_mission', methods=['POST'])
def complete_mission():
    user_conn = None
    missions_conn = None
    try:
        nickname = session.get('nickname')
        if not nickname: return jsonify({"error": "Not logged in"}), 401
        
        slot_id = request.json.get('slot_id')
        user_conn = get_user_db_connection()
        player = get_player(user_conn, nickname)
        if not player: return jsonify({"error": "Player not found"}), 404
    
        missions_conn = get_missions_db_connection()
    
        slot_info = user_conn.execute('SELECT * FROM user_mission_slots WHERE id = ? AND user_id = ?', (slot_id, player['id'])).fetchone()
        if not slot_info or not slot_info['mission_id']:
            return jsonify({"error": "Слот не знайдено або він порожній"}), 404
        
        mission_info_row = missions_conn.execute('SELECT * FROM missions WHERE id = ?', (slot_info['mission_id'],)).fetchone()
        mission_info = dict(mission_info_row) if mission_info_row else None
        if not mission_info:
            return jsonify({"error": "Опис місії не знайдено"}), 404

        if slot_info['current_progress'] < mission_info['target_progress']:
            return jsonify({"error": "Місія ще не виконана"}), 400

        main_reward, level_reward, level, m_class = mission_info['main_reward'], mission_info['level_reward_points'], mission_info['level'], mission_info['m_class']
        currency_reward = mission_info.get('currency_reward', 0)
        
        user_conn.execute('BEGIN')

        # Перевіряємо, чий зараз хід
        current_turn_player = get_current_turn_player_nickname(user_conn)
        if current_turn_player == nickname:
            # Якщо хід гравця, додаємо валюту до тимчасового рахунку
            user_conn.execute('UPDATE users SET currency_earned_this_turn = currency_earned_this_turn + ? WHERE id = ?', (currency_reward, player['id']))

        user_conn.execute('UPDATE users SET score = score + ? WHERE id = ?', (main_reward, player['id']))
        user_conn.execute(f"UPDATE users SET level{level}_score = level{level}_score + ? WHERE id = ?", (level_reward, player['id']))
        
        if level < 3:
            user_conn.execute('UPDATE user_class_progress SET unlocked_tier = ? WHERE user_id = ? AND mission_class = ? AND unlocked_tier = ?', (level + 1, player['id'], m_class, level))

        user_conn.execute('UPDATE user_mission_slots SET mission_id = NULL, current_progress = 0 WHERE id = ?', (slot_id,))
        user_conn.execute('INSERT OR IGNORE INTO completed_missions (user_id, mission_id) VALUES (?, ?)', (player['id'], mission_info['id']))

        # Завжди логуємо валюту в історію
        user_conn.execute('INSERT INTO score_history (user_id, nickname, reason, score_change, level_score_change, level, timestamp, currency_change) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (player['id'], nickname, mission_info['name'], main_reward, level_reward, level, datetime.now().isoformat(), currency_reward))
        
        user_conn.commit()
        
        socketio.emit('update_required', {'reason': 'score_updated', 'nickname': nickname})
        return jsonify({
            "success": True, 
            "message": f"Місія виконана! Отримано {main_reward} балів.",
            "currency_reward": currency_reward
        })
    except Exception as e:
        if user_conn: user_conn.rollback()
        return handle_api_error(e)
    finally:
        if user_conn: user_conn.close()
        if missions_conn: missions_conn.close()

@app.route('/api/get_players_info')
def get_players_info():
    try:
        conn = get_user_db_connection()
        players = conn.execute('SELECT nickname, faction, score, level1_score, level2_score, level3_score FROM users ORDER BY score DESC').fetchall()
        conn.close()
        
        player_list = []
        for p in players:
            player_data = dict(p)
            player_data['faction_color'] = FACTIONS.get(p['faction'])
            player_list.append(player_data)
            
        return jsonify(player_list)
    except Exception as e:
        return handle_api_error(e)

@app.route('/api/get_score_history')
def get_score_history():
    try:
        conn = get_user_db_connection()
        history = conn.execute('''
            SELECT h.*, u.faction 
            FROM score_history h
            LEFT JOIN users u ON h.user_id = u.id
            ORDER BY h.timestamp DESC
        ''').fetchall()
        conn.close()
        
        history_list = []
        for row in history:
            history_data = dict(row)
            history_data['faction_color'] = FACTIONS.get(row['faction'])
            history_list.append(history_data)

        return jsonify(history_list)
    except Exception as e:
        return handle_api_error(e)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
