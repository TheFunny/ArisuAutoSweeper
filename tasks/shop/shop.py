from enum import Flag

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from module.ui.switch import Switch
from tasks.base.assets.assets_base_page import BACK
from tasks.base.page import page_main, page_shop
from tasks.shop.assets.assets_shop import *
from tasks.shop.ui import ShopUI


class ShopStatus(Flag):
    SELECT_SHOP = 0
    SELECT_ITEMS = 1
    PURCHASE = 2
    REFRESH = 3
    END = 4
    FINISH = -1

class Shop(ShopUI):
    @property
    def shop_info(self):
        """Similiar to bounty_info and scrimmage_info.
        Returns a list with elements the select button, check button, how many times do make purchases and the list of items"""
        info = []
        if self.config.NormalShop_Enable:
            normal_config = self.config.cross_get(["Shop", "NormalShop"])
            normal_items = [num for num in range(1, 21) if normal_config[str(num)]]
            if normal_items:
                SWITCH_NORMAL = Switch('NormalShop_Switch')
                SWITCH_NORMAL.add_state('on', NORMAL_ON)
                SWITCH_NORMAL.add_state('off', NORMAL_OFF)
                info.append([SWITCH_NORMAL, self.config.NormalShop_Purchases, normal_items])

        if self.config.TacticalChallengeShop_Enable:
            tc_config = self.config.cross_get(["Shop", "TacticalChallengeShop"])
            tc_items = [num for num in range(1, 16) if tc_config[str(num)]]
            if tc_items:
                SWITCH_TC = Switch('TacticalChallengeShop_Switch')
                SWITCH_TC.add_state('on', TC_ON)
                SWITCH_TC.add_state('off', TC_OFF)
                info.append([SWITCH_TC, self.config.TacticalChallengeShop_Purchases, tc_items])

        return info

    @property
    def valid_task(self) -> list:
        task = self.shop_info
        if not task:
            logger.warning('Shop enabled but no task set')
        return task

    @property
    def current_shop(self):
        return self.task[0][0]

    @property
    def current_purchase_count(self):
        return self.task[0][1]
    
    @property
    def current_item_list(self):
        return self.task[0][2]

    def handle_shop(self, status):
        match status:
            case ShopStatus.SELECT_SHOP:
                if not self.task:
                    return ShopStatus.FINISH
                if self.select_shop(self.current_shop):
                    self.reset_swipe_flags()
                    return ShopStatus.SELECT_ITEMS
            case ShopStatus.SELECT_ITEMS:
                self.select_items(self.current_item_list)
                return ShopStatus.PURCHASE
            case ShopStatus.PURCHASE:
                if self.make_purchase() and self.current_purchase_count > 1:
                    return ShopStatus.REFRESH
                return ShopStatus.END
            case ShopStatus.REFRESH:
                if self.refresh_shop(self.current_purchase_count):
                    return ShopStatus.SELECT_SHOP
                return ShopStatus.END
            case ShopStatus.END:
                if self.appear(page_shop.check_button):
                    self.task.pop(0)
                    return ShopStatus.SELECT_SHOP
                self.click_with_interval(BACK, interval=2)
            case ShopStatus.FINISH:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        """Reset the shop and items position by going main and then shop"""
        self.ui_ensure(page_main)
        self.ui_ensure(page_shop)

        self.task = self.valid_task
        action_timer = Timer(0.5, 1)
        status = ShopStatus.SELECT_SHOP

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self.handle_shop(status)

            if status == ShopStatus.FINISH:
                break

        self.config.task_delay(server_update=True)
