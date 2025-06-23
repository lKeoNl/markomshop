import sqlite3  # или другой драйвер БД


def lowercase_product_names():
    # Подключение к БД (убедитесь, что путь правильный)
    conn = sqlite3.connect('users.db')  # или используйте ваше подключение Flask
    cursor = conn.cursor()

    try:
        # 1. Получаем все текущие записи
        cursor.execute("SELECT id, name FROM products")
        products = cursor.fetchall()

        # 2. Обновляем каждую запись
        updated_count = 0
        for product in products:
            product_id = product[0]
            lowercase_name = product[1].lower()  # Преобразуем в нижний регистр

            cursor.execute("""
                           UPDATE products
                           SET name = ?
                           WHERE id = ?
                           """, (lowercase_name, product_id))
            updated_count += 1

        # 3. Сохраняем изменения
        conn.commit()
        print(f"✅ Успешно обновлено {updated_count} записей в таблице products")

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# Для Flask (если используете Flask-SQLAlchemy)
# @app.cli.command('lowercase-products')
# def lowercase_products_command():
#     lowercase_product_names()
#     print("Названия продуктов обновлены")

# Запуск
if __name__ == '__main__':
    lowercase_product_names()