import pytest   # Не забудьте добавить импорт библиотеки.
# import os
# import pathlib
from anki.loader import TextFileLoader


# @pytest.fixture()
# def tmp_file():
#     # Создаём объект пути до файла.
#     path = pathlib.Path("./test_words.txt")
#     # Сохраняем слова в файл.
#     path.write_text("hello,привет\n", encoding="utf-8")
#     # Возвращаем путь до файла из фикстуры.
#     yield str(path)

#     # Удаляем созданный ранее файл.
#     os.remove(path)
# упрощаем:
@pytest.fixture()
def tmp_file(tmp_path):
    # Создаём объект пути до файла.
    path = tmp_path / "test_words.txt"
    # Сохраняем в файл слова.
    path.write_text("hello,привет\n", encoding="utf-8")
    # Возвращаем путь до файла из фикстуры.
    return str(path)


def test_load_words_loads_words_from_comma_separated_values(tmp_file):
    """Метод `load_words` класса `TextFileLoader` должен выполнить
    загрузку слов из файла, путь до которого передан
    при инициализации экземпляра класса `TextFileLoader`.
    """
    loader = TextFileLoader(file_path=tmp_file)
    words = loader.load_words()
    assert words == {"hello": "привет"}


# тесты из задачи:
def test_save_words_saves_words_as_comma_separated_values(tmp_path):
    file_path = tmp_path / 'words.txt'

    loader = TextFileLoader(file_path=file_path)

    words = {
        'hello': 'привет',
        'world': 'мир',
    }

    loader.save_words(words)

    content = file_path.read_text(encoding='utf-8')

    assert content == 'hello,привет\nworld,мир\n'
