import os
import platform
import json
import sys
from colorama import Fore, Style
from enum import Enum
from typing import Optional

from language import language, get_translation

os.environ["PYTHONVERBOSE"] = "0"
os.environ["PYINSTALLER_VERBOSE"] = "0"

import time
import random
from logger import logging
from browser_utils import BrowserManager
from get_email_code import EmailVerificationHandler
from logo import print_logo
from config import Config
from datetime import datetime

# Define EMOJI dictionary
EMOJI = {"ERROR": get_translation("error"), "WARNING": get_translation("warning"), "INFO": get_translation("info")}


class VerificationStatus(Enum):
    """Verification status enum"""
    VERIFICATION_CODE_PAGE = "验证"  # Verify button text
    SUCCESS_PAGE = "Gemini"  # Success indicator


def save_screenshot(tab, stage: str, timestamp: bool = True) -> None:
    """
    Save a screenshot of the page

    Args:
        tab: Browser tab object
        stage: Stage identifier for the screenshot
        timestamp: Whether to add a timestamp
    """
    try:
        # Create screenshots directory
        screenshot_dir = "screenshots"
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)

        # Generate filename
        if timestamp:
            filename = f"gemini_{stage}_{int(time.time())}.png"
        else:
            filename = f"gemini_{stage}.png"

        filepath = os.path.join(screenshot_dir, filename)

        # Save screenshot
        tab.get_screenshot(filepath)
        logging.debug(f"Screenshot saved: {filepath}")
    except Exception as e:
        logging.warning(f"Failed to save screenshot: {str(e)}")


