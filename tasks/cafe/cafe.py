import cv2
import numpy as np
from enum import Enum

from module.logger import logger
from module.base.timer import Timer
from module.base.button import ClickButton
from module.base.utils.utils import area_offset
from module.ocr.ocr import Digit
from tasks.base.page import page_cafe
from tasks.base.ui import UI
from tasks.cafe.assets.assets_cafe import *


class CafeStatus(Enum):
    STUDENT_LIST = 0
    OCR = 1
    REWARD = 2
    GOT = 3
    CLICK = 4
    CHECK = 5
    FINISHED = -1


class Cafe(UI):
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
        lower_hsv = np.array([17, 200, 220])
        upper_hsv = np.array([28, 255, 255])
        # get mask
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        # generate result
        return cv2.bitwise_and(image, image, mask=mask)

    def _match_clickable_points(self, image, threshold=0.9):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = self.btn.matched_button.image
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        return [point for point in zip(*loc[::-1])]

    def _get_clickable_buttons(self, threshold=0.9, offset=(0, 0)):
        image = cv2.copyMakeBorder(self.device.image, 20, 20, 10, 60, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        image = self._extract_clickable_from_image(image)
        points = self._match_clickable_points(image, threshold)
        points = self.merge_points(points)
        if not points:
            return []
        area = area_offset((0, 0, self.btn.width, self.btn.height), offset)
        return [
            ClickButton(
                button=area_offset(area, offset=point),
                name=self.btn.name
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

    def _get_reward_num(self):
        ocr = Digit(OCR_CAFE)
        num = ocr.detect_and_ocr(self.device.image)
        if len(num) != 1:
            logger.warning(f'Invalid reward num: {num}')
        num = float(num[0].ocr_text.rstrip('%'))
        logger.attr('Reward', num)
        return num

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
                if self.match_color(GOT_REWARD):
                    self.device.click(GET_REWARD_CLOSE)
                    return CafeStatus.GOT
                if not self.appear(GET_REWARD):
                    return CafeStatus.OCR
                if self.match_color(GET_REWARD):
                    self.device.click(GET_REWARD)
            case CafeStatus.GOT:
                logger.info('Cafe reward have been got')
                self.appear_then_click(GET_REWARD_CLOSE)
                return CafeStatus.CLICK
            case CafeStatus.CLICK:
                buttons = self._get_clickable_buttons(offset=(45, 10))
                self.click = len(buttons)
                logger.attr('Clickable', self.click)
                if not buttons:
                    return CafeStatus.CHECK
                self.device.click(buttons[0])
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
        self.btn = CLICKABLE_TEMPLATE
        self.click = 0
        self.check = 0

        is_reward_on = self.config.Cafe_Reward
        is_touch_on = self.config.Cafe_Touch
        self.is_adjust_on = self.config.Cafe_AutoAdjust

        self.ui_ensure(page_cafe)

        status = CafeStatus.STUDENT_LIST
        loading_timer = Timer(2).start()
        action_timer = Timer(1.5, count=1)  # cant be too fast
        check_timer = Timer(1, count=1)
        is_list = False
        is_reset = False
        is_enable = is_reward_on or is_touch_on

        while is_enable:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if not loading_timer.reached():
                continue

            if not is_list and status == CafeStatus.STUDENT_LIST and self.appear(STUDENT_LIST):
                is_list = True
                loading_timer = Timer(5).start()
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

            if status == CafeStatus.CHECK and not check_timer.reached_and_reset():
                continue

            if action_timer.reached_and_reset():
                status = self._handle_cafe(status)
                logger.attr('Status', status)

            if status is CafeStatus.FINISHED:
                break

        self.config.task_delay(server_update=True, minute=180)
