from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.base.assets.assets_base_page import SCHEDULE_CHECK
from tasks.schedule.assets.assets_schedule import *
from tasks.schedule.scroll_select import ScrollSelect
import numpy as np


SCROLL_SELECT = ScrollSelect(window_button=SCROLL, first_item_button=FIRST_ITEM, expected_button=LOCATIONS, clickx=1114)
xs = np.linspace(299, 995, 3, dtype=int)
ys = np.linspace(268, 573, 3, dtype=int)

class ScheduleUI(UI):
    def select_then_check(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper):
        timer = Timer(8, 10).start()
        while 1:
            self.device.screenshot()
            self.appear_then_click(dest_enter, interval=1)
            self.handle_affection_level_up()
            if self.appear(dest_check):
                return True
            
            if timer.reached():
                return False
    
    def click_then_check(self, coords, dest_check: ButtonWrapper):
        click_coords = self.device.click_methods.get(self.config.Emulator_ControlMethod, self.device.click_adb)
        timer = Timer(3, 5).start()
        wait = Timer(1).start()
        while 1:
            click_coords(*coords)
            self.device.screenshot()
            if self.appear_then_click(dest_check):
                return True
            while not wait.reached_and_reset():
                pass
            if timer.reached():
                return False
            
    def enter_location(self, location):
        SCROLL_SELECT.select_location(self, location)
        if not self.appear(LOCATIONS):
            logger.error("Unable to navigate to page for location {}".format(location + 1))
            return False
        return self.select_then_check(LOCATIONS, LOCATIONS_POPUP)
                    
    def select_classrooms(self, ticket, classrooms):
        for classroom in classrooms:
            if ticket == 0:
                return False
            classroom = int(classroom) - 1
            col = int(classroom % len(xs))
            row = int((classroom - col) / len(ys))
            targetloc = (xs[col], ys[row])
            if not self.click_then_check(targetloc, START_LESSON):
                logger.info(f"Classroom {classroom + 1} does not exist or has already been clicked")
                continue
            if self.select_then_check(START_LESSON, CONFIRM):
                ticket -= 1
            if not self.select_then_check(CONFIRM, LOCATIONS_POPUP):
                break
        return True

    def get_ticket(self):
        """
        Page:
            in: page_bounty
        """
        if not self.appear(SCHEDULE_CHECK):
            logger.warning('OCR failed due to invalid page')
            return False
        ticket, _, total = DigitCounter(OCR_TICKET).ocr_single_line(self.device.image)
        if total == 0:
            logger.warning('Invalid ticket')
            return False
        logger.attr('ScheduleTicket', ticket)
        #self.config.stored.BountyTicket.set(ticket)
        return ticket
