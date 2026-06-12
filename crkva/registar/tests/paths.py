"""Помоћник: путање унутар стабла репозиторијума, независне од радног директоријума.

CI покреће тестове из корена репо-а (`python crkva/manage.py test`), док
`make coverage` покреће из `crkva/` (због .coveragerc source путања). Тестови
који читају фајлове са диска морају да рачунају путању од __file__, а не од
cwd, да би прошли у оба случаја (#222).
"""

import pathlib

# .../crkva/registar/tests/paths.py → parents[3] је корен репозиторијума.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def repo_path(*delovi: str) -> pathlib.Path:
    """Апсолутна путања унутар репозиторијума, независна од cwd."""
    return REPO_ROOT.joinpath(*delovi)
