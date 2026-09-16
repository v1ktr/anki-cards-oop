from anki.anki import Anki
from anki.loader import TextFileLoader


def test_integration(tmp_path):
    file_path = tmp_path / 'words.txt'

    file_path.write_text(
        'hello,привет\n'
        'world,мир\n',
        encoding='utf-8',
    )

    loader = TextFileLoader(file_path=file_path)

    words = loader.load_words()

    anki = Anki(words=words)

    assert anki.words == {
        'hello': 'привет',
        'world': 'мир',
    }

    anki.add_word('python', 'питон')

    loader.save_words(anki.words)

    content = file_path.read_text(encoding='utf-8')

    assert content == (
        'hello,привет\n'
        'world,мир\n'
        'python,питон\n'
    )
