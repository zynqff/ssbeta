from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
from typing import List, Dict, Any

# --- 1. КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sUper_sEcrEt_kEy_fOr_pRojeCt_2024' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'
login_manager.login_message = 'Для доступа к этой странице необходимо войти.'


# --- 2. МОДЕЛИ ДАННЫХ ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_data = db.Column(db.Text, default="Это ваша личная информация.")
    read_poems_json = db.Column(db.Text, default='[]') 
    is_admin = db.Column(db.Boolean, default=False) 
    pinned_poem_title = db.Column(db.String(200), nullable=True) 
    # НОВОЕ ПОЛЕ: Настройка показа вкладки "Все" (по умолчанию False/скрыта)
    show_all_tab = db.Column(db.Boolean, default=False) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def read_poems_titles(self) -> List[str]:
        """Возвращает список заголовков прочитанных стихов."""
        try:
            return json.loads(self.read_poems_json)
        except (TypeError, json.JSONDecodeError):
            return []

    @read_poems_titles.setter
    def read_poems_titles(self, titles: List[str]):
        """Устанавливает список прочитанных стихов."""
        self.read_poems_json = json.dumps(titles)

    def is_poem_read(self, title: str) -> bool:
        """Проверяет, прочитан ли стих."""
        return title in self.read_poems_titles
    
    def toggle_poem_read_status(self, title: str) -> str:
        """Переключает статус прочтения стиха. Возвращает 'marked' или 'unmarked'."""
        current_reads = self.read_poems_titles
        
        if title in current_reads:
            current_reads.remove(title)
            action = 'unmarked'
        else:
            current_reads.append(title)
            action = 'marked'
            
        self.read_poems_titles = current_reads
        return action
    
    def toggle_pinned_poem(self, title: str) -> str:
        """Переключает статус изучаемого стиха (закреплен/откреплен).
        Возвращает 'pinned' или 'unpinned'."""
        if self.pinned_poem_title == title:
            self.pinned_poem_title = None  # Открепить
            return 'unpinned'
        else:
            # Закрепить новый, открепив старый (т.к. можно учить только один)
            self.pinned_poem_title = title
            return 'pinned'
            
# НОВАЯ МОДЕЛЬ ДЛЯ СТИХОВ В БД
class Poem(db.Model):
    title = db.Column(db.String(200), primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)


