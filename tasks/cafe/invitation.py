import re
from datetime import datetime, timedelta
from enum import Enum

import numpy as np

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_size, area_offset
from module.config.utils import get_server_next_update
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.cafe.assets.assets_cafe import *


class InvitationOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('モI', 'モエ')
        return result


class InvitationStatus(Enum):
    MOMOTALK = 0
    OCR = 1
    SELECT = 2
    CONFIRM = 3
    SUBSTITUTE = 4
    IN_SECOND = 5
    INVITED = 6
    FAILED = 7
    FINISHED = -1


class Invitation:
    swipe_vector_range = (0.65, 0.85)
    cafe_update = ["04:00", "16:00"]

    def __init__(self, name: str):
        self.name = name
        self.ocr = InvitationOcr(OCR_NAME)
        self.list = OCR_NAME
        self.item = MOMOTALK_ITEM
        self.invite = MOMOTALK_INVITE

        self.target_names = []
        self.waiting_hour = None
        self.substitute = None
        self.choice = None

        self.invited = []
        self.current_names = []

    def __str__(self):
        return f'Invitation({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def swipe_page(self, main: ModuleBase, vector_range=None, reverse=False):
        """
        Args:
            main:
            vector_range (tuple[float, float]):
            reverse (bool):
        """
        if vector_range is None:
            vector_range = self.swipe_vector_range
        vector = np.random.uniform(*vector_range)
        width, height = area_size(self.list.button)
        vector = (0, -vector * height)

        if reverse:
            vector = (-vector[0], -vector[1])
        name = f'{self.name}_SWIPE'
        main.device.swipe_vector(vector, self.list.button, name=name)
        main.device.click_record_remove(name)

    def load_names(self, main: ModuleBase):
        names = self.ocr.detect_and_ocr(main.device.image)
        if not names:
            logger.warning(f'No valid names in {self.ocr.name}')
            return
        self.current_names = []
        for name_ in names:
            name: str = name_.ocr_text.replace(' ', '')
            if name.isdigit():
                continue
            if name.startswith('('):
                if not self.current_names:
                    continue
                n = self.current_names.pop(len(self.current_names) - 1)
                self.current_names.append((n[0] + name, n[1]))
                continue
            self.current_names.append((name, name_.box))

    @property
    def is_invitation(self) -> bool:
        return get_server_next_update(self.cafe_update) - datetime.now() > timedelta(hours=self.waiting_hour)

    @property
    def names(self):
        return list(map(lambda x: x[0], self.current_names))

    @property
    def target_name(self):
        return self.target_names[0] if self.target_names else None

    def on_success(self):
        logger.info(f'Invited {self.target_name}')
        self.invited.append(self.target_name)
        self.target_names.pop(0)

    def on_failed(self):
        logger.warning(f'Failed to invite {self.target_name}')
        self.target_names.pop(0)

    def insight_name(self, name: str, main: ModuleBase, skip_first_screenshot=True) -> bool:
        """
        Args:
            name:
            main:
            skip_first_screenshot:
        """
        logger.info(f'Insight name: {name}')
        last_names: set[str] = set()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_names(main)

            if name in self.names:
                return True

            names = self.names
            if names and last_names == set(names):
                logger.warning(f'Name not found: {name}')
                return False
            last_names = set(names)

            self.swipe_page(main)

            main.wait_until_stable(
                self.list.button,
                timer=Timer(0, 0),
                timeout=Timer(1.5, 5)
            )

    def select_name_invite(
            self,
            main: ModuleBase,
            name: str = None,
            insight: bool = True,
            skip_first_screenshot: bool = True
    ) -> bool:
        """
        Args:
            main:
            name:
            insight:
            skip_first_screenshot:

        Returns:
            If success
        """
        if name is None:
            if not self.target_name:
                return False
            name = self.target_name
        if insight and not self.insight_name(name, main, skip_first_screenshot):
            return False

        logger.info(f'Select name: {name}')
        click_interval = Timer(1, 2)
        load_names_interval = Timer(1, 5)
        timeout = Timer(10, 10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if load_names_interval.reached_and_reset() and not insight:
                self.load_names(main)

            name_box = next(filter(lambda x: x[0] == name, self.current_names), None)
            if name_box is None:
                logger.warning(f'No name {name} in {self.ocr.name}')
                continue

            search_box = area_offset((0, 0, *area_size(self.item.area)), name_box[1][:2])
            self.invite.load_search(search_box)
            click_button = self.invite.match_multi_template(main.device.image)

            if not click_button:
                logger.warning(f'No clickable {self.invite.name}')
                continue

            if click_interval.reached_and_reset():
                main.device.click(click_button[0])
                return True

            if timeout.reached():
                logger.warning(f'No clickable {self.invite.name}')
                return False


invitation = Invitation('test')


def handle_invitation_status(status: InvitationStatus, main: ModuleBase) -> InvitationStatus:
    match status:
        case InvitationStatus.MOMOTALK:
            if not invitation.is_invitation:
                logger.info('Invitation waiting until next refresh')
                return InvitationStatus.FINISHED
            if main.appear(CAFE_INVITED):
                logger.info('Invitation in cooldown')
                return InvitationStatus.FINISHED
            if invitation.choice != 'list_top' and invitation.target_name is None:
                logger.warning('No student to be invited or all invitations failed')
                return InvitationStatus.FINISHED
            if main.appear(CHECK_MOMOTALK):
                return InvitationStatus.OCR
            main.appear_then_click(CAFE_INVITE)
        case InvitationStatus.OCR:
            if invitation.choice == 'list_top':
                invitation.load_names(main)
                invitation.target_names = invitation.names
                invitation.choice = 'list'
            if invitation.select_name_invite(main):
                return InvitationStatus.SELECT
            return InvitationStatus.FAILED
        case InvitationStatus.SELECT:
            if main.appear(INVITE_CONFIRM):
                return InvitationStatus.CONFIRM
            if main.config.LANG == 'jp' and main.appear(INVITE_IN_SECOND):
                return InvitationStatus.IN_SECOND
            if main.appear(INVITE_SUBSTITUTE):
                return InvitationStatus.SUBSTITUTE
        case InvitationStatus.CONFIRM:
            main.appear_then_click(INVITE_CONFIRM)
            if not main.appear(INVITE_CONFIRM):
                invitation.on_success()
                return InvitationStatus.INVITED
        case InvitationStatus.IN_SECOND:
            main.appear_then_click(INVITE_IN_SECOND_CLOSE)
            return InvitationStatus.FAILED
        case InvitationStatus.SUBSTITUTE:
            if not invitation.substitute:
                main.appear_then_click(INVITE_SUBSTITUTE_CLOSE)
                return InvitationStatus.FAILED
            else:
                main.appear_then_click(INVITE_SUBSTITUTE)
                if not main.appear(INVITE_SUBSTITUTE):
                    return InvitationStatus.INVITED
        case InvitationStatus.INVITED:
            main.appear_then_click(MOMOTALK_CLOSE)
            if not main.appear(MOMOTALK_CLOSE):
                return InvitationStatus.FINISHED
        case InvitationStatus.FAILED:
            main.appear_then_click(MOMOTALK_CLOSE)
            if not main.appear(CHECK_MOMOTALK):
                invitation.on_failed()
                return InvitationStatus.MOMOTALK
        case InvitationStatus.FINISHED:
            pass
        case _:
            logger.warning(f'Invalid status: {status}')
    return status


def handle_invitation(main: ModuleBase):
    if not main.config.Invitation_Enable:
        logger.info('Invitation disabled')
        return True
    invitation.waiting_hour = main.config.Invitation_WaitingHour
    invitation.choice = main.config.Invitation_Choice
    invitation.substitute = main.config.Invitation_Substitute
    if invitation.choice == 'by_name' and not invitation.target_names:
        name = main.config.Invitation_Name
        name = re.sub(r'[ \t\r\n]', '', name)
        name = re.sub(r'[＞﹥›˃ᐳ❯]', '>', name)
        name = re.sub(r'（', '(', name)
        name = re.sub(r'）', ')', name)
        invitation.target_names = name.split('>')
    status = InvitationStatus.MOMOTALK
    action_timer = Timer(1, 1)
    loading_timer = Timer(1, 1)
    while 1:
        main.device.screenshot()

        if not loading_timer.reached():
            continue

        if action_timer.reached_and_reset():
            logger.attr('Status', status)
            status = handle_invitation_status(status, main)

        if status == InvitationStatus.FINISHED:
            return True
