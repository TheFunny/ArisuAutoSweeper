from enum import Enum

from module.base.timer import Timer
from module.logger import logger
from tasks.base.page import CIRCLE_CHECK, MAIN_GO_TO_CIRCLE
from tasks.base.ui import UI
from tasks.circle.assets.assets_circle import *


class CircleStatus(Enum):
    """
    Circle status
    """
    REWARD = 0
    GOT = 1
    FINISHED = -1


class Circle(UI):
    def _enter_circle(self):
        self.ui_goto_main()
        action_timer = Timer(1, 8)
        while not self.appear(CIRCLE_CHECK):
            self.device.screenshot()
            if not action_timer.reached_and_reset():
                continue
            if self.appear(CIRCLE):
                self.click_with_interval(CIRCLE, 3)
                continue
            else:
                self.device.click(MAIN_GO_TO_CIRCLE)

    def _handle_circle(self, status):
        match status:
            case CircleStatus.REWARD:
                if self.appear_then_click(GET_REWARD_AP):
                    logger.info("Get circle AP reward")
                    return CircleStatus.FINISHED
            case CircleStatus.GOT:
                logger.info("Circle AP reward have been got")
                return CircleStatus.FINISHED
            case _:
                logger.warning(f"Invalid status: {status}")
        return status

    def run(self):
        self._enter_circle()

        status = CircleStatus.REWARD
        action_timer = Timer(0.5)
        ap_timer = Timer(2).start()

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if ap_timer.reached() and status == CircleStatus.REWARD:
                status = CircleStatus.GOT

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self._handle_circle(status)

            if status is CircleStatus.FINISHED:
                break

        self.config.task_delay(server_update=True)
