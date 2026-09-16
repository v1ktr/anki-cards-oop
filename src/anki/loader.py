from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, Self, TextIO

import requests
from requests import Response


class LoaderProtocol(Protocol):
    """Структурный интерфейс загрузчика словаря Anki.

    Подходит и для файловых загрузчиков, и для сетевого:
    достаточно методов `load_words`, `save_words` и фабрики `from_source`.
    """

    def load_words(self) -> dict[str, str]:
        ...

    def save_words(self, words: dict[str, str]) -> None:
        ...

    @classmethod
    def from_source(cls, source: str) -> Self:
        ...


class LoaderRegistry:
    """Реестр загрузчиков, регистрируемых декоратором со стратегией применимости."""

    _registry: dict[type[LoaderProtocol], Callable[[str], bool]]

    def __init__(self) -> None:
        self._registry = {}

    def register(
        self,
        predicate: Callable[[str], bool],
    ) -> Callable[[type[LoaderProtocol]], type[LoaderProtocol]]:
        """Регистрирует класс загрузчика и стратегию его выбора."""

        def decorator(cls: type[LoaderProtocol]) -> type[LoaderProtocol]:
            self._registry[cls] = predicate
            return cls

        return decorator

    def get_loader(self, source: str) -> type[LoaderProtocol]:
        """Находит подходящий загрузчик для `source`."""
        for loader_cls, predicate in self._registry.items():
            if predicate(source):
                return loader_cls

        raise ValueError(f'Неизвестный источник: {source}')


loader_registry = LoaderRegistry()


class BaseFileLoader:
    """Базовый загрузчик словаря Anki из файла.

    Содержит общую логику открытия, чтения и записи файла.
    Формат данных реализуется в классах-наследниках.
    """

    DEFAULT_FILE_PATH: str = './words.txt'
    _file_path: Path

    def __init__(self, *, file_path: str | Path | None = None) -> None:
        if file_path is None:
            file_path = self.DEFAULT_FILE_PATH

        self._file_path = Path(file_path)

        if self._file_path.exists() and self._file_path.is_dir():
            raise ValueError(
                f'Путь {file_path} является директорией, а должен быть файлом'
            )

    def load_words(self) -> dict[str, str]:
        """Загружает слова и переводы из файла.

        Если файл отсутствует, возвращается пустой словарь.
        Формат строк определяется методом `_load_from_file`
        в классе-наследнике.

        Returns:
            Словарь, содержащий слова и соответствующие им переводы.
        """
        if not self._file_path.exists():
            return {}

        encoding = self._detect_encoding()

        with self._file_path.open('r', encoding=encoding) as file_object:
            return self._load_from_file(file_object)

    def save_words(self, words: dict[str, str]) -> None:
        """Сохраняет словарь слов и переводов в файл.

        Формат записи определяется методом `_save_to_file`
        в классе-наследнике.

        Args:
            words: Словарь, содержащий слова и соответствующие им переводы.

        Raises:
            ValueError: Если переданное значение не является словарём.
        """
        if not isinstance(words, dict):
            raise ValueError(
                'Значением параметра `words` должен быть словарь'
            )

        encoding = self._detect_encoding()

        with self._file_path.open(
            'w', encoding=encoding, newline='\n'
        ) as file_object:
            self._save_to_file(words, file_object)

    def _detect_encoding(self) -> str:
        """Определяет кодировку существующего файла или выбирает utf-8."""
        if not self._file_path.exists():
            return 'utf-8'

        raw = self._file_path.read_bytes()

        if not raw:
            return 'utf-8'

        try:
            raw.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            return 'cp1251'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        """Реализует логику загрузки данных определённого формата из `file_object`.

        Метод должен быть переопределён в наследниках.

        Parameters
        ----------
        file_object : FileLike
            FileLike объект, из которого идёт чтение данных

        Returns
        -------
        dict
            Словарь с загруженными словами
        """
        raise NotImplementedError

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        """Реализует логику сохранения слов в определённом формате в файл `file_object`.

        Метод должен быть переопределён в наследниках.

        Parameters
        ----------
        words : dict
            Словарь с словами и переводами
        file_object : FileLike
            FileLike объект, в который идёт запись данных

        Returns
        -------
        None
        """
        raise NotImplementedError

    @classmethod
    def from_source(cls, source: str) -> Self:
        """Создаёт загрузчик из пути к локальному файлу."""
        return cls(file_path=source)


