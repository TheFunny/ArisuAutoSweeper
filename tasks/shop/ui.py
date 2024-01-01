import numpy as np

from module.base.timer import Timer
from module.base.base import ModuleBase
from module.base.utils import area_size
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.shop.assets.assets_shop import *

ITEM_POSITIONS = {
    1: (650, 200), 2: (805, 200), 3: (960, 200), 4: (1110, 200),
    5: (650, 460), 6: (805, 460), 7: (960, 460), 8: (1110, 460),
    9: (650, 200), 10: (805, 200), 11: (960, 200), 12: (1110, 200),
    13: (650, 460), 14: (805, 460), 15: (960, 460), 16: (1110, 460),
    17: (650, 460), 18: (805, 460), 19: (960, 460), 20: (1110, 460),
}

class ShopUI(UI):
    def __init__(self, config, device):
        super().__init__(config, device)

        self.click_coords = self.device.click_methods.get(self.config.Emulator_ControlMethod, self.device.click_adb)
        self.swipe_vector_range = (0.85, 0.9)
        self.swipe_flags = {8:False, 16: False}
        self.list = ITEM_LIST

    def swipe_page(self, direction: str, main: ModuleBase, vector_range=None, reverse=False):
        """
        Args:
            direction: up, down
            main:
            vector_range (tuple[float, float]):
            reverse (bool):
        """
        if vector_range is None:
            vector_range = self.swipe_vector_range
        vector = np.random.uniform(*vector_range)
        width, height = area_size(self.list.button)
        if direction == 'up':
            vector = (0, vector * height)
        elif direction == 'down':
            vector = (0, -vector * height)
        else:
            logger.warning(f'Unknown swipe direction: {direction}')
            return

        if reverse:
            vector = (-vector[0], -vector[1])
        main.device.swipe_vector(vector, self.list.button)

    def select_then_check(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper):
        timer = Timer(5, 10).start()
        while 1:
            self.device.screenshot()
            self.appear_then_click(dest_enter, interval=1)
            if self.appear(dest_check):
                return True
            if timer.reached():
                return False

    def select_shop(self, shop_switch):
        """
        Set skip switch to on
        Returns:
            True if switch is set, False if switch not found
        """
        if not shop_switch.appear(main=self):
            logger.info(f'{shop_switch.name} not found')
            return False
        shop_switch.set('on', main=self)

        return True
    
    def select_items(self, item_list):
        """
        Select items in the item list checking if swipe is required each time.
        However, swipes are inaccurate and clicks too fast.
        """
        timer = Timer(1).start()
        for item in item_list:
            if self.should_swipe(item):
                self.swipe_page('down', self)

                self.wait_until_stable(
                    self.list.button,
                    timer=Timer(3, 0),
                    timeout=Timer(1.5, 5)
                )
            while not timer.reached_and_reset():
                pass
            self.click_coords(*ITEM_POSITIONS[item])        

    def should_swipe(self, item):
        """
        Return True based on two checkpoints: 
        one at 8 and the other at 16. 
        Only once for each checkpoint.
        """
        if (9 <= item <= 16) and not self.swipe_flags[8]:
            self.swipe_flags[8] = True
            return True
        elif item > 17 and not self.swipe_flags[16]:
            self.swipe_flags[16] = True
            return True
        return False
    
    def reset_swipe_flags(self):
        self.swipe_flags[8], self.swipe_flags[16] = False, False

    def make_purchase(self):
        if self.select_then_check(PURCHASE, CONFIRM_PURCHASE) and self.appear_then_click(CONFIRM_PURCHASE):
            return True
        logger.warning("No items were selected. Unable to purchase.")
        return False

    def refresh_shop(self, need_count):
        """
        Refresh the shop 
        """
        refresh_count = self.get_refresh_count()
        if refresh_count:
            purchased_count = 4 - refresh_count
            if need_count > purchased_count and self.appear_then_click(CONFIRM_REFRESH):
                logger.info("Refreshed the shop")
                return True
        return False
                                
    def get_refresh_count(self):
        if not self.select_then_check(REFRESH, CONFIRM_REFRESH):
            logger.warning('OCR failed due to invalid page')
            return False
        count, _, total = DigitCounter(OCR_REFRESH).ocr_single_line(self.device.image)
        if total == 0:
            logger.warning('Invalid count')
            return False
        return count

