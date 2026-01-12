from pintar import dye

def test_dye():
    assert repr(dye("Hello World", fore="#FF0000"))[1:-1] == r"\x1b[0m\x1b[38;2;255;0;0m\x1b[49m\x1b[22mHello World\x1b[0m\x1b[39m\x1b[49m\x1b[22m"
    