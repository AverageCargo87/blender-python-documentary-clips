"""The overlap check used for every Russian text in this repository."""
from lib import textcheck as T


def test_normalize():
    assert T.normalize('Ёлка, «ЁЖ» \u2014 и+ ёж!') == 'елка еж и еж'
    assert T.normalize('Праро́дина') == 'прародина'                  # stress mark used for speech synthesis
    assert T.normalize('Сначала лю+ди') == 'сначала люди'                    # '+' stress notation
    assert T.normalize('Mixed CASE 2025') == 'mixed case 2025'


def test_shared_runs_found_and_merged():
    corpus = ['один два три четыре пять шесть семь восемь девять десять']
    idx = T.build_index(corpus, 8)
    hit = T.shared_runs('ноль один два три четыре пять шесть семь восемь девять', idx, 8)
    assert hit == ['один два три четыре пять шесть семь восемь девять']   # two overlapping 8-grams merged into one run
    assert T.shared_runs('один два три четыре пять шесть семь', idx, 8) == []   # 7 words is below the threshold


def test_punctuation_and_case_do_not_hide_overlap():
    idx = T.build_index(['Один, два; три - четыре: пять шесть семь восемь.'], 8)
    assert T.shared_runs('ОДИН два три четыре пять, шесть, семь, восемь', idx, 8)


def test_clean_text_passes():
    idx = T.build_index(['совсем другой текст про древний мир и раскопки в долине реки'], 8)
    assert T.shared_runs('Прародина человека: Африка. На юге Африки нашли останки австралопитека.', idx, 8) == []
