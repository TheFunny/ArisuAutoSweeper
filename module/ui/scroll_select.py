"""
Original Author: sanmusen214(https://github.com/sanmusen214)
Adapted from https://github.com/sanmusen214/BAAH/blob/1.2/modules/AllTask/SubTask/ScrollSelect.py
"""

from module.base.timer import Timer
from module.logger import logger


class ScrollSelect:
    """
    Scroll and select the corresponding level by clicking on the right-side window.
    
    Parameters
    ----------
    window_starty: 
        Y-coordinate of the upper edge of the window
    first_item_endy: 
        Y-coordinate of the lower edge of the first item
    window_endy:
        Y-coordinate of the lower edge of the window
    clickx: int
        Base X-coordinate for sliding and clicking the button
    hasexpectimage: function
        Function to determine the appearance of the expected image after clicking, returns a boolean
    swipeoffsetx: int
        X offset of the base X-coordinate during sliding to prevent accidental button clicks
    finalclick: bool
        Whether to click on clickx and the last row after the sliding ends
    """

    def __init__(self, window_button, first_item_button, expected_button, clickx, swipeoffsetx=-100, responsey=40,
                 finalclick=True) -> None:
        # TODO: Actually, only concerned about the height of one element, completely displaying the Y of the first button, completely displaying the Y of the bottom button, the number of complete elements that the window can contain, the height of the last element in the window, and the left offset and response distance.
        self.window_starty = window_button.area[1]
        self.window_endy = window_button.area[3]
        self.first_item_endy = first_item_button.area[3]
        self.windowheight = window_button.height
        self.itemheight = first_item_button.height
        self.clickx = clickx
        self.expected_button = expected_button
        self.swipeoffsetx = swipeoffsetx
        self.responsey = responsey
        self.finalclick = finalclick

    def compute_swipe(self, main, x1, y1, distance, responsey):
        """
        Swipe vertically from bottom to top, actual swipe distance calculated based on the distance between two target points, considering inertia.
        """
        distance = abs(distance)
        logger.info(f"Swipe distance: {distance}")
        # 0-50
        if distance < 50:
            main.device.swipe((x1, y1), (x1, y1 - (distance + responsey)), duration=2)
        else:
            # Effective swipe distance for the Chinese server is 60
            main.device.swipe((x1, y1), (x1, int(y1 - (distance + responsey - 4 * (1 + distance / 100)))),
                              duration=1 + distance / 100)

    def select_index(self, main, target_index, clickoffsety=0) -> None:
        click_coords = main.device.click_methods.get(main.config.Emulator_ControlMethod, main.device.click_adb)
        logger.info("Scroll and select the {}-th level".format(target_index + 1))
        self.scroll_right_up(main, scrollx=self.clickx + self.swipeoffsetx)
        # Calculate how many complete elements are on one page
        itemcount = self.windowheight // self.itemheight
        # Calculate how much height the last incomplete element on this page occupies
        lastitemheight = self.windowheight % self.itemheight
        # Height below the incomplete element
        hiddenlastitemheight = self.itemheight - lastitemheight
        # Center point of the height of the first element
        start_center_y = self.window_starty + self.itemheight // 2
        # Center point of the last complete element on this page
        end_center_y = start_center_y + (itemcount - 1) * self.itemheight
        # If the target element is on the current page
        if target_index < itemcount:
            # Center point of the target element
            target_center_y = start_center_y + self.itemheight * target_index
            self.run_until(main,
                           lambda: click_coords(self.clickx, target_center_y),
                           lambda: main.appear(self.expected_button),
                           )
        else:
            # Start scrolling from the gap in the middle of the levels
            scroll_start_from_y = self.window_endy - self.itemheight // 2
            # The target element is on subsequent pages
            # Calculate how much the page should be scrolled
            scrolltotal_distance = (target_index - itemcount) * self.itemheight + hiddenlastitemheight
            logger.info("Height hidden by the last element: %d" % hiddenlastitemheight)
            # First, slide up the hidden part, add a little distance to let the system recognize it as a swipe event
            self.compute_swipe(main, self.clickx + self.swipeoffsetx, scroll_start_from_y, hiddenlastitemheight,
                               self.responsey)
            logger.info(f"Swipe distance: {hiddenlastitemheight}")
            # Update scrolltotal_distance
            scrolltotal_distance -= hiddenlastitemheight
            # Still need to scroll up (target_index - itemcount) * self.itemheight
            # Important: slide the height of (itemcount - 1) elements each time
            if itemcount == 1:
                scroll_distance = itemcount * self.itemheight
            else:
                scroll_distance = (itemcount - 1) * self.itemheight
            while scroll_distance <= scrolltotal_distance:
                self.compute_swipe(main, self.clickx + self.swipeoffsetx, scroll_start_from_y, scroll_distance,
                                   self.responsey)
                scrolltotal_distance -= scroll_distance
            if scrolltotal_distance > 5:
                # Last slide
                self.compute_swipe(main, self.clickx + self.swipeoffsetx, scroll_start_from_y, scrolltotal_distance,
                                   self.responsey)
            if self.finalclick:
                # Click on the last row
                clicky = (self.window_endy - self.itemheight // 2) + clickoffsety
                logger.info(clicky)
                self.run_until(main,
                               lambda: click_coords(self.clickx, clicky),
                               lambda: main.appear(self.expected_button)
                               )

    def run_until(self, main, func1, func2, times=6, sleeptime=1.5) -> bool:
        """
        Repeat the execution of func1 up to a maximum of times or until func2 evaluates to True.
        
        func1 should perform a single valid operation or internally call a screenshot function.
        A screenshot is triggered before evaluating func2.

        After each execution of func1, wait for sleeptime seconds.

        If func2 evaluates to True, exit and return True. Otherwise, return False.

        Note: The comment assumes that func1 produces a meaningful operation or internally calls a screenshot function,
        and func2 is evaluated after each execution of func1.
        """
        for i in range(times):
            main.device.screenshot()
            if func2():
                return True
            func1()
            timer = Timer(sleeptime).start()
            while not timer.reached_and_reset():
                pass
        main.device.screenshot()
        if func2():
            return True
        logger.warning("run_until exceeded max times")
        return False

    def scroll_right_up(self, main, scrollx=928, times=3):
        """
        scroll to top
        """
        for i in range(times):
            main.device.swipe((scrollx, 226), (scrollx, 561), duration=0.2)
        timer = Timer(0.5).start()
        while not timer.reached_and_reset():
            pass
