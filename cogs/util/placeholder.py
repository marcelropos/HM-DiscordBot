from typing import Any


class Placeholder:
    """
    Wraps a variable.

    Decorators like want to have a value already at the beginning. We cannot provide this value at this time.
    We give them this placeholder instead, which later carries a suitable value.
    Of course, we need to adjust the original decoration properly.
    """

    def __init__(self):
        self.__item: list[Any] = [None]

    def __bool__(self):
        return True if self.__item[0] else False

    @property
    def item(self) -> Any:
        return self.__item[0]

    @item.setter
    def item(self, item: Any):
        self.__item[0] = item
