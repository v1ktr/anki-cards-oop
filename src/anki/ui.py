from __future__ import annotations

from collections.abc import Callable

from anki.anki import Anki


class TextUI:
    STOP_WORD: str = 'стоп'
    _anki_game: Anki
    _is_running: bool
    _command_definition: list[
        tuple[Callable[..., None], str, Callable[..., bool]]
    ]

    def __init__(self, anki_game: Anki) -> None:
        self._anki_game = anki_game
        self._is_running = False

        has_words: Callable[..., bool] = lambda: len(self._anki_game) > 0

        # (функция, описание, условие видимости)
        self._command_definition = [
            (self.start_game, 'Начать игру', has_words),
            (self.add_words, 'Добавить слова', lambda: True),
            (
                self.train_until_mistake,
                'Тренировка до первой ошибки',
                has_words,
            ),
            (
                self.train_until_time_runs_out,
                'Тренировка на время',
                has_words,
            ),
            (self.find_translation, 'Найти перевод', has_words),
            (self.show_words, 'Показать все слова', has_words),
            (self.stop, 'Выход', lambda: True),
        ]

    def stop(self) -> None:
        """Останавливает главный цикл меню."""
        self._is_running = False

    def get_available_commands(self) -> list[tuple[Callable[..., None], str]]:
        """Возвращает доступные команды для меню."""
        commands: list[tuple[Callable[..., None], str]] = []
        for func, description, is_visible in self._command_definition:
            if is_visible():
                commands.append((func, description))
        return commands

    def start_game(self) -> None:
        """Запускает режим игры с проверкой переводов.

        Пользователь получает случайные слова и вводит их переводы.
        Игра продолжается до ввода ключевого слова STOP_WORD.
        """
        print(f'Для выхода из игры введите "{self.STOP_WORD}".')

        while True:
            try:
                word = self._anki_game.get_random_word()
            except ValueError as error:
                print(error)
                break

            print(f'Переведите слово: {word}')

            translation = input('Ваш перевод: ')

            if translation.strip().lower() == self.STOP_WORD:
                break

            if self._anki_game.check_translation(word, translation):
                print('Правильно!')
            else:
                correct_translation = self._anki_game.get_translation(word)
                print(
                    f'Неправильно. Правильный перевод: {correct_translation}'
                )

    def add_words(self) -> None:
        """Позволяет пользователю добавлять слова и переводы.

        Добавление продолжается до ввода ключевого слова STOP_WORD.
        """
        print(f'Для выхода введите "{self.STOP_WORD}".')

        while True:
            word = input('Введите слово: ')

            if word.strip().lower() == self.STOP_WORD:
                break

            translation = input('Введите перевод: ')

            if translation.strip().lower() == self.STOP_WORD:
                break

            self._anki_game.add_word(word, translation)

            print('Слово добавлено.')

    def train_until_mistake(self) -> None:
        """Запускает тренировку до первой ошибки.

        После завершения выводит число правильных ответов и время игры.
        """
        print(
            f'Режим: тренировка до первой ошибки. '
            f'Для выхода введите "{self.STOP_WORD}".'
        )
        training_session = self._anki_game.start_zero_mistakes_training()

        while True:
            word = training_session.get_random_word()
            print(f'Переведите слово: {word}')

            translation = input('Ваш перевод: ')
            if translation.strip().lower() == self.STOP_WORD:
                training_session.end_session()
                break

            is_correct = training_session.check_translation(word, translation)
            if is_correct:
                print('Правильно!')
            else:
                print(
                    'Неправильно. Правильный перевод:',
                    self._anki_game.get_translation(word),
                )
                break

        user_stat = training_session.get_stat()
        print(f'Правильных ответов: {user_stat["correct_answers"]}')
        print(f'Время игры: {user_stat["total_time"]}')

    def train_until_time_runs_out(self) -> None:
        """Запускает тренировку с ограничением по времени.

        После завершения выводит число правильных ответов и время игры.
        """
        print(
            f'Режим: тренировка на время. '
            f'Для выхода введите "{self.STOP_WORD}".'
        )
        time_limit = float(input('Введите время тренировки в секундах: '))
        training_session = self._anki_game.start_time_limited_training(
            time_limit
        )

        while training_session.active:
            word = training_session.get_random_word()
            print(f'Переведите слово: {word}')

            translation = input('Ваш перевод: ')
            if translation.strip().lower() == self.STOP_WORD:
                training_session.end_session()
                break

            is_correct = training_session.check_translation(word, translation)
            if is_correct:
                print('Правильно!')
            else:
                print(
                    'Неправильно. Правильный перевод:',
                    self._anki_game.get_translation(word),
                )

        user_stat = training_session.get_stat()
        print(f'Правильных ответов: {user_stat["correct_answers"]}')
        print(f'Время игры: {user_stat["total_time"]}')

    def show_words(self) -> None:
        """Выводит все слова и их переводы.

        Каждая пара выводится в формате:
        «слово - перевод».
        """
        print(f'Всего слов: {len(self._anki_game)}')

        for word, translation in self._anki_game:
            print(f'{word} - {translation}')

    def find_translation(self) -> None:
        """Ищет перевод слова в словаре игры."""
        word = input('Введите слово: ')

        if word in self._anki_game:
            translation = self._anki_game.get_translation(word)
            print(f'Перевод: {translation}')
        else:
            print(f'Слово "{word}" отсутствует в словаре.')

    def main_loop(self) -> None:
        """Главный цикл с динамическим меню."""
        self._is_running = True

        while self._is_running:
            menu_choices: list[str] = []
            commands: dict[str, Callable[..., None]] = {}

            for index, (func, description) in enumerate(
                self.get_available_commands(), 1
            ):
                menu_choices.append(f'{index}. {description}')
                commands[str(index)] = func

            print('Меню:\n' + '\n'.join(menu_choices))
            choice = input('Выберите пункт: ')

            if choice in commands:
                commands[choice]()
            else:
                print('Неверный пункт меню')
            print()
