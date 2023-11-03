import random
from enum import Enum

from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.ui.switch import Switch
from tasks.base.page import page_tactical_challenge
from tasks.base.ui import UI
from tasks.tactical_challenge.assets.assets_tactical_challenge import *

SWITCH_SKIP = Switch('Skip_switch')
SWITCH_SKIP.add_state('on', SKIP_ON)
SWITCH_SKIP.add_state('off', SKIP_OFF)


class TCStatus(Enum):
    """
    Tactical challenge status
    """
    REWARD = 0
    OCR = 1
    SELECT = 2
    PREPARE = 3
    SKIP = 4
    START = 5
    RESULT = 6
    WIN = 7
    LOSE = 8
    FINAL = 9
    FINISHED = -1


class TacticalChallenge(UI):
    select_players = (PLAYER_SELECT_FIRST, PLAYER_SELECT_SECOND, PLAYER_SELECT_THIRD)

    def _get_ticket(self):
        """
        Page:
            in: page_tactical_challenge
        """
        ocr = DigitCounter(OCR_TICKET).ocr_single_line(self.device.image)
        # number of tickets remaining
        ticket, _, total = ocr
        if total == 0:
            logger.warning('Invalid ticket')
            return False, 5
        logger.attr('Ticket', ticket)

        return True, ticket

    def _get_reward(self):
        if self.match_color(GET_REWARD_DAILY):
            self.device.click(GET_REWARD_DAILY)
            logger.info('Get tc daily reward')
            return True
        if self.match_color(GET_REWARD_CREDIT):
            self.device.click(GET_REWARD_CREDIT)
            logger.info('Get tc credit reward')
            return True
        if self.match_color(GOT_REWARD_DAILY) and self.match_color(GOT_REWARD_CREDIT):
            logger.info('Both tc reward got')
            return True

        return False

    def _set_skip(self):
        """
        Set skip switch to on
        :returns: True if switch is set, False if switch not found
        """
        if not SWITCH_SKIP.appear(main=self):
            logger.info('Skip switch not found')
            return False
        SWITCH_SKIP.set('on', main=self)

        return True

    def _player_select(self, select):
        if select:
            return random.choice(self.select_players)
        else:
            return self.select_players[select]

    def _handle_challenge(self, status):
        match status:
            case TCStatus.REWARD:
                if self._get_reward():
                    return TCStatus.OCR
            case TCStatus.OCR:
                is_valid, ticket = self._get_ticket()
                if not is_valid:
                    return status
                if ticket == 0:
                    return TCStatus.FINISHED
                return TCStatus.SELECT
            case TCStatus.SELECT:
                self.appear_then_click(self.select)
                if self.appear(PREPARE_CHALLENGE):
                    return TCStatus.PREPARE
            case TCStatus.PREPARE:
                self.appear_then_click(PREPARE_CHALLENGE)
                if not self.appear(PREPARE_CHALLENGE):
                    return TCStatus.SKIP
            case TCStatus.SKIP:
                if not self._set_skip():
                    return TCStatus.SKIP
                return TCStatus.START
            case TCStatus.START:
                self.appear_then_click(START_CHALLENGE)
                if not self.appear(START_CHALLENGE):
                    return TCStatus.RESULT
            case TCStatus.RESULT:
                if self.appear_then_click(CHALLENGE_WIN):
                    return TCStatus.WIN
                if self.appear_then_click(CHALLENGE_LOSE):
                    return TCStatus.LOSE
            case TCStatus.WIN | TCStatus.LOSE:
                if self.appear(CHALLENGE_WIN) or self.appear(CHALLENGE_LOSE):
                    return TCStatus.RESULT
                is_valid, ticket = self._get_ticket()
                if not is_valid:
                    return status
                if ticket == 0:
                    return TCStatus.FINISHED
                return TCStatus.FINAL
            case TCStatus.FINAL | TCStatus.FINISHED:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        self.ui_ensure(page_tactical_challenge)

        self.select = self._player_select(self.config.TacticalChallenge_PlayerSelect)
        status = TCStatus.REWARD
        action_timer = Timer(1, count=1)
        # ensure reward can be clicked
        ui_timer = Timer(2).start()

        while 1:
            self.device.screenshot()
            if self.ui_additional():
                continue
            if not ui_timer.reached():
                continue
            if action_timer.reached_and_reset():
                logger.attr('Status', status.name)
                status = self._handle_challenge(status)
            if status in (TCStatus.FINAL, TCStatus.FINISHED):
                break

        if status is TCStatus.FINISHED:
            self.config.task_delay(server_update=True)
        else:
            self.config.task_delay(minute=1)
