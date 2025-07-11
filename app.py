import os
from dotenv import load_dotenv
import re
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


def get_db():
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise ValueError("DATABASE_URL not set in .env")

    try:
        if "?sslmode=" not in db_url:
            db_url += "?sslmode=require"

        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print("Ошибка подключения к БД:", e)
        return None


def update_quantity(product_id, delta, user_id):
    db = get_db()

    cur = db.execute(
        "SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s",
        (user_id, product_id)
    )
    row = cur.fetchone()

    if row:
        new_quantity = row['quantity'] + delta
        if new_quantity > 0:
            db.execute(
                "UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
                (new_quantity, user_id, product_id)
            )
        else:
            db.execute(
                "DELETE FROM cart WHERE user_id = %s AND product_id = %s",
                (user_id, product_id)
            )
        db.commit()
        return max(new_quantity, 0)
    else:
        if delta > 0:

            product_row = db.execute(
                "SELECT name FROM products WHERE id = %s",
                (product_id,)
            ).fetchone()

            product_name = product_row['name'] if product_row else 'Неизвестно'

            db.execute(
                "INSERT INTO cart (user_id, product_id, product_name, quantity) VALUES (%s, %s, %s, %s)",
                (user_id, product_id, product_name, delta)
            )
            db.commit()
            return delta
        return 0



@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        login = data.get('login', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()

        errors = {}

        if not name:
            errors['name'] = 'Заполните обязательное поле'
        elif len(name) > 20 or not re.match(r'^[А-Яа-яЁё\s]+$', name):
            errors['name'] = 'Некорректное имя'

        if not email:
            errors['email'] = 'Заполните обязательное поле'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Некорректный email'

        if not login:
            errors['login'] = 'Заполните обязательное поле'
        elif len(login) > 20 or not re.match(r'^[А-Яа-яЁё0-9]+$', login):
            errors['login'] = 'Некорректный логин'

        if not password:
            errors['password'] = 'Заполните обязательное поле'
        elif len(password) < 6 or not re.search(r'[А-ЯA-Z]', password):
            errors['password'] = 'Пароль должен содержать хотя бы 6 символов и одну заглавную букву'

        if not confirm_password:
            errors['confirm_password'] = 'Заполните обязательное поле'
        elif confirm_password != password:
            errors['confirm_password'] = 'Пароли не совпадают'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            errors['email'] = 'Этот email уже используется'

        cursor.execute("SELECT 1 FROM users WHERE login = %s", (login,))
        if cursor.fetchone():
            errors['login'] = 'Этот логин уже используется'

        if errors:
            conn.close()
            if request.is_json:
                return jsonify({'success': False,
                                'errors': errors
                                }), 400
            else:
                session['errors'] = errors
                return redirect(url_for('reg'))

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, login, password) VALUES (%s, %s, %s, %s)",
            (name, email, login, hashed_password)
        )
        conn.commit()
        conn.close()

        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Вы успешно зарегистрировались!',
                'redirect': url_for('login')
            })
        else:
            session['notification'] = 'Вы успешно зарегистрировались!'
            return redirect(url_for('login'))

    errors = session.pop('errors', {})
    return render_template('reg.html', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        errors = {}

        if not email:
            errors['email'] = 'Заполните обязательное поле'
        if not password:
            errors['password'] = 'Заполните обязательное поле'

        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            else:
                return render_template('index.html', errors=errors, values={'email': email})

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            if request.is_json:
                return jsonify({'success': True,
                                'redirect': url_for('store')})
            else:
                return redirect(url_for('store'))
        else:
            errors['password'] = 'Неверный email или пароль'
            if request.is_json:
                return jsonify({'success': False,
                                'errors': errors
                                }), 401
            else:
                return render_template('index.html', errors=errors, values={'email': email})

    return render_template('index.html', errors={}, values={})



@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/store', methods=['GET'])
def store():
    conn = get_db()
    cursor = conn.cursor()

    new_products = []
    for category in ['vegetables', 'fruits']:
        cursor.execute("""SELECT id, category, name, image_url
                          FROM products
                          WHERE category = %s
                          ORDER BY id DESC LIMIT 4""", (category,))
        new_products.extend(cursor.fetchall())
    new_product_list = [
        {'id': row[0], 'category': row[1], 'name': row[2], 'image_url': row[3]}
        for row in new_products
    ]

    new_drinks = []
    for category in ['drinks']:
        cursor.execute("""SELECT id, category, name, image_url
                          FROM products
                          WHERE category = %s
                          ORDER BY id DESC LIMIT 5""", (category,))
        new_drinks.extend(cursor.fetchall())
    new_drinks_list = [
        {'id': row[0], 'category': row[1], 'name': row[2], 'image_url': row[3]} for row in new_drinks
    ]

    new_nuts = []
    for category in ['nuts']:
        cursor.execute("""SELECT id, category, name, image_url
                          FROM products
                          WHERE category = %s
                          ORDER BY id DESC LIMIT 5""", (category,))
        new_nuts.extend(cursor.fetchall())
    new_nuts_list = [
        {'id': row[0], 'category': row[1], 'name': row[2], 'image_url': row[3]} for row in new_nuts
    ]

    conn.close()
    return render_template('store.html',
                           new_products=new_product_list,
                           new_drinks=new_drinks_list,
                           new_nuts=new_nuts_list)


@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    comment = data.get('comment', '').strip()
    agreement = data.get('agreement', False)

    errors = {}

    if not name:
        errors['name'] = 'Укажите имя'
    elif len(name) > 20 or not re.match(r'^[a-zA-Z\s]+$', name):
        errors['name'] = 'Допустимы только латинские буквы'

    if not email:
        errors['email'] = 'Укажите адрес электронной почты'
    elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors['email'] = 'Некорректный формат почты'

    if phone:
        if not re.match(r'^\d+$', phone):
            errors['phone'] = 'Допустимы только цифры'
        elif len(phone) > 11:
            errors['phone'] = 'Телефон не должен превышать 11 цифр'

    if comment and len(comment) > 120:
        errors['comment'] = 'Комментарий не должен превышать 120 символов'

    if not agreement:
        errors['agreement'] = 'Подтвердите согласие'

    if errors:
        return jsonify({'success': False,
                        'errors': errors
                        }), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (name, email, phone, comment) VALUES (%s, %s, %s, %s)",
        (name, email, phone, comment)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True,
                   'message': 'Спасибо за отзыв!'})



