document.addEventListener('DOMContentLoaded', () => {
    // Инициализация иконок Lucide
    lucide.createIcons();

    const API = "/api";
    let currentPassword = generateSecurePassword();

    // Инициализация приложения
    initializeApp();

    // ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

    function initializeApp() {
        setupNavigation();
        loadPositions();
        loadStatistics();
        setupEventListeners();
        updatePreview();
    }

    function setupNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            // Удаляем active со всех вкладок и ссылок
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

            // Добавляем active к текущей ссылке
            this.classList.add('active');

            // Получаем data-tab атрибут
            const tabName = this.getAttribute('data-tab');

            if (tabName) {
                // Находим соответствующую вкладку
                const tabId = tabName + '-tab';
                const tabElement = document.getElementById(tabId);

                if (tabElement) {
                    tabElement.classList.add('active');
                } else {
                    console.warn(`Вкладка с ID "${tabId}" не найдена`);

                    // Показываем первую вкладку по умолчанию
                    const firstTab = document.querySelector('.tab-content');
                    if (firstTab) {
                        firstTab.classList.add('active');
                    }
                }
            }
        });
    });

    // Активируем первую вкладку при загрузке
    const firstLink = document.querySelector('.nav-link');
    const firstTab = document.querySelector('.tab-content');

    if (firstLink && firstTab) {
        firstLink.classList.add('active');
        firstTab.classList.add('active');
    }
}

    function setupEventListeners() {
        // Поля ввода для предпросмотра
        ['lastName', 'firstName', 'middleName'].forEach(id => {
            document.getElementById(id).addEventListener('input', updatePreview);
        });

        // Основная форма регистрации
        document.getElementById('regForm').addEventListener('submit', handleRegistration);

        // Форма создания почты
        document.getElementById('mailForm').addEventListener('submit', handleMailCreation);

        // Генерация пароля
        document.getElementById('mailPassword').value = generateSecurePassword();
    }

    // ==================== РАБОТА С API ====================

    async function loadPositions() {
        try {
            const response = await fetch(`${API}/positions`);
            if (!response.ok) throw new Error('Ошибка загрузки должностей');

            const data = await response.json();
            const select = document.getElementById('position');

            if (data.positions && Array.isArray(data.positions)) {
                data.positions.forEach(position => {
                    const option = document.createElement('option');
                    option.value = position;
                    option.textContent = position;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки должностей:', error);
            showNotification('Ошибка загрузки списка должностей', 'error');
        }
    }

    async function loadStatistics() {
        try {
            // Здесь можно загружать статистику с сервера
            // Для демо - случайные числа
            document.getElementById('users-today').textContent = Math.floor(Math.random() * 10);
            document.getElementById('users-week').textContent = Math.floor(Math.random() * 50);
            document.getElementById('users-total').textContent = Math.floor(Math.random() * 200);
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }

    // ==================== ОБРАБОТКА ФОРМ ====================

    async function handleRegistration(e) {
        e.preventDefault();

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalContent = submitBtn.innerHTML;

        // Показываем загрузку
        submitBtn.innerHTML = '<i data-lucide="loader" class="spin"></i> Создание...';
        submitBtn.disabled = true;

        try {
            // Собираем данные
            const userData = {
                lastName: document.getElementById('lastName').value.trim(),
                firstName: document.getElementById('firstName').value.trim(),
                middleName: document.getElementById('middleName').value.trim(),
                position: document.getElementById('position').value,
                department: document.getElementById('department').value,
                adRequired: document.getElementById('adRequired').checked,
                mailRequired: document.getElementById('mailRequired').checked,
                bitwardenRequired: document.getElementById('bitwardenRequired').checked
            };

            // Валидация
            if (!userData.lastName || !userData.firstName || !userData.position) {
                throw new Error('Заполните все обязательные поля');
            }

            // Отправка на сервер
            const response = await fetch(`${API}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();

            if (response.ok) {
                showNotification(
                    `✅ Сотрудник создан успешно!<br>
                    Логин: ${result.login}<br>
                    Email: ${result.email || 'Не создан'}<br>
                    Статус: ${result.message}`,
                    'success'
                );

                // Показываем детали в модальном окне
                showResultModal(result);

                // Очищаем форму
                setTimeout(() => clearForm(), 1000);

                // Обновляем статистику
                loadStatistics();
            } else {
                throw new Error(result.detail || result.message || 'Ошибка сервера');
            }

        } catch (error) {
            console.error('Ошибка регистрации:', error);
            showNotification(`❌ Ошибка: ${error.message}`, 'error');
        } finally {
            // Восстанавливаем кнопку
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled = false;
            lucide.createIcons();
        }
    }

    async function handleMailCreation(e) {
        e.preventDefault();

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalContent = submitBtn.innerHTML;

        // Показываем загрузку
        submitBtn.innerHTML = '<i data-lucide="loader" class="spin"></i> Создание почты...';
        submitBtn.disabled = true;

        try {
            const mailData = {
                lastName: document.getElementById('mailLastName').value.trim(),
                firstName: document.getElementById('mailFirstName').value.trim(),
                login: document.getElementById('mailLogin').value.trim(),
                password: document.getElementById('mailPassword').value,
                domain: document.getElementById('mailDomain').value
            };

            // Валидация
            if (!mailData.lastName || !mailData.firstName || !mailData.login || !mailData.password) {
                throw new Error('Заполните все обязательные поля');
            }

            // Отправка на специальный endpoint для создания только почты
            const response = await fetch(`${API}/create-mail-only`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(mailData)
            });

            const result = await response.json();

            if (response.ok) {
                showNotification(
                    `✅ Почтовый ящик создан успешно!<br>
                    Email: ${mailData.login}@${mailData.domain}<br>
                    Статус: ${result.message}`,
                    'success'
                );

                // Очищаем форму почты
                resetMailForm();
            } else {
                throw new Error(result.detail || result.message || 'Ошибка сервера');
            }

        } catch (error) {
            console.error('Ошибка создания почты:', error);
            showNotification(`❌ Ошибка: ${error.message}`, 'error');
        } finally {
            // Восстанавливаем кнопку
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled = false;
            lucide.createIcons();
        }
    }

    // ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

    function updatePreview() {
        const lastName = document.getElementById('lastName').value.trim();
        const firstName = document.getElementById('firstName').value.trim();

        if (lastName && firstName) {
            const login = generateLogin(lastName, firstName);
            document.getElementById('preview-login').textContent = login;
            document.getElementById('preview-email').textContent = `${login}@company.ru`;
        } else {
            document.getElementById('preview-login').textContent = '-';
            document.getElementById('preview-email').textContent = '-';
        }
    }

    function generateLogin(lastName, firstName) {
        // Транслитерация и создание логина
        const translitDict = {
            'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e',
            'ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
            'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
            'ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ь':'',
            'ы':'y','ъ':'','э':'e','ю':'yu','я':'ya'
        };

        const translit = (text) => {
            return text.toLowerCase().split('').map(c => translitDict[c] || c).join('');
        };

        return `${translit(lastName)}.${translit(firstName).charAt(0)}`;
    }

    function generatePassword() {
        currentPassword = generateSecurePassword();
        document.getElementById('preview-password').textContent = currentPassword;
        showNotification('Пароль сгенерирован', 'info');
    }

    function generateSecurePassword(length = 12) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
        let password = '';
        for (let i = 0; i < length; i++) {
            password += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return password;
    }

    function clearForm() {
        document.getElementById('regForm').reset();
        updatePreview();
        showNotification('Форма очищена', 'info');
    }

    function resetMailForm() {
        document.getElementById('mailForm').reset();
        document.getElementById('mailPassword').value = generateSecurePassword();
    }

    function togglePassword(inputId) {
        const input = document.getElementById(inputId);
        const icon = input.nextElementSibling.querySelector('i');

        if (input.type === 'password') {
            input.type = 'text';
            icon.setAttribute('data-lucide', 'eye-off');
        } else {
            input.type = 'password';
            icon.setAttribute('data-lucide', 'eye');
        }
        lucide.createIcons();
    }

    // ==================== МОДАЛЬНЫЕ ОКНА И УВЕДОМЛЕНИЯ ====================

    function showNotification(message, type = 'info') {
        // Создаем контейнер если его нет
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i data-lucide="x"></i>
            </button>
        `;

        container.appendChild(notification);
        lucide.createIcons();

        // Автоудаление
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    function showResultModal(result) {
        const modal = document.getElementById('resultModal');
        const content = document.getElementById('modalContent');

        let html = `
            <div class="result-summary">
                <h4>Результаты создания:</h4>
                <ul class="result-list">
                    <li class="result-success">
                        <i data-lucide="check-circle"></i>
                        <span>Пользователь зарегистрирован</span>
                        <code>${result.login}</code>
                    </li>
        `;

        if (result.email) {
            html += `
                <li class="result-success">
                    <i data-lucide="check-circle"></i>
                    <span>Почтовый ящик создан</span>
                    <code>${result.email}</code>
                </li>
            `;
        }

        html += `
                    <li class="result-info">
                        <i data-lucide="info"></i>
                        <span>Данные сохранены в БД</span>
                    </li>
                </ul>

                <div class="result-actions">
                    <button class="btn-outline" onclick="copyToClipboard('${result.login}')">
                        <i data-lucide="copy"></i>
                        Копировать логин
                    </button>
                    ${result.email ? `
                    <button class="btn-outline" onclick="copyToClipboard('${result.email}')">
                        <i data-lucide="copy"></i>
                        Копировать email
                    </button>
                    ` : ''}
                </div>
            </div>
        `;

        content.innerHTML = html;
        modal.classList.add('active');
        lucide.createIcons();
    }

    function closeModal() {
        document.getElementById('resultModal').classList.remove('active');
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Скопировано в буфер обмена', 'success');
        });
    }

    // ==================== БЫСТРЫЕ ДЕЙСТВИЯ ====================

    function openMailForm() {
        // Переключаемся на вкладку почты
        document.querySelector('[data-tab="mail"]').click();

        // Автозаполняем форму почты данными из основной формы
        const lastName = document.getElementById('lastName').value;
        const firstName = document.getElementById('firstName').value;

        if (lastName && firstName) {
            const login = generateLogin(lastName, firstName);
            document.getElementById('mailLastName').value = lastName;
            document.getElementById('mailFirstName').value = firstName;
            document.getElementById('mailLogin').value = login;
        }

        showNotification('Переход в форму создания почтового ящика', 'info');
    }

    async function testConnections() {
        try {
            const response = await fetch(`${API}/health`);
            const data = await response.json();

            if (response.ok) {
                showNotification('✅ Все системы доступны', 'success');
            } else {
                showNotification('⚠️ Проблемы с подключением', 'error');
            }
        } catch (error) {
            showNotification('❌ Ошибка подключения к серверу', 'error');
        }
    }

    async function searchEmployee() {
        const query = document.getElementById('searchEmployee').value.trim();
        if (!query) {
            showNotification('Введите поисковый запрос', 'warning');
            return;
        }

        try {
            const response = await fetch(`${API}/search?q=${encodeURIComponent(query)}`);
            const employees = await response.json();

            const container = document.getElementById('employeeList');
            if (employees.length === 0) {
                container.innerHTML = '<div class="empty-state">Сотрудники не найдены</div>';
                return;
            }

            let html = '<div class="employee-grid">';
            employees.forEach(emp => {
                html += `
                    <div class="employee-card">
                        <div class="employee-info">
                            <h4>${emp.lastName} ${emp.firstName}</h4>
                            <small>${emp.position || 'Должность не указана'}</small>
                            <div class="employee-login">${emp.login || 'Логин не указан'}</div>
                        </div>
                        <button class="btn-small" onclick="addMailToEmployee('${emp.id}', '${emp.login}')">
                            <i data-lucide="mail-plus"></i>
                            Добавить почту
                        </button>
                    </div>
                `;
            });
            html += '</div>';

            container.innerHTML = html;
            lucide.createIcons();

        } catch (error) {
            console.error('Ошибка поиска:', error);
            showNotification('Ошибка при поиске сотрудников', 'error');
        }
    }

    // Делаем функции глобальными для использования в onclick
    window.generatePassword = generatePassword;
    window.clearForm = clearForm;
    window.openMailForm = openMailForm;
    window.testConnections = testConnections;
    window.searchEmployee = searchEmployee;
    window.resetMailForm = resetMailForm;
    window.togglePassword = togglePassword;
    window.closeModal = closeModal;
    window.copyToClipboard = copyToClipboard;

    // Добавляем стили для уведомлений и анимаций
    const style = document.createElement('style');
    style.textContent = `
        .spin {
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
        }

        .notification {
            padding: 16px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .notification.success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }

        .notification.error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }

        .notification.info {
            background: #dbeafe;
            color: #1e40af;
            border: 1px solid #93c5fd;
        }

        .notification.warning {
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }

        .notification-content {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        }

        .notification-close {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
            opacity: 0.7;
        }

        .notification-close:hover {
            opacity: 1;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
        }

        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .modal-close {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
        }

        .modal-body {
            padding: 20px;
        }

        .modal-footer {
            padding: 20px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: flex-end;
        }

        .result-list {
            list-style: none;
            padding: 0;
            margin: 20px 0;
        }

        .result-list li {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 6px;
        }

        .result-success {
            background: #d1fae5;
            color: #065f46;
        }

        .result-error {
            background: #fee2e2;
            color: #991b1b;
        }

        .result-info {
            background: #dbeafe;
            color: #1e40af;
        }

        .result-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    `;
    document.head.appendChild(style);
});