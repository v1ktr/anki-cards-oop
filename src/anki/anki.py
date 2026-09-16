from __future__ import annotations

import random
import time
from collections.abc import Iterator
from typing import TypedDict


class SessionStats(TypedDict):
    """Статистика тренировочной сессии."""

    correct_answers: int
    total_time: float


class TrainingSession:
    """Базовый класс тренировочной сессии.

    Хранит состояние тренировки и делегирует работу со словарём
    экземпляру Anki.
    """

    def __init__(self, anki: 'Anki') -> None:
        self.active: bool = True

        self._anki: Anki = anki
        self._start_time: float = time.time()
        self._end_time: float = self._start_time
        self._user_score: int = 0
        self._last_word: str | None = None

    def get_random_word(self) -> str:
        """Возвращает случайное слово из словаря игры.

        Returns:
            Случайное слово из словаря.

        Raises:
            ValueError: Если тренировочная сессия не активна.
        """
        if not self.active:
            raise ValueError('Тренировочная сессия не активна.')

        word = self._anki.get_random_word()
        self._last_word = word
        return word

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод слова в рамках тренировки.

        Args:
            word: Проверяемое слово.
            translation: Перевод, введённый пользователем.

        Returns:
            True, если перевод правильный, иначе False.

        Raises:
            ValueError: Если тренировочная сессия не активна.
            ValueError: Если проверяется не последнее выданное слово
                или повторно то же самое слово.
        """
        if not self.active:
            raise ValueError('Тренировочная сессия не активна.')

        normalized_word = self._anki.normalize_word(word)

        if self._last_word is None or normalized_word != self._last_word:
            raise ValueError('Работаем только с последним выданным словом.')

        self._last_word = None
        return self._anki.check_translation(word, translation)

    def end_session(self) -> None:
        """Завершает тренировочную сессию.

        Raises:
            ValueError: Если тренировочная сессия не активна.
        """
        if not self.active:
            raise ValueError('Тренировочная сессия не активна.')

        self.active = False
        self._end_time = time.time()
        self._anki.end_session()

    def get_stat(self) -> SessionStats:
        """Возвращает статистику текущей тренировочной сессии.

        Returns:
            Словарь с количеством правильных ответов и временем игры.
        """
        if self.active:
            total_time = time.time() - self._start_time
        else:
            total_time = self._end_time - self._start_time

        return {
            'correct_answers': self._user_score,
            'total_time': total_time,
        }


class ZeroMistakesTraining(TrainingSession):
    """Тренировка, которая завершается после первой ошибки."""

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод и завершает сессию при ошибке.

        Args:
            word: Проверяемое слово.
            translation: Перевод, введённый пользователем.

        Returns:
            True, если перевод правильный, иначе False.
        """
        is_correct = super().check_translation(word, translation)

        if is_correct:
            self._user_score += 1
        else:
            self.end_session()

        return is_correct


