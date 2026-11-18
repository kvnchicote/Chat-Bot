from ragbot.text_utils import normalized, exact_quote_in_source


def test_quote_across_linebreaks():
    assert exact_quote_in_source('un plazo fijo es una inversión', 'un plazo fijo\nes una inversión')


def test_quote_not_in_pdf():
    assert not exact_quote_in_source('La tasa de inflación es 5%', 'El plazo fijo tiene interés.')


def test_empty_quote():
    assert not exact_quote_in_source('', 'Texto de prueba')
