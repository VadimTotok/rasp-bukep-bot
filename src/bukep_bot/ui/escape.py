from html import escape as _html_escape


def esc(s: object) -> str:
    return _html_escape("" if s is None else str(s), quote=False)
