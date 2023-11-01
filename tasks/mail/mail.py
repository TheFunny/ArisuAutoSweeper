from module.base.timer import Timer
from module.logger import logger
from tasks.base.page import page_mail
from tasks.base.ui import UI
from tasks.mail.assets.assets_mail import *


class Mail(UI):
    def run(self):
        self.ui_ensure(page_mail)
        action_timer = Timer(1).start()

        while 1:
            self.device.screenshot()
            if self.ui_additional():
                continue
            if action_timer.reached_and_reset():
                if self.match_color(MAIL_RECEIVE):
                    self.device.click(MAIL_RECEIVE)
                    logger.info("Receive mail")
                    continue
                if self.appear(MAIL_RECEIVED):
                    logger.info("Mail have been received")
                    break

        self.config.task_delay(server_update=True)
