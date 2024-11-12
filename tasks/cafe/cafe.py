from enum import Enum

from module.base.timer import Timer
from module.logger import logger
from module.ui.switch import Switch
from tasks.base.page import page_cafe
from tasks.cafe.assets.assets_cafe import *
from tasks.cafe.invitation import handle_invitation
from tasks.cafe.ui import CafeUI

SWITCH_CAFE = Switch('Cafe_switch')
SWITCH_CAFE.add_state('off', CHANGE_CAFE_NOT_SELECTED)
SWITCH_CAFE.add_state('on', CHANGE_CAFE_SELECTED)

SWITCH_CAFE_SELECT = Switch('Cafe_switch_select')
SWITCH_CAFE_SELECT.add_state('1', CAFE_FIRST)
SWITCH_CAFE_SELECT.add_state('2', CAFE_SECOND)


class CafeStatus(Enum):
    STUDENT_LIST = 0
    OCR = 1
    REWARD = 2
    GOT = 3
    INVITATION = 4
    CLICK = 5
    CHECK = 6
    FINISHED = -1


class Cafe(CafeUI):
    @property
    def is_second_cafe_on(self):
        return self.config.Cafe_SecondCafe

    def _handle_cafe(self, status):
        match status:
            case CafeStatus.STUDENT_LIST:
                self.appear_then_click(STUDENT_LIST)
                if not self.appear(STUDENT_LIST):
                    return CafeStatus.OCR
            case CafeStatus.OCR:
                reward = self.get_reward_num()
                if reward == 0:
                    return CafeStatus.GOT
                if self.appear_then_click(CHECK_REWARD):
                    return CafeStatus.REWARD
            case CafeStatus.REWARD:
                if not self.appear(GET_REWARD_CLOSE):
                    self.click_with_interval(CHECK_REWARD)
                    return status
                if self.match_color(GOT_REWARD):
                    self.device.click(GET_REWARD_CLOSE)
                    return CafeStatus.GOT
                if self.match_color(GET_REWARD):
                    self.click_with_interval(GET_REWARD)
            case CafeStatus.GOT:
                logger.info('Cafe reward have been got')
                self.appear_then_click(GET_REWARD_CLOSE)
                if not self.appear(GET_REWARD_CLOSE):
                    return CafeStatus.INVITATION
            case CafeStatus.INVITATION:
                if handle_invitation(self):
                    return CafeStatus.CLICK
            case CafeStatus.CLICK:
                buttons = self.get_clickable_buttons(offset=(45, 10))
                self.click = len(buttons)
                logger.attr('Clickable', self.click)
                if not buttons:
                    return CafeStatus.CHECK
                self.click_with_interval(buttons[0], interval=1)
            case CafeStatus.CHECK:
                buttons = self.get_clickable_buttons()
                if not self.is_adjust_on:
                    if not buttons:
                        return CafeStatus.FINISHED
                    else:
                        return CafeStatus.CLICK
                if not buttons:
                    self.check += 1
                else:
                    self.check = 0
                    return CafeStatus.CLICK
                match self.check:
                    case 1:
                        self.reset_cafe_position('left')
                    case 2:
                        self.reset_cafe_position('right')
                    case 3:
                        self.reset_cafe_position('init')
                    case 4:
                        return CafeStatus.FINISHED
            case CafeStatus.FINISHED:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        self.click = 0
        self.check = 0

        is_reward_on = self.config.Cafe_Reward
        is_touch_on = self.config.Cafe_Touch
        self.is_adjust_on = self.config.Cafe_AutoAdjust

        self.ui_ensure(page_cafe)

        status = CafeStatus.STUDENT_LIST
        loading_timer = Timer(2).start()
        action_timer = Timer(1, count=1)
        is_list = False
        is_reset = False
        is_second = False
        is_enable = is_reward_on or is_touch_on

        while 1:
            if not is_enable:
                break

            self.device.screenshot()

            if self.ui_additional() or self.cafe_additional():
                continue

            if not loading_timer.reached():
                continue

            if not is_list and status == CafeStatus.STUDENT_LIST and self.appear(STUDENT_LIST):
                is_list = True
                loading_timer = Timer(3).start()
                continue

            if not is_reward_on and status == CafeStatus.OCR:
                logger.info('Skip reward')
                status = CafeStatus.CLICK
                continue

            if not is_touch_on and status == CafeStatus.CLICK:
                logger.info('Skip touch')
                status = CafeStatus.FINISHED
                continue

            if is_touch_on and not is_reset and status == CafeStatus.CLICK:
                self.reset_cafe_position('init')
                is_reset = True
                continue

            if self.is_second_cafe_on and not is_second and status == CafeStatus.FINISHED:
                if not SWITCH_CAFE.appear(main=self):
                    logger.warning('Cafe switch not found')
                    continue
                if SWITCH_CAFE.get(main=self) == 'off':
                    SWITCH_CAFE.set('on', main=self)
                    logger.info('Switching to second cafe')
                if not SWITCH_CAFE_SELECT.appear(main=self):
                    logger.info('Cafe switch select not found')
                    continue
                match (SWITCH_CAFE_SELECT.get(main=self)):
                    case '1':
                        if self.click_with_interval(CAFE_SECOND):
                            continue
                    case '2':
                        logger.info('Cafe second arrived')
                        SWITCH_CAFE.set('off', main=self)
                        status = CafeStatus.STUDENT_LIST
                        is_list = False
                        is_second = True
                        self.check = 0

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self._handle_cafe(status)

            if not self.is_second_cafe_on:
                if status is CafeStatus.FINISHED:
                    logger.info('Second cafe is not supported or disabled')
                    logger.info('Cafe finished')
                    break
            else:
                if is_second and status is CafeStatus.FINISHED:
                    logger.info('Cafe finished')
                    break

        self.config.task_delay(server_update=True, minute=180)
