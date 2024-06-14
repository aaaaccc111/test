from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import secrets
import random
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

db_file = 'cinema.db'


def create_connection(db_file):
    """
    資料庫連接
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def generate_verification_code():
    """
    以亂數方式生成四碼驗證碼
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(4))


def validate_phone(phone):
    """
    驗證手機號碼格式，09 開頭，後面接 8 位數字
    """
    return re.match(r'^09\d{8}$', phone)


def validate_email(email):
    """
    驗證email格式
    """
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)


def validate_password(password):
    """
    驗證密碼格式
    """
    return re.match(r'^[0-9a-zA-Z]{8,}$', password)


# 首頁
@app.route('/')
def index():
    return render_template('index.html')

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'phone' in session:
        return redirect(url_for('index'))

    if 'admin' in session:
        return redirect(url_for('movie_list'))

    error_message = None
    if request.method == 'POST':
        phone = request.form['phone']

        #手機號碼格式錯誤，則顯示錯誤訊息，並重新傳送一次login.html
        if not validate_phone(phone):
            error_message = '手機號碼格式錯誤'
            return render_template('login.html',error=error_message)

        #手機號碼格式正確，則檢查uesrs資料表中是否有此手機號碼
        with create_connection(db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE userphone = ?", (phone,))
            user = c.fetchone()

        #如果有，則顯示登入表單，讓使用者輸入密碼、驗證碼
        if user:
            if 'password' in request.form:
                password = request.form['password']
                input_verification_code = request.form['verification_code']
                #如果密碼錯誤，則顯示錯誤訊息，並重新傳送一次login.html
                if user['password'] != password:
                    error_message = '密碼錯誤'
                    system_verification_code = generate_verification_code()
                    session['system_verification_code'] \
                        = system_verification_code
                    return render_template(
                        'login.html',
                        show_password=True,
                        phone=phone,
                        error=error_message,
                        verification_code=system_verification_code,
                        new_user=False
                        )
                #如果驗證碼錯誤，則顯示錯誤訊息，並重新傳送一次login.html
                if (input_verification_code !=
                        session.get('system_verification_code')):
                    error_message = '驗證碼錯誤'
                    system_verification_code = generate_verification_code()
                    session['system_verification_code']\
                        = system_verification_code
                    return render_template(
                        'login.html',
                        show_password=True,
                        phone=phone,
                        error=error_message,
                        verification_code=system_verification_code,
                        new_user=False
                        )
                session['phone'] = phone  # 將手機號碼存入 session
                return redirect(url_for('index'))
            else:
                system_verification_code = generate_verification_code()
                session['system_verification_code'] \
                    = system_verification_code
                return render_template(
                        'login.html',
                        show_password=True,
                        phone=phone,
                        error=error_message,
                        verification_code=system_verification_code,
                        new_user=False
                        )

        #如果沒有，則顯示註冊表單，讓使用者輸入信箱、密碼、確認密碼、驗證碼
        else:
            if 'password' in request.form:
                phone = request.form['phone']
                email = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                input_verification_code = request.form['verification_code']

                if not validate_email(email):
                    error_message = '信箱格式錯誤'
                    system_verification_code = generate_verification_code()
                    session['system_verification_code'] \
                        = system_verification_code
                    return render_template(
                            'login.html',
                            show_password=False,
                            phone=phone,
                            error=error_message,
                            verification_code=system_verification_code,
                            new_user=True
                            )

                if not validate_password(password):
                    error_message = '密碼格式錯誤'
                    system_verification_code = generate_verification_code()
                    session['system_verification_code'] \
                        = system_verification_code
                    return render_template(
                            'login.html',
                            show_password=False,
                            phone=phone,
                            error=error_message,
                            verification_code=system_verification_code,
                            new_user=True
                            )

                if password != confirm_password:
                    error_message = '請確認密碼是否一致'
                    system_verification_code = generate_verification_code()
                    session['system_verification_code'] \
                        = system_verification_code
                    return render_template(
                            'login.html',
                            show_password=False,
                            phone=phone,
                            error=error_message,
                            verification_code=system_verification_code,
                            new_user=True
                            )

                if (input_verification_code !=
                        session.get('system_verification_code')):
                    error_message = '驗證碼錯誤'
                    system_verification_code = generate_verification_code()
                    session['system_verification_code'] \
                        = system_verification_code
                    return render_template(
                            'login.html',
                            show_password=False,
                            phone=phone,
                            error=error_message,
                            verification_code=system_verification_code,
                            new_user=True
                            )

                #註冊後將輸入的資料存入資料uesrs資料表中
                with create_connection(db_file) as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO users "
                        "(userphone, mail, password) VALUES (?, ?, ?)",
                        (phone, email, password)
                    )
                    conn.commit()

                session['phone'] = phone  # 將手機號碼存入 session
                return redirect(url_for('index'))

            else:
                system_verification_code = generate_verification_code()
                session['system_verification_code'] \
                    = system_verification_code
                return render_template(
                        'login.html',
                        show_password=True,
                        phone=phone,
                        verification_code=system_verification_code,
                        new_user=True
                        )

    else:
        return render_template(
                'login.html',
                show_password=False,
                new_user=False
                )

