import random
import sys
import time


STOP_WORD = 'СТОП'


def _is_stop(text: str) -> bool:
    """Проверяет, является ли ввод завершающим словом."""
    return text.strip().lower() == STOP_WORD.lower()


def load_words(filename='words.txt'):
    """Загружает словарь из файла

    Строки без запятой или с несколькими запятыми игнорируются.
    При отсутствии файла программа завершается с кодом 1.
    """
    try:
        with open(filename, encoding='utf-8') as file:
            words = {}
            for line in file:
                parts = line.strip().split(',')
                if len(parts) != 2:
                    continue
                word, translation = parts[0].strip(), parts[1].strip()
                if word:
                    words[word] = translation
            return words
    except FileNotFoundError:
        print(f'Файл {filename} не найден.')
        sys.exit(1)


def print_statistics(score, total_time):
    """Выводит итоговую статистику по завершении игры:
    - общее количество правильных ответов
    - общее затраченное время
    - среднее время на ответ.
    """
    print(f'Ваш итоговый счет: {score}')
    if score > 0:
        average = f'{total_time / score:.2f} сек.'
    else:
        average = '—'
    print(
        f'Время игры: {total_time:.2f} секунд '
        f'(среднее время: {average})'
    )


def ask_and_check(word, correct):
    """Спрашивает перевод слова и проверяет ответ пользователя.

    Возвращает кортеж (нужен_выход, ответ_верный, время_ответа).
    """
    print(f'Ваше слово: {word}')
    start = time.time()
    answer = input('Ваш перевод: ')
    end = time.time()
    if _is_stop(answer):
        return True, False, 0.0
    answer_time = end - start
    is_correct = answer.strip().lower() == correct.strip().lower()
    return False, is_correct, answer_time


def start_game(words):
    """Запускает режим обычной тренировки"""
    if not words:
        print('В словаре нет слов для игры.')
        return

    print('Чтобы закончить, введите СТОП')
    score = 0
    total_time = 0.0
    keys = list(words)

    while True:
        word = random.choice(keys)
        is_stop, is_correct, answer_time = ask_and_check(word, words[word])
        if is_stop:
            print('Спасибо за игру!')
            break
        total_time += answer_time
        if is_correct:
            score += 1
            print(f'Верно! Время на ответ: {answer_time:.2f} секунд')
        else:
            print(
                f'Неправильно, правильный ответ: {words[word]} '
                f'(Время на ответ: {answer_time:.2f} секунд)'
            )

    print_statistics(score, total_time)


def train_until_mistake(words):
    """Запускает режим «до первой ошибки»"""
    print(
        'Режим: Игра до первой ошибки! '
        'Чтобы выйти вручную, введите СТОП'
    )
    if not words:
        print('В словаре нет слов для игры.')
        return

    score = 0
    total_time = 0.0
    keys = list(words)

    while True:
        word = random.choice(keys)
        is_stop, is_correct, answer_time = ask_and_check(word, words[word])
        if is_stop:
            print('Выход из режима по запросу пользователя.')
            break
        total_time += answer_time
        if is_correct:
            score += 1
            print(
                f'Верно! Всего очков: {score} '
                f'(ответ за {answer_time:.2f} секунд)'
            )
        else:
            print(
                f'Ошибка! Неверно. Правильный ответ: {words[word]}'
            )
            break

    print_statistics(score, total_time)


def add_words(words):
    """Добавляет новые слова"""
    print('Чтобы закончить, введите СТОП')
    while True:
        word = input('Введите слово: ')
        if _is_stop(word):
            break
        translation = input('Введите перевод: ')
        if _is_stop(translation):
            break
        words[word.strip()] = translation.strip()


def show_all_words(words):
    """Отображает весь словарь"""
    print(
        '; '.join(
            f'{word} - {translation}'
            for word, translation in words.items()
        )
    )


def save_words(words, filename='words.txt'):
    """Сохраняет словарь"""
    with open(filename, 'w', encoding='utf-8') as file:
        for word, translation in words.items():
            file.write(f'{word}, {translation}\n')
    print(f'Было сохранено {len(words)} слов в файл {filename}')


def main():
    """Запускает главное меню тренажёра словарного запаса."""
    words = load_words()
    print(
        f'Было загружено {len(words)} слов из файла words.txt'
    )

    menu = '''Меню:
    1. Начать игру
    2. Добавить слова
    3. Тренировка до первой ошибки
    4. Вывод всех слов
    5. Выход
    '''

    while True:
        print(menu)
        choice = input('Пункт меню: ').strip()
        if choice == '1':
            start_game(words)
        elif choice == '2':
            add_words(words)
        elif choice == '3':
            train_until_mistake(words)
        elif choice == '4':
            show_all_words(words)
        elif choice == '5':
            save_words(words)
            sys.exit()
        else:
            print('Неизвестный пункт меню')


if __name__ == '__main__':
    main()
