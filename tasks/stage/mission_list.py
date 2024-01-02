import re

import numpy as np

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_pad, area_size, area_offset
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.stage.assets.assets_stage_list import *


class StageList:
    swipe_vector_range = (0.65, 0.70)

    def __init__(
            self,
            name,
            button_list: ButtonWrapper = None,
            button_index: ButtonWrapper = None,
            button_item: ButtonWrapper = None,
            button_enter: ButtonWrapper = None,
            button_stars: ButtonWrapper = None,
            swipe_direction: str = "down"
    ):
        self.name = name
        self.stage = button_list if button_list else STAGE_LIST
        self.index_ocr = Ocr(button_index if button_index else OCR_INDEX, lang='zhs')
        self.stage_item = (button_item if button_item else STAGE_ITEM).button
        self.enter = button_enter if button_enter else STAGE_ENTER
        self.sweepable = button_stars if button_stars else STAGE_STARS
        self.swipe_direction = swipe_direction

        self.current_index_min = 1
        self.current_index_max = 1
        self.current_indexes: list[tuple[str, tuple]] = []

    def __str__(self):
        return f'StageList({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    @property
    def _indexes(self) -> list[int]:
        return [x[0] for x in self.current_indexes]

    def load_stage_indexes(self, main: ModuleBase):
        self.current_indexes = list(
            filter(
                lambda x: re.match(r'^\d{1,2}-?[\dA-Z]$', x[0]) and x[0] != '00',
                map(lambda x: (x.ocr_text, x.box), self.index_ocr.detect_and_ocr(main.device.image))
            )
        )
        if not self.current_indexes:
            logger.warning(f'No valid index in {self.index_ocr.name}')
            return
        indexes = self._indexes

        self.current_index_min = min(indexes)
        self.current_index_max = max(indexes)
        logger.attr(self.index_ocr.name, f'Index range: {self.current_index_min} - {self.current_index_max}')

    def swipe_page(self, direction: str, main: ModuleBase, vector_range=None, reverse=False):
        """
        Args:
            direction: up, down
            main:
            vector_range (tuple[float, float]):
            reverse (bool):
        """
        if vector_range is None:
            vector_range = self.swipe_vector_range
        vector = np.random.uniform(*vector_range)
        width, height = area_size(self.stage.button)
        if direction == 'up':
            vector = (0, vector * height)
        elif direction == 'down':
            vector = (0, -vector * height)
        else:
            logger.warning(f'Unknown swipe direction: {direction}')
            return

        if reverse:
            vector = (-vector[0], -vector[1])
        main.device.swipe_vector(vector, self.stage.button, name=f'{self.name}_SWIPE')

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
                return True

            indexes = self._indexes
            if indexes and last_indexes == set(indexes):
                logger.warning(f'No more index {index}')
                return False
            last_indexes = set(indexes)

            if index < self.current_index_min:
                self.swipe_page(self.swipe_direction, main, reverse=True)
            elif index > self.current_index_max:
                self.swipe_page(self.swipe_direction, main)

            main.wait_until_stable(
                self.stage.button,
                timer=Timer(0, 0),
                timeout=Timer(1.5, 5)
            )

    def insight_max_sweepable_index(self, main: ModuleBase, skip_first_screenshot=True) -> int:
        """
        Args:
            main:
            skip_first_screenshot:

        Returns:
            Index of max sweepable stage
        """
        logger.info('Insight sweepable index')
        max_sweepable_index = 0
        last_max_sweepable_index = 0

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_stage_indexes(main=main)

            sweepable_index = next(
                filter(
                    lambda x: not self.is_sweepable(main, self.search_box(x[-1][:2])),
                    self.current_indexes
                ), None
            )

            # all sweepable
            if sweepable_index is None:
                logger.info('All sweepable')
                max_sweepable_index = self.current_index_max
                self.swipe_page(self.swipe_direction, main)
                if max_sweepable_index == last_max_sweepable_index:
                    logger.info(f'Max sweepable index: {max_sweepable_index}')
                    return max_sweepable_index
                last_max_sweepable_index = max_sweepable_index
            # all not sweepable
            elif int(sweepable_index[0]) == self.current_index_min:
                logger.info('All not sweepable')
                if int(sweepable_index[0]) == 1:
                    logger.warning('No sweepable index')
                    return 0
                self.swipe_page(self.swipe_direction, main, reverse=True)
            else:
                logger.info(f'Sweepable index: {int(sweepable_index[0]) - 1}')
                return int(sweepable_index[0]) - 1

            main.wait_until_stable(
                self.stage.button,
                timer=Timer(0, 0),
                timeout=Timer(1.5, 5)
            )

    def is_sweepable(self, main: ModuleBase, search_box) -> bool:
        self.sweepable.load_search(search_box)
        return main.appear(self.sweepable, similarity=0.8)

    def search_box(
            self,
            index_cord: tuple[int, int],
            padding: tuple[int, int] = (-20, -15)
    ) -> tuple[int, int, int, int]:
        stage_item_box = area_pad((*padding, *area_size(self.stage_item)))
        return area_offset(stage_item_box, index_cord)

    def select_index_enter(
            self,
            main: ModuleBase,
            index: int,
            insight: bool = True,
            sweepable: bool = True,
            padding: tuple[int, int] = (-20, -15),
            skip_first_screenshot: bool = True,
            interval: int = 1.5
    ) -> bool:
        # insight index, if failed, return False
        if insight and not self.insight_index(index, main, skip_first_screenshot):
            return False
        logger.info(f'Select index: {index}')
        click_interval = Timer(interval)
        load_index_interval = Timer(1)
        timeout = Timer(15, 10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # load index if not insight
            if load_index_interval.reached_and_reset():
                self.load_stage_indexes(main=main)

            # find box of index
            index_box = next(filter(lambda x: x[0] == index, self.current_indexes), None)

            if index_box is None:
                logger.warning(f'No index {index} in {self.index_ocr.name}')
                continue

            search_box = self.search_box(index_box[-1][:2], padding)
            if sweepable and not self.is_sweepable(main, search_box):
                logger.warning(f'Index {index} is not sweepable')
                return False

            self.enter.load_search(search_box)
            click_button = self.enter.match_multi_template(main.device.image)

            if not click_button:
                logger.warning(f'No clickable {self.enter.name}')
                continue

            if click_interval.reached_and_reset():
                main.device.click(click_button[0])
                return True

            if timeout.reached():
                logger.warning(f'{self.enter.name} failed')
                return False
