import sqlite3

def lowercase_cart_product_names():
    # Подключение к БД
    conn = sqlite3.connect('users.db')  # Убедитесь, что имя БД правильное
    cursor = conn.cursor()

    try:
        # 1. Получаем все записи из cart
        cursor.execute("SELECT id, product_name FROM cart")
        cart_items = cursor.fetchall()

        # 2. Обновляем product_name для каждой записи
        updated_count = 0
        for item in cart_items:
            item_id = item[0]
            lowercase_name = item[1].lower()  # Преобразуем в нижний регистр

            cursor.execute("""
                UPDATE cart
                SET product_name = ?
                WHERE id = ?
            """, (lowercase_name, item_id))
            updated_count += 1

        # 3. Сохраняем изменения
        conn.commit()
        print(f"✅ Успешно обновлено {updated_count} записей в таблице cart")

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Для Flask (если используете Flask-SQLAlchemy)
# @app.cli.command('lowercase-cart-names')
# def lowercase_cart_command():
#     lowercase_cart_product_names()
#     print("Названия продуктов в корзине обновлены")

# Запуск
if __name__ == '__main__':
    lowercase_cart_product_names()