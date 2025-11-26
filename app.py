from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
from typing import List

# --- 1. КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ ---
app = Flask(__name__)
# ВАЖНО: Замените этот ключ на длинную случайную строку!
app.config['SECRET_KEY'] = 'sUper_sEcrEt_kEy_fOr_pRojeCt_2024' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # Название файла БД
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'
login_manager.login_message = 'Для доступа к этой странице необходимо войти.'


# --- 2. МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ И ДАННЫХ ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_data = db.Column(db.String(500), default="Это ваша личная информация.")
    read_poems = db.Column(db.String(10000), default='[]')
    is_admin = db.Column(db.Boolean, default=False) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_read_poems(self) -> List[str]:
        """Возвращает список заголовков прочитанных стихов."""
        try:
            return json.loads(self.read_poems)
        except (TypeError, json.JSONDecodeError):
            return []

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login использует эту функцию для загрузки пользователя."""
    return db.session.get(User, int(user_id))

def create_admin_user():
    """Создает фиксированного администратора, если его нет (Логин: admin, Пароль: zynqochka)."""
    admin_username = 'admin'
    admin_password = 'zynqochka'
    
    admin_user = User.query.filter_by(username=admin_username).first()
    
    if not admin_user:
        new_admin = User(username=admin_username, is_admin=True)
        new_admin.set_password(admin_password)
        db.session.add(new_admin)
        db.session.commit()
        print(f"*** Создан фиксированный администратор: Логин='{admin_username}', Пароль='{admin_password}' ***")
    elif not admin_user.is_admin:
        admin_user.is_admin = True
        db.session.commit()
        print(f"*** Пользователю '{admin_username}' назначены права администратора. ***")


# --- 3. ДАННЫЕ (Ваши стихи) ---
# Стихи хранятся в словаре, где ключ - это название стиха
_poems_data = {
    "Плач Ярославны": { "title": "Плач Ярославны", "author": "пер. Н. Заболоцкого", "text": "Над широким берегом Дуная,\nНад великой Галицкой землей\nПлачет, из Путивля долетая,\nГолос Ярославны молодой:..." },
    "К Чаадаеву": { "title": "К Чаадаеву", "author": "А. С. Пушкин", "text": "Любви, надежды, тихой славы\nНедолго нежил нас обман,\nИсчезли юные забавы,\nКак сон, как утренний туман;..." },
    "Анчар": { "title": "Анчар", "author": "А. С. Пушкин", "text": "В пустыне чахлой и скупой,\nНа почве, зноем раскаленной,\nАнчар, как грозный часовой,\nСтоит — один во всей вселенной...." },
    "Пророк (Пушкин)": { "title": "Пророк (Пушкин)", "author": "А. С. Пушкин", "text": "Духовной жаждою томим,\nВ пустыне мрачной я влачился, —\nИ шестикрылый серафим\nНа перепутье мне явился...." },
    "Письмо Онегина": { "title": "Письмо Онегина", "author": "А. С. Пушкин", "text": "Предвижу все: вас оскорбит\nПечальной тайны объясненье.\nКакое горькое презренье\nВаш гордый взгляд изобразит!..." },
    "Смерть Поэта": { "title": "Смерть Поэта", "author": "М. Ю. Лермонтов", "text": "Отмщенье, государь, отмщенье!\nПаду к ногам твоим:\nБудь справедлив и накажи убийцу,..." },
    "Родина": { "title": "Родина", "author": "М. Ю. Лермонтов", "text": "Люблю отчизну я, но странною любовью!\nНе победит ее рассудок мой.\nНи слава, купленная кровью,..." },
    "Пророк (Лермонтов)": { "title": "Пророк (Лермонтов)", "author": "М. Ю. Лермонтов", "text": "С тех пор как Вечный Судия\nМне дал всеведенье пророка,\nВ очах людей читаю я\nСтраницы злобы и порока...." },
    "Отговорила роща золотая": { "title": "Отговорила роща золотая", "author": "С. А. Есенин", "text": "Отговорила роща золотая\nБерёзовым, весёлым языком,\nИ журавли, печально пролетая,\nУж не жалеют больше ни о ком...." },
    "Шаганэ ты моя, Шаганэ": { "title": "Шаганэ ты моя, Шаганэ", "author": "С. А. Есенин", "text": "Шаганэ ты моя, Шаганэ!\nПотому, что я с севера, что ли,\nЯ готов рассказать тебе поле,\nПро волнистую рожь при луне...." },
    "Не жалею, не зову, не плачу": { "title": "Не жалею, не зову, не плачу", "author": "С. А. Есенин", "text": "Не жалею, не зову, не плачу,\nВсе пройдет, как с белых яблонь дым.\nУвяданья золотом охваченный,\nЯ не буду больше молодым...." },
    "Послушайте!": { "title": "Послушайте!", "author": "В. В. Маяковский", "text": "Послушайте!\nВедь, если звезды зажигают —\nзначит — это кому-нибудь нужно?..." },
    "Мне нравится, что вы больны не мной": { "title": "Мне нравится, что вы больны не мной", "author": "М. И. Цветаева", "text": "Мне нравится, что Вы больны не мной,\nМне нравится, что я больна не Вами,\nЧто никогда тяжелый шар земной\nНе уплывет под нашими ногами...." },
    "Не с теми я, кто бросил землю": { "title": "Не с теми я, кто бросил землю", "author": "А. А. Ахматова", "text": "Не с теми я, кто бросил землю\nНа растерзание врагам.\nИх грубой лести я не внемлю,\nИм песен я своих не дам...." },
    "Я убит подо Ржевом": { "title": "Я убит подо Ржевом", "author": "А. Т. Твардовский", "text": "Я убит подо Ржевом,\nВ безыменном болоте,\nВ пятой роте, на левом,\nПри жестоком налете...." },
    "Властителям и судиям": { "title": "Властителям и судиям", "author": "Гавриил Державин", "text": "Восстал всевышний бог, да судит\nЗемных богов во сонме их;\nДоколе, рек, доколь вам будет\nЩадить неправедных и злых?..." },
    "А судьи кто?": { "title": "А судьи кто?", "author": "А. С. Грибоедов", "text": "А судьи кто? — За древностию лет\nК свободной жизни их вражда непримирима,\nСужденья черпают из забытых газет\nВремен Очаковских и покоренья Крыма;..." },
    "О, весна без конца и без краю…": { "title": "О, весна без конца и без краю…", "author": "А. А. Блок", "text": "О, весна без конца и без краю —\nБез конца и без краю мечта!\nУзнаю тебя, жизнь! Принимаю!\nИ приветствую звоном щита!..." }
}


# --- 4. МАРШРУТЫ (URL-АДРЕСА) ---

@app.route('/')
def index():
    """Главная страница."""
    read_titles = []
    is_admin = False
    if current_user.is_authenticated:
        read_titles = current_user.get_read_poems()
        is_admin = current_user.is_admin
    
    return render_template('index.html', 
                           poems=list(_poems_data.values()),
                           read_titles=read_titles,
                           is_admin=is_admin)

@app.route('/toggle_read', methods=['POST'])
@login_required
def toggle_read():
    """Маршрут для переключения состояния 'прочитано/не прочитано' (через AJAX)."""
    data = request.get_json()
    poem_title = data.get('title')
    
    if not poem_title:
        return jsonify({"success": False, "message": "Не указан заголовок стиха"}), 400
    
    read_titles = current_user.get_read_poems()
    
    if poem_title in read_titles:
        read_titles.remove(poem_title)
        action = "unmarked"
    else:
        read_titles.append(poem_title)
        action = "marked"

    try:
        current_user.read_poems = json.dumps(read_titles)
        db.session.commit()
        
        return jsonify({"success": True, "action": action})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Ошибка при обновлении БД: {str(e)}"}), 500

@app.route('/delete_poem/<string:title>', methods=['POST'])
@login_required
def delete_poem(title):
    """Удаляет стих, доступен только администраторам."""
    global _poems_data
    
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Доступ запрещен. Требуются права администратора."}), 403
        
    if title in _poems_data:
        try:
            del _poems_data[title]
            return jsonify({"success": True, "message": f"Стих '{title}' успешно удален."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Ошибка при удалении: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "message": "Стих не найден."}), 404

@app.route('/add_poem', methods=['GET', 'POST'])
@login_required
def add_poem():
    """Позволяет администратору добавить новый стих."""
    global _poems_data
    
    if not current_user.is_admin:
        flash('Доступ запрещен. Эта страница только для администраторов.', 'error')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        text = request.form.get('text', '').strip()

        if not title or not author or not text:
            flash('Все поля должны быть заполнены.', 'error')
            return redirect(url_for('add_poem'))

        if title in _poems_data:
            flash(f'Стих с названием "{title}" уже существует.', 'error')
            return redirect(url_for('add_poem'))
            
        new_poem = {
            "title": title,
            "author": author,
            "text": text
        }
        _poems_data[title] = new_poem
        
        flash(f'Стих "{title}" успешно добавлен!', 'success')
        return redirect(url_for('index'))
        
    return render_template('add_poem.html')


@app.route('/edit_poem/<string:title>', methods=['GET', 'POST'])
@login_required
def edit_poem(title):
    """Позволяет администратору редактировать существующий стих."""
    global _poems_data
    
    if not current_user.is_admin:
        flash('Доступ запрещен. Эта страница только для администраторов.', 'error')
        return redirect(url_for('index'))

    poem = _poems_data.get(title)
    if not poem:
        flash('Стих для редактирования не найден.', 'error')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        new_title = request.form.get('title', '').strip()
        new_author = request.form.get('author', '').strip()
        new_text = request.form.get('text', '').strip()

        if not new_title or not new_author or not new_text:
            flash('Все поля должны быть заполнены.', 'error')
            return redirect(url_for('edit_poem', title=title)) 

        if new_title != title and new_title in _poems_data:
            flash(f'Стих с новым названием "{new_title}" уже существует.', 'error')
            return redirect(url_for('edit_poem', title=title))
            
        if new_title != title:
            # Если название изменилось, удаляем старую запись
            del _poems_data[title] 
        
        # Обновляем/создаем запись с новыми данными (ключ словаря может быть новым)
        _poems_data[new_title] = {
            "title": new_title,
            "author": new_author,
            "text": new_text
        }
        
        flash(f'Стих "{new_title}" успешно обновлен!', 'success')
        return redirect(url_for('index'))
        
    return render_template('edit_poem.html', poem=poem)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации."""
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует!', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 4:
            flash('Пароль должен быть не менее 4 символов.', 'error')
            return redirect(url_for('register'))
            
        new_user = User(username=username)
        new_user.set_password(password)
            
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация прошла успешно! Вы можете войти.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему."""
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'С возвращением, {user.username}!', 'success') 
            return redirect(url_for('index'))
        else:
            flash('Неправильный логин или пароль.', 'error')
            
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Страница профиля пользователя."""
    if request.method == 'POST':
        new_data = request.form.get('user_data')
        
        current_user.user_data = new_data
        db.session.commit()
        flash('Данные профиля обновлены!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user_data=current_user.user_data)

@app.route('/logout')
@login_required
def logout():
    """Выход из системы."""
    logout_user()
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('index'))


# --- 5. ЗАПУСК ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        create_admin_user() 
    app.run(debug=True)