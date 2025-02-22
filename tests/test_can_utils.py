import rox_icu.can_utils as utils
from rox_icu.dbc import get_dbc


def test_dbc():

    utils.create_dbc(node_id=10)


def test_get_dbc():

    dbc = get_dbc()
    assert dbc.exists()
