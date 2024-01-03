from enum import Enum

from module.base.timer import Timer
from module.logger import logger
from tasks.tactical_challenge.assets.assets_tactical_challenge import *
from tasks.momotalk.ui import MomoTalkUI

class MomoTalkStatus(Enum):
    OPEN = 0
    SORT = 1
    CHECK = 2
    CHAT = 3
    STORY = 4
    FINISHED = -1

class MomoTalk(MomoTalkUI):
    def handle_momotalk(self, status):
        match status:
            case MomoTalkStatus.OPEN:
                if self.open_momotalk():
                    return MomoTalkStatus.SORT
                return MomoTalkStatus.FINISHED
            case MomoTalkStatus.SORT:
                if self.sort_messages():
                    return MomoTalkStatus.CHECK
            case MomoTalkStatus.CHECK:
                if self.check_first_student():
                    return MomoTalkStatus.CHAT
                return MomoTalkStatus.FINISHED                
            case MomoTalkStatus.CHAT:
                if self.chat():
                    return MomoTalkStatus.STORY
                return MomoTalkStatus.OPEN
            case MomoTalkStatus.STORY:
                if self.skip_story():
                    return MomoTalkStatus.CHAT    
            case MomoTalkStatus.FINISHED:
                return status                
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        action_timer = Timer(0.5, 1)
        status = MomoTalkStatus.OPEN

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self.handle_momotalk(status)

            if status == MomoTalkStatus.FINISHED:
                break

        self.config.task_delay(server_update=True)

