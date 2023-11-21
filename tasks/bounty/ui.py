from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.bounty.assets.assets_bounty import *
from tasks.stage.list import StageList
from tasks.stage.sweep import StageSweep

BOUNTY_LIST = StageList('BountyList')
BOUNTY_SWEEP = StageSweep('BountySweep', 6)


class BountyUI(UI):
    def select_bounty(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper):
        timer = Timer(5, 10).start()
        while 1:
            self.device.screenshot()
            self.appear_then_click(dest_enter, interval=1)
            if self.appear(dest_check):
                return True
            if timer.reached():
                return False

    def enter_stage(self, index: int) -> bool:
        if BOUNTY_LIST.select_index_enter(self, index):
            return True
        return False

    def do_sweep(self, num: int) -> bool:
        if BOUNTY_SWEEP.do_sweep(self, num=num):
            return True
        return False

    def get_ticket(self):
        """
        Page:
            in: page_bounty
        """
        if not self.appear(CHECK_BOUNTY):
            logger.warning('OCR failed due to invalid page')
            return False
        ticket, _, total = DigitCounter(OCR_TICKET).ocr_single_line(self.device.image)
        if total == 0:
            logger.warning('Invalid ticket')
            return False
        logger.attr('BountyTicket', ticket)
        self.config.stored.BountyTicket.set(ticket)
        return True
