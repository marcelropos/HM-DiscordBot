from discord.ui import View, Select


class SelectRoleView(View):
    def __init__(self, custom_selects: list[Select], timeout=120):
        super().__init__(timeout=timeout)
        self.custom_selects: dict[Select, bool] = {}
        for custom_select in custom_selects:
            self.add_item(custom_select)
            # noinspection PyUnresolvedReferences
            custom_select.set_view(self)
            self.custom_selects[custom_select] = False

    def finished_interaction(self, custom_select: Select):
        self.custom_selects[custom_select] = True
        if all(x for x in self.custom_selects.values()):
            self.stop()
