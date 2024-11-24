import random
import string

# Функция для генерации случайного ключа
def generate_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
