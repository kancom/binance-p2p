import asyncio
import os
import time
from io import BytesIO
from typing import Awaitable, Callable, Dict, List, Tuple

import cv2
import numpy as np
import seleniumwire.undetected_chromedriver as uc
from HLISA.hlisa_action_chains import HLISA_ActionChains
from loguru import logger
from p2p.application import QueueRepo, UserInteractionEnum
from PIL import Image, ImageChops
from pydantic.main import BaseModel
from pydantic.types import PositiveInt
from selenium.common.exceptions import TimeoutException as SelTimeOutExc
from selenium.webdriver import ActionChains
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from twocaptcha import TwoCaptcha

PIXELS_EXTENSION = 10


class PuzzleSolver:
    def __init__(self, piece_path, background_path):
        self.piece_path = piece_path
        self.background_path = background_path

    def get_position(self):
        template, x_inf, y_sup, y_inf = self.__piece_preprocessing()
        background = self.__background_preprocessing(y_sup, y_inf)

        res = cv2.matchTemplate(background, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc

        origin = x_inf
        end = top_left[0] + PIXELS_EXTENSION

        return end - origin

    def __background_preprocessing(self, y_sup, y_inf):
        background = self.__sobel_operator(self.background_path)
        background = background[y_sup:y_inf, :]
        background = self.__extend_background_boundary(background)
        background = self.__img_to_grayscale(background)

        return background

    def __piece_preprocessing(self):
        img = self.__sobel_operator(self.piece_path)
        x, w, y, h = self.__crop_piece(img)
        template = img[y:h, x:w]

        template = self.__extend_template_boundary(template)
        template = self.__img_to_grayscale(template)

        return template, x, y, h

    def __crop_piece(self, img):
        white_rows = []
        white_columns = []
        r, c = img.shape

        for row in range(r):
            for x in img[row, :]:
                if x != 0:
                    white_rows.append(row)

        for column in range(c):
            for x in img[:, column]:
                if x != 0:
                    white_columns.append(column)

        x = white_columns[0]
        w = white_columns[-1]
        y = white_rows[0]
        h = white_rows[-1]

        return x, w, y, h

    def __extend_template_boundary(self, template):
        extra_border = np.zeros((template.shape[0], PIXELS_EXTENSION), dtype=int)
        template = np.hstack((extra_border, template, extra_border))

        extra_border = np.zeros((PIXELS_EXTENSION, template.shape[1]), dtype=int)
        template = np.vstack((extra_border, template, extra_border))

        return template

    def __extend_background_boundary(self, background):
        extra_border = np.zeros((PIXELS_EXTENSION, background.shape[1]), dtype=int)
        return np.vstack((extra_border, background, extra_border))

    def __sobel_operator(self, img_path):
        scale = 1
        delta = 0
        ddepth = cv2.CV_16S

        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        img = cv2.GaussianBlur(img, (3, 3), 0)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(
            gray,
            ddepth,
            1,
            0,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv2.BORDER_DEFAULT,
        )
        grad_y = cv2.Sobel(
            gray,
            ddepth,
            0,
            1,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv2.BORDER_DEFAULT,
        )
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

        return grad

    def __img_to_grayscale(self, img):
        tmp_path = "/tmp/sobel.png"
        cv2.imwrite(tmp_path, img)
        return cv2.imread(tmp_path, 0)


class JigSawSolver:
    _solver = None
    _action = None
    margin = 3
    # inspired by https://ask-hellobi-com.translate.goog/blog/cuiqingcai/9796?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=ru&_x_tr_pto=wapp
    def __init__(self, driver) -> None:
        self._driver = driver

    def solve(self):
        def image_to_slider(
            *,
            image: WebElement,
            slider: WebElement,
            sub_image: WebElement,
            image_x: int,
        ) -> int:
            ttl_width = image.size["width"]
            img_max = ttl_width - sub_image.size["width"]
            slider_max = ttl_width - slider.size["width"]
            return round(image_x * slider_max / img_max)

        self._solver = PuzzleSolver(
            piece_path="/tmp/diff.png", background_path="/tmp/wide.png"
        )
        self._action = ActionChains(self._driver, duration=50)

        slider, slider_box = self.get_slider_controls()
        image = self.get_image()
        sub_image = self.get_sub_image(image)

        self.make_images(slider=slider, image=image, sub_image=sub_image)
        sub_img_sz = sub_image.size
        logger.debug(f"{slider_box.size}, {image.size}, {sub_image.size}")

        offset = self._solver.get_position()
        logger.debug(f"{offset}, {2*sub_img_sz['width']}")

        offset = image_to_slider(
            image=image,
            slider=slider_box,
            sub_image=sub_image,
            image_x=offset,
        )
        curr_pos = 2 * sub_img_sz["width"]
        # curr_pos = image_to_slider(
        #     image=image,
        #     slider=slider_box,
        #     sub_image=sub_image,
        #     image_x=2 * sub_img_sz["width"],
        # )
        logger.debug(f"{offset}, {curr_pos}")

        track = self.get_track(offset, current=curr_pos)
        logger.debug(track)
        for x in track:
            self._action.move_by_offset(xoffset=x, yoffset=0)
        self._action.perform()
        time.sleep(0.5)
        self._action.release().perform()

    def get_slider_controls(self) -> Tuple[WebElement, WebElement]:
        slider = self._driver.find_element(By.CLASS_NAME, "verify-slider")
        candidates = slider.find_elements(By.TAG_NAME, "div")
        arrow = [c for c in candidates if c.get_attribute("_id") == "ar"][0]
        box = [c for c in candidates if c.get_attribute("_id") == "slth"][0]
        return arrow, box

    def get_image(self) -> WebElement:
        slider = self._driver.find_element(By.CLASS_NAME, "verify-slider")
        parent = slider.find_element(By.XPATH, "./..")
        children = parent.find_elements(By.TAG_NAME, "div")
        image = [c for c in children if c.get_attribute("_id") == "im"][0]
        return image

    def get_sub_image(self, image: WebElement) -> WebElement:
        return image.find_element(By.TAG_NAME, "div")

    def make_images(
        self, slider: WebElement, image: WebElement, sub_image: WebElement
    ) -> Tuple[Image.Image, Image.Image]:
        if self._action is None:
            raise ValueError("_action is None")
        sub_img_sz = sub_image.size

        screenshot = image.screenshot_as_png
        pil_img_wide = Image.open(BytesIO(screenshot))
        pil_img_wide.save("/tmp/wide.png")

        self._action.click_and_hold(slider)
        track = self.get_track(2 * sub_img_sz["width"])
        for x in track:
            self._action.move_by_offset(xoffset=x, yoffset=0)
        self._action.perform()

        screenshot = image.screenshot_as_png
        pil_img_left = Image.open(BytesIO(screenshot))
        pil_img_left = pil_img_left.crop(
            (0, 0, sub_img_sz["width"], pil_img_wide.height)
        )
        pil_img_left.save("/tmp/left.png")
        pil_img = pil_img_wide.copy()
        pil_img.paste(pil_img_left)
        pil_img.save("/tmp/res.png")

        diff = ImageChops.subtract(pil_img_wide.convert("RGB"), pil_img.convert("RGB"))
        diff = diff.crop(
            (self.margin, 0, sub_img_sz["width"] - self.margin, diff.height)
        )
        diff.save("/tmp/diff.png")
        return pil_img_wide, diff

    def get_track(self, distance, current=0) -> list:
        # https://github.com/EragoGeneral/python-demo/blob/cbb9d447be9f3f37d3c332f55a3ac57c08d25630/spider/ocr/slide_code.py#L122
        track = []
        E = 1
        mid = current + (distance - current) * 4 / 5
        t = 0.2
        v = 0
        while round(abs(current - distance)) > E:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            step = round(move)
            # if step != 0:
            track.append(step)
            # print(round(abs(current - distance)), sum(track))
        return track


class ActionDescr(BaseModel):
    name: str
    priority: PositiveInt
    action: Callable[[webdriver.Remote, str, str], Awaitable]


class BinanceAuthenticator:
    # geetest captcha https://2captcha.com/lang/python
    # https://www.deathbycaptcha.com/faq
    LOGIN_URL = "https://accounts.binance.com/en/login"
    PG_LOAD_TIMEOUT = 0.5

    def __init__(
        self,
        driver_url: str,
        captcha_solver_key: str,
        user_queue_repo: QueueRepo,
    ):
        self._driver_url = driver_url
        self._captcha_solver_key = captcha_solver_key
        self._user_question_repo = user_queue_repo
        self._remote_driver = True
        self._search_actions: Dict[tuple, ActionDescr] = self._build_search_map()
        if os.path.exists(self._driver_url):
            self._remote_driver = False

    async def _sec_code_option(self, driver, login, password):
        inputs = driver.find_elements(By.TAG_NAME, "input")
        if len(inputs) > 1:
            await self._sec_code_enter(driver, login)
        else:
            await self._single_auth_code(driver, login)

    async def _failed_action(self, driver, login, password):
        return False

    async def _completed_action(self, driver, login, password):
        return True

    def _build_search_map(self) -> Dict[tuple, ActionDescr]:
        result = {
            (By.XPATH, "//*[text()='Please select all images with']"): ActionDescr(
                name="grid captcha",
                priority=2,
                action=self._solve_grid_captcha,
            ),
            # (By.XPATH, "//*[text()='Security Verification']"): ActionDescr(
            #     name="geetest-like captcha",
            #     priority=2,
            #     action=self._geetest_captcha,
            # ),
            (By.XPATH, "//*[text()='Security verification']"): ActionDescr(
                name="security codes",
                priority=3,
                action=self._sec_code_option,
            ),
            (By.XPATH, "//*[text()='Deposit']"): ActionDescr(
                name="deposit page", priority=4, action=self._completed_action
            ),
            (
                By.XPATH,
                "//*[contains(text(),'The password you entered is incorrect')]",
            ): ActionDescr(name="wrong pass", priority=5, action=self._failed_action),
            (By.NAME, "username"): ActionDescr(
                name="login", priority=1, action=self._login_enter
            ),
            (By.NAME, "password"): ActionDescr(
                name="password", priority=1, action=self._pass_enter
            ),
        }

        return result

    async def _try_next_action(
        self, driver: webdriver.Remote, login: str, password: str
    ):
        _found_map: Dict[int, List[ActionDescr]] = {}
        for k, v in self._search_actions.items():
            try:
                WebDriverWait(driver, 2).until(EC.presence_of_element_located(k))
                logger.debug(f"{v.name}@{v.priority} found")
                key = v.priority
                if key not in _found_map:
                    _found_map[key] = []
                _found_map[key].append(v)
            except SelTimeOutExc:
                pass
        if len(_found_map) == 0:
            return
        k = max(_found_map.keys())
        v = _found_map[k]
        if len(v) > 1:
            logger.warning(f"two item with the same prio found {k},{v}")
        logger.debug(f"trying {v[0].name}")
        return await v[0].action(driver, login, password)

    async def _solve_grid_captcha(self, driver, login, password):
        sz = 9
        for _ in range(3):
            try:
                e = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "bcap-image-cell-container")
                    )
                )
            except Exception as e:
                pass
        e = driver.find_element(By.CLASS_NAME, "bcap-modal")
        screen = e.screenshot_as_base64
        e.screenshot("/tmp/screen.png")
        grid = driver.find_elements(By.CLASS_NAME, "bcap-image-cell-container")
        for s in range(len(grid) // sz):
            s_grid = grid[s * sz : s * sz + sz]
            if all(g_.is_enabled() and g_.is_displayed() for g_ in s_grid):
                grid = [g for g in s_grid]
                break
        if grid is None or len(grid) == 0:
            raise ValueError("grid is not detected")
        submits = driver.find_elements(By.CLASS_NAME, "bcap-verify-button")
        submit = [g for g in submits if g.is_enabled() and g.is_displayed()][0]
        if submit is None:
            raise ValueError("submit button is not detected")

        solver = TwoCaptcha(self._captcha_solver_key)
        try:
            logger.debug("starting solver")
            result: dict = solver.grid(
                screen,
                rows=3,
                cols=3,
                lang="en",
            )  # OK|click:3/8/9
            if "click" not in result["code"]:
                raise ValueError(f"couldn't resolve {result}")
            _, cells = result["code"].split(":")
            logger.debug(cells)
            actions = HLISA_ActionChains(driver)
            _cells = cells.split("/")
            if len(_cells) == 0:
                raise ValueError(f"unclear response from solver {cells}")
            elif len(_cells) >= 8:
                logger.debug("reporting bad solving")
                solver.report(result["captchaId"], correct=False)
            for cell in _cells:
                actions.move_to_element(grid[int(cell) - 1]).click().perform()
            actions.click(submit).perform()
            logger.debug(f"{submit} clicked")
        except Exception as e:
            logger.error(e)

    async def _single_auth_code(self, driver, login):
        inputs = driver.find_elements(By.TAG_NAME, "input")
        auth_inputs = [x for x in inputs if x.accessible_name == "Authenticator Code"]
        auth_input = None
        if len(auth_inputs) > 0:
            auth_input = auth_inputs[0]
        if auth_input is not None:
            auth_code = await self._user_question_repo.query(
                login, question=UserInteractionEnum.ASK_AUTH_CODE
            )
            auth_input.clear()
            auth_input.send_keys(auth_code)
            submit = driver.find_element(By.XPATH, "//*[text()='Submit']")
            driver.execute_script("arguments[0].click()", submit)
            for _ in range(3):
                time.sleep(self.PG_LOAD_TIMEOUT)
                try:
                    e = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//*[text()='success']")
                        )
                    )
                    logger.debug("security codes succeed")
                    return
                except:
                    pass

    async def _geetest_captcha(
        self, driver: webdriver.Remote, login: str, password: str
    ):
        solver = JigSawSolver(driver)
        solver.solve()

    async def _sec_code_enter(self, driver, login):
        for _ in range(3):
            for code in driver.find_elements(By.XPATH, "//*[text()='Get Code']"):
                time.sleep(self.PG_LOAD_TIMEOUT)
                driver.execute_script("arguments[0].click()", code)
            inputs = driver.find_elements(By.TAG_NAME, "input")
            phone_input = [
                x
                for x in inputs
                if x.accessible_name == "Phone Number Verification Code"
            ][0]
            email_input = [
                x for x in inputs if x.accessible_name == "Email Verification Code"
            ][0]
            auth_inputs = [
                x for x in inputs if x.accessible_name == "Authenticator Code"
            ]
            auth_input = None
            if len(auth_inputs) > 0:
                auth_input = auth_inputs[0]

            email_code = await self._user_question_repo.query(
                login, question=UserInteractionEnum.ASK_EMAIL_CODE
            )
            phone_code = await self._user_question_repo.query(
                login, question=UserInteractionEnum.ASK_PHONE_CODE
            )
            email_input.send_keys(Keys.CONTROL + "a")
            phone_input.send_keys(Keys.CONTROL + "a")
            email_input.send_keys(email_code)
            phone_input.send_keys(phone_code)
            if auth_input is not None:
                auth_code = await self._user_question_repo.query(
                    login, question=UserInteractionEnum.ASK_AUTH_CODE
                )
                auth_input.send_keys(Keys.CONTROL + "a")
                auth_input.send_keys(auth_code)
            submit = driver.find_element(By.XPATH, "//*[text()='Submit']")
            driver.execute_script("arguments[0].click()", submit)
            for _ in range(3):
                time.sleep(self.PG_LOAD_TIMEOUT)
                try:
                    e = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//*[text()='success']")
                        )
                    )
                    logger.debug("security codes succeed")
                    return
                except:
                    pass

        logger.error("Security codes failed after 3 attempts")

    async def _login_enter(self, driver, login, password):
        login_input = driver.find_element(By.NAME, "username")
        login_input.send_keys(Keys.CONTROL + "a")
        login_input.send_keys(login)
        try:
            cookie = driver.find_element(By.XPATH, "//*[text()='Accept All Cookies']")
            cookie.click()
        except:
            pass
        btn = driver.find_element(By.ID, "click_login_submit")
        driver.execute_script("arguments[0].click()", btn)
        logger.debug("login clicked")

    async def _pass_enter(self, driver, login, password):
        pass_input = driver.find_element(By.NAME, "password")
        pass_input.send_keys(Keys.CONTROL + "a")
        pass_input.send_keys(password)
        try:
            cookie = driver.find_element(By.XPATH, "//*[text()='Accept All Cookies']")
            cookie.click()
        except:
            pass
        btn = driver.find_element(By.ID, "click_login_submit")
        driver.execute_script("arguments[0].click()", btn)
        logger.debug("pass clicked")

    async def get_auth_headers(self, login: str, password: str) -> dict:
        logger.debug(
            f"{self._driver_url}, {self._remote_driver}, {os.getenv('SERVICE')}"
        )
        await self._user_question_repo.put_notification(
            user_id=login, notification=UserInteractionEnum.AUTH_REQUIRED
        )
        if self._remote_driver:
            options = uc.ChromeOptions()
            try:
                driver = webdriver.Remote(
                    self._driver_url,
                    desired_capabilities=DesiredCapabilities.CHROME,
                    options=options,
                    seleniumwire_options={"addr": os.getenv("SERVICE"), "port": 8087},
                )
            except Exception as ex:
                logger.error(ex)
                await self._user_question_repo.put_notification(
                    user_id=login, notification=UserInteractionEnum.AUTH_FAILED
                )
                raise
        else:
            driver = webdriver.Chrome(self._driver_url)
        logger.debug(driver)
        driver.get(self.LOGIN_URL)

        logger.debug("waiting security verification")
        res = None
        for _ in range(30):
            try:
                res = await self._try_next_action(driver, login, password)
                if res is not None:
                    break
            except:
                pass

        if res:
            logger.debug("login succeed")
            await self._user_question_repo.put_notification(
                user_id=login, notification=UserInteractionEnum.AUTHENTICATED
            )
            # wait until "Deposit" btn appeared
            # fully loaded
            for idx in range(len(driver.requests) - 1, 0, -1):
                req = driver.requests[idx]
                if "https://www.binance.com/bapi" in req.url and len(req.headers) > 0:
                    logger.debug(f"all done. {req.headers}")
                    driver.quit()
                    return dict(req.headers)
        logger.debug("login UNsucceed")
        await self._user_question_repo.put_notification(
            user_id=login, notification=UserInteractionEnum.AUTH_FAILED
        )
        driver.quit()
        # wait for other lock to be expired
        await asyncio.sleep(5)
        raise ValueError("headers were not found")
