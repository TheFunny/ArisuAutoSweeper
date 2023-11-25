from enum import Flag

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.assets.assets_base_page import BACK
from tasks.base.page import page_bounty
from tasks.bounty.assets.assets_bounty import *
from tasks.bounty.ui import BountyUI


class BountyStatus(Flag):
    OCR = 0
    SELECT = 1
    ENTER = 2
    SWEEP = 3
    END = 4
    FINISH = 5


class Bounty(BountyUI):
    @property
    def bounty_info(self):
        bounty = (SELECT_HIGHWAY, SELECT_DESERT_RAILROAD, SELECT_SCHOOLHOUSE)
        check = (CHECK_HIGHWAY, CHECK_DESERT_RAILROAD, CHECK_SCHOOLHOUSE)
        stage = (self.config.Highway_Stage, self.config.DesertRailroad_Stage, self.config.Schoolhouse_Stage)
        count = (self.config.Highway_Count, self.config.DesertRailroad_Count, self.config.Schoolhouse_Count)
        info = zip(bounty, check, stage, count)
        return filter(lambda x: x[3] > 0, info)

    @property
    def valid_task(self) -> list:
        task = list(self.bounty_info)
        if not task:
            logger.warning('Bounty enabled but no task set')
            self.error_handler()
        return task

    def error_handler(self):
        action = self.config.Bounty_OnError
        if action == 'stop':
            raise RequestHumanTakeover
        elif action == 'skip':
            with self.config.multi_set():
                self.config.task_delay(server_update=True)
                self.config.task_stop()

    @property
    def is_ticket_enough(self) -> bool:
        return self.current_ticket >= self.current_count

    @property
    def current_bounty(self):
        return self.task[0][:2]

    @property
    def current_stage(self):
        return self.task[0][2]

    @property
    def current_count(self):
        return self.task[0][3]

    @property
    def current_ticket(self):
        return self.config.stored.BountyTicket.value

    def handle_bounty(self, status):
        match status:
            case BountyStatus.OCR:
                if self.get_ticket():
                    if self.current_ticket == 0 or not self.task:
                        return BountyStatus.FINISH
                    return BountyStatus.SELECT
            case BountyStatus.SELECT:
                if not self.is_ticket_enough:
                    logger.warning('Bounty ticket not enough')
                    self.error_handler()
                if self.select_bounty(*self.current_bounty):
                    return BountyStatus.ENTER
            case BountyStatus.ENTER:
                if self.enter_stage(self.current_stage):
                    return BountyStatus.SWEEP
                else:
                    self.error_handler()
            case BountyStatus.SWEEP:
                if self.do_sweep(self.current_count):
                    self.task.pop(0)
                    return BountyStatus.END
                return BountyStatus.ENTER
            case BountyStatus.END:
                if self.appear(CHECK_BOUNTY):
                    return BountyStatus.OCR
                self.click_with_interval(BACK, interval=2)
            case BountyStatus.FINISH:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        self.ui_ensure(page_bounty)
        self.task = self.valid_task
        action_timer = Timer(0.5, 1)
        status = BountyStatus.OCR

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self.handle_bounty(status)

            if status == BountyStatus.FINISH:
                break

        self.config.task_delay(server_update=True)
