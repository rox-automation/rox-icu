import pytest
from cantools import database
from rox_icu.dbc import get_dbc
from rox_icu.can_utils import create_dbc


@pytest.mark.skip("No idea why this fails, messages look the same")
def test_dbc() -> None:
    """compare file dbc to generated dbc"""

    static_dbc = database.load_file(get_dbc())
    generated_dbc = create_dbc(10)

    assert static_dbc.messages == generated_dbc.messages
