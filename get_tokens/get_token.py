import urllib.parse
import webbrowser
import requests
import urllib3

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Данные приложения из документации
client_id = "J34ZMt9oJv3jnx4KuSf2E5RQTxKmNbR5"
client_secret = 'dJyVVMrC2cPftztWdXHjukt2SY97SZMT'
redirect_uri = "https://localhost"
scope = "biz.api userinfo"
state = "some_unique_state_string"  # Рекомендуется генерировать случайную строку для безопасности
token_url = "https://o2.mail.ru/token"

# Формирование URL для авторизации
params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": scope,
    "state": state
}
auth_url = "https://o2.mail.ru/login?" + urllib.parse.urlencode(params)

print("Перейдите по ссылке для авторизации:")
print(auth_url)

# Автоматически открываем браузер (опционально)
webbrowser.open(auth_url)

# Вставьте скопированный URL сюда
redirect_url = input("Вставьте полный URL из адресной строки браузера: ")

# Извлекаем параметры из URL
parsed = urllib.parse.urlparse(redirect_url)
params = urllib.parse.parse_qs(parsed.query)

# Получаем код авторизации
authorization_code = params.get('code', [None])[0]
state_code = params.get('state', [None])[0]


if authorization_code:
    print(f"Код авторизации получен: {authorization_code}")
else:
    print("Код не найден в URL. Проверьте наличие параметра 'code'")


# Данные для запроса на получение токена
token_data = {
    "grant_type": "authorization_code",
    "code": authorization_code,
    "redirect_uri": redirect_uri
}

# Basic Auth
auth = (client_id, client_secret)
tokens = None  # Инициаизация переменной для токенов
# Отправляем запрос с отключенной проверкой SSL (для разработки!)
try:
    response = requests.post(
        token_url,
        data=token_data,
        auth=auth,
        verify=False,  # Отключаем проверку SSL
        timeout=30
    )

    if response.status_code == 200:
        tokens = response.json()
        print(tokens)
        print("Токены получены успешно!")
        print(f"Access Token: {tokens['access_token']}")
        print(f"Refresh Token: {tokens['refresh_token']}")
    else:
        print(f"Ошибка {response.status_code}: {response.text}")

except requests.exceptions.SSLError as e:
    print(f"SSL ошибка: {e}")
    # Попробуем с отключенной проверкой
    response = requests.post(token_url, data=token_data, auth=auth, verify=False)
    print(f"Ответ с отключенным SSL: {response.text}")

access_token = tokens['access_token']
refresh_token = tokens['refresh_token']


# Тестирование работы токена
def get_user_info_safe(access_token):
    """Безопасное получение информации о пользователе"""
    userinfo_url = f"https://o2.mail.ru/userinfo?access_token={access_token}"

    try:
        response = requests.get(
            userinfo_url,
            verify=False,  # Отключаем проверку SSL
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка API: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None


user_info = get_user_info_safe(access_token)

# Пример использования
if user_info:
    print("✅ Данные пользователя получены:")
    print(f"Имя: {user_info.get('name')}")
    print(f"Email: {user_info.get('email')}")
    print(f"Имя: {user_info.get('first_name')}")
    print(f"Фамилия: {user_info.get('last_name')}")


