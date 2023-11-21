import cv2
import numpy as np

from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.ui import UI
from tasks.cafe.assets.assets_cafe import *


class CafeUI(UI):
    template = CLICKABLE_TEMPLATE

    def get_reward_num(self):
        ocr = Digit(OCR_CAFE)
        num = ocr.detect_and_ocr(self.device.image)
        if len(num) != 1:
            logger.warning(f'Invalid reward num: {num}')
        num = float(num[0].ocr_text.rstrip('%'))
        logger.attr('Reward', num)
        return num

    @staticmethod
    def extract_clickable_from_image(image):
        # convert to hsv for better color matching
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        # set color range
        lower_hsv = np.array([18, 200, 220])
        upper_hsv = np.array([30, 255, 255])
        # get mask
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        # generate result
        return cv2.bitwise_and(image, image, mask=mask)

    def get_clickable_buttons(self, similarity=0.8, offset=(45, 10)):
        image = self.extract_clickable_from_image(self.device.image)
        self.template.matched_button._button_offset = offset
        self.template.load_offset(self.template)
        self.template.load_search(BOX_SEARCH.area)
        points = self.template.match_multi_template(image, similarity)
        return points

    def reset_cafe_position(self, direction: str):
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

    def cafe_additional(self) -> bool:
        if self.appear_then_click(INVENTORY):
            return True
        if self.appear_then_click(MOMOTALK_CLOSE):
            return True
        return False