def is_txt_source(source: str) -> bool:
    return source.endswith('.txt') and not source.startswith('http')


def is_tsv_source(source: str) -> bool:
    return source.endswith('.tsv') and not source.startswith('http')


def is_json_source(source: str) -> bool:
    return source.endswith('.json') and not source.startswith('http')


def is_http_source(source: str) -> bool:
    return source.startswith('http')


@loader_registry.register(is_txt_source)
class TextFileLoader(BaseFileLoader):
    """
    Реализует логику загрузки слов из текстового файла и логику сохранения
    слов в текстовый файл.

    Формат записи: "слово,перевод"
    """

    DEFAULT_FILE_PATH: str = './words.txt'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        words: dict[str, str] = {}

        for line in file_object:
            parts = line.split(',')

            if len(parts) != 2:
                continue

            word, translation = parts[0].strip(), parts[1].strip()

            if word:
                words[word] = translation

        return words

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        for word, translation in words.items():
            file_object.write(f'{word},{translation}\n')


@loader_registry.register(is_tsv_source)
class TSVFileLoader(BaseFileLoader):
    """
    Реализует логику загрузки слов из TSV файла и логику сохранения
    слов в TSV файл.

    Формат записи: "слово\\tперевод"
    """

    DEFAULT_FILE_PATH: str = './words.tsv'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        words: dict[str, str] = {}

        for line in file_object:
            parts = line.split('\t')

            if len(parts) != 2:
                continue

            word, translation = parts[0].strip(), parts[1].strip()

            if word:
                words[word] = translation

        return words

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        for word, translation in words.items():
            file_object.write(f'{word}\t{translation}\n')


@loader_registry.register(is_json_source)
class JsonFileLoader(BaseFileLoader):
    """
    Реализует логику загрузки слов из JSON файла и логику сохранения
    слов в JSON файл.

    Формат записи: JSON-объект {"слово": "перевод"}
    """

    DEFAULT_FILE_PATH: str = './words.json'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        data: Any = json.load(file_object)
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value) for key, value in data.items()}

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        json.dump(words, file_object, indent=2, ensure_ascii=False)


@loader_registry.register(is_http_source)
class JsonNetworkLoader:
    """Загружает словарь Anki по HTTP/HTTPS-ссылке.

    Класс не работает с локальным файлом: слова читаются из JSON
    по переданному URL. Сохранение в сеть не поддерживается.
    """

    url: str

    def __init__(self, url: str) -> None:
        self.url = url

    @classmethod
    def from_source(cls, source: str) -> Self:
        """Создаёт сетевой загрузчик из HTTP(S)-ссылки."""
        return cls(url=source)

    def load_words(self) -> dict[str, str]:
        """Загружает слова и переводы по ссылке из атрибута `url`.

        Сначала пробует разобрать ответ как JSON. Если это не JSON
        (например, `.txt` или `.tsv`), разбирает текст по расширению URL.

        Returns:
            Словарь, содержащий слова и соответствующие им переводы.
        """
        response = requests.get(self.url)

        try:
            words: Any = response.json()
        except ValueError:
            words = None

        if isinstance(words, dict):
            return {str(key): str(value) for key, value in words.items()}

        return self._parse_text_response(response)

    def _parse_text_response(self, response: Response) -> dict[str, str]:
        """Разбирает текстовый ответ сервера как CSV или TSV."""
        text = response.content.decode('utf-8')
        suffix = Path(self.url.split('?', 1)[0]).suffix.lower()
        delimiter = '\t' if suffix == '.tsv' else ','

        words: dict[str, str] = {}

        for line in text.splitlines():
            parts = line.split(delimiter)

            if len(parts) != 2:
                continue

            word, translation = parts[0].strip(), parts[1].strip()

            if word:
                words[word] = translation

        return words

    def save_words(self, words: dict[str, str]) -> None:
        """Заглушка: сетевой загрузчик не сохраняет словарь.

        Args:
            words: Словарь слов и переводов. Не используется.
        """
        return None
