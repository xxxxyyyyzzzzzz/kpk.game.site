import pandas as pd
import sqlite3
import re
import os
import math
import io

# --- ВБУДОВАНІ ДАНІ (з вашого файлу "Коефіціенти 1.0 (3).xlsx") ---
# Дані вставлено "як є", без жодних змін, згідно з вашим проханням.
CSV_DATA = """Дія,Коефіціент,Дозволи,Об'єкт,Коефіціент,Кількість
МІсії захисту,,,,
Побудувати,2,"Окоп, Барикаду, Мега барикаду, Колючий дріт, Вежу, Турель",Окоп,2,1 - 4
,,,Барикаду,3,1
,,,Мега барикаду,4,1-2
,,,Колючий дріт,3,1-2
,,,Вежу,4,1-2
,,,Турель,5,1-2
Знищити на підконтрольному секторі,3,"ворога, мутантів",ворога,5,1-5
,,,мутантів,3,1-5
Придбати,2,"броню",броню,3,1-4
Захопити,2,"сектори",сектори,1.5,3-6
Відремонтувати,3,"броню персонажа, броню",броню персонажа,3,1-4
,,,броню,3,1-4
Полікувати,3,"персонажа",персонажа,4,1-3
Нанести шкоду з турелі,2.5,"ворогу, мутантам",ворогу,5,1-5
,,,мутантам,3,1-5
Місії атаки,,,,
Вбити,3,"NPC, Ігрових персонажів",NPC,4,1-4
,,,Ігрових персонажів,5,1-5
Знищити,3,"Будівлі, Транспорт, Турель, Техніку, Захисні споруди",Будівлі,6,1-4
,,,Транспорт,6,1-3
,,,Турель,7,1-2
,,,Техніку,5,1-4
,,,Захисні споруди,4,1-4
Побудувати,2,"Радіовежу",Радіовежу,6,1
Застосувати,1.5,"Артилерію, Гранати",Артилерію,7,1 - 3
,,,Гранати,5,1-4
Стати ворожим до,3,"NPC",NPC,4,1-4
Нанести шкоду з,2,"Артилерії, Гранати, Транспорту",Артилерії,7,1-2
,,,Гранати,5,1-4
,,,Транспорту,6,1-3
Перехопити,5,"Точку",Точку,15,1
Місії економіка,,,,
Купити,2,"Предмет магазину, Найманців, Транпорт з магазину",Предмет магазину,2,1-9
,,,Найманців,4,1-3
,,,Транспорт з магазину,4,1-3
Налагодити стосунки з,4,"NPC",NPC,8,1-2
Побудувати,2,"Ринок, Покращення точки",Ринок,3,1
,,,Покращення точки,3,1-3
Накопити,1,"Валюту, Залізо",Валюту,0.5,"10, 15, 20, 30"
,,,Залізо,2,"4, 6, 8, 10, 12"
Подружитись,4,"NPC",NPC,8,1-2
Торгувати з,2,"Гравцем, NPC",Гравцем,5,1-2
,,,NPC,8,1-2
Нанести шкоду,3,"Найманцями, Транспортом",Найманцями,4,1-3
,,,Транспортом,6,1-3
Витратити,1,"Валюту, Залізо",Валюту,0.5,"10, 15, 20, 30"
,,,Залізо,2,"4, 6, 8, 10, 12"
Місії лут,,,,
Здобути,2,"Артефакт, Шматки мутантів, мисливський ніж",Артефакт,12,1-3
,,,Шматки мутантів,2,1-8
,,,мисливський ніж,3,1-3
Вбити,2,"Мутантів 1 рів., Мутантів 2 рів., Мутантів 3 рів.",Мутантів 1 рів.,2,1-8
,,,Мутантів 2 рів.,5,1-5
,,,Мутантів 3 рів.,7,1-4
дійти до,3,"центрального сектора",центрального сектора,5,1
Використати,3,"мисливський ніж",мисливський ніж,3,1-3
Обікрасти,4,"склад, лут дроном",склад,6,1
,,,лут дроном,1,1-4
Побудувати,1,"склад",склад,6,1
Обмінятись з,2,"NPC",NPC,8,1-3
Дослідити,4,"Аномалії 1 рів., Аномалії 2 рів., Аномалії 3 рів.",Аномалії 1 рів.,5,1-2
,,,Аномалії 2 рів.,5,1-2
,,,Аномалії 3 рів.,5,1-2
"""

