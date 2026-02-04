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
    SUCCESS_PAGE = "Gemini Enterprise"  # Success indicator


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
    
    # Step 2: Click "开始 30 天试用" (Start 30-day trial)
    try:
        print(f"✅ 步骤2: 点击 '开始 30 天试用' 按钮")
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
        
        # Try to find verification code input field with more specific selectors
        code_input = None
        selectors = [
            "@name=code",
            "@type=text",
            "tag:input",
            "xpath://input[@type='text']",
            "css:input[type='text']"
        ]
        
        for selector in selectors:
            try:
                code_input = tab.ele(selector, timeout=3)
                if code_input:
                    print(f"   找到验证码输入框 (选择器: {selector})")
                    break
            except:
                continue
        
        if not code_input:
            logging.error("未找到验证码输入框")
            save_screenshot(tab, "code_input_not_found")
            return False
        
        # Clear any existing text in the input field
        try:
            code_input.clear()
            time.sleep(0.5)
        except:
            pass
        
        # 模拟真实用户输入：逐个字符输入
        print("   模拟真实用户输入验证码...")
        for char in code:
            code_input.input(char)
            time.sleep(random.uniform(0.1, 0.3))  # 每个字符之间的随机延迟
        
        # 模拟鼠标移动
        print("   模拟鼠标移动...")
        try:
            # 先移动到输入框
            code_input.hover()
            time.sleep(0.5)
            # 然后移动到页面其他位置
            tab.run_js("window.scrollBy(0, 50);")
            time.sleep(0.5)
            tab.run_js("window.scrollBy(0, -50);")
            time.sleep(0.5)
        except:
            pass
        
        time.sleep(random.uniform(1, 2))
        save_screenshot(tab, "code_entered")
        print(f"   ✅ 验证码已输入")
        
    except Exception as e:
        logging.error(f"输入验证码失败: {str(e)}")
        save_screenshot(tab, "code_input_error")
        return False
    
    # Step 8: Click verify button
    try:
        print(f"✅ 步骤8: 点击验证按钮提交验证码")
        
        # 等待页面完全加载，确保按钮可点击
        time.sleep(3)
        
        clicked = False
        
        # 方法1: 尝试常用按钮文本（优先"验证"按钮）
        button_texts = ["验证", "Verify", "提交", "继续", "下一步", "Submit", "Continue"]
        for text in button_texts:
            try:
                print(f"   查找按钮: '{text}'...")
                # 设置 10 秒超时，表示最多等待 10 秒来定位元素
                verify_button = tab.ele(text, timeout=15)
                if verify_button:
                    print(f"   ✅ 找到按钮: '{text}'，准备点击")
                    
                    # 确保元素可见
                    time.sleep(1)
                    
                    # 尝试滚动到元素
                    try:
                        verify_button.scroll.to_see()
                        print("   已滚动到按钮位置")
                    except Exception as e:
                        print(f"   滚动失败: {str(e)}")
                    
                    time.sleep(1)
                    
                    # 模拟鼠标悬停
                    try:
                        verify_button.hover()
                        print("   已模拟鼠标悬停")
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # 检查按钮是否可点击
                    try:
                        is_enabled = verify_button.states.is_enabled
                        is_displayed = verify_button.states.is_displayed
                        print(f"   按钮状态: 可点击={is_enabled}, 可见={is_displayed}")
                    except:
                        print("   无法检查按钮状态，继续尝试点击")
                    
                    # 尝试多种点击方式
                    click_success = False
                    
                    # 优先使用 JS 点击 (更可靠)
                    try:
                        print("   尝试JS点击...")
                        tab.run_js("arguments[0].click();", verify_button)
                        click_success = True
                        print(f"   ✅ 通过JS成功点击 '{text}' 按钮")
                    except Exception as e2:
                        print(f"   JS点击失败: {str(e2)}")
                    
                    # 其次尝试普通点击
                    if not click_success:
                        try:
                            print("   尝试普通点击...")
                            verify_button.click()
                            click_success = True
                            print(f"   ✅ 成功点击 '{text}' 按钮")
                        except Exception as e1:
                            print(f"   普通点击失败: {str(e1)}")
                    
                    # 最后尝试 JS dispatchEvent 点击
                    if not click_success:
                        try:
                            print("   尝试JS dispatchEvent点击...")
                            js_code = '''
                            var event = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            arguments[0].dispatchEvent(event);
                            '''
                            tab.run_js(js_code, verify_button)
                            click_success = True
                            print(f"   ✅ 通过JS dispatchEvent成功点击 '{text}' 按钮")
                        except Exception as e3:
                            print(f"   JS dispatchEvent点击失败: {str(e3)}")
                    
                    if click_success:
                        # 检查点击是否生效（页面是否跳转或出现加载状态）
                        print("   检查点击是否生效...")
                        time.sleep(2)
                        if tab.ele(text, timeout=1): # 如果按钮还在，可能没点成功
                            print(f"   ⚠️ 按钮 '{text}' 仍然存在，尝试再次点击...")
                            try:
                                tab.run_js("arguments[0].click();", verify_button)
                                print("   已重试点击")
                            except:
                                pass
                        
                        clicked = True
                        break
            except Exception as e:
                print(f"   查找 '{text}' 失败: {str(e)}")
                continue
        
        # 方法2: 尝试通用提交按钮选择器
        if not clicked:
            print("   未找到文本按钮，尝试通用选择器...")
            selectors = ["@type=submit", "xpath://button[@type='submit']", "tag:button"]
            for selector in selectors:
                try:
                    verify_button = tab.ele(selector, timeout=5)
                    if verify_button:
                        print(f"   找到提交按钮 ({selector})")
                        time.sleep(1)
                        
                        # 尝试滚动到元素
                        try:
                            verify_button.scroll.to_see()
                            print("   已滚动到按钮位置")
                        except Exception as e:
                            print(f"   滚动失败: {str(e)}")
                        
                        time.sleep(1)
                        
                        # 优先尝试JS点击
                        try:
                            tab.run_js("arguments[0].click();", verify_button)
                            print(f"   ✅ 通过JS点击了选择器按钮")
                            clicked = True
                            break
                        except Exception as e:
                            # 尝试普通点击
                            try:
                                verify_button.click()
                                print(f"   ✅ 通过选择器点击了提交按钮")
                                clicked = True
                                break
                            except Exception as e2:
                                print(f"   选择器点击失败: {str(e2)}")
                except Exception as e:
                    print(f"   选择器 '{selector}' 失败: {str(e)}")
                    continue
        
        # 方法3: 尝试 Enter 键提交（兜底方案）
        if not clicked:
            try:
                print("   尝试按 Enter 键提交")
                inputs = tab.eles("tag:input")
                if inputs:
                    # 先聚焦到最后一个输入框
                    tab.run_js("arguments[0].focus();", inputs[-1])
                    time.sleep(0.5)
                    # 发送Enter键
                    inputs[-1].input('\n')
                    print("   ✅ 按下 Enter 键")
                    clicked = True
            except Exception as e:
                print(f"   Enter键提交失败: {str(e)}")
        
        if clicked:
            print("   等待页面响应...")
            time.sleep(10)  # 增加等待时间到10秒
            
            # 检查页面是否跳转
            current_url = tab.url
            print(f"   当前页面 URL: {current_url}")
            
            # 检查是否仍在验证页面
            if "/verify" in current_url.lower() or "verification" in current_url.lower():
                print("   ⚠️ 页面未跳转，验证可能失败")
                save_screenshot(tab, "verification_failed")
                print(f"   ✅ 验证码提交完成，截图已保存")
                
                print("\n" + "=" * 60)
                print("  🛑 测试断点：程序在步骤8结束后停止")
                print("=" * 60 + "\n")
                return False  # 测试断点：在步骤8结束后停止
            else:
                print("   ✅ 页面已跳转，验证成功")
        else:
            print("   ⚠️ 所有提交方式都失败，尝试等待页面自动跳转")
            time.sleep(15)  # 增加等待时间到15秒
            
            # 检查页面是否跳转
            current_url = tab.url
            print(f"   当前页面 URL: {current_url}")
            if "/verify" in current_url.lower() or "verification" in current_url.lower():
                print("   ⚠️ 页面未跳转，验证可能失败")
            else:
                print("   ✅ 页面已跳转，验证成功")
        
        save_screenshot(tab, "after_verification_submit")
        print(f"   ✅ 验证码提交完成，截图已保存")
        
        print("\n" + "=" * 60)
        print("  🛑 测试断点：程序在步骤8结束后停止")
        print("=" * 60 + "\n")
        return False  # 测试断点：在步骤8结束后停止
            
    except Exception as e:
        print(f"提交验证码时出现异常: {str(e)}")
        save_screenshot(tab, "verification_submit_error")
        time.sleep(5)
    
    # Step 9: Wait for page navigation after verification
    print(f"\n✅ 步骤9: 等待验证完成后的页面跳转...")
    
    # Wait for page to navigate to the next step
    max_wait_time = 15
    wait_time = 0
    check_interval = 2
    
    while wait_time < max_wait_time:
        time.sleep(check_interval)
        wait_time += check_interval
        
        current_url = tab.url
        print(f"   当前页面 URL: {current_url}")
        
        # Check if we've reached the profile creation page
        if "/admin/create" in current_url or "/home/cid/" in current_url:
            print(f"   ✅ 页面已跳转到下一步")
            break
        
        # Check if we're still on verification page
        if "/verify" in current_url:
            print(f"   仍在验证页面，继续等待...")
            continue
    
    save_screenshot(tab, "after_verification")
    print(f"   ✅ 验证完成，截图已保存")
    
    # Step 10: Fill in personal information
    try:
        print(f"\n✅ 步骤10: 填写个人信息")
        time.sleep(3)
        
        # Check current URL to determine if we're on the profile creation page
        current_url = tab.url
        print(f"   当前页面 URL: {current_url}")
        
        if "/admin/create" not in current_url and "/home/cid/" not in current_url:
            print(f"   ⚠️ 未跳转到个人信息填写页面，可能已经完成注册")
            save_screenshot(tab, "current_page_check")
            return True
        
        # Try to find name input field
        name_input = None
        selectors = [
            "@name=displayName",
            "@placeholder=全名",
            "@placeholder=Full name",
            "tag:input",
            "xpath://input[@type='text']"
        ]
        
        for selector in selectors:
            try:
                name_input = tab.ele(selector, timeout=3)
                if name_input:
                    print(f"   找到姓名输入框 (选择器: {selector})")
                    break
            except:
                continue
        
        if not name_input:
            logging.warning("未找到姓名输入框，可能已经跳转到主页面")
        else:
            # Use the first name from the email (before the timestamp)
            display_name = account.split('@')[0]
            import re
            name_only = re.sub(r'\d+', '', display_name)
            if name_only:
                display_name = name_only
            
            print(f"   输入姓名: {display_name}")
            
            # Clear any existing text
            try:
                name_input.clear()
                time.sleep(0.5)
            except:
                pass
            
            name_input.input(display_name)
            time.sleep(random.uniform(1, 2))
            save_screenshot(tab, "name_entered")
            print(f"   ✅ 姓名已填写")
        
    except Exception as e:
        logging.warning(f"填写姓名时出现异常: {str(e)}")
    
    # Step 11: Click "同意并开始使用" button
    try:
        print(f"\n✅ 步骤11: 点击 '同意并开始使用' 按钮")
        time.sleep(2)
        
        # Try to find the agree and start button
        create_button = None
        button_texts = ["同意并开始使用", "开始使用", "同意并继续", "创建账号", "Agree and get started", "Get started"]
        
        for text in button_texts:
            try:
                create_button = tab.ele(text, timeout=3)
                if create_button:
                    print(f"   找到按钮: {text}")
                    break
            except:
                continue
        
        if not create_button:
            # Try to find button by type
            try:
                create_button = tab.ele("@type=submit", timeout=3)
                if create_button:
                    print(f"   找到提交按钮")
            except:
                pass
        
        if create_button:
            # Scroll to button
            try:
                create_button.scroll.to_see()
                time.sleep(1)
            except:
                pass
            
            # Try to click the button
            click_success = False
            try:
                create_button.click()
                click_success = True
                print(f"   ✅ 已点击 '{create_button.text()}' 按钮")
            except Exception as e1:
                print(f"   普通点击失败: {str(e1)}")
                try:
                    tab.run_js("arguments[0].click();", create_button)
                    click_success = True
                    print(f"   ✅ 通过JS点击了按钮")
                except Exception as e2:
                    print(f"   JS点击也失败: {str(e2)}")
            
            if click_success:
                print("   账号创建请求已提交")
                time.sleep(5)
                save_screenshot(tab, "account_created")
            else:
                logging.warning("点击创建账号按钮失败")
        else:
            logging.warning("未找到创建账号按钮")
            
    except Exception as e:
        logging.warning(f"点击创建账号按钮时出现异常: {str(e)}")
        time.sleep(3)
    
    # Step 12: Check if registration is successful
    print(f"\n✅ 步骤12: 检查注册结果...")
    
    # Wait for page to load completely
    time.sleep(5)
    
    # Take final screenshot
    save_screenshot(tab, "final_page")
    
    # Get current URL
    current_url = tab.url
    print(f"\n最终页面 URL: {current_url}")
    
    # Check for success indicators
    # Success: URL contains /home/cid/ (main dashboard)
    if "/home/cid/" in current_url:
        print("\n" + "=" * 60)
        print("  ✅ Gemini Enterprise 注册成功！")
        print("=" * 60)
        print(f"  📧 邮箱: {account}")
        print(f"  🔑 密码: {password}")
        print(f"  🌐 控制台: {current_url}")
        print("=" * 60 + "\n")
        return True
    # Alternative success: URL contains /admin/create but page shows success
    elif "/admin/create" in current_url:
        # Check if we can find success indicators on the page
        try:
            page_text = tab.html
            if "Gemini Enterprise" in page_text and ("免费试用" in page_text or "30天" in page_text):
                print("\n" + "=" * 60)
                print("  ✅ Gemini Enterprise 注册成功！")
                print("=" * 60)
                print(f"  📧 邮箱: {account}")
                print(f"  🔑 密码: {password}")
                print(f"  🌐 当前页面: {current_url}")
                print("=" * 60 + "\n")
                return True
            else:
                logging.warning("仍在创建页面，可能需要等待或重试")
                return False
        except:
            logging.warning("仍在创建页面，可能需要等待或重试")
            return False
    # Check if we're on any Gemini Business page
    elif "business.gemini.google" in current_url:
        print("\n" + "=" * 60)
        print("  ✅ Gemini Enterprise 注册成功！")
        print("=" * 60)
        print(f"  📧 邮箱: {account}")
        print(f"  🔑 密码: {password}")
        print(f"  🌐 当前页面: {current_url}")
        print("=" * 60 + "\n")
        return True
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