class TimeLimitedTraining(TrainingSession):
    """Тренировка с ограничением по времени."""

    def __init__(self, anki: 'Anki', time_limit: float = 60.0) -> None:
        super().__init__(anki)
        self._time_limit: float = time_limit

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод и завершает сессию по истечении времени.

        Последний ответ принимается даже после истечения лимита:
        время проверяется после ответа.

        Args:
            word: Проверяемое слово.
            translation: Перевод, введённый пользователем.

        Returns:
            True, если перевод правильный, иначе False.
        """
        is_correct = super().check_translation(word, translation)

        if is_correct:
            self._user_score += 1

        if time.time() - self._start_time >= self._time_limit:
            self.end_session()

        return is_correct


class Anki:
    """Предоставляет функциональность для работы со словарём Anki-карточек.

    Класс хранит пары слов и их переводов, нормализует добавляемые
    слова и предоставляет методы для управления словарём.
    """

    app_version: str = '0.0.1'
    _words: dict[str, str]
    _session_active: bool

    def __init__(self, *, words: dict[str, str] | None = None) -> None:
        words = words if words is not None else {}

        if not isinstance(words, dict):
            raise ValueError('Значением параметра `words` должен быть словарь')

        self._words = self._normalize_dict(words)
        self._session_active = False

    def _normalize_dict(self, words: dict[str, str]) -> dict[str, str]:
        """Возвращает нормализованную копию словаря слов и переводов.

        Args:
            words: Словарь, содержащий слова и их переводы.

        Returns:
            Новый словарь с нормализованными ключами и значениями.

        Raises:
            ValueError: Если переданное значение не является словарём
                или содержит нестроковые ключи либо значения.
        """
        if not isinstance(words, dict):
            raise ValueError('words должен быть словарём.')

        normalized_words: dict[str, str] = {}

        for word, translation in words.items():
            normalized_word = self.normalize_word(word)
            normalized_translation = self.normalize_word(translation)
            normalized_words[normalized_word] = normalized_translation

        return normalized_words

    @staticmethod
    def normalize_word(word: str) -> str:
        """Нормализует слово перед сохранением в словарь.

        Удаляет пробелы в начале и конце строки и приводит слово
        к нижнему регистру.

        Args:
            word: Слово, которое необходимо нормализовать.

        Returns:
            Нормализованное слово в виде строки.

        Raises:
            ValueError: Если переданное значение не является строкой.
        """
        if not isinstance(word, str):
            raise ValueError('Слово должно быть строкой.')

        return word.strip().lower()

    def add_word(self, word: str, translation: str) -> None:
        """Добавляет слово и его перевод в словарь.

        Перед добавлением слово и перевод нормализуются с помощью
        метода normalize_word.

        Args:
            word: Слово для добавления в словарь.
            translation: Перевод слова.

        Raises:
            ValueError: Если слово или перевод не являются строками.
        """
        if not isinstance(word, str):
            raise ValueError('Слово должно быть строкой.')

        if not isinstance(translation, str):
            raise ValueError('Перевод должен быть строкой.')

        word = self.normalize_word(word)
        translation = self.normalize_word(translation)

        self._words[word] = translation

    @property
    def words(self) -> dict[str, str]:
        """Копия словаря слов и переводов.

        Геттер возвращает копию, чтобы внешний код не мог напрямую
        изменить внутренние данные объекта.
        """
        return self._words.copy()

    @words.setter
    def words(self, value: dict[str, str]) -> None:
        """Заменяет словарь слов нормализованной копией `value`.

        Args:
            value: Словарь слов и переводов.

        Raises:
            ValueError: Если переданное значение не является словарём
                или содержит нестроковые ключи либо значения.
            ValueError: Если тренировка активна.
        """
        if self._session_active:
            raise ValueError(
                'Полное изменение слов недопустимо в ходе активной тренировки'
            )

        self._words = self._normalize_dict(value)

    def __contains__(self, word: object) -> bool:
        """Проверяет наличие слова в словаре Anki.

        Перед проверкой слово нормализуется с помощью метода
        normalize_word.

        Args:
            word: Слово, наличие которого необходимо проверить.

        Returns:
            True, если нормализованное слово есть в словаре,
            иначе False.

        Raises:
            ValueError: Если word не является строкой.
        """
        if not isinstance(word, str):
            raise ValueError('Слово должно быть строкой.')

        word = self.normalize_word(word)
        return word in self._words

    def __iter__(self) -> Iterator[tuple[str, str]]:
        """Возвращает итератор по парам «слово — перевод».

        Returns:
            Итератор кортежей (слово, перевод).
        """
        return iter(self._words.items())

    def __len__(self) -> int:
        """Возвращает количество слов в словаре.

        Returns:
            Число слов в игре.
        """
        return len(self._words)

    def __str__(self) -> str:
        """Возвращает строковое представление объекта Anki.

        Returns:
            Строку с количеством слов в словаре.
        """
        return f'Anki: {len(self)} слов.'

    def get_random_word(self) -> str:
        """Возвращает случайное слово из словаря.

        Returns:
            Случайное слово из словаря.

        Raises:
            ValueError: Если словарь не содержит слов.
        """
        if not self._words:
            raise ValueError('В словаре нет слов для игры.')

        return random.choice(list(self._words))

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет правильность перевода слова.

        Перед проверкой слово и перевод нормализуются.

        Args:
            word: Проверяемое слово.
            translation: Перевод, введённый пользователем.

        Returns:
            True, если перевод правильный, иначе False.

        Raises:
            ValueError: Если указанное слово отсутствует в словаре.
        """
        word = self.normalize_word(word)
        translation = self.normalize_word(translation)

        if word not in self._words:
            raise ValueError(f'Слово "{word}" отсутствует в словаре.')

        return self._words[word] == translation

    def get_translation(self, word: str) -> str:
        """Возвращает перевод указанного слова.

        Перед поиском слово нормализуется.

        Args:
            word: Слово, для которого нужно получить перевод.

        Returns:
            Перевод слова.

        Raises:
            ValueError: Если указанное слово отсутствует в словаре.
        """
        word = self.normalize_word(word)

        if word not in self._words:
            raise ValueError(f'Слово "{word}" отсутствует в словаре.')

        return self._words[word]

    def start_zero_mistakes_training(self) -> ZeroMistakesTraining:
        """Начинает тренировку до первой ошибки.

        Returns:
            Объект тренировочной сессии ZeroMistakesTraining.

        Raises:
            RuntimeError: Если тренировка уже начата.
        """
        if self._session_active:
            raise RuntimeError('Нельзя начать тренировку, если она уже начата')

        self._session_active = True
        return ZeroMistakesTraining(self)

    def start_time_limited_training(
        self, time_limit: float = 60.0
    ) -> TimeLimitedTraining:
        """Начинает тренировку с ограничением по времени.

        Args:
            time_limit: Лимит времени тренировки в секундах.

        Returns:
            Объект тренировочной сессии TimeLimitedTraining.

        Raises:
            RuntimeError: Если тренировка уже начата.
        """
        if self._session_active:
            raise RuntimeError('Нельзя начать тренировку, если она уже начата')

        self._session_active = True
        return TimeLimitedTraining(self, time_limit)

    def end_session(self) -> None:
        """Завершает текущую тренировочную сессию.

        Raises:
            RuntimeError: Если тренировочная сессия не активна.
        """
        if not self._session_active:
            raise RuntimeError(
                'Нельзя завершить неактивную сессию тренировки'
            )

        self._session_active = False