# --- КОНСТАНТИ ---
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'missions.db')
CURRENCY_COEFFICIENT = 0.33

# Словник для правильного найменування класів місій
CLASS_MAPPING = {
    'захисту': 'Захист',
    'атаки': 'Атака',
    'економіка': 'Економіка',
    'лут': 'Лут'
}

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def parse_quantity(quantity_str):
    """
    Розбирає рядок з кількістю.
    Підтримує діапазони (напр. '1-9') та списки через кому (напр. '10, 15, 20').
    """
    quantities = []
    if isinstance(quantity_str, str):
        quantity_str = quantity_str.strip().replace(" ", "")
        if '-' in quantity_str:
            try:
                start, end = map(int, quantity_str.split('-'))
                quantities = list(range(start, end + 1))
            except (ValueError, TypeError):
                pass
        elif ',' in quantity_str:
            try:
                quantities = [int(q.strip()) for q in quantity_str.split(',')]
            except (ValueError, TypeError):
                pass
        else:
            try:
                quantities = [int(quantity_str)]
            except (ValueError, TypeError):
                pass
    return quantities

def calculate_mission_level(points):
    """Визначає рівень місії на основі зароблених балів згідно з новими правилами."""
    if 1 <= points <= 27:
        return 1
    elif 28 <= points <= 60:
        return 2
    elif 61 <= points <= 150:
        return 3
    return 0 # Рівень 0 для місій, що не вписуються в діапазон

def map_range(value, in_min, in_max, out_min, out_max):
    """Перетворює значення з одного діапазону в інший (лінійна інтерполяція)."""
    if in_max == in_min:
        return out_min # Уникаємо ділення на нуль
    return ((value - in_min) * (out_max - out_min) / (in_max - in_min)) + out_min

def calculate_level_reward_points(points, level):
    """
    Розраховує бали прокачування (I, II, III) на основі основних балів та рівня місії.
    Використовує лінійну інтерполяцію для плавного розподілу.
    """
    if level == 1:
        # Мапуємо бали з діапазону [1, 27] в діапазон балів прокачки [0.2, 0.5]
        return round(map_range(points, 1, 27, 0.3, 0.7), 1)
    elif level == 2:
        # Мапуємо бали з діапазону [28, 60] в діапазон балів прокачки [0.6, 0.9]
        return round(map_range(points, 28, 60, 0.6, 0.9), 1)
    elif level == 3:
        # Мапуємо бали з діапазону [61, 150] в діапазон балів прокачки [1.0, 1.5]
        return round(map_range(points, 61, 150, 1.0, 1.5), 1)
    return 0.0

def calculate_currency_reward(points):
    """Розраховує кількість валюти як 0.33 від балів, заокруглюючи вгору."""
    return math.ceil(points * CURRENCY_COEFFICIENT)

