import traceback

from tasks.base.assets.assets_base_page import *


class Page:
    # Key: str, page name like "page_main"
    # Value: Page, page instance
    all_pages = {}

    @classmethod
    def clear_connection(cls):
        for page in cls.all_pages.values():
            page.parent = None

    @classmethod
    def init_connection(cls, destination):
        """
        Initialize an A* path finding among pages.

        Args:
            destination (Page):
        """
        cls.clear_connection()

        visited = [destination]
        visited = set(visited)
        while 1:
            new = visited.copy()
            for page in visited:
                for link in cls.iter_pages():
                    if link in visited:
                        continue
                    if page in link.links:
                        link.parent = page
                        new.add(link)
            if len(new) == len(visited):
                break
            visited = new

    @classmethod
    def iter_pages(cls):
        return cls.all_pages.values()

    @classmethod
    def iter_check_buttons(cls):
        for page in cls.all_pages.values():
            yield page.check_button

    def __init__(self, check_button):
        self.check_button = check_button
        self.links = {}
        (filename, line_number, function_name, text) = traceback.extract_stack()[-2]
        self.name = text[:text.find('=')].strip()
        self.parent = None
        Page.all_pages[self.name] = self

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def link(self, button, destination):
        self.links[destination] = button


# Main Page
page_main = Page(MAIN_GO_TO_PURCHASE)

# Cafe
page_cafe = Page(CAFE_CHECK)
page_cafe.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_CAFE, destination=page_cafe)

# Schedule
page_schedule = Page(SCHEDULE_CHECK)
page_schedule.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_SCHEDULE, destination=page_schedule)

# Circle
page_circle = Page(CIRCLE_CHECK)
page_circle.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_CIRCLE, destination=page_circle)

# Crafting Chamber
page_crafting = Page(CRAFTING_CHECK)
page_crafting.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_CRAFTING, destination=page_crafting)

# Shop
page_shop = Page(SHOP_CHECK)
page_shop.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_SHOP, destination=page_shop)

# Gacha
page_gacha = Page(GACHA_CHECK)
page_gacha.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_GACHA, destination=page_gacha)

# Account Info
page_account_info = Page(ACCOUNT_INFO_CHECK)
page_account_info.link(HOME, destination=page_main)

# Mail
page_mail = Page(MAIL_CHECK)
page_mail.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_MAIL, destination=page_mail)

# Task (Daily)
page_task = Page(TASK_CHECK)
page_task.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_TASK, destination=page_task)

# MomoTalk
page_momo_talk = Page(MOMOTALK_CHECK)
page_momo_talk.link(MOMOTALK_GO_TO_MAIN, destination=page_main)
page_main.link(MAIN_GO_TO_MOMOTALK, destination=page_momo_talk)

# Work
page_work = Page(WORK_CHECK)
page_work.link(HOME, destination=page_main)
page_main.link(MAIN_GO_TO_WORK, destination=page_work)

# Mission
page_mission = Page(MISSION_CHECK)
page_mission.link(HOME, destination=page_main)
page_mission.link(BACK, destination=page_work)
page_work.link(WORK_GO_TO_MISSION, destination=page_mission)

# Story
page_story = Page(STORY_CHECK)
page_story.link(HOME, destination=page_main)
page_story.link(BACK, destination=page_work)
page_work.link(WORK_GO_TO_STORY, destination=page_story)

# Bounty
page_bounty = Page(BOUNTY_CHECK)
page_bounty.link(HOME, destination=page_main)
page_bounty.link(BACK, destination=page_work)
page_work.link(WORK_GO_TO_BOUNTY, destination=page_bounty)

# Commissions
page_commissions = Page(COMMISSIONS_CHECK)
page_commissions.link(HOME, destination=page_main)
page_commissions.link(BACK, destination=page_work)
page_work.link(WORK_GO_TO_COMMISSIONS, destination=page_commissions)

# School Exchange
page_school_exchange = Page(SCHOOL_EXCHANGE_CHECK)
page_school_exchange.link(HOME, destination=page_main)
page_school_exchange.link(BACK, destination=page_work)
page_work.link(WORK_GO_TO_SCHOOL_EXCHANGE, destination=page_school_exchange)

# Tactical Challenge
page_tactical_challenge = Page(TACTICAL_CHALLENGE_CHECK)
page_tactical_challenge.link(HOME, destination=page_main)
page_tactical_challenge.link(BACK, destination=page_work)
page_work.link(WORK_GO_TO_TACTICAL_CHALLENGE, destination=page_tactical_challenge)
