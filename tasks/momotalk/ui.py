from module.base.timer import Timer
from module.base.base import ModuleBase
from module.logger import logger
from module.ui.switch import Switch
from module.base.utils import point_in_area, area_size
from tasks.base.ui import UI
from tasks.base.page import page_main, page_momo_talk
from tasks.momotalk.assets.assets_momotalk import *
import cv2
import numpy as np

"""None of the switches works"""
SWITCH_MESSAGE = Switch("Message_switch")
SWITCH_MESSAGE.add_state("on", MESSAGE_ON)
SWITCH_MESSAGE.add_state("off", MESSAGE_OFF)

SWITCH_UNREAD = Switch("Unread_switch")
SWITCH_UNREAD.add_state("on", UNREAD_ON)
SWITCH_UNREAD.add_state("off", UNREAD_OFF)

SWITCH_SORT = Switch("Sort_switch")
SWITCH_SORT.add_state("on", SORT_ON)
SWITCH_SORT.add_state("off", SORT_OFF)

"""Required for template matching as reply and story 
button can be found in different locations"""
REPLY_TEMPLATE = REPLY.matched_button.image
STORY_TEMPLATE = STORY.matched_button.image

class MomoTalkUI(UI):
    def __init__(self, config, device):
        super().__init__(config, device)
        self.swipe_vector_range = (0.65, 0.85)
        self.list = CHAT_AREA

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
        width, height = area_size(self.list.button)
        if direction == 'up':
            vector = (0, vector * height)
        elif direction == 'down':
            vector = (0, -vector * height)
        else:
            logger.warning(f'Unknown swipe direction: {direction}')
            return

        if reverse:
            vector = (-vector[0], -vector[1])
        main.device.swipe_vector(vector, self.list.button)

    def select_then_check(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper, similarity=0.85):
        timer = Timer(5, 10).start()
        while 1:
            self.device.screenshot()
            self.appear_then_click(dest_enter, interval=1, similarity=similarity)
            if self.appear(dest_check, similarity=similarity):
                return True
            if timer.reached():
                return False

    def select_then_disappear(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper, force_select=False):
        timer = Timer(5, 10).start()
        while 1:
            self.device.screenshot()
            if force_select or self.appear(dest_enter):
                self.click_with_interval(dest_enter, interval=1)
            if not self.appear(dest_check):
                return True
            if timer.reached():
                return False

    def set_switch(self, switch):
        """
        Set switch to on. However, unsure why is inaccurate in momotalk.
        Returns:
            True if switch is set, False if switch not found
        """
        if not switch.appear(main=self):
            logger.info(f'{switch.name} not found')
            return False
        switch.set('on', main=self)

        return True
    
    def click_all(self, template, x_add=0, y_add=0):
        """
        Find the all the locations of the template adding an offset if specified and click them. 
        TODO: filter coords that are not inside the chat area as otherwise it will close momotalk.
        If after filter, no coords then swipe.
        """
        click_coords = self.device.click_methods.get(self.config.Emulator_ControlMethod, self.device.click_adb)
        image = self.device.screenshot()
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)
        seen = set()
        for pt in zip(*locations[::-1]):
            center_pt = (int(pt[0] + template.shape[1] / 2 + x_add), int(pt[1] + template.shape[0] / 2 + y_add))
            seen.add(center_pt)
        if seen:
            seen = filter(lambda x: point_in_area(x, CHAT_AREA.area), seen)
            [click_coords(coords[0], coords[1]) for coords in seen]
            self.swipe_page("down", self)
            return True
        return False

    def open_momotalk(self):
        """
        Go to main and check if there are any red notifications in momotalk.
        If yes, open it otherwise it means no student available for interaction.
        """
        self.ui_ensure(page_main)
        if self.match_color(NOTIFICATION_BADGE, threshold=80):
            self.ui_ensure(page_momo_talk)
            while not self.select_then_check(MESSAGE_OFF, MESSAGE_ON):
                pass
            return True
        logger.warn("No students available for interaction")
        return False
    
    def sort_messages(self):
        """
        Switch from newest to unread and sort the messages in descending order
        """
        logger.info("Sorting messages...")
        steps = [UNREAD, CONFIRM_SORT, UNREAD_OFF, UNREAD_ON]
        for i in range(len(steps)-2):
            self.select_then_check(steps[i], steps[i+1], similarity=0.95)    
        return not self.appear(CONFIRM_SORT) and self.appear(UNREAD) and self.appear(SORT_ON)

    def check_first_student(self):
        """
        If the first student has a red notification return True and start chat. 
        Otherwise it means no students are available for interaction.
        """
        if self.match_color(FIRST_UNREAD, threshold=80) and self.select_then_disappear(FIRST_UNREAD, SELECT_STUDENT, force_select=True):
            return True
        logger.warn("No students available for interaction")
        return False
    
    def chat(self):
        """
        Waits for the chat area to be stable and then 
        check if a reply or story button is found and click them. 
        If the begin story button is found skip story.
        """
        logger.info("Chatting with student...")
        stability_counter = 0
        while 1:
            self.wait_until_stable(CHAT_AREA, timer=Timer(10, 10))
            if self.appear(BEGIN_STORY):
                logger.info("Begin Story detected")
                return True
            if self.click_all(REPLY_TEMPLATE, y_add=62):
                logger.info("Clicked on reply")
                stability_counter = 0
                continue
            if self.click_all(STORY_TEMPLATE, y_add=62):
                logger.info("Clicked on story")
                stability_counter = 0
                continue
            logger.info("No new message detected")
            stability_counter += 1
            if stability_counter > 3:
                return False        
                
    def skip_story(self):
        """
        Skip story by executing a series of steps. Returns True if the confirm skip
        button is clicked and disappears 
        """
        logger.info("Attempting to skip story...")
        steps = [BEGIN_STORY, MENU, SKIP]
        for step in steps:
            self.appear_then_click(step)
        if self.appear_then_click(CONFIRM_SKIP) and not self.appear(CONFIRM_SKIP, interval=5):
            logger.info("Skipped story successfully")
            return True
        return False