def create_database_and_table():
    """Створює файл бази даних та таблицю 'missions', видаляючи стару версію, якщо вона існує."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Існуючий файл бази даних '{DB_FILE}' видалено.")
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Створюємо таблицю з точною структурою, яку очікує app.py
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        m_class TEXT NOT NULL,
        level INTEGER NOT NULL,
        target_progress INTEGER NOT NULL,
        main_reward INTEGER NOT NULL,
        level_reward_points REAL NOT NULL,
        currency_reward INTEGER NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Базу даних '{DB_FILE}' та сумісну таблицю 'missions' створено успішно.")

def generate_missions():
    """Основна функція для генерації та збереження місій з вбудованих даних."""
    try:
        # Використовуємо io.StringIO для читання даних зі змінної, ніби це файл
        data_io = io.StringIO(CSV_DATA)
        df = pd.read_csv(data_io, header=0, usecols=range(6))
        df.columns = ['action', 'action_coeff', 'permissions', 'object', 'object_coeff', 'quantity_str']
    except Exception as e:
        print(f"ПОМИЛКА при обробці вбудованих даних: {e}")
        return

    # --- Обробка даних ---
    
    # 1. Заповнюємо пропущені значення для дій, коефіцієнтів та дозволів,
    #    щоб кожний об'єкт мав відповідну дію.
    df['action'] = df['action'].ffill()
    df['action_coeff'] = df['action_coeff'].ffill()
    df['permissions'] = df['permissions'].ffill()

    # 2. Присвоюємо клас місії, базуючись на заголовках (напр. "МІсії захисту")
    mission_class = "Невідомий"
    df['mission_class'] = ''
    for index, row in df.iterrows():
        action_str = str(row['action'])
        if 'місії' in action_str.lower():
            # Витягуємо назву класу (напр., "захисту")
            raw_class = action_str.lower().replace('місії', '').strip()
            # Знаходимо правильну назву з великої літери (напр., "Захист")
            mission_class = CLASS_MAPPING.get(raw_class, "Невідомий")
        
        df.at[index, 'mission_class'] = mission_class
        
    # 3. Видаляємо рядки, де немає об'єкта (це видалить рядки-заголовки)
    df.dropna(subset=['object'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # --- Генерація та запис в БД ---
    create_database_and_table()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    mission_count = 0

    for index, row in df.iterrows():
        try:
            action = str(row['action'])
            action_coeff = float(str(row['action_coeff']).replace(',', '.'))
            obj = str(row['object'])
            object_coeff = float(str(row['object_coeff']).replace(',', '.'))
            quantity_str = str(row['quantity_str'])
            current_mission_class = str(row['mission_class'])
            permissions = str(row['permissions'])

            # !!! ЖОРСТКА ПЕРЕВІРКА ДОЗВОЛІВ !!!
            # Створюємо список дозволених об'єктів для поточної дії.
            allowed_items = [item.strip() for item in permissions.split(',')]
            
            # Перевіряємо точне входження назви об'єкта в список дозволених.
            if obj not in allowed_items:
                # Пропускаємо комбінацію, якщо об'єкт не входить до списку дозволених
                continue

            quantities = parse_quantity(quantity_str)
            
            if not quantities:
                continue

            # Створюємо окрему місію для кожної можливої кількості
            for qty in quantities:
                # Розрахунок основних балів
                points = int(action_coeff * object_coeff * qty)
                
                if points <= 0:
                    continue

                # Розрахунок всіх інших параметрів на основі балів
                level = calculate_mission_level(points)
                level_reward = calculate_level_reward_points(points, level)
                currency = calculate_currency_reward(points)
                
                mission_name = f"{action} {obj}"
                mission_description = f"Потрібно: {action} {qty} од. '{obj}'"

                # Додаємо згенеровану місію в базу даних
                cursor.execute('''
                INSERT INTO missions (name, description, m_class, level, target_progress, main_reward, level_reward_points, currency_reward)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mission_name, mission_description, current_mission_class, level, 
                    qty, points, level_reward, currency
                ))
                mission_count += 1

        except (ValueError, TypeError) as e:
            continue
            
    conn.commit()
    conn.close()
    
    print(f"🎉 Генерацію завершено! Успішно створено {mission_count} місій.")

def run_diagnostics():
    """Перевіряє вміст щойно створеної бази даних та виводить звіт по класах та рівнях."""
    if not os.path.exists(DB_FILE):
        print("\nДІАГНОСТИКА: Файл бази даних не знайдено.")
        return
        
    print("\n--- Діагностика згенерованої Бази Даних ---")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT m_class, level, COUNT(*) FROM missions GROUP BY m_class, level ORDER BY m_class, level")
        results = cursor.fetchall()
        
        if not results:
            print("ПОПЕРЕДЖЕННЯ: База даних 'missions' порожня!")
        else:
            print("Знайдено наступну кількість місій за класом та рівнем:")
            print("+-------------+--------+-----------+")
            print("| Клас        | Рівень | Кількість |")
            print("+-------------+--------+-----------+")
            for row in results:
                print(f"| {row[0]:<11} | {row[1]:^6} | {row[2]:^9} |")
            print("+-------------+--------+-----------+")
            
    except sqlite3.Error as e:
        print(f"ПОМИЛКА під час діагностики: {e}")
    finally:
        conn.close()

# --- Точка входу в скрипт ---
if __name__ == '__main__':
    generate_missions()
    run_diagnostics()
