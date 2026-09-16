from __future__ import annotations

import argparse
from pathlib import Path
from types import TracebackType

from anki.anki import Anki
from anki.loader import LoaderProtocol, loader_registry
from anki.ui import TextUI

DEFAULT_WORDS_PATH: Path = Path(__file__).resolve().parent / 'words.txt'


def get_loader(source: str) -> LoaderProtocol:
    """Автоматически выбирает загрузчик в зависимости от `source`.

    Parameters
    ----------
    source : str
        Источник для получения слов: путь к файлу или HTTP(S)-ссылка.

    Returns
    -------
    LoaderProtocol
        Экземпляр загрузчика
    """
    loader_cls = loader_registry.get_loader(source)
    return loader_cls.from_source(source)


class GameContext:
    """Контекстный менеджер жизненного цикла игры Anki.

    При входе загружает слова из загрузчика в экземпляр `Anki`.
    При выходе сохраняет текущий словарь через загрузчик,
    в том числе если внутри блока возникло исключение.
    """

    _loader: LoaderProtocol
    _anki: Anki

    def __init__(self, loader: LoaderProtocol, anki: Anki) -> None:
        self._loader = loader
        self._anki = anki

    def __enter__(self) -> GameContext:
        self._anki.words = self._loader.load_words()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._loader.save_words(self._anki.words)


def main() -> None:
    """Запускает приложение Anki."""
    # Создали объект парсера аргументов командной строки.
    parser = argparse.ArgumentParser(prog='anki')

    # Добавили новый аргумент.
    parser.add_argument(
        '--source',
        default=str(DEFAULT_WORDS_PATH),
        help='Путь до локального файла со словами или ссылка для загрузки',
        metavar='SOURCE_PATH',
    )

    # Распарсили аргументы командной строки.
    args = parser.parse_args()

    loader = get_loader(args.source)
    anki = Anki()

    with GameContext(loader, anki):
        ui = TextUI(anki)
        ui.main_loop()


if __name__ == '__main__':
    main()
