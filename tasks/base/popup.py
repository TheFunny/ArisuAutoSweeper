from module.base.base import ModuleBase
from module.base.timer import Timer
from tasks.base.assets.assets_base_popup import *
from tasks.base.assets.assets_base_page import LOADING_CHECK


class PopupHandler(ModuleBase):
    def handle_loading(self, interval=5) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear(LOADING_CHECK, interval=interval):
            timer = Timer(0.5).start()
            while 1:
                if timer.reached_and_reset():
                    self.device.screenshot()
                    if self.appear(LOADING_CHECK):
                        self.device.stuck_record_clear()
                        continue
                    else:
                        break
            return True

        return False

    def handle_reward(self, interval=5) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(GET_REWARD, interval=interval):
            timer = Timer(0.2).start()
            while 1:
                if timer.reached_and_reset():
                    self.device.screenshot()
                    if self.appear(GET_REWARD):
                        self.device.click(GET_REWARD)
                    else:
                        break
            return True

        return False

    def handle_reward_skip(self, interval=5) -> bool:
        if self.appear_then_click(GET_REWARD_SKIP, interval=interval):
            return True

    def handle_daily_news(self, interval=5) -> bool:
        if self.appear_then_click(DAILY_NEWS, interval=interval):
            return True

        return False

    def handle_daily_reward(self, interval=5) -> bool:
        if self.appear_then_click(DAILY_REWARD, interval=interval):
            return True

        return False

    def handle_network_reconnect(self, interval=5) -> bool:
        if self.appear_then_click(NETWORK_RECONNECT, interval=interval):
            return True

        return False

    def handle_affection_level_up(self, interval=5) -> bool:
        if self.appear_then_click(AFFECTION_LEVEL_UP, interval=interval):
            timer = Timer(0.2).start()
            while 1:
                if timer.reached_and_reset():
                    self.device.screenshot()
                    if self.appear(AFFECTION_LEVEL_UP):
                        self.device.click(AFFECTION_LEVEL_UP)
                    else:
                        break
            return True

        return False

    def handle_new_student(self, interval=5) -> bool:
        if self.appear_then_click(GET_NEW_STUDENT, interval=interval):
            return True

        return False
