import numpy as np

from module.base.timer import Timer
from module.base.utils import area_size
from module.logger import logger
from module.ui.switch import Switch
from tasks.base.page import page_main, page_momo_talk
from tasks.base.ui import UI
from tasks.momotalk.assets.assets_momotalk import *

SWITCH_SIDEBAR = Switch("Sidebar_switch", is_selector=True)
SWITCH_SIDEBAR.add_state("student", SWITCH_STUDENT_CHECK, SWITCH_STUDENT)
SWITCH_SIDEBAR.add_state("message", SWITCH_MESSAGE_CHECK, SWITCH_MESSAGE)

SWITCH_UNREAD = Switch("Unread_switch")
SWITCH_UNREAD.add_state("on", UNREAD_ON)
SWITCH_UNREAD.add_state("off", UNREAD_OFF)

SWITCH_SORT = Switch("Sort_switch")
SWITCH_SORT.add_state("ascending", SORT_ASCENDING)
SWITCH_SORT.add_state("descending", SORT_DESCENDING)

"""Required for template matching as reply and story 
button can be found in different locations"""
REPLY_TEMPLATE = REPLY
STORY_TEMPLATE = STORY
CHATTING_TEMPLATE = CHATTING


class MomoTalkUI(UI):
    swipe_vector_range = (0.65, 0.85)
    list = CHAT_AREA

    def swipe_page(self, direction: str, vector_range=None, reverse=False):
        """
        Args:
            direction: up, down
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
        self.device.swipe_vector(vector, self.list.button)

    def select_then_disappear(self, dest_enter: ButtonWrapper, dest_check: ButtonWrapper):
        timer = Timer(5, 10).start()
        while 1:
            self.device.screenshot()
            self.click_with_interval(dest_enter, interval=1)
            if not self.appear(dest_check):
                return True
            if timer.reached():
                return False

    def set_switch(self, switch, state='on'):
        """
        Set switch to on. However, unsure why is inaccurate in momotalk.
        Returns:
            True if switch is set, False if switch not found
        """
        if not switch.appear(main=self):
            logger.info(f'{switch.name} not found')
            return False
        switch.set(state, main=self)

        return True

    def click_all(self, template: ButtonWrapper, offset: tuple[int, int] = (0, 0)) -> bool:
        """
        Find the all the locations of the template adding an offset if specified and click them. 
        If after filter, no coords then swipe.
        """
        template.load_search(self.list.area)
        template.matched_button._button_offset = offset
        seen = template.match_multi_template(self.device.image, similarity=0.8)
        if seen:
            if any(offset):
                for button in seen:
                    self.device.click(button)
                self.swipe_page("down")
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
            while SWITCH_SIDEBAR.get(self) != "message":
                SWITCH_SIDEBAR.set("message", self)
            return True
        logger.warning("No students available for interaction")
        return False

    def sort_messages(self):
        """
        Switch from newest to unread and sort the messages in descending order
        """
        while 1:
            self.device.screenshot()
            if self.set_switch(SWITCH_UNREAD):
                self.click_with_interval(CONFIRM_SORT, interval=2)
                continue
            if self.appear(UNREAD, similarity=0.95):
                break
            self.click_with_interval(UNREAD, interval=2)
        return self.set_switch(SWITCH_SORT, "descending")

    def check_first_student(self):
        """
        If the first student has a red notification return True and start chat. 
        Otherwise it means no students are available for interaction.
        """
        if self.match_color(FIRST_UNREAD, threshold=80) and self.select_then_disappear(FIRST_UNREAD, SELECT_STUDENT):
            return True
        logger.warning("No students available for interaction")
        return False

    def chat(self):
        """
        Waits for the chat area to be stable and then 
        check if a reply or story button is found and click them. 
        If the begin story button is found skip story.
        """
        timer = Timer(8, 5).start()
        logger.info("Chatting with student...")
        while 1:
            self.device.screenshot()
            if self.appear(BEGIN_STORY):
                logger.info("Begin Story detected")
                return True
            elif self.click_all(CHATTING_TEMPLATE):
                timer.reset()
            elif self.click_all(REPLY_TEMPLATE, offset=(0, 62)):
                logger.info("Clicked on reply")
                timer.reset()
            elif self.click_all(STORY_TEMPLATE, offset=(0, 62)):
                logger.info("Clicked on story")
                timer.reset()
            elif timer.reached():
                logger.info("No new message detected")
                return False

    def skip_story(self):
        """
        Skip story by executing a series of steps. Returns True if the confirm skip
        button is clicked and disappears 
        """
        logger.info("Attempting to skip story...")
        steps = [CONFIRM_SKIP, SKIP, MENU, BEGIN_STORY]
        timer = Timer(1).start()
        while 1:
            self.device.screenshot()
            if self.handle_reward():
                logger.info("Skipped story successfully")
                return True
            for step in steps:
                if self.appear_then_click(step):
                    while not timer.reached_and_reset():
                        pass
                    break
