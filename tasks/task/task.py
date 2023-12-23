from module.base.timer import Timer
from module.logger import logger
from tasks.base.page import page_task
from tasks.base.ui import UI
from tasks.task.assets.assets_task import *


class Task(UI):
    def run(self):
        self.ui_ensure(page_task)
        action_timer = Timer(1).start()

        while 1:
            self.device.screenshot()
            if self.ui_additional():
                continue
            if action_timer.reached_and_reset():
                if self.match_color(CLAIM_ALL):
                    self.device.click(CLAIM_ALL)
                    logger.info("Click Claim All")
                    continue
                if self.match_color(CLAIM):
                    self.device.click(CLAIM)
                    logger.info("Click Claim")
                    continue
                if self.match_color(CLAIMED) and self.match_color(CLAIMED_ALL):
                    logger.info("All claimed")
                    break

        self.config.task_delay(minute=120)
