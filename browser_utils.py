from DrissionPage import ChromiumOptions, Chromium
import sys
import os
import logging
from dotenv import load_dotenv

def _load_env():
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    dotenv_path = os.path.join(application_path, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)


_load_env()


class BrowserManager:
    def __init__(self):
        self.browser = None

    def init_browser(self, user_agent=None):
        """初始化浏览器"""
        co = self._get_browser_options(user_agent)
        self.browser = Chromium(co)
        return self.browser

    def _get_browser_options(self, user_agent=None):
        """获取浏览器配置"""
        co = ChromiumOptions()

        browser_path = os.getenv("BROWSER_PATH")
        if browser_path:
            co.set_paths(browser_path=browser_path)

        co.set_pref("credentials_enable_service", False)
        co.set_argument("--hide-crash-restore-bubble")
        proxy = os.getenv("BROWSER_PROXY")
        if proxy:
            co.set_proxy(proxy)

        co.auto_port()
        if user_agent:
            co.set_user_agent(user_agent)

        co.headless(
            os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        )  # 生产环境使用无头模式

        # Mac 系统特殊处理
        if sys.platform == "darwin":
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")

        return co


    def quit(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
