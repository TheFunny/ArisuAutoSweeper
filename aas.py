from module.alas import AzurLaneAutoScript
from module.logger import logger


class ArisuAutoSweeper(AzurLaneAutoScript):
    def restart(self):
        from tasks.login.login import Login
        Login(self.config, device=self.device).app_restart()

    def start(self):
        from tasks.login.login import Login
        Login(self.config, device=self.device).app_start()

    def goto_main(self):
        from tasks.login.login import Login
        from tasks.base.ui import UI
        if self.device.app_is_running():
            logger.info('App is already running, goto main page')
            UI(self.config, device=self.device).ui_goto_main()
        else:
            logger.info('App is not running, start app and goto main page')
            Login(self.config, device=self.device).app_start()
            UI(self.config, device=self.device).ui_goto_main()

    def cafe(self):
        from tasks.cafe.cafe import Cafe
        Cafe(config=self.config, device=self.device).run()

    def circle(self):
        from tasks.circle.circle import Circle
        Circle(config=self.config, device=self.device).run()

    def mail(self):
        from tasks.mail.mail import Mail
        Mail(config=self.config, device=self.device).run()

    def bounty(self):
        from tasks.bounty.bounty import Bounty
        Bounty(config=self.config, device=self.device).run()

    def scrimmage(self):
        from tasks.scrimmage.scrimmage import Scrimmage
        Scrimmage(config=self.config, device=self.device).run()

    def tactical_challenge(self):
        from tasks.tactical_challenge.tactical_challenge import TacticalChallenge
        TacticalChallenge(config=self.config, device=self.device).run()

    def task(self):
        from tasks.task.task import Task
        Task(config=self.config, device=self.device).run()

    def shop(self):
        from tasks.shop.shop import Shop
        Shop(config=self.config, device=self.device).run()

    def momotalk(self):
        from tasks.momotalk.momotalk import MomoTalk
        MomoTalk(config=self.config, device=self.device).run()

    def mission(self):
        from tasks.mission.mission import Mission
        Mission(config=self.config, device=self.device).run()

    def schedule(self):
        from tasks.schedule.schedule import Schedule
        Schedule(config=self.config, device=self.device).run()

    def auto_mission(self):
        from tasks.auto_mission.auto_mission import AutoMission
        AutoMission(config=self.config, device=self.device).run()

    def data_update(self):
        from tasks.item.data_update import DataUpdate
        DataUpdate(config=self.config, device=self.device).run()

if __name__ == '__main__':
    aas = ArisuAutoSweeper('aas')
    aas.loop()
    # aas.goto_main()
