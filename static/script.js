document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    const API = "http://127.0.0.1:8000/api";

    // 1. Вкладки
    document.querySelectorAll('.nav-link').forEach(link => {
        link.onclick = () => {
            document.querySelectorAll('.nav-link, .tab-content').forEach(el => el.classList.remove('active'));
            link.classList.add('active');
            document.getElementById(link.dataset.tab + '-tab').classList.add('active');
        };
    });

    // 2. Транслитерация
    const tr = (s) => {
        const dict = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ь':'','ы':'y','ъ':'','э':'e','ю':'yu','я':'ya'};
        return s.toLowerCase().split('').map(c => dict[c] || c).join('');
    };

    const updatePreview = () => {
        const l = tr(document.getElementById('ln').value);
        const f = tr(document.getElementById('fn').value).charAt(0);
        const login = l && f ? `${l}.${f}` : '-';
        document.getElementById('p-login').textContent = login;
        document.getElementById('p-mail').textContent = login !== '-' ? `${login}@company.ru` : '-';
    };

    document.querySelectorAll('input').forEach(i => i.oninput = updatePreview);

    // 3. Загрузка данных
    fetch(`${API}/positions`)
        .then(r => r.json())
        .then(data => {
            const s = document.getElementById('pos');
            s.innerHTML = data.map(p => `<option value="${p}">${p}</option>`).join('');
        });

    // 4. Отправка
    document.getElementById('regForm').onsubmit = async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button');
        btn.style.opacity = 0.5;

        const payload = {
            lastName: document.getElementById('ln').value,
            firstName: document.getElementById('fn').value,
            position: document.getElementById('pos').value,
            mailRequired: document.getElementById('needMail').checked
        };

        try {
            const res = await fetch(`${API}/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            alert("Пользователь создан: " + data.login);
        } catch (err) {
            alert("Ошибка связи с сервером");
        } finally {
            btn.style.opacity = 1;
        }
    };
});