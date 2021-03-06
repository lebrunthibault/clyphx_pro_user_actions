from typing import Any

from a_protocol_0.components.actionGroups.AbstractActionGroup import AbstractActionGroup


class ActionGroupSet(AbstractActionGroup):
    """
    This manager is supposed to group mundane tasks on Live like debug
    or one shot actions on a set (like upgrading to the current naming scheme)
    """

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(ActionGroupSet, self).__init__(channel=14, filter_active_tracks=False, *a, **k)
        # LOG encoder
        self.add_encoder(id=1, name="log current", on_press=self.parent.logManager.log_current)

        # LOGS encoder
        self.add_encoder(id=2, name="log set", on_press=self.parent.logManager.log_set)

        # CHeCK encoder
        self.add_encoder(id=3, name="check", on_press=self.parent.setFixerManager.check_set)

        # FIX encoder
        self.add_encoder(id=4, name="fix", on_press=self.parent.setFixerManager.refresh_set_appearance)

        # CLR encoder
        self.add_encoder(id=5, name="clear logs", on_press=lambda: self.parent.log_notice("clear_logs"))
