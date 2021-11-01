from time import sleep
from typing import Callable, Optional

from botocore.exceptions import ClientError, WaiterError


def endeavor(
    func: Callable[[], None],
    on_exception: Optional[Callable[[], None]] = None,
) -> None:
    attempt = 0
    max_attempts = 20

    while attempt < max_attempts:
        try:
            func()
            return
        except ClientError as ex:
            if "throttl" not in str(ex).lower():
                if on_exception:
                    on_exception()
                    return
                raise

            sleep(8)
            attempt += 1

        except WaiterError:
            if on_exception:
                on_exception()
                return
            raise