#管理員登入頁面
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'admin' in session:
        return redirect(url_for('movie_list'))

    if 'phone' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['admin']
        password = request.form['password']
        conn = create_connection(db_file)
        admin = conn.execute(
            'SELECT * FROM admin WHERE username = ? AND password = ?',
            (username, password)).fetchone()
        conn.close()

        #如果admin資料表中無此管理員帳號密碼，則顯示錯誤訊息，並重新傳送一次admin_login.html
        if admin is None:
            error_message = '帳號或密碼錯誤'
            return render_template('admin_login.html', error=error_message)

        session['admin'] = username  # 將管理員帳號存入 session
        return redirect(url_for('movie_list'))

    return render_template('admin_login.html')


@app.route('/admin/add_movie', methods=['GET', 'POST'])
def add_movie():

    #判斷管理員帳密是否有登入，若無則導向admin_login.html
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    #新增電影資料
    if request.method == 'POST':
        movie_name = request.form['title']
        movie_description = request.form['director']
        movie_rating = request.form['rating']

        conn = create_connection(db_file)

        #將輸入的電影資料存入movies資料表中
        conn.execute(
            'INSERT INTO movies (title, director, rating) VALUES (?, ?, ?)',
            (movie_name, movie_description, movie_rating)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('movie_list'))

    return render_template('addmovie.html')

@app.route('/admin/movie_list', methods=['GET', 'POST'])
def movie_list():

    #判斷管理員帳密是否有登入，若無則導向admin_login.html
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = create_connection(db_file)
    c = conn.cursor()



    #刪除電影及增修場次
    if request.method == 'POST':
        if 'delete_movie_id' in request.form:
            movie_id = request.form['delete_movie_id']
            c.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            conn.commit()
        elif 'edit_showtime_movie_id' in request.form:
            movie_id = request.form['edit_showtime_movie_id']
            return redirect(url_for('edit_showtime', movie_id=movie_id))

    c.execute("SELECT id, title, director, rating FROM movies")
    all_movies = c.fetchall()
    conn.close()

    return render_template('movielist.html', all_movies=all_movies)

@app.route('/admin/edit_showtime/<int:movie_id>', methods=['GET', 'POST'])
def edit_showtime(movie_id):
    # 判斷管理員帳密是否有登入，若無則導向admin_login.html
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = create_connection(db_file)
    c = conn.cursor()

    if request.method == 'POST':
        if 'date' in request.form and 'time' in request.form and 'seats' in request.form:
            date = request.form['date']
            time = request.form['time']
            seats = request.form['seats']

            if int(seats) > 50:
                error_message = '座位數量不可超過50'
                c.execute("SELECT id, showtime, seats_count FROM showtimes WHERE movie_id = ?", (movie_id,))
                showtimes = c.fetchall()
                showtimes = [dict(showtime) for showtime in showtimes]
                return render_template('editshowtime.html', movie_id=movie_id, showtimes=showtimes, error=error_message)

            # 將選擇的日期和時間合併成一個時間格式
            showtime = f"{date} {time}"
            c.execute("INSERT INTO showtimes (movie_id, showtime, seats_count) VALUES (?, ?, ?)", (movie_id, showtime, seats))
            conn.commit()

    c.execute("SELECT id, showtime, seats_count FROM showtimes WHERE movie_id = ?", (movie_id,))
    showtimes = c.fetchall()
    showtimes = [dict(showtime) for showtime in showtimes]  # 將每個 Row 對象轉換為字典

    conn.close()
    return render_template('editshowtime.html', movie_id=movie_id, showtimes=showtimes)




@app.route('/admin/delete_showtime/<int:movie_id>', methods=['POST'])
def delete_showtime(movie_id):

    #判斷管理員帳密是否有登入，若無則導向admin_login.html
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    showtime_ids = request.form.getlist('delete_showtimes')

    if showtime_ids:
        conn = create_connection(db_file)
        c = conn.cursor()
        c.execute("DELETE FROM showtimes WHERE id IN ({})".format(','.join('?' * len(showtime_ids))), showtime_ids)
        conn.commit()
        conn.close()

    return redirect(url_for('edit_showtime', movie_id=movie_id))


@app.route('/movies', methods=['GET', 'POST'])
def movies():
    if request.method == 'GET':
        conn = create_connection(db_file)
        c = conn.cursor()

        try:
            c.execute("SELECT title, director, rating FROM movies")
            all_movies = c.fetchall()

            print(all_movies)

        except Exception as e:
            print("Error: ", e)
            all_movies = []

        conn.close()

        return render_template('movies.html', all_movies=all_movies)

    elif request.method == 'POST':
        title = request.form['title']
        director = request.form['director']
        year = request.form['year']

        with create_connection(db_file) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO movies (title, director, year) VALUES (?, ?, ?)", (title, director, year))
            conn.commit()

        conn = create_connection(db_file)
        c = conn.cursor()
        c.execute("SELECT title, director, year FROM movies")
        all_movies = c.fetchall()
        conn.close()

        return render_template('movies.html', all_movies=all_movies)


