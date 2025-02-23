#!/usr/bin/env python3
""" Mock ICU board for testing """

from rox_icu.firmware import mocks

mocks.mock_hardware()

# pylint: disable=C0413
from rox_icu.utils import run_main_async  # noqa: E402
import rox_icu.firmware.remote_io.main as remote_io  # noqa: E402


NODE_ID = 10


def main(node_id: int = NODE_ID):

    remote_io.NODE_ID = node_id
    run_main_async(remote_io.main())


if __name__ == "__main__":
    main()