def sign_up_gemini_account(browser, tab, account, email_handler):
    """Gemini Enterprise account registration process"""
    print("\n" + "=" * 60)
    print("  🚀 开始 Gemini Enterprise 注册流程")
    print("=" * 60 + "\n")
    
    # Step 1: Visit Gemini Enterprise page
    gemini_url = "https://cloud.google.com/gemini-enterprise"
    print(f"✅ 步骤1: 访问注册页面")
    tab.get(gemini_url)
    time.sleep(3)
    save_screenshot(tab, "landing_page")
    
    try:
        # Handle cookie consent if present
        cookie_button = tab.ele("OK, got it", timeout=2)
        if cookie_button:
            cookie_button.click()
            time.sleep(1)
    except:
        pass
    
    # Step 2: Click "开始使用" (Get Started)
    try:
        print(f"\n✅ 步骤2: 点击 '开始使用' 按钮")
        get_started = tab.ele("开始使用", timeout=5)
        if get_started:
            get_started.click()
            time.sleep(2)
            save_screenshot(tab, "after_get_started")
    except Exception as e:
        logging.error(f"点击 '开始使用' 失败: {str(e)}")
        return False
    
    # Step 3: Click "开始 30 天试用" (Start 30-day trial)
    try:
        print(f"✅ 步骤3: 点击 '开始 30 天试用' 按钮")
        time.sleep(3)  # 增加等待时间，确保页面加载
        
        # Try multiple possible button texts
        trial_button = None
        button_texts = ["开始 30 天试用", "开始试用", "免费试用", "试用"]
        
        for text in button_texts:
            try:
                trial_button = tab.ele(text, timeout=3)
                if trial_button:
                    print(f"   找到按钮: {text}")
                    # Scroll to element  to make sure it's visible
                    try:
                        trial_button.scroll.to_see()
                    except:
                        pass
                    trial_button.click()
                    print(f"   已点击 '{text}' 按钮")
                    break
            except Exception as e:
                logging.debug(f"尝试查找 '{text}' 失败: {str(e)}")
                continue
        
        if not trial_button:
            logging.error("未找到试用按钮")
            save_screenshot(tab, "trial_button_not_found")
            return False
            
        time.sleep(3)
        save_screenshot(tab, "after_trial_click")
    except Exception as e:
        logging.error(f"点击试用按钮失败: {str(e)}")
        save_screenshot(tab, "trial_click_error")
        return False
    
    # Step 4: Enter email address
    try:
        print(f"\n✅ 步骤4: 输入邮箱地址: {account}")
        # Wait for email input field
        time.sleep(2)
        
        # Try different selectors for email input
        email_input = None
        selectors = ["@name=email", "@type=email", "tag:input"]
        
        for selector in selectors:
            try:
                email_input = tab.ele(selector, timeout=2)
                if email_input:
                    break
            except:
                continue
        
        if not email_input:
            logging.error("未找到邮箱输入框")
            save_screenshot(tab, "email_input_not_found")
            return False
        
        email_input.input(account)
        time.sleep(random.uniform(1, 2))
        save_screenshot(tab, "email_entered")
        
    except Exception as e:
        logging.error(f"输入邮箱失败: {str(e)}")
        save_screenshot(tab, "email_input_error")
        return False
    
    # Step 5: Click "使用邮箱继续" (Continue with email)
    try:
        print(f"✅ 步骤5: 点击 '使用邮箱继续' 按钮")
        continue_button = tab.ele("使用邮箱继续", timeout=5)
        if not continue_button:
            # Try alternative text
            continue_button = tab.ele("继续", timeout=2)
        
        if continue_button:
            continue_button.click()
            time.sleep(3)
            save_screenshot(tab, "after_email_submit")
        else:
            logging.error("未找到继续按钮")
            return False
            
    except Exception as e:
        logging.error(f"点击继续按钮失败: {str(e)}")
        return False
    
    # Step 6: Wait for and enter verification code
    print(f"\n✅ 步骤6: 等待邮箱验证码...")
    
    # Wait a bit for email to arrive
    time.sleep(5)
    
    # Get verification code
    max_attempts = 3
    code = None
    for attempt in range(max_attempts):
        print(f"   ⏳ 尝试获取验证码 (第 {attempt + 1}/{max_attempts} 次)")
        code = email_handler.get_verification_code()
        if code:
            break
        if attempt < max_attempts - 1:
            time.sleep(5)
    
    if not code:
        logging.error("无法获取验证码")
        save_screenshot(tab, "verification_code_failed")
        return False
    
    print(f"   ✅ 成功获取验证码: {code}")
    
    # Step 7: Enter verification code
    try:
        print(f"\n✅ 步骤7: 输入验证码: {code}")
        time.sleep(2)
        
        # Try to find verification code input field
        code_input = None
        selectors = ["@name=code", "@type=text", "tag:input"]
        
        for selector in selectors:
            try:
                code_input = tab.ele(selector, timeout=2)
                if code_input:
                    break
            except:
                continue
        
        if not code_input:
            logging.error("未找到验证码输入框")
            save_screenshot(tab, "code_input_not_found")
            return False
        
        code_input.input(code)
        time.sleep(random.uniform(1, 2))
        save_screenshot(tab, "code_entered")
        
    except Exception as e:
        logging.error(f"输入验证码失败: {str(e)}")
        save_screenshot(tab, "code_input_error")
        return False
    
    # Step 8: Click verify button or wait for auto-verification
    try:
        print(f"✅ 步骤8: 提交验证码")
        time.sleep(3)
        
        clicked = False
        
        # 方法1: 尝试常用按钮文本
        button_texts = ["验证", "提交", "继续", "下一步", "Verify", "Continue"]
        for text in button_texts:
            try:
                print(f"   查找按钮: '{text}'...")
                verify_button = tab.ele(text, timeout=2)
                if verify_button:
                    print(f"   找到按钮: '{text}'，准备点击")
                    # 确保元素可见
                    time.sleep(1)
                    verify_button.scroll.to_see()
                    time.sleep(0.5)
                    
                    # 尝试多种点击方式
                    click_success = False
                    try:
                        # 方式1: 普通点击
                        verify_button.click()
                        click_success = True
                        print(f"   ✅ 成功点击 '{text}' 按钮")
                    except Exception as e1:
                        logging.debug(f"   普通点击失败: {str(e1)}")
                        try:
                            # 方式2: JS点击
                            tab.run_js(f"arguments[0].click();", verify_button)
                            click_success = True
                            print(f"   ✅ 通过JS成功点击 '{text}' 按钮")
                        except Exception as e2:
                            logging.debug(f"   JS点击也失败: {str(e2)}")
                    
                    if click_success:
                        clicked = True
                        break
            except Exception as e:
                logging.debug(f"   查找 '{text}' 失败: {str(e)}")
                continue
        
        # 方法2: 尝试通用提交按钮选择器
        if not clicked:
            print("   未找到文本按钮，尝试通用选择器...")
            selectors = ["@type=submit", "xpath://button[@type='submit']"]
            for selector in selectors:
                try:
                    verify_button = tab.ele(selector, timeout=2)
                    if verify_button:
                        print(f"   找到提交按钮 ({selector})")
                        time.sleep(1)
                        verify_button.scroll.to_see()
                        time.sleep(0.5)
                        verify_button.click()
                        print(f"   ✅ 通过选择器点击了提交按钮")
                        clicked = True
                        break
                except Exception as e:
                    logging.debug(f"   选择器 '{selector}' 失败: {str(e)}")
                    continue
        
        # 方法3: 尝试 Enter 键提交（兜底方案）
        if not clicked:
            try:
                print("   尝试按 Enter 键提交")
                inputs = tab.eles("tag:input")
                if inputs:
                    inputs[-1].input('\n')
                    print("   ✅ 按下 Enter 键")
                    clicked = True
            except Exception as e:
                logging.debug(f"   Enter键提交失败: {str(e)}")
                logging.warning("   ⚠️ 未找到提交方式，等待自动验证")
        
        if clicked:
            print("   等待页面响应...")
            time.sleep(5)
        else:
            logging.warning("   ⚠️ 所有提交方式都失败，可能需要手动操作")
            time.sleep(10)  # 给用户更多时间手动操作
            
        save_screenshot(tab, "after_verification_submit")
            
    except Exception as e:
        logging.warning(f"提交验证码时出现异常: {str(e)}")
        save_screenshot(tab, "verification_submit_error")
        time.sleep(5)
    
    # Step 9: Wait for name input page after verification
    print(f"\n✅ 步骤9: 等待验证完成...")
    time.sleep(5)
    save_screenshot(tab, "after_verification")
    
    # Step 10: Fill in name field
    try:
        print(f"\n✅ 步骤10: 填写姓名")
        time.sleep(2)
        
        # Try to find name input field
        name_input = None
        selectors = ["@name=displayName", "@placeholder=全名", "tag:input"]
        
        for selector in selectors:
            try:
                name_input = tab.ele(selector, timeout=3)
                if name_input:
                    break
            except:
                continue
        
        if not name_input:
            logging.warning("未找到姓名输入框，可能已经跳转到主页面")
        else:
            # Use the first name from the email (before the timestamp)
            # e.g., John1764305393@domain.com -> John
            display_name = account.split('@')[0]  # Get email prefix
            # Try to extract just the name part (remove numbers if any)
            import re
            name_only = re.sub(r'\d+', '', display_name)  # Remove digits
            if name_only:
                display_name = name_only
            
            print(f"   输入姓名: {display_name}")
            name_input.input(display_name)
            time.sleep(random.uniform(1, 2))
            save_screenshot(tab, "name_entered")
        
    except Exception as e:
        logging.warning(f"填写姓名时出现异常: {str(e)}")
    
    # Step 11: Click "同意并开始使用" button
    try:
        print(f"✅ 步骤11: 点击 '同意并开始使用' 按钮")
        time.sleep(2)
        
        # Try to find the agree and start button
        create_button = None
        button_texts = ["同意并开始使用", "开始使用", "同意并继续", "创建账号"]
        
        for text in button_texts:
            try:
                create_button = tab.ele(text, timeout=3)
                if create_button:
                    print(f"   找到按钮: {text}")
                    create_button.click()
                    print(f"   已点击 '{text}' 按钮")
                    break
            except:
                continue
        
        if not create_button:
            logging.warning("未找到创建账号按钮")
        else:
            print("   账号创建请求已提交")
            time.sleep(5)
            save_screenshot(tab, "account_created")
            
    except Exception as e:
        logging.warning(f"点击创建账号按钮时出现异常: {str(e)}")
        time.sleep(3)
    
    # Step 12: Check if registration is successful
    print(f"\n✅ 步骤12: 检查注册结果...")
    time.sleep(3)
    save_screenshot(tab, "final_page")
    
    current_url = tab.url
    print(f"\n最终页面 URL: {current_url}")
    
    # Check for success indicators - must be at business.gemini.google/home/cid/
    if "business.gemini.google/home/cid/" in current_url:
        print("\n" + "=" * 60)
        print("  ✅ Gemini Enterprise 注册成功！")
        print("=" * 60)
        return True
    elif "business.gemini.google/admin/create" in current_url:
        logging.warning("仍在创建页面，可能需要等待或重试")
        return False
    else:
        logging.warning(f"注册状态未知，当前 URL: {current_url}")
        return False




