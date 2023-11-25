from enum import Enum

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.assets.assets_base_page import BACK
from tasks.base.page import page_school_exchange
from tasks.scrimmage.assets.assets_scrimmage import *
from tasks.scrimmage.ui import ScrimmageUI


class ScrimmageStatus(Enum):
    OCR = 0
    SELECT = 1
    ENTER = 2
    SWEEP = 3
    END = 4
    FINISH = 5


class Scrimmage(ScrimmageUI):
    @property
    def scrimmage_info(self):
        scrimmage = (SELECT_TRINITY, SELECT_GEHENNA, SELECT_MILLENNIUM)
        check = (CHECK_TRINITY, CHECK_GEHENNA, CHECK_MILLENNIUM)
        stage = (self.config.Trinity_Stage, self.config.Gehenna_Stage, self.config.Millennium_Stage)
        count = (self.config.Trinity_Count, self.config.Gehenna_Count, self.config.Millennium_Count)
        ap = (10 if stage == 1 else 15 for stage in stage)
        info = zip(scrimmage, check, stage, count, ap)
        return filter(lambda x: x[3] > 0, info)

    @property
    def valid_task(self) -> list:
        task = list(self.scrimmage_info)
        if not task:
            logger.warning('Scrimmage enabled but no task set')
            self.error_handler()
        return task

    def error_handler(self):
        action = self.config.Scrimmage_OnError
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
    def is_ap_enough(self) -> bool:
        return self.current_ap >= self.current_task_ap

    @property
    def current_scrimmage(self):
        return self.task[0][:2]

    @property
    def current_stage(self):
        return self.task[0][2]

    @property
    def current_count(self):
        return self.task[0][3]

    @property
    def current_task_ap(self):
        return self.task[0][4] * self.current_count

    @property
    def current_ticket(self):
        return self.config.stored.ScrimmageTicket.value

    @property
    def current_ap(self):
        return self.config.stored.AP.value

    def update_ap(self):
        ap = self.config.stored.AP
        ap_old = ap.value
        ap_new = ap_old - self.current_task_ap
        ap.set(ap_new, ap.total)
        logger.info(f'Set AP: {ap_old} -> {ap_new}')

    def handle_scrimmage(self, status):
        match status:
            case ScrimmageStatus.OCR:
                if self.get_ticket():
                    if self.current_ticket == 0 or not self.task:
                        return ScrimmageStatus.FINISH
                    return ScrimmageStatus.SELECT
            case ScrimmageStatus.SELECT:
                if not self.is_ticket_enough:
                    logger.warning('Scrimmage ticket not enough')
                    self.error_handler()
                if not self.is_ap_enough:
                    logger.warning('AP not enough')
                    self.error_handler()
                if self.select_scrimmage(*self.current_scrimmage):
                    return ScrimmageStatus.ENTER
            case ScrimmageStatus.ENTER:
                if self.enter_stage(self.current_stage):
                    return ScrimmageStatus.SWEEP
                else:
                    self.error_handler()
            case ScrimmageStatus.SWEEP:
                if self.do_sweep(self.current_count):
                    self.update_ap()
                    self.task.pop(0)
                    return ScrimmageStatus.END
                return ScrimmageStatus.ENTER
            case ScrimmageStatus.END:
                if self.appear(CHECK_SCRIMMAGE):
                    return ScrimmageStatus.OCR
                self.click_with_interval(BACK, interval=2)
            case ScrimmageStatus.FINISH:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        self.ui_ensure(page_school_exchange)
        self.task = self.valid_task
        action_timer = Timer(0.5, 1)
        status = ScrimmageStatus.OCR

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self.handle_scrimmage(status)

            if status == ScrimmageStatus.FINISH:
                break

        self.config.task_delay(server_update=True)
        self.config.task_call('DataUpdate')
