<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Сборник Стихов</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        /* ... CSS стили остаются без изменений ... */
        :root {
            --accent-color: #38bdf8;
            --text-color: #374151;
        }
        /* ... Остальные стили ... */
        .sort-btn {
            padding: 8px 16px;
            border-radius: 9999px;
            border: 1px solid #e5e7eb;
            background-color: #ffffff;
            color: #374151;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            cursor: pointer;
        }
        .sort-btn:hover {
            background-color: #f3f4f6;
            border-color: #d1d5db;
        }
        .sort-btn.active {
            background-color: var(--accent-color);
            color: #ffffff;
            border-color: var(--accent-color);
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen p-4 sm:p-8 text-gray-700">

    <div class="container mx-auto max-w-5xl">
        <header class="text-center mb-8">
            <h1 class="text-3xl sm:text-4xl font-extrabold text-gray-800 mb-4">
                Сборник Cтихов
            </h1>

            <div class="mb-6 flex justify-center space-x-4">
                {% if current_user.is_authenticated %}
                    <a href="{{ url_for('profile') }}" class="text-lg font-bold text-sky-600 hover:text-sky-800 transition-colors">
                        Профиль ({{ current_user.username }})
                    </a>
                    <span class="text-gray-400">|</span>
                    <a href="{{ url_for('logout') }}" class="text-lg font-medium text-gray-500 hover:text-red-500 transition-colors">
                        Выйти
                    </a>
                {% else %}
                    <a href="{{ url_for('login') }}" class="text-lg font-bold text-sky-600 hover:text-sky-800 transition-colors">
                        Войти
                    </a>
                    <span class="text-gray-400">|</span>
                    <a href="{{ url_for('register') }}" class="text-lg font-medium text-gray-500 hover:text-sky-800 transition-colors">
                        Регистрация
                    </a>
                {% endif %}
            </div>
            <div class="relative max-w-lg mx-auto">
                <input type="search" id="searchInput" placeholder="Поиск по названию, автору или тексту..." class="w-full px-4 py-3 rounded-full border-2 border-gray-200 focus:ring-2 focus:ring-sky-400 focus:border-sky-400 transition-all duration-300 outline-none shadow-sm">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 absolute right-4 top-1/2 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
            </div>
        </header>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="mb-4 max-w-lg mx-auto p-3 rounded-lg text-center">
                    {% for category, message in messages %}
                        <p class="font-semibold text-sm" style="color: {{ 'green' if category == 'success' else 'red' }};">
                            {{ message }}
                        </p>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        <div class="flex justify-center items-center flex-wrap gap-2 sm:gap-4 mb-6">
            <span class="text-gray-600 font-semibold hidden sm:block">Сортировать:</span>
            <div id="sort-buttons" class="flex flex-wrap justify-center gap-2">
                <button data-sort="title" data-order="asc" class="sort-btn active">По названию (А-Я)</button>
                <button data-sort="title" data-order="desc" class="sort-btn">По названию (Я-А)</button>
                <button data-sort="length" data-order="asc" class="sort-btn">По длине (короче)</button>
                <button data-sort="length" data-order="desc" class="sort-btn">По длине (длиннее)</button>
            </div>
        </div>

        <div id="grid" class="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            </div>
        <p id="noResults" class="text-center text-gray-500 hidden mt-8">Ничего не найдено.</p>
    </div>

    <div id="modal" class="modal fixed inset-0 flex items-center justify-center p-4 bg-gray-900 bg-opacity-60 z-[100] transition-opacity duration-300">
        <div class="modal-card bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6 sm:p-8 transform transition-transform duration-300 scale-95 relative" role="dialog" aria-modal="true">
            <button id="closeBtn" class="absolute top-3 right-3 p-2 rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors" aria-label="Закрыть">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
            <h2 id="modalTitle" class="text-xl sm:text-2xl font-bold text-gray-800 text-center mb-2 leading-tight"></h2>
            <p id="modalAuthor" class="text-center text-gray-500 mb-6"></p>
            <pre id="modalText" class="poem text-base text-gray-700 leading-relaxed"></pre>
        </div>
    </div>

    <script>
        // БЛОК 3: ИНЪЕКЦИЯ ДАННЫХ ИЗ FLASK/PYTHON В JAVASCRIPT
        // ВНИМАНИЕ: Здесь мы используем фильтр Jinja2 `tojson` для безопасной передачи Python-данных в JS.
        const poems = {{ poems | tojson }};
        
        // Получаем ссылки на DOM-элементы (Без изменений)
        const grid = document.getElementById('grid');
        const searchInput = document.getElementById('searchInput');
        const noResults = document.getElementById('noResults');
        const modal = document.getElementById('modal');
        const modalCard = modal.querySelector('.modal-card');
        const modalTitle = document.getElementById('modalTitle');
        const modalAuthor = document.getElementById('modalAuthor');
        const modalText = document.getElementById('modalText');
        const closeBtn = document.getElementById('closeBtn');
        const sortButtonsContainer = document.getElementById('sort-buttons');

        let allPoems = [];
        let currentSort = { type: 'title', order: 'asc' };

        // ... Все ваши остальные функции JavaScript (getLineString, renderPoems, openModal, closeModal, sortPoems, filterAndRender)
        // ДОЛЖНЫ ОСТАТЬСЯ ТАКИМИ ЖЕ, КАК И БЫЛИ в исходном файле, 
        // так как они работают с переменной `poems`, которую мы теперь инжектируем.

        // Функция для правильного склонения слова "строка"
        function getLineString(count) {
            const lastDigit = count % 10;
            const lastTwoDigits = count % 100;
            if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
                return `${count} строк`;
            }
            if (lastDigit === 1) {
                return `${count} строка`;
            }
            if (lastDigit >= 2 && lastDigit <= 4) {
                return `${count} строки`;
            }
            return `${count} строк`;
        }
        
        // Генерируем карточки стихов
        function renderPoems(poemsToRender) {
            grid.innerHTML = '';
            if (poemsToRender.length === 0) {
                noResults.classList.remove('hidden');
            } else {
                noResults.classList.add('hidden');
            }

            poemsToRender.forEach(poem => {
                const card = document.createElement('div');
                card.className = 'bg-white rounded-xl shadow-lg p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-xl hover:-translate-y-1 cursor-pointer';
                
                const content = document.createElement('div');
                content.innerHTML = `
                    <h2 class="text-lg font-semibold mb-1 text-gray-800">${poem.title}</h2>
                    <p class="text-sm text-gray-500 mb-4">${poem.author}</p>
                `;

                const button = document.createElement('button');
                button.textContent = 'Читать';
                button.className = 'w-full mt-auto bg-sky-500 hover:bg-sky-600 text-white font-medium py-2 px-4 rounded-lg shadow-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500';
                
                card.onclick = () => openModal(poem);

                card.appendChild(content);
                card.appendChild(button);
                grid.appendChild(card);
            });
        }

        // Открывает модальное окно
        function openModal(poem) {
            modalTitle.textContent = poem.title;
            // Убедитесь, что `poem.lineCount` существует (см. window.onload ниже)
            modalAuthor.textContent = `${poem.author} • ${getLineString(poem.lineCount)}`;
            modalText.textContent = poem.text;
            
            modal.classList.add('open');
            setTimeout(() => modalCard.classList.remove('scale-95'), 10);
            document.body.style.overflow = 'hidden';
        }

        // Закрывает модальное окно
        function closeModal() {
            modalCard.classList.add('scale-95');
            modal.classList.remove('open');
            document.body.style.overflow = '';
        }
        
        // Сортировка массива стихов
        function sortPoems(poemsList) {
            const { type, order } = currentSort;
            return [...poemsList].sort((a, b) => {
                if (type === 'title') {
                    return order === 'asc' 
                        ? a.title.localeCompare(b.title, 'ru') 
                        : b.title.localeCompare(a.title, 'ru');
                }
                if (type === 'length') {
                    return order === 'asc' 
                        ? a.lineCount - b.lineCount 
                        : b.lineCount - a.lineCount;
                }
                return 0;
            });
        }

        // Фильтрация и отображение стихов
        function filterAndRender() {
            const searchTerm = searchInput.value.toLowerCase().trim();
            const filteredPoems = searchTerm === '' 
                ? allPoems 
                : allPoems.filter(poem => 
                    poem.title.toLowerCase().includes(searchTerm) ||
                    poem.author.toLowerCase().includes(searchTerm) ||
                    poem.text.toLowerCase().includes(searchTerm)
                );
            const sortedPoems = sortPoems(filteredPoems);
            renderPoems(sortedPoems);
        }

        // Добавляем обработчики событий
        searchInput.addEventListener('input', filterAndRender);
        closeBtn.addEventListener('click', closeModal);

        sortButtonsContainer.addEventListener('click', (e) => {
            const targetButton = e.target.closest('button.sort-btn');
            if (!targetButton) return;

            currentSort.type = targetButton.dataset.sort;
            currentSort.order = targetButton.dataset.order;
            
            sortButtonsContainer.querySelector('.active').classList.remove('active');
            targetButton.classList.add('active');

            filterAndRender();
        });

        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });
        
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modal.classList.contains('open')) {
                closeModal();
            }
        });

        // Запускаем генерацию карточек после загрузки страницы
        window.onload = () => {
            // Единожды вычисляем количество строк для каждого стиха
            allPoems = poems.map(poem => ({
                ...poem,
                // Добавляем вычисление lineCount, как было в вашем коде
                lineCount: poem.text.split('\n').length
            }));
            // Первичная отрисовка с сортировкой по умолчанию
            filterAndRender();
        };
    </script>
</body>
</html>