class EmailGenerator:
    def __init__(
        self,
        password="".join(
            random.choices(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
                k=12,
            )
        ),
    ):
        configInstance = Config()
        configInstance.print_config()
        self.domain = configInstance.get_domain()
        self.names = self.load_names()
        self.default_password = password
        self.default_first_name = self.generate_random_name()
        self.default_last_name = self.generate_random_name()

    def load_names(self):
        try:
            with open("names-dataset.txt", "r") as file:
                return file.read().split()
        except FileNotFoundError:
            logging.warning(get_translation("names_file_not_found"))
            # Fallback to a small set of default names if the file is not found
            return ["John", "Jane", "Alex", "Emma", "Michael", "Olivia", "William", "Sophia", 
                    "James", "Isabella", "Robert", "Mia", "David", "Charlotte", "Joseph", "Amelia"]

    def generate_random_name(self):
        """Generate a random username"""
        return random.choice(self.names)

    def generate_email(self, length=4):
        """Generate a random email address"""
        length = random.randint(0, length)  # Generate a random int between 0 and length
        timestamp = str(int(time.time()))[-length:]  # Use the last length digits of timestamp
        return f"{self.default_first_name}{timestamp}@{self.domain}"

    def get_account_info(self):
        """Get complete account information"""
        return {
            "email": self.generate_email(),
            "password": self.default_password,
            "first_name": self.default_first_name,
            "last_name": self.default_last_name,
        }