@app.route('/vegetables', methods=['GET', 'POST'])
def vegetables():
    scroll_to_form = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        comment = request.form.get('comment', '').strip()
        agreement = request.form.get('agreement')

        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'comment': comment,
            'agreement': agreement
        }

        errors = {}
        if not name:
            errors['name'] = 'Укажите имя'
        elif len(name) > 20 or not re.match(r'^[a-zA-Z\s]+$', name):
            errors['name'] = 'Допустимы только латинские буквы'

        if not email:
            errors['email'] = 'Укажите адрес электронной почты'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Некорректный формат почты'

        if phone:
            if not re.match(r'^\d+$', phone):
                errors['phone'] = 'Допустимы только цифры'
            elif len(phone) > 11:
                errors['phone'] = 'Телефон не должен превышать 11 цифр'

        if comment and len(comment) > 120:
            errors['comment'] = 'Комментарий не должен превышать 120 символов'

        if not agreement:
            errors['agreement'] = 'Подтвердите согласие'

        if errors:
            session['errors'] = errors
            session['values'] = values
            session['scroll_to_form'] = True
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (name, email, phone, comment) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, comment))
            conn.commit()
            conn.close()
            session['scroll_to_form'] = True
            session['notification'] = 'Спасибо за отзыв!'

        return redirect(url_for('vegetables'))

    errors = session.pop('errors', {})
    values = session.pop('values', {})
    success = session.pop('success', False)
    scroll_to_form = session.pop('scroll_to_form', {})
    message = session.pop('message', None)

    conn = get_db()
    cursor = conn.cursor()

    vegetables = []
    for category in ['vegetables']:
        cursor.execute("""
                SELECT id, category, name, image_url 
                FROM products 
                WHERE category = %s 
                ORDER BY id DESC 
            """, (category,))
        vegetables.extend(cursor.fetchall())
    vegetables_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in vegetables
    ]

    fruits = []
    for category in ['fruits']:
        cursor.execute("""
                    SELECT id, category, name, image_url 
                    FROM products 
                    WHERE category = %s 
                    ORDER BY id DESC 
                """, (category,))
        fruits.extend(cursor.fetchall())
    fruits_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in fruits
    ]

    greenery = []
    for category in ['greenery']:
        cursor.execute("""
                        SELECT id, category, name, image_url 
                        FROM products 
                        WHERE category = %s 
                        ORDER BY id DESC 
                    """, (category,))
        greenery.extend(cursor.fetchall())
    greenery_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in greenery
    ]


    conn.close()
    return render_template('vegetables.html',
                           vegetables=vegetables_list,
                           fruits=fruits_list,
                           greenery=greenery_list,
                           errors=errors,
                           values=values,
                           scroll_to_form=scroll_to_form,
                           message=message,
                           success=success)


