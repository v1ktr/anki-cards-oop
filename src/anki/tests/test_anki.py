from anki.anki import Anki  # импорт из пакета anki, файла anki.py класса Anki
import pytest   # Не забудьте добавить импорт библиотеки.


@pytest.mark.parametrize(
    "word, case, expected", [
        (
            "hello",
            "корректных данных",
            "hello"
        ),
        (
            "hello world",
            "отсутствия пробельных символов в начале или конце строки",
            "hello world"
        ),
        (
            "python",
            "корректных данных",
            "python"
        )
    ]
)
def test_normalize_word_method_returns_valid_input_unchanged(
    word, case, expected
):
    """Метод `normalize_word` класса `Anki` должен вернуть переданную строку
    неизменённой, если:
     - строка записана в нижнем регистре, 
     - в начале и в конце строки нет пробелов. 
    """
    assert Anki.normalize_word(word) == expected, (
        "Метод `normalize_word` должен возвращать неизменённую строку,"
        f" если {case}"
    )


@pytest.mark.parametrize(
    "word, expected", [
        ("pYtHoN", "python"),
        ("Hello World", "hello world"),
        ("   Python   ", "python"),
        ("\tHello World\n", "hello world")]
)
def test_normalize_word_method_normalizes_word(word, expected):
    """Метод `normalize_word` класса `Anki` должен выполнить нормализацию
    строки:
        - все символы приведены к нижнему регистру;
        - удалены пробелы в начале и в конце строки.
    """
    assert Anki.normalize_word(word) == expected, (
        "Метод `normalize_word` должен нормализовать"
        " некорректно отформатированные строки."
    )


@pytest.mark.parametrize('invalid_input', [
    1,
    [],
    set(),
])
def test_normalize_word_raises_ValueError_on_invalid_input(invalid_input):
    """Метод `normalize_word` класса `Anki` должен выдавать исключение
    `ValueError`, если в качестве значения параметра `word`
    передана не строка.
    """
    with pytest.raises(ValueError, match='должно быть строкой'):
        Anki.normalize_word(invalid_input)
        pytest.fail(
            "Метод `normalize_word` должен выдавать ValueError"
            " для нестроковых параметров"
        )


# тесты из задачи:
@pytest.mark.parametrize('invalid_words', [
    [],
    (),
    'слово',
    123,
])
def test_anki_init_raises_ValueError_on_invalid_input(invalid_words):
    with pytest.raises(ValueError):
        Anki(words=invalid_words)


@pytest.mark.parametrize('word, translation', [
    (123, 'перевод'),
    ('слово', 123),
    (None, 'перевод'),
    ('слово', None),
])
def test_anki_add_word_raises_ValueError_on_invalid_input(
    word,
    translation,
):
    anki = Anki()

    with pytest.raises(ValueError):
        anki.add_word(word, translation)


def test_get_random_word_returns_word_without_translation():
    anki = Anki(words={'hello': 'привет', 'world': 'мир'})

    word = anki.get_random_word()

    assert word in {'hello', 'world'}
    assert word != 'привет'
    assert word != 'мир'


def test_get_random_word_raises_if_dictionary_is_empty():
    anki = Anki()

    with pytest.raises(ValueError):
        anki.get_random_word()


def test_check_translation_returns_bool_and_normalizes_input():
    anki = Anki(words={'hello': 'привет', 'world': 'мир'})

    assert anki.check_translation('  HeLLo ', ' ПРИВЕТ') is True
    assert anki.check_translation('hello', 'something') is False


def test_check_translation_raises_if_word_is_missing():
    anki = Anki(words={'hello': 'привет'})

    with pytest.raises(ValueError):
        anki.check_translation('python', 'питон')


def test_get_translation_returns_translation_for_normalized_word():
    anki = Anki(words={'hello': 'привет', 'world': 'мир'})

    assert anki.get_translation('  HELLO ') == 'привет'


def test_get_translation_raises_if_word_is_missing():
    anki = Anki(words={'hello': 'привет'})

    with pytest.raises(ValueError):
        anki.get_translation('python')