def get_user_agent():
    """Get user_agent"""
    try:
        # Use JavaScript to get user agent
        browser_manager = BrowserManager()
        browser = browser_manager.init_browser()
        user_agent = browser.latest_tab.run_js("return navigator.userAgent")
        browser_manager.quit()
        return user_agent
    except Exception as e:
        logging.error(f"Failed to get user agent: {str(e)}")
        return None


def print_end_message():
    logging.info("\n\n\n\n\n")
    logging.info("=" * 50)
    logging.info("🎉 所有操作已完成！")
    logging.info("=" * 50)



if __name__ == "__main__":
    print_logo()
    
    # Add language selection
    print("\n")
    language.select_language_prompt()
    
    browser_manager = None
    try:
        logging.info("=== 初始化 Gemini Enterprise 自动注册工具 ===")

        logging.info("初始化浏览器...")

        # Get user_agent
        user_agent = get_user_agent()
        if not user_agent:
            logging.error("获取 user_agent 失败，使用默认值")
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # Remove "HeadlessChrome" from user_agent
        user_agent = user_agent.replace("HeadlessChrome", "Chrome")

        browser_manager = BrowserManager()
        browser = browser_manager.init_browser(user_agent)

        # Get and print browser's user-agent
        user_agent = browser.latest_tab.run_js("return navigator.userAgent")

        logging.info("配置信息加载完成")

        logging.info("生成随机邮箱账号...")

        email_generator = EmailGenerator()
        first_name = email_generator.default_first_name
        last_name = email_generator.default_last_name
        account = email_generator.generate_email()
        password = email_generator.default_password

        logging.info(f"✅ 生成邮箱账号: {account}")

        logging.info("初始化邮箱验证处理器...")
        email_handler = EmailVerificationHandler(account)

        tab = browser.latest_tab

        logging.info("开始注册流程...")

        if sign_up_gemini_account(browser, tab, account, email_handler):
            print("\n" + "=" * 60)
            print("  🎉 注册完成！账号信息如下：")
            print("=" * 60)
            print(f"  📧 邮箱: {account}")
            print(f"  🔑 密码: {password}")
            print("=" * 60 + "\n")
            print_end_message()
        else:
            logging.error("❌ 注册失败，请查看日志了解详情")

    except Exception as e:
        logging.error(f"程序出错: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
    finally:
        if browser_manager:
            logging.info("等待 10 秒后关闭浏览器...")
            time.sleep(10)
            browser_manager.quit()
        input("按 Enter 键退出程序...")
