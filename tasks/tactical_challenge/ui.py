from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.ui.switch import Switch
from tasks.base.ui import UI
from tasks.tactical_challenge.assets.assets_tactical_challenge import *

SWITCH_SKIP = Switch('Skip_switch')
SWITCH_SKIP.add_state('on', SKIP_ON)
SWITCH_SKIP.add_state('off', SKIP_OFF)


class TacticalChallengeUI(UI):
    def get_ticket(self):
        """
        Page:
            in: page_tactical_challenge
        """
        ticket, _, total = DigitCounter(OCR_TICKET).ocr_single_line(self.device.image)
        if total == 0:
            logger.warning('Invalid ticket')
            return False
        logger.attr('TacticalChallengeTicket', ticket)
        self.config.stored.TacticalChallengeTicket.set(ticket)
        return True

    def get_reward(self):
        timer = Timer(10, 10).start()
        action_timer = Timer(0.5, 1)
        while 1:
            self.device.screenshot()
            if not action_timer.reached_and_reset():
                continue
            if self.handle_insufficient_inventory():
                logger.warning('Insufficient inventory, skip reward')
                return True
            if self.ui_additional():
                continue
            if self.match_color(GOT_REWARD_DAILY) and self.match_color(GOT_REWARD_CREDIT):
                return True
            if self.match_color(GET_REWARD_DAILY):
                self.click_with_interval(GET_REWARD_DAILY, 0.3)
                logger.info('Get daily reward')
                continue
            if self.match_color(GET_REWARD_CREDIT):
                self.click_with_interval(GET_REWARD_CREDIT, 0.3)
                logger.info('Get credit reward')
                continue
            if timer.reached():
                return False

    def set_skip(self):
        """
        Set skip switch to on
        Returns:
            True if switch is set, False if switch not found
        """
        if not SWITCH_SKIP.appear(main=self):
            logger.info('Skip switch not found')
            return False
        SWITCH_SKIP.set('on', main=self)

        return True
