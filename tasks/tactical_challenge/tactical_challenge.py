import random
from enum import Enum

from module.base.timer import Timer
from module.logger import logger
from tasks.base.page import page_tactical_challenge
from tasks.tactical_challenge.assets.assets_tactical_challenge import *
from tasks.tactical_challenge.ui import TacticalChallengeUI


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


class TacticalChallenge(TacticalChallengeUI):
    select_players = (PLAYER_SELECT_FIRST, PLAYER_SELECT_SECOND, PLAYER_SELECT_THIRD)

    @property
    def current_ticket(self):
        return self.config.stored.TacticalChallengeTicket.value

    def _player_select(self, select):
        if not select:
            return random.choice(self.select_players)
        else:
            return self.select_players[select - 1]

    def _handle_challenge(self, status):
        match status:
            case TCStatus.REWARD:
                if self.ui_additional():
                    return status
                if self.get_reward():
                    return TCStatus.OCR
            case TCStatus.OCR:
                if self.get_ticket():
                    if self.current_ticket == 0:
                        return TCStatus.FINISHED
                    return TCStatus.SELECT
            case TCStatus.SELECT:
                self.appear_then_click(self.select)
                if self.appear(PREPARE_CHALLENGE):
                    return TCStatus.PREPARE
            case TCStatus.PREPARE:
                self.appear_then_click(PREPARE_CHALLENGE)
                if self.appear(START_CHALLENGE):
                    return TCStatus.SKIP
            case TCStatus.SKIP:
                if not self.set_skip():
                    return TCStatus.SKIP
                return TCStatus.START
            case TCStatus.START:
                self.appear_then_click(START_CHALLENGE)
                if self.appear(CHALLENGE_WIN) or self.appear(CHALLENGE_LOSE):
                    return TCStatus.RESULT
            case TCStatus.RESULT:
                if self.appear_then_click(CHALLENGE_WIN):
                    return TCStatus.WIN
                if self.appear_then_click(CHALLENGE_LOSE):
                    return TCStatus.LOSE
            case TCStatus.WIN | TCStatus.LOSE:
                if self.appear_then_click(CHALLENGE_WIN) or self.appear_then_click(CHALLENGE_LOSE):
                    return status
                if self.get_ticket():
                    if self.current_ticket == 0:
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
