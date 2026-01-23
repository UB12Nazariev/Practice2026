import secrets
import string


def generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def generate_login(
    last_name: str,
    first_name: str,
    middle_name: str | None = None
) -> str:
    def normalize(value: str) -> str:
        return (
            value
            .lower()
            .replace("ь", "")
            .replace("ъ", "")
        )

    TRANSLIT_MAP = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l',
        'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sch',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }

    INITIAL_TRANSLIT_MAP = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'e', 'ж': 'z', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l',
        'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c',
        'ш': 's', 'щ': 's',
        'ы': 'y', 'э': 'e',
        'ю': 'y', 'я': 'y'
    }

    def translit(value: str) -> str:
        return "".join(TRANSLIT_MAP.get(ch, ch) for ch in value)

    def translit_initial(ch: str) -> str:
        return INITIAL_TRANSLIT_MAP.get(ch, ch)

    last = translit(normalize(last_name))
    first_initial = translit_initial(normalize(first_name)[0])

    login_parts = [last, first_initial]

    if middle_name and middle_name.strip():
        middle_initial = translit_initial(normalize(middle_name)[0])
        login_parts.append(middle_initial)

    return ".".join(login_parts)

