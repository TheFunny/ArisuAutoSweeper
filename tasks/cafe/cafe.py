import cv2
import numpy as np
from enum import Enum

from module.logger import logger
from module.base.timer import Timer
from module.base.button import ClickButton
from module.base.utils.utils import area_offset
from module.ocr.ocr import Digit
from module.ui.switch import Switch
from tasks.base.page import page_cafe
from tasks.base.ui import UI
from tasks.cafe.assets.assets_cafe import *


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
    CLICK = 4
    CHECK = 5
    FINISHED = -1


class Cafe(UI):
    template = CLICKABLE_TEMPLATE

    @staticmethod
    def merge_points(points, threshold=3):
        if len(points) <= 1:
            return points
        result = []
        for point in points:
            if not result:
                result.append(point)
                continue
            if point[0] - result[-1][0] < threshold and point[1] - result[-1][1] < threshold:
                result[-1] = ((point[0] + result[-1][0]) // 2, (point[1] + result[-1][1]) // 2)
                continue
            result.append(point)
        return result

    @staticmethod
    def _extract_clickable_from_image(image):
        # convert to hsv for better color matching
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # set color range
        lower_hsv = np.array([18, 200, 220])
        upper_hsv = np.array([30, 255, 255])
        # get mask
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        # generate result
        return cv2.bitwise_and(image, image, mask=mask)

    def _match_clickable_points(self, image, threshold=0.8):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(self.template.matched_button.image, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        return [point for point in zip(*loc[::-1])]

    def _get_clickable_buttons(self, threshold=0.8, offset=(0, 0)):
        image = self.device.image
        h, w = image.shape[:2]
        image = cv2.rectangle(image, (0, 10), (w - 25, h - 10), (0, 0, 0), 50)
        image = self._extract_clickable_from_image(image)
        points = self._match_clickable_points(image, threshold)
        points = self.merge_points(points)
        if not points:
            return []
        area = area_offset((0, 0, self.template.width, self.template.height), offset)
        return [
            ClickButton(
                button=area_offset(area, offset=point),
                name=self.template.name
            )
            for point in points
        ]

    def _reset_cafe_position(self, direction: str):
        width = BOX_CAFE.width
        height = BOX_CAFE.height
        r = np.random.uniform(0.6, 0.8)
        vector_down = (width * r, height * r)
        vector_up = (width * r, -height * r)
        vector_left = (-width * r, 0)
        vector_right = (width * r, 0)
        random_r = (-5, -5, 5, 5)
        match direction:
            case 'init':
                self.device.pinch()
                self.device.swipe_vector(vector_down, box=BOX_CAFE.area, random_range=random_r, padding=5)
                self.device.swipe_vector(vector_right, box=BOX_CAFE.area, random_range=random_r, padding=5)
                self.device.swipe_vector(vector_up, box=BOX_CAFE.area, random_range=random_r, padding=5)
                self.device.swipe_vector(vector_up, box=BOX_CAFE.area, random_range=random_r, padding=5)
            case 'left':
                self.device.swipe_vector(vector_left, box=BOX_CAFE.area, random_range=random_r, padding=5)
                self.device.swipe_vector(vector_left, box=BOX_CAFE.area, random_range=random_r, padding=5)
            case 'right':
                self.device.swipe_vector(vector_right, box=BOX_CAFE.area, random_range=random_r, padding=5)
                self.device.swipe_vector(vector_right, box=BOX_CAFE.area, random_range=random_r, padding=5)
        # solve too much swipe causing restart
        self.device.click_record_clear()

    def _get_reward_num(self):
        ocr = Digit(OCR_CAFE)
        num = ocr.detect_and_ocr(self.device.image)
        if len(num) != 1:
            logger.warning(f'Invalid reward num: {num}')
        num = float(num[0].ocr_text.rstrip('%'))
        logger.attr('Reward', num)
        return num

    def _cafe_additional(self) -> bool:
        if self.appear_then_click(INVENTORY):
            return True
        if self.appear_then_click(MOMOTALK_CLOSE):
            return True
        return False

    def _handle_cafe(self, status):
        match status:
            case CafeStatus.STUDENT_LIST:
                self.appear_then_click(STUDENT_LIST)
                if not self.appear(STUDENT_LIST):
                    return CafeStatus.OCR
            case CafeStatus.OCR:
                reward = self._get_reward_num()
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
                    return CafeStatus.CLICK
            case CafeStatus.CLICK:
                buttons = self._get_clickable_buttons(offset=(45, 10))
                self.click = len(buttons)
                logger.attr('Clickable', self.click)
                if not buttons:
                    return CafeStatus.CHECK
                self.click_with_interval(buttons[0], interval=1)
            case CafeStatus.CHECK:
                buttons = self._get_clickable_buttons()
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
                        self._reset_cafe_position('left')
                    case 2:
                        self._reset_cafe_position('right')
                    case 3:
                        self._reset_cafe_position('init')
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
        is_second_cafe_on = self.config.Cafe_SecondCafe

        self.ui_ensure(page_cafe)

        status = CafeStatus.STUDENT_LIST
        loading_timer = Timer(2).start()
        action_timer = Timer(1, count=1)  # cant be too fast
        is_list = False
        is_reset = False
        is_second = False
        is_enable = is_reward_on or is_touch_on

        while 1:
            if not is_enable:
                break

            self.device.screenshot()

            if self.ui_additional() or self._cafe_additional():
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
                self._reset_cafe_position('init')
                is_reset = True
                continue

            if is_second_cafe_on and not is_second and status == CafeStatus.FINISHED:
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

            if not is_second_cafe_on:
                if status is CafeStatus.FINISHED:
                    break
            else:
                if is_second and status is CafeStatus.FINISHED:
                    break

        self.config.task_delay(server_update=True, minute=180)
