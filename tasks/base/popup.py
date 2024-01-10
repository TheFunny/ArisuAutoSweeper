from module.base.base import ModuleBase
from module.base.timer import Timer
from tasks.base.assets.assets_base_popup import *
from tasks.base.assets.assets_base_page import LOADING_CHECK


class PopupHandler(ModuleBase):
    def handle_loading(self) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear(LOADING_CHECK):
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

    def handle_reward(self) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear(GET_REWARD) or self.match_color(GET_REWARD, threshold=30):
            while 1:
                self.device.screenshot()
                if self.appear(GET_REWARD) or self.match_color(GET_REWARD, threshold=30):
                    self.click_with_interval(GET_REWARD, interval=0.5)
                else:
                    break
            return True

        return False

    def handle_reward_skip(self, interval=5) -> bool:
        if self.appear_then_click(GET_REWARD_SKIP, interval=interval):
            return True

    def handle_daily_news(self, interval=2) -> bool:
        if self.appear_then_click(DAILY_NEWS, interval=interval):
            return True

        return False

    def handle_daily_reward(self, interval=2) -> bool:
        if self.appear_then_click(DAILY_REWARD, interval=interval):
            return True

        return False

    def handle_network_reconnect(self, interval=5) -> bool:
        if self.appear_then_click(NETWORK_RECONNECT, interval=interval):
            return True
        if self.appear_then_click(NETWORK_RECONNECT_OK, interval=interval):
            return True

        return False

    def handle_affection_level_up(self) -> bool:
        if self.appear_then_click(AFFECTION_LEVEL_UP):
            while 1:
                self.device.screenshot()
                if self.appear(AFFECTION_LEVEL_UP):
                    self.click_with_interval(AFFECTION_LEVEL_UP, interval=1)
                else:
                    break
            return True

        return False

    def handle_new_student(self, interval=5) -> bool:
        if self.appear_then_click(GET_NEW_STUDENT, interval=interval):
            return True

        return False

    def handle_ap_exceed(self, interval=5) -> bool:
        if self.appear_then_click(AP_EXCEED, interval=interval):
            return True

        return False

    def handle_insufficient_inventory(self, interval=5) -> bool:
        if self.appear_then_click(INSUFFICIENT_INVENTORY, interval=interval):
            return True

        return False

    def handle_item_expired(self, interval=5) -> bool:
        if self.appear_then_click(ITEM_EXPIRED, interval=interval):
            return True

        return False

    def handle_location_level_up(self, interval=5) -> bool:
        if self.appear_then_click(LOCATION_LEVEL_UP, interval=interval):
            return True

        return False
    
    def handle_level_up(self, interval=5) -> bool:
        if self.appear_then_click(LEVEL_UP, interval=interval):
            return True

        return False
    
    def handle_quit(self, interval=5) -> bool:
        if self.appear_then_click(QUIT, interval=interval):
            return True

        return False
    