# ФУНКЦИЯ ДЛЯ СЕРИАЛИЗАЦИИ ОБЪЕКТОВ POEM В СЛОВАРИ PYTHON (JSON-совместимые)
def serialize_poems(poems: List[Poem]) -> List[Dict[str, Any]]:
    """Преобразует список объектов Poem в список словарей для JSON-сериализации."""
    serialized_data = []
    for poem in poems:
        serialized_data.append({
            'title': poem.title,
            'author': poem.author,
            'text': poem.text
        })
    return serialized_data

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def initialize_db_data():
    """
    Создает БД и заполняет ее стихами и администратором.
    Эта функция должна быть вызвана при запуске.
    """
    with app.app_context():
        db.create_all()

        # --- 1. ВАШ АККАУНТ АДМИНИСТРАТОРА ---
        
        # 🚨 ЗАМЕНИТЕ ЭТИ ДВЕ СТРОКИ НА ВАШИ РЕАЛЬНЫЕ ЛОГИН И ПАРОЛЬ 
        ADMIN_USERNAME = 'admin' 
        ADMIN_PASSWORD = 'zynqochka' 
        # -----------------------------------------------------------

        if not User.query.filter_by(username=ADMIN_USERNAME).first():
            default_admin = User.query.filter_by(username='admin').first()
            if default_admin and default_admin.username != ADMIN_USERNAME:
                db.session.delete(default_admin)
                
            admin_user = User(username=ADMIN_USERNAME, is_admin=True)
            admin_user.set_password(ADMIN_PASSWORD) 
            db.session.add(admin_user)
            db.session.commit()
            print(f"Администратор '{ADMIN_USERNAME}' создан с вашим паролем.")

        # --- 2. ВАШИ СТИХИ (ИЗ ПАМЯТИ) ---
        
        _poems_data_to_migrate = {
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
        
        if not Poem.query.first():
            poems_to_add = []
            for poem_data in _poems_data_to_migrate.values():
                poems_to_add.append(Poem(
                    title=poem_data['title'],
                    author=poem_data['author'],
                    text=poem_data['text']
                ))
            
            db.session.add_all(poems_to_add)
            db.session.commit()
            print("Стихи добавлены в базу данных.")

# --- 4. МАРШРУТЫ (URL-АДРЕСА) ---

@app.route('/')
def index():
    """Главная страница."""
    
    poems = Poem.query.all()
    serialized_poems = serialize_poems(poems)
    
    read_titles = []
    pinned_title = None 
    is_admin = False
    show_all_tab = False 
    
    if current_user.is_authenticated:
        read_titles = current_user.read_poems_titles
        pinned_title = current_user.pinned_poem_title 
        is_admin = current_user.is_admin
        show_all_tab = current_user.show_all_tab 
    
    return render_template('index.html', 
                           poems=serialized_poems,
                           read_titles=read_titles,
                           pinned_title=pinned_title, 
                           is_admin=is_admin,
                           show_all_tab=show_all_tab) 


@app.route('/toggle_read', methods=['POST'])
@login_required
def toggle_read():
    """Маршрут для переключения состояния 'прочитано/не прочитано' (через AJAX)."""
    data = request.get_json()
    poem_title = data.get('title')
    
    if not poem_title:
        return jsonify({"success": False, "message": "Не указан заголовок стиха"}), 400
    
    if not Poem.query.get(poem_title):
        return jsonify({"success": False, "message": "Стих не найден"}), 404

    try:
        action = current_user.toggle_poem_read_status(poem_title)
        db.session.commit()
        
        return jsonify({"success": True, "action": action})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Ошибка при обновлении БД: {str(e)}"}), 500


@app.route('/toggle_pin', methods=['POST'])
@login_required
def toggle_pin():
    """Переключает статус изучаемого стиха (закреплен/откреплен) (через AJAX)."""
    data = request.get_json()
    poem_title = data.get('title')
    
    if not poem_title:
        return jsonify({"success": False, "message": "Не указан заголовок стиха"}), 400
    
    if not Poem.query.get(poem_title):
        return jsonify({"success": False, "message": "Стих не найден"}), 404
        
    try:
        action = current_user.toggle_pinned_poem(poem_title)
        db.session.commit()
        
        pinned_title = current_user.pinned_poem_title if action == 'pinned' else None
        
        return jsonify({"success": True, "action": action, "pinned_title": pinned_title})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Ошибка при обновлении БД: {str(e)}"}), 500


@app.route('/delete_poem/<string:title>', methods=['POST'])
@login_required
def delete_poem(title):
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Доступ запрещен. Требуются права администратора."}), 403
        
    poem = Poem.query.get(title)
    if not poem:
        return jsonify({"success": False, "message": "Стих не найден."}), 404
        
    try:
        # Удаляем стих из списка прочитанных и закрепленных у всех пользователей
        for user in User.query.all():
            if user.is_poem_read(title):
                current_reads = user.read_poems_titles
                current_reads.remove(title)
                user.read_poems_titles = current_reads
                
            if user.pinned_poem_title == title:
                user.pinned_poem_title = None
                
            db.session.add(user)

        db.session.delete(poem)
        db.session.commit()
        return jsonify({"success": True, "message": f"Стих '{title}' успешно удален."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Ошибка при удалении: {str(e)}"}), 500

@app.route('/add_poem', methods=['GET', 'POST'])
@login_required
def add_poem():
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

        if Poem.query.get(title):
            flash(f'Стих с названием "{title}" уже существует.', 'error')
            return redirect(url_for('add_poem'))
            
        new_poem = Poem(title=title, author=author, text=text)
        db.session.add(new_poem)
        db.session.commit()
        
        flash(f'Стих "{title}" успешно добавлен!', 'success')
        return redirect(url_for('index'))
        
    return render_template('add_poem.html')


@app.route('/edit_poem/<string:title>', methods=['GET', 'POST'])
@login_required
def edit_poem(title):
    if not current_user.is_admin:
        flash('Доступ запрещен. Эта страница только для администраторов.', 'error')
        return redirect(url_for('index'))

    poem = Poem.query.get(title)
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

        if new_title != title:
            if Poem.query.get(new_title):
                flash(f'Стих с новым названием "{new_title}" уже существует.', 'error')
                return redirect(url_for('edit_poem', title=title))
            
            for user in User.query.all():
                if user.is_poem_read(title):
                    current_reads = user.read_poems_titles
                    current_reads.remove(title)
                    current_reads.append(new_title)
                    user.read_poems_titles = current_reads
                
                if user.pinned_poem_title == title:
                    user.pinned_poem_title = new_title
                    
                db.session.add(user)
                    
            db.session.delete(poem)
            new_poem_obj = Poem(title=new_title, author=new_author, text=new_text)
            db.session.add(new_poem_obj)

        else:
            poem.author = new_author
            poem.text = new_text
        
        db.session.commit()
        
        flash(f'Стих "{new_title}" успешно обновлен!', 'success')
        return redirect(url_for('index'))
        
    return render_template('edit_poem.html', poem=poem)


@app.route('/register', methods=['GET', 'POST'])
def register():
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
    if request.method == 'POST':
        
        # --- 1. Обработка смены пароля ---
        new_password = request.form.get('new_password')
        if new_password:
            if len(new_password) < 4:
                flash('Новый пароль должен быть не менее 4 символов.', 'error')
                return redirect(url_for('profile'))
                
            current_user.set_password(new_password)
            db.session.commit()
            flash('Пароль успешно изменён!', 'success')
            return redirect(url_for('profile'))
        
        # --- 2. Обработка обновления личных данных и настроек ---
        new_data = request.form.get('user_data')
        show_all = request.form.get('show_all_tab') == 'on' 
        
        if new_data is not None:
            current_user.user_data = new_data
        
        current_user.show_all_tab = show_all 
        
        db.session.commit()
        flash('Настройки профиля обновлены!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', 
                           user_data=current_user.user_data,
                           show_all_tab=current_user.show_all_tab) 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('index'))


# --- 5. ЗАПУСК (Инициализация только для локального dev-режима) ---
if __name__ == '__main__':
    # Эта функция вызывается только при локальном запуске (python app.py)
    # На Render/Gunicorn она будет вызвана через команду запуска.
    initialize_db_data() 
    app.run(debug=True)