from enum import Enum

from module.base.timer import Timer
from module.logger import logger
from tasks.base.page import page_task
from tasks.base.ui import UI
from tasks.task.assets.assets_task import *


class TaskStatus(Enum):
    """
    Task status
    """
    CLAIM_ALL = 0
    CLAIM = 1
    FINISHED = -1

class Task(UI):
    def _handle_task(self, status):
        match status:
            case TaskStatus.CLAIM_ALL:
                if self.match_color(CLAIM_ALL):
                    self.device.click(CLAIM_ALL)
                    logger.info("Click Claim All")
                else:
                    return TaskStatus.CLAIM
            case TaskStatus.CLAIM:
                if self.match_color(CLAIM):
                    self.device.click(CLAIM)
                    logger.info("Click Claim")
                else:
                    return TaskStatus.FINISHED
            case _:
                logger.warning(f"Invalid status: {status}")
        return status

    def run(self):
        self.ui_ensure(page_task)

        status = TaskStatus.CLAIM_ALL
        action_timer = Timer(0.5)

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self._handle_task(status)

            if status is TaskStatus.FINISHED:
                break

        self.config.task_delay(server_update=True)