@app.route('/ticket', methods=['GET', 'POST'])
def ticket():
    return render_template('ticket.html')


@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if 'phone' in session:
        if request.method == 'POST':
            showtime_id = request.form.get('showtime_id')
            selected_seats = request.form.getlist('seat')
            movie_id = request.form.get('movie_id')

            with create_connection(db_file) as conn:
                c = conn.cursor()
                for seat in selected_seats:
                    c.execute("INSERT INTO buy (userphone, showtime_id, seat_number) VALUES (?, ?, ?)", (session['phone'], showtime_id, seat))
                    c.execute("UPDATE seats SET booked = 1 WHERE showtime_id = ? AND seat_number = ?", (showtime_id, seat))
                conn.commit()
            return redirect(url_for('member'))
        else:
            if 'movie_id' in request.args:
                movie_id = request.args['movie_id']
                conn = create_connection(db_file)
                c = conn.cursor()
                c.execute("""
                    SELECT movies.title, showtimes.id AS showtime_id, showtimes.showtime, showtimes.seats_count
                    FROM movies
                    JOIN showtimes ON movies.id = showtimes.movie_id
                    WHERE movies.id = ?
                """, (movie_id,))
                movie_showtimes = c.fetchall()
                conn.close()
                return render_template('buy.html', movie_showtimes=movie_showtimes)
            else:
                conn = create_connection(db_file)
                c = conn.cursor()
                c.execute("SELECT id, title FROM movies")
                movies = c.fetchall()
                conn.close()
                return render_template('buy.html', movies=movies)
    else:
        return redirect(url_for('login'))

"""

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        selected_seats = request.form.get('selected_seats').split(',')
        adult_quantity = int(request.form.get('adult_quantity'))
        concession_quantity = int(request.form.get('concession_quantity'))
        disabled_quantity = int(request.form.get('disabled_quantity'))
        senior_quantity = int(request.form.get('senior_quantity'))

    return render_template('booking.html',
                               selected_seats=selected_seats,
                               adult_quantity=adult_quantity,
                               concession_quantity=concession_quantity,
                               disabled_quantity=disabled_quantity,
                               senior_quantity=senior_quantity)
"""

@app.route('/member', methods=['GET', 'POST'])
def member():
    if 'phone' in session:
        phone = session['phone']

        if request.method == 'GET':
            with create_connection(db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT mail FROM users WHERE userphone = ?", (phone,))
                user = c.fetchone()
                email = user['mail'] if user else None

                c.execute("SELECT buy.id AS buy_id, movies.title AS movie_title, showtimes.showtime AS showtime, buy.seat_number AS seat_number FROM buy JOIN showtimes ON buy.showtime_id = showtimes.id JOIN movies ON showtimes.movie_id = movies.id WHERE buy.userphone = ?", (phone,))
                purchases = c.fetchall()

            return render_template('member.html', phone=phone, email=email, purchases=purchases)


        elif request.method == 'POST':
            new_email = request.form['new_email']

            with create_connection(db_file) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET mail = ? WHERE userphone = ?", (new_email, phone))
                conn.commit()

            return redirect(url_for('member'))

    else:
        return redirect(url_for('login'))


@app.route('/chpwd', methods=['GET', 'POST'])
def chpwd():
    if 'phone' in session:
        phone = session['phone']

        if request.method == 'POST':
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            input_verification_code = request.form['verification_code']

            with create_connection(db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT password FROM users WHERE userphone = ?", (phone,))
                user = c.fetchone()

            if user['password'] != old_password:
                error_message = '舊密碼錯誤'
                system_verification_code = generate_verification_code()
                session['system_verification_code'] = system_verification_code
                return render_template('chpwd.html', phone=phone, error=error_message, verification_code=system_verification_code)

            if not validate_password(new_password):
                error_message = '新密碼格式錯誤'
                system_verification_code = generate_verification_code()
                session['system_verification_code'] = system_verification_code
                return render_template('chpwd.html', phone=phone, error=error_message, verification_code=system_verification_code)

            if new_password != confirm_password:
                error_message = '請確認新密碼是否一致'
                system_verification_code = generate_verification_code()
                session['system_verification_code'] = system_verification_code
                return render_template('chpwd.html', phone=phone, error=error_message, verification_code=system_verification_code)

            if input_verification_code != session.get('system_verification_code'):
                error_message = '驗證碼錯誤'
                system_verification_code = generate_verification_code()
                session['system_verification_code'] = system_verification_code
                return render_template('chpwd.html', phone=phone, error=error_message, verification_code=system_verification_code)

            with create_connection(db_file) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET password = ? WHERE userphone = ?", (new_password, phone))
                conn.commit()

            return redirect(url_for('member'))

        else:
            system_verification_code = generate_verification_code()
            session['system_verification_code'] = system_verification_code
            return render_template('chpwd.html', phone=phone, verification_code=system_verification_code)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('phone', None)  # 刪除 session 中的手機號碼
    return redirect(url_for('index'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None) # 刪除 session 中的管理員帳號
    return redirect(url_for('admin_login'))
