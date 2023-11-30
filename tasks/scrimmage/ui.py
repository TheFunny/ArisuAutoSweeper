from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.scrimmage.assets.assets_scrimmage import *
from tasks.stage.list import StageList
from tasks.stage.sweep import StageSweep

SCRIMMAGE_LIST = StageList('ScrimmageList')
SCRIMMAGE_SWEEP = StageSweep('ScrimmageSweep', 6)


class ScrimmageUI(UI):
    def select_scrimmage(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper):
        timer = Timer(5, 10).start()
        while 1:
            self.device.screenshot()
            self.appear_then_click(dest_enter, interval=1)
            if self.appear(dest_check):
                return True
            if timer.reached():
                return False

    def enter_stage(self, index: int) -> bool:
        if not index:
            index = SCRIMMAGE_LIST.insight_max_sweepable_index(self)
        if SCRIMMAGE_LIST.select_index_enter(self, index, insight=False):
            return True
        return False

    def do_sweep(self, num: int) -> bool:
        if SCRIMMAGE_SWEEP.do_sweep(self, num=num):
            return True
        return False

    def get_ticket(self):
        """
        Page:
            in: page_bounty
        """
        if not self.appear(CHECK_SCRIMMAGE):
            logger.warning('OCR failed due to invalid page')
            return False
        ticket, _, total = DigitCounter(OCR_TICKET).ocr_single_line(self.device.image)
        if total == 0:
            logger.warning('Invalid ticket')
            return False
        logger.attr('ScrimmageTicket', ticket)
        self.config.stored.ScrimmageTicket.set(ticket)
        return True
