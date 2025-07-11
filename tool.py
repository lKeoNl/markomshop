import psycopg2

def get_db():
    db_url = "postgresql://markomshop_zqfs_user:4nyEt0vHOQeH59CiShRJRAyKsWcw5C03@dpg-d1n7h2uuk2gs739m5ka0-a.frankfurt-postgres.render.com/markomshop_zqfs"
    conn = psycopg2.connect(db_url)
    return conn

def insert_products():
    products_data = [
        # Vegetables
        ("vegetables", "баклажаны", "static/images/баклажаны.jpg"),
        ("vegetables", "огурцы", "static/images/огурцы.jpg"),
        ("vegetables", "помидоры", "static/images/помидоры.jpg"),
        ("vegetables", "морковь", "static/images/морковь.jpg"),
        ("vegetables", "картофель", "static/images/картофель.jpg"),
        ("vegetables", "лук", "static/images/лук.jpg"),
        ("vegetables", "чеснок", "static/images/чеснок.jpg"),
        ("vegetables", "редис", "static/images/редис.jpg"),
        ("vegetables", "батат", "static/images/батат.jpg"),
        ("vegetables", "перец болгарский", "static/images/перец_болгарский.jpg"),

        # Fruits
        ("fruits", "авокадо", "static/images/авокадо.jpg"),
        ("fruits", "ананас", "static/images/ананас.jpg"),
        ("fruits", "гранат", "static/images/гранат.jpg"),
        ("fruits", "грейпфрут", "static/images/грейпфрут.jpg"),
        ("fruits", "груша дюшес", "static/images/груша_дюшес.jpg"),
        ("fruits", "персик", "static/images/персик.jpg"),
        ("fruits", "банан", "static/images/банан.jpg"),
        ("fruits", "апельсин", "static/images/апельсин.jpg"),
        ("fruits", "киви", "static/images/киви.jpg"),
        ("fruits", "вишня", "static/images/вишня.jpg"),
        ("fruits", "виноград", "static/images/виноград.jpg"),
        ("fruits", "клубника", "static/images/клубника.jpg"),
        ("fruits", "малина", "static/images/малина.jpg"),
        ("fruits", "черешня", "static/images/черешня.jpg"),
        ("fruits", "арбуз", "static/images/арбуз.jpg"),

        # Drinks
        ("drinks", "вода минеральная негаз.", "static/images/вода_минеральная_негаз.jpg"),
        ("drinks", "вода минеральная газ.", "static/images/вода_минеральная_газ.jpg"),
        ("drinks", "сок апельсин", "static/images/сок_апельсин.jpg"),
        ("drinks", "сок банан", "static/images/сок_банан.jpg"),
        ("drinks", "сок гранат", "static/images/сок_гранат.jpg"),
        ("drinks", "сок грейпфрут", "static/images/сок_грейпфрут.jpg"),
        ("drinks", "сок яблоко", "static/images/сок_яблоко.jpg"),
        ("drinks", "сок ананас", "static/images/сок_ананас.jpg"),
        ("drinks", "сок вишня", "static/images/сок_вишня.jpg"),
        ("drinks", "сок томат", "static/images/сок_томат.jpg"),

        # Nuts
        ("nuts", "фундук в скорлупе", "static/images/фундук_в_скорлупе.jpg"),
        ("nuts", "фундук очищенный", "static/images/фундук_очищенный.jpg"),
        ("nuts", "грецкий орех", "static/images/грецкий_орех.jpg"),
        ("nuts", "фисташки в скорлупе", "static/images/фисташки_в_скорлупе.jpg"),
        ("nuts", "фисташки очищенные", "static/images/фисташки_очищенные.jpg"),
        ("nuts", "миндаль", "static/images/миндаль.jpg"),
        ("nuts", "кешью", "static/images/кешью.jpg"),
        ("nuts", "макадамия", "static/images/макадамия.jpg"),
        ("nuts", "арахис в скорлупе", "static/images/арахис_в_скорлупе.jpg"),
        ("nuts", "арахис очищенный", "static/images/арахис_очищенный.jpg"),

        # Greenery
        ("greenery", "петрушка", "static/images/петрушка.jpg"),
        ("greenery", "укроп", "static/images/укроп.jpg"),
        ("greenery", "лук зелёный", "static/images/лук_зелёный.jpg"),
        ("greenery", "кинза", "static/images/кинза.jpg"),
        ("greenery", "мелисса", "static/images/мелисса.jpg"),
        ("greenery", "шпинат", "static/images/шпинат.jpg"),
        ("greenery", "руккола", "static/images/руккола.jpg"),
        ("greenery", "базилик", "static/images/базилик.jpg"),
        ("greenery", "листья салата", "static/images/листья_салата.jpg"),
        ("greenery", "сельдерей", "static/images/сельдерей.jpg"),

        # Meat
        ("meat", "грудка куриная", "static/images/грудка_куриная.jpg"),
        ("meat", "бёдра куриные", "static/images/бёдра_куриные.jpg"),
        ("meat", "крылья куриные", "static/images/крылья_куриные.jpg"),
        ("meat", "ноги куриные", "static/images/ноги_куриные.jpg"),
        ("meat", "филе куриное", "static/images/филе_куриное.jpg"),
        ("meat", "фарш куриный", "static/images/фарш_куриный.jpg"),
        ("meat", "курица", "static/images/курица.jpg"),
        ("meat", "грудка индюшиная", "static/images/грудка_индюшиная.jpg"),
        ("meat", "ноги индюшиные", "static/images/ноги_индюшиные.jpg"),
        ("meat", "бёдра индюшиные", "static/images/бёдра_индюшиные.jpg"),
        ("meat", "фарш индюшиный", "static/images/фарш_индюшиный.jpg"),
        ("meat", "индейка", "static/images/индейка.jpg"),
        ("meat", "грудка утиная", "static/images/грудка_утиная.jpg"),
        ("meat", "ноги утиные", "static/images/ноги_утиные.jpg"),
        ("meat", "утка", "static/images/утка.jpg"),
        ("meat", "вырезка говяжья", "static/images/вырезка_говяжья.jpg"),
        ("meat", "рёбра говяжьи", "static/images/рёбра_говяжьи.jpg"),
        ("meat", "грудинка говяжья", "static/images/грудинка_говяжья.jpg"),
        ("meat", "фарш говяжий", "static/images/фарш_говяжий.jpg"),
        ("meat", "печень говяжья", "static/images/печень_говяжья.jpg"),
        ("meat", "рёбра свиные", "static/images/рёбра_свиные.jpg"),
        ("meat", "вырезка свиная", "static/images/вырезка_свиная.jpg"),
        ("meat", "сало свиное", "static/images/сало_свиное.jpg"),
        ("meat", "грудка свиная", "static/images/грудка_свиная.jpg"),
        ("meat", "фарш свиной", "static/images/фарш_свиной.jpg")
    ]

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Вставляем все товары одним запросом
        cursor.executemany(
            "INSERT INTO products (category, name, image_url) VALUES (%s, %s, %s)",
            products_data
        )
        conn.commit()
        print(f"Добавлено {len(products_data)} товаров!")

    except Exception as e:
        print(f"Ошибка при добавлении товаров: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Запускаем заполнение
insert_products()