@app.route('/meat', methods=['GET', 'POST'])
def meat():
    scroll_to_form = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        comment = request.form.get('comment', '').strip()
        agreement = request.form.get('agreement')

        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'comment': comment,
            'agreement': agreement
        }

        errors = {}
        if not name:
            errors['name'] = 'Укажите имя'
        elif len(name) > 20 or not re.match(r'^[a-zA-Z\s]+$', name):
            errors['name'] = 'Допустимы только латинские буквы'

        if not email:
            errors['email'] = 'Укажите адрес электронной почты'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Некорректный формат почты'

        if phone:
            if not re.match(r'^\d+$', phone):
                errors['phone'] = 'Допустимы только цифры'
            elif len(phone) > 11:
                errors['phone'] = 'Телефон не должен превышать 11 цифр'

        if comment and len(comment) > 120:
            errors['comment'] = 'Комментарий не должен превышать 120 символов'

        if not agreement:
            errors['agreement'] = 'Подтвердите согласие'

        if errors:
            session['errors'] = errors
            session['values'] = values
            session['scroll_to_form'] = True
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (name, email, phone, comment) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, comment))
            conn.commit()
            conn.close()
            session['scroll_to_form'] = True
            session['notification'] = 'Спасибо за отзыв!'

        return redirect(url_for('meat'))

    errors = session.pop('errors', {})
    values = session.pop('values', {})
    success = session.pop('success', False)
    scroll_to_form = session.pop('scroll_to_form', {})
    message = session.pop('message', None)

    conn = get_db()
    cursor = conn.cursor()

    meat = []
    for category in ['meat']:
        cursor.execute("""
                        SELECT id, category, name, image_url 
                        FROM products 
                        WHERE category = %s 
                        ORDER BY id DESC 
                        LIMIT 15 OFFSET 10
                    """, (category,))
        meat.extend(cursor.fetchall())
    poultry_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in meat
    ]

    meat = []
    for category in ['meat']:
        cursor.execute("""
                    SELECT id, category, name, image_url 
                    FROM products 
                    WHERE category = %s 
                    ORDER BY id DESC 
                    LIMIT 5 OFFSET 5
                """, (category,))
        meat.extend(cursor.fetchall())
    beef_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in meat
    ]

    meat = []
    for category in ['meat']:
        cursor.execute("""
                SELECT id, category, name, image_url 
                FROM products 
                WHERE category = %s 
                ORDER BY id DESC 
                LIMIT 5
            """, (category,))
        meat.extend(cursor.fetchall())
    pork_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in meat
    ]

    conn.close()
    return render_template('meat.html',
                           poultry=poultry_list,
                           beef=beef_list,
                           pork=pork_list,
                           errors=errors,
                           values=values,
                           scroll_to_form=scroll_to_form,
                           message=message,
                           success=success)


