import random
import re

class CoordinateGenerator:
    """
    Клас для генерації координат ігрових сутностей на полі 25x25.
    Враховує виключені зони, спеціальні зони для спавну та правила дзеркальної генерації.
    """

    def __init__(self):
        # --- 1. Налаштування ігрового поля та зон ---
        self.GRID_WIDTH = 25
        self.GRID_HEIGHT = 25
        self.all_coords = self._generate_all_coords()

        # Визначення всіх заборонених та спеціальних зон у числових координатах
        excluded_zones = self._parse_zones(['A1:E5', 'U1:Y5', 'A21:E25', 'U21:Y25'])
        zones_5x5 = self._parse_zones(['F1:T5', 'U6:Y20', 'F21:T25', 'A6:E20'])
        zones_3x3 = self._parse_zones(['F6:O10', 'P6:T15', 'K16:T20', 'F11:J20'])
        zones_1x1 = self._parse_zones(['K11:O15'])

        # Створення наборів дозволених для спавну координат
        self.valid_coords_general = self.all_coords - excluded_zones
        self.valid_coords_5x5 = zones_5x5.intersection(self.valid_coords_general)
        self.valid_coords_3x3 = zones_3x3.intersection(self.valid_coords_general)
        self.valid_coords_1x1 = zones_1x1.intersection(self.valid_coords_general)

        # --- 2. Визначення правил генерації згідно з таблицею ---
        # Кожен словник - це правила для однієї "Новини"
        self.NEWS_RULES = {
            1: {
                "Мутанти 1": ("8-16", "5x5", "100%"),
                "Мутанти 2": ("4-8", "3x3", "100%"),
                "Мутанти 3": ("1-2", "1x1", "66%"),
                "Нанокс": ("2-4", "any", "25%"),
                "Воля": ("3-5", "50%", "50%"),
                "Обовʼязок": ("3-5", "any", "50%"),
                "Псі-випромінювач": ("1", "3x3", "33%"),
                "Аномалії": ("1-3", "any", "100%"),
                "Викид": ("50%",),
                "Транспорт нанокс": ("0", "any", "0%"),
            },
            2: {
                "Мутанти 1": ("4-12", "5x5", "100%"),
                "Мутанти 2": ("8-12", "5x5", "100%"),
                "Мутанти 3": ("1-4", "3x3", "100%"),
                "Нанокс": ("2-8", "any", "50%"),
                "Воля": ("3-5", "any", "75%"),
                "Обовʼязок": ("3-5", "any", "75%"),
                "Псі-випромінювач": ("1", "3x3", "50%"),
                "Аномалії": ("2-4", "any", "100%"),
                "Викид": ("50%",),
                "Транспорт нанокс": ("1-3", "any", "33%"),
            },
            3: { # Правила для Новини 3 такі ж, як для Новини 2
                "Мутанти 1": ("4-12", "5x5", "100%"),
                "Мутанти 2": ("8-12", "5x5", "100%"),
                "Мутанти 3": ("1-4", "3x3", "100%"),
                "Нанокс": ("2-8", "any", "50%"),
                "Воля": ("3-5", "any", "75%"),
                "Обовʼязок": ("3-5", "any", "75%"),
                "Псі-випромінювач": ("2", "3x3", "50%"), # Зміна кількості
                "Аномалії": ("2-4", "any", "100%"),
                "Викид": ("50%",),
                "Транспорт нанокс": ("1-3", "any", "33%"),
            },
            4: {
                "Мутанти 1": ("0", "5x5", "0%"),
                "Мутанти 2": ("8-16", "5x5", "100%"),
                "Мутанти 3": ("4-8", "3x3", "100%"),
                "Нанокс": ("4-6", "any", "100%"),
                "Воля": ("2-5", "any", "40%"),
                "Обовʼязок": ("2-4", "any", "40%"),
                "Псі-випромінювач": ("1", "3x3", "50%"),
                "Аномалії": ("3-6", "any", "100%"),
                "Викид": ("50%",),
                "Транспорт нанокс": ("1-3", "any", "66%"),
            },
        }

    # --- Допоміжні функції для роботи з координатами ---

    def _to_xy(self, a1_coord):
        """Перетворює координату формату 'A1' в числову (0, 0)."""
        match = re.match(r"([A-Y])(\d+)", a1_coord.upper())
        if not match:
            raise ValueError(f"Неправильний формат координати: {a1_coord}")
        col, row = match.groups()
        x = ord(col) - ord('A')
        y = int(row) - 1
        return x, y

    def _to_a1(self, xy_coord):
        """Перетворює числову координату (0, 0) в формат 'A1'."""
        x, y = xy_coord
        col = chr(ord('A') + x)
        row = y + 1
        return f"{col}{row}"

    def _generate_all_coords(self):
        """Створює набір всіх можливих числових координат на полі."""
        return {(x, y) for x in range(self.GRID_WIDTH) for y in range(self.GRID_HEIGHT)}

    def _parse_zones(self, zone_list):
        """Парсить список зон ('A1:B2') і повертає набір числових координат."""
        coords = set()
        for zone in zone_list:
            start_a1, end_a1 = zone.split(':')
            start_x, start_y = self._to_xy(start_a1)
            end_x, end_y = self._to_xy(end_a1)
            for x in range(start_x, end_x + 1):
                for y in range(start_y, end_y + 1):
                    coords.add((x, y))
        return coords

    # --- Основна логіка генерації ---

    def _get_spawn_params(self, rule):
        """Розбирає правило ('1-3', 'any', '50%') на кількість, зону та шанс."""
        quantity_str = rule[0]
        if '-' in quantity_str:
            min_q, max_q = map(int, quantity_str.split('-'))
            quantity = random.randint(min_q, max_q)
        else:
            quantity = int(quantity_str)

        zone_type = "any"
        chance = 100
        
        if len(rule) == 3:
            zone_type = rule[1]
            chance = int(rule[2].replace('%', ''))
        elif len(rule) == 2:
            # Для сутностей типу "Воля", де немає зони
            chance = int(rule[1].replace('%', ''))
        elif len(rule) == 1: # Для "Викиду"
            chance = int(rule[0].replace('%', ''))

        return quantity, zone_type, chance

    def _get_valid_spawn_pool(self, zone_type, occupied_coords):
        """Повертає список доступних координат для спавну залежно від зони."""
        if zone_type == '5x5':
            pool = self.valid_coords_5x5
        elif zone_type == '3x3':
            pool = self.valid_coords_3x3
        elif zone_type == '1x1':
            pool = self.valid_coords_1x1
        else: # 'any'
            pool = self.valid_coords_general
        
        return list(pool - occupied_coords)

    def _generate_mirrored(self, quantity, zone_type, occupied_coords):
        """
        Спеціальна функція для дзеркальної генерації "Мутантів".
        Генерує 1 точку і віддзеркалює її в 3 інших чвертях.
        """
        generated_coords = set()
        spawn_pool = self._get_valid_spawn_pool(zone_type, occupied_coords)
        
        # Центр для віддзеркалення (індекси 0-24)
        center_x, center_y = 12, 12

        # Нам потрібно згенерувати `quantity / 4` груп дзеркальних мутантів
        # Оскільки мутанти 1 і 2 завжди генеруються в кількості, кратній 4
        num_groups = quantity // 4 

        attempts = 0
        max_attempts = 1000 # Запобіжник від нескінченного циклу

        while len(generated_coords) < quantity and attempts < max_attempts:
            if not spawn_pool: break # Немає вільних місць

            # 1. Вибираємо випадкову точку-оригінал
            p1 = random.choice(spawn_pool)
            
            # 2. Розраховуємо дзеркальні точки
            p2 = (2 * center_x - p1[0], p1[1]) # Дзеркально по горизонталі
            p3 = (p1[0], 2 * center_y - p1[1]) # Дзеркально по вертикалі
            p4 = (2 * center_x - p1[0], 2 * center_y - p1[1]) # Дзеркально по центру
            
            mirror_group = {p1, p2, p3, p4}
            
            # 3. Перевіряємо, чи всі 4 точки валідні
            #    - Вони повинні бути в дозволеній зоні (наприклад, 5x5)
            #    - Вони не повинні бути вже зайняті
            is_valid_group = True
            for p in mirror_group:
                if p not in spawn_pool:
                    is_valid_group = False
                    break
            
            if is_valid_group:
                generated_coords.update(mirror_group)
                # Видаляємо використані координати з пулу, щоб не зайняти їх знову
                spawn_pool = [c for c in spawn_pool if c not in mirror_group]

            attempts += 1

        return list(generated_coords)


    def generate_for_news(self, news_id):
        """
        Основна функція, яка генерує сутності для вказаного номеру новини.
        """
        if news_id not in self.NEWS_RULES:
            return {"error": f"Новина з ID {news_id} не знайдена."}

        rules = self.NEWS_RULES[news_id]
        results = {}
        occupied_coords = set()

        for entity, rule in rules.items():
            # Обробка події "Викид" окремо
            if entity == "Викид":
                chance = int(rule[0].replace('%', ''))
                if random.randint(1, 100) <= chance:
                    results["Подія: Викид"] = "Стався"
                else:
                    results["Подія: Викид"] = "Не стався"
                continue

            # Отримуємо параметри спавну
            quantity, zone_type, chance = self._get_spawn_params(rule)

            # Перевіряємо шанс спавну
            if random.randint(1, 100) > chance or quantity == 0:
                results[entity] = []
                continue

            # Вибираємо метод генерації
            if entity in ["Мутанти 1", "Мутанти 2"]:
                # Використовуємо дзеркальну генерацію
                new_coords_xy = self._generate_mirrored(quantity, zone_type, occupied_coords)
            else:
                # Стандартна генерація
                new_coords_xy = []
                spawn_pool = self._get_valid_spawn_pool(zone_type, occupied_coords)
                
                # Перемішуємо пул для випадковості
                random.shuffle(spawn_pool)
                
                # Беремо потрібну кількість координат
                count = min(quantity, len(spawn_pool))
                new_coords_xy = spawn_pool[:count]

            # Оновлюємо зайняті координати та зберігаємо результат
            occupied_coords.update(new_coords_xy)
            results[entity] = [self._to_a1(xy) for xy in new_coords_xy]

        return results


# --- Приклад використання ---
if __name__ == "__main__":
    generator = CoordinateGenerator()

    # Симуляція гри: генерація для 4 новин поспіль
    for i in range(1, 5):
        print(f"--- Генерація для Новини {i} ---")
        generated_data = generator.generate_for_news(i)
        
        # Гарний вивід результатів
        for entity, coords in generated_data.items():
            if isinstance(coords, list):
                # Виводимо кількість та самі координати
                print(f"  {entity} (згенеровано {len(coords)}): {', '.join(coords) if coords else 'немає'}")
            else:
                # Для подій типу "Викид"
                print(f"  {entity}: {coords}")
        print("-" * 30 + "\n")

