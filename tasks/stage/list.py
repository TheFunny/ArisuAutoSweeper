import cv2
import numpy as np

from module.base.base import ModuleBase
from module.base.button import ButtonWrapper, ClickButton
from module.base.timer import Timer
from module.base.utils import area_pad, area_size, area_offset, random_rectangle_vector_opted
from module.logger import logger
from module.ocr.ocr import Ocr


class StageList:
    drag_vector_range = (0.65, 0.85)

    def __init__(
            self,
            name,
            area_stage: ButtonWrapper,
            area_index: ButtonWrapper,
            area_item: ButtonWrapper,
            button_enter: ButtonWrapper,
            drag_direction: str = "down"
    ):
        self.name = name
        self.stage = area_stage
        self.index_ocr = Ocr(area_index, lang='en')
        self.stage_item = area_item.button
        self.enter = button_enter
        self.drag_direction = drag_direction

        self.current_index_min = 1
        self.current_index_max = 1
        self.current_indexes = []

    def __str__(self):
        return f'StageList({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    @property
    def _indexes(self) -> list[int]:
        return list(map(lambda x: int(x.ocr_text), self.current_indexes))

    def load_stage_indexes(self, main: ModuleBase):
        self.current_indexes = list(
            filter(lambda x: x.ocr_text.isdigit(), self.index_ocr.detect_and_ocr(main.device.image))
        )
        if not self.current_indexes:
            logger.warning(f'No valid index in {self.index_ocr.name}')
            return
        indexes = self._indexes

        self.current_index_min = min(indexes)
        self.current_index_max = max(indexes)
        logger.attr(self.index_ocr.name, f'Index range: {self.current_index_min} - {self.current_index_max}')

    def drag_page(self, direction: str, main: ModuleBase, vector_range=None, reverse=False):
        """
        Args:
            direction: up, down
            main:
            vector_range (tuple[float, float]):
            reverse (bool):
        """
        if vector_range is None:
            vector_range = self.drag_vector_range
        vector = np.random.uniform(*vector_range)
        width, height = area_size(self.stage.button)
        if direction == 'up':
            vector = (0, vector * height)
        elif direction == 'down':
            vector = (0, -vector * height)
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return

        if reverse:
            vector = (-vector[0], -vector[1])
        p1, p2 = random_rectangle_vector_opted(vector, box=self.stage.button)
        main.device.drag(p1, p2, name=f'{self.name}_DRAG')

    def insight_index(self, index: int, main: ModuleBase, skip_first_screenshot=True) -> bool:
        """
        Args:
            index:
            main:
            skip_first_screenshot:

        Returns:
            If success
        """
        logger.info(f'Insight index: {index}')
        last_indexes: set[int] = set()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_stage_indexes(main=main)

            if self.current_index_min <= index <= self.current_index_max:
                break

            if index < self.current_index_min:
                self.drag_page(self.drag_direction, main, reverse=True)
            elif index > self.current_index_max:
                self.drag_page(self.drag_direction, main)

            main.wait_until_stable(
                self.stage.button,
                timer=Timer(0, 0),
                timeout=Timer(1.5, 5)
            )

            indexes = self._indexes
            if indexes and last_indexes == set(indexes):
                logger.warning(f'No more index {index}')
                return False
            last_indexes = set(indexes)

        return True

    @staticmethod
    def _match_clickable_points(image, template, threshold=0.85):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        return [point for point in zip(*loc[::-1])]

    def select_index_enter(
            self,
            index: int,
            main: ModuleBase,
            insight: bool = True,
            skip_first_screenshot: bool = True,
            interval: int = 5
    ) -> bool:
        if insight and not self.insight_index(index, main, skip_first_screenshot):
            return False
        logger.info(f'Select index: {index}')
        click_interval = Timer(interval)
        load_index_interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if load_index_interval.reached_and_reset():
                self.load_stage_indexes(main=main)

            index_box = next(filter(lambda x: int(x.ocr_text) == index, self.current_indexes), None)

            if index_box is None:
                logger.warning(f'No index {index} in {self.index_ocr.name}')
                return False

            stage_item_box = area_pad((0, 0, *area_size(self.stage_item)))
            search_box = area_offset(stage_item_box, index_box.box[:2])
            search_image = main.image_crop(search_box)
            points = self._match_clickable_points(search_image, self.enter.matched_button.image)

            if not points:
                logger.warning(f'No clickable {self.enter.name}')
                return False

            point = area_offset((0, 0, *area_size(self.enter.button)), points[0])
            click_button = ClickButton(area_offset(point, search_box[:2]), name=self.enter.name)

            if click_interval.reached_and_reset():
                main.device.click(click_button)
                return True