@app.route('/drinks', methods=['GET', 'POST'])
def drinks():
    scroll_to_form = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        comment = request.form.get('comment', '').strip()
        agreement = request.form.get('agreement')

        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'comment': comment,
            'agreement': agreement
        }

        errors = {}
        if not name:
            errors['name'] = 'Укажите имя'
        elif len(name) > 20 or not re.match(r'^[a-zA-Z\s]+$', name):
            errors['name'] = 'Допустимы только латинские буквы'

        if not email:
            errors['email'] = 'Укажите адрес электронной почты'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Некорректный формат почты'

        if phone:
            if not re.match(r'^\d+$', phone):
                errors['phone'] = 'Допустимы только цифры'
            elif len(phone) > 11:
                errors['phone'] = 'Телефон не должен превышать 11 цифр'

        if comment and len(comment) > 120:
            errors['comment'] = 'Комментарий не должен превышать 120 символов'

        if not agreement:
            errors['agreement'] = 'Подтвердите согласие'

        if errors:
            session['errors'] = errors
            session['values'] = values
            session['scroll_to_form'] = True
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (name, email, phone, comment) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, comment))
            conn.commit()
            conn.close()
            session['scroll_to_form'] = True
            session['notification'] = 'Спасибо за отзыв!'

        return redirect(url_for('drinks'))

    errors = session.pop('errors', {})
    values = session.pop('values', {})
    success = session.pop('success', False)
    scroll_to_form = session.pop('scroll_to_form', {})
    message = session.pop('message', None)

    conn = get_db()
    cursor = conn.cursor()

    drinks = []
    for category in ['drinks']:
        cursor.execute("""
                SELECT id, category, name, image_url 
                FROM products 
                WHERE category = %s 
                ORDER BY id ASC 
            """, (category,))
        drinks.extend(cursor.fetchall())
    drinks_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in drinks
    ]

    conn.close()

    return render_template('drinks.html',
                           drinks=drinks_list,
                           errors=errors,
                           values=values,
                           scroll_to_form=scroll_to_form,
                           message=message,
                           success=success)


@app.route('/nuts', methods=['GET', 'POST'])
def nuts():
    scroll_to_form = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        comment = request.form.get('comment', '').strip()
        agreement = request.form.get('agreement')

        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'comment': comment,
            'agreement': agreement
        }

        errors = {}
        if not name:
            errors['name'] = 'Укажите имя'
        elif len(name) > 20 or not re.match(r'^[a-zA-Z\s]+$', name):
            errors['name'] = 'Допустимы только латинские буквы'

        if not email:
            errors['email'] = 'Укажите адрес электронной почты'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Некорректный формат почты'

        if phone:
            if not re.match(r'^\d+$', phone):
                errors['phone'] = 'Допустимы только цифры'
            elif len(phone) > 11:
                errors['phone'] = 'Телефон не должен превышать 11 цифр'

        if comment and len(comment) > 120:
            errors['comment'] = 'Комментарий не должен превышать 120 символов'

        if not agreement:
            errors['agreement'] = 'Подтвердите согласие'

        if errors:
            session['errors'] = errors
            session['values'] = values
            session['scroll_to_form'] = True
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (name, email, phone, comment) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, comment))
            conn.commit()
            conn.close()
            session['scroll_to_form'] = True
            session['notification'] = 'Спасибо за отзыв!'

        return redirect(url_for('nuts'))

    errors = session.pop('errors', {})
    values = session.pop('values', {})
    success = session.pop('success', False)
    scroll_to_form = session.pop('scroll_to_form', {})
    message = session.pop('message', None)

    conn = get_db()
    cursor = conn.cursor()

    nuts = []
    for category in ['nuts']:
        cursor.execute("""
                SELECT id, category, name, image_url 
                FROM products 
                WHERE category = %s 
                ORDER BY id ASC 
            """, (category,))
        nuts.extend(cursor.fetchall())
    nuts_list = [
        {
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        }
        for row in nuts
    ]

    conn.close()

    return render_template('nuts.html',
                           nuts=nuts_list,
                           errors=errors,
                           values=values,
                           scroll_to_form=scroll_to_form,
                           message=message,
                           success=success)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = session['user_id']
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    conn = get_db()
    c = conn.cursor()

    product_name = data.get('product_name')

    c.execute('SELECT id, quantity FROM cart WHERE user_id=%s AND product_id=%s', (user_id, product_id))
    row = c.fetchone()

    if row:
        c.execute('UPDATE cart SET quantity = quantity + %s WHERE id = %s', (quantity, row[0]))
    else:
        c.execute('INSERT INTO cart (user_id, product_id, product_name, quantity) VALUES (%s, %s, %s, %s)',
                  (user_id, product_id, product_name, quantity))

    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT product_id, product_name, quantity
        FROM cart
        WHERE user_id = %s
    ''', (user_id,))
    items = cursor.fetchall()

    return render_template('cart.html', items=items)


@app.route('/cart/increase/<int:product_id>', methods=['POST'])
def increase_quantity(product_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    new_quantity = update_quantity(product_id, +1, user_id)
    return jsonify({'new_quantity': new_quantity})

@app.route('/cart/decrease/<int:product_id>', methods=['POST'])
def decrease_quantity(product_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401


    new_quantity = update_quantity(product_id, -1, user_id)
    return jsonify({'new_quantity': new_quantity})



@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q', '').strip()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        comment = request.form.get('comment', '').strip()
        agreement = request.form.get('agreement')

        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'comment': comment,
            'agreement': agreement
        }

        errors = {}
        if not name:
            errors['name'] = 'Укажите имя'
        elif len(name) > 20 or not re.match(r'^[a-zA-Z\s]+$', name):
            errors['name'] = 'Допустимы только латинские буквы'

        if not email:
            errors['email'] = 'Укажите адрес электронной почты'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Некорректный формат почты'

        if phone:
            if not re.match(r'^\d+$', phone):
                errors['phone'] = 'Допустимы только цифры'
            elif len(phone) > 11:
                errors['phone'] = 'Телефон не должен превышать 11 цифр'

        if comment and len(comment) > 120:
            errors['comment'] = 'Комментарий не должен превышать 120 символов'

        if not agreement:
            errors['agreement'] = 'Подтвердите согласие'

        if errors:
            session['errors'] = errors
            session['values'] = values
            session['scroll_to_form'] = True
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (name, email, phone, comment) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, comment))
            conn.commit()
            conn.close()
            session['scroll_to_form'] = True
            session['notification'] = 'Спасибо за отзыв!'
        query_from_form = request.form.get('q', '').strip()
        return redirect(url_for('search', q=query_from_form))

    products = []
    if request.method == 'GET' and query:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category, name, image_url
            FROM products
            WHERE UPPER(name) LIKE UPPER(%s)
        """, (f"%{query}%",))
        products = cursor.fetchall()
        conn.close()

    print("Поисковый запрос:", query)
    print("Найдено товаров:", len(products))

    errors = session.pop('errors', {})
    values = session.pop('values', {})
    scroll_to_form = session.pop('scroll_to_form', False)
    message = session.pop('message', None)

    return render_template(
        'search.html',
        query=query,
        products=[{
            'id': row[0],
            'category': row[1],
            'name': row[2],
            'image_url': row[3]
        } for row in products],
        errors=errors,
        values=values,
        scroll_to_form=scroll_to_form,
        message=message
    )






if __name__ == '__main__':
    app.run(debug=True)


