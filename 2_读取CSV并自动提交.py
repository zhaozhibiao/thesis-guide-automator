import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
import json

# 读取配置文件
config = {}
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception as e:
    print("读取 config.json 失败，请检查配置文件格式！", e)
    exit(1)

csv_file = '各学生指导记录_待审核.csv'
if not os.path.exists(csv_file):
    print(f"找不到文件 {csv_file}！请先运行 1_生成并导出指导记录.py 并核对数据。")
    exit(1)

# 读取包含所有学生所有扩写记录的 CSV
df_csv = pd.read_csv(csv_file, encoding='utf-8-sig')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-proxy-server')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--remote-allow-origins=*')

print("正在启动浏览器...")
try:
    driver_path = ChromeDriverManager().install()
    service = Service(executable_path=driver_path, host='127.0.0.1')
    driver = webdriver.Chrome(service=service, options=chrome_options)
except Exception as e:
    print("启动失败:", e)
    driver = webdriver.Chrome(options=chrome_options)

driver.get('https://co2.cnki.net/Login.html?dp=tute&r=1604392739553')
print("等待登录完成...如果出现验证码，请在 60 秒内手动完成验证！")

wait = WebDriverWait(driver, 10) 
wait.until(EC.presence_of_element_located((By.ID, 'username')))
role=driver.find_element(By.CSS_SELECTOR,'#rolebox > span[data-id="2"]')
driver.execute_script("arguments[0].click();", role)
username_field = driver.find_element(By.ID,'username')
password_field = driver.find_element(By.ID,'password')

username_field.send_keys(config.get('cnki_username', ''))
password_field.send_keys(config.get('cnki_password', ''))
agreement=driver.find_element(By.CSS_SELECTOR,'#agreement')
driver.execute_script("arguments[0].click();", agreement)
login_button = driver.find_element(By.ID,'loginBtn')
driver.execute_script("arguments[0].click();", login_button)

wait = WebDriverWait(driver, 60) 
wait.until(EC.element_to_be_clickable((By.ID, 'yearsList')))
yearsList= driver.find_element(By.ID,'yearsList')

li_elements=driver.find_element(By.XPATH,'//*[@id="yearsList"]/li[1]')
driver.execute_script("arguments[0].click();", li_elements)

wait = WebDriverWait(driver, 30) 
wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="roleList"]/li[1]')))
role=driver.find_element(By.XPATH,'//*[@id="roleList"]/li[1]')
driver.execute_script("arguments[0].click();", role)

wait = WebDriverWait(driver, 20) 
wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="nav"]/li[5]/a')))
doc=driver.find_element(By.XPATH,'//*[@id="nav"]/li[5]/a')
driver.execute_script("arguments[0].click();", doc)

wait = WebDriverWait(driver, 10) 
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#nav > li:nth-child(5) > ul > li:nth-child(3) > a')))
zhidao=driver.find_element(By.CSS_SELECTOR,'#nav > li:nth-child(5) > ul > li:nth-child(3) > a')
driver.execute_script("arguments[0].click();", zhidao)

wait = WebDriverWait(driver, 20) 
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'[title="指导教师提交指导记录"]')))
frame = driver.find_element(By.CSS_SELECTOR,'[title="指导教师提交指导记录"]')
driver.switch_to.frame(frame)

wait = WebDriverWait(driver, 20) 
wait.until(EC.presence_of_element_located((By.XPATH,'//div[1]/div[3]/div/div[1]/div[2]/div[2]')))

print("正在等待学生列表数据加载...")
time.sleep(4) # 等待 EasyUI 异步数据加载

info = driver.find_element(By.XPATH,'//div[1]/div[3]/div/div[1]/div[2]/div[2]')
student_rows = info.find_elements(By.TAG_NAME,"tr")
total_students = len(student_rows)
print(f"当前页面共发现 {total_students} 名学生！")

for s_index in range(total_students):
    # 根据序号提取该学生在 CSV 中的所有记录
    student_records = df_csv[df_csv['学生序号'] == s_index]
    if student_records.empty:
        print(f"CSV 中未找到序号为 {s_index} 的学生数据，跳过。")
        continue

    # 重新获取学生元素
    info = driver.find_element(By.XPATH,'//div[1]/div[3]/div/div[1]/div[2]/div[2]')
    student = info.find_elements(By.TAG_NAME,"tr")[s_index]
    
    # 提取标识只用于日志展示
    topic = student_records.iloc[0]['学生标识']
    print(f"\n正在提交学生 [{topic}] 的记录...")

    xinzeng=student.find_elements(By.CSS_SELECTOR,"td[field='operate']> div > a")
    if len(xinzeng)>1:
        filage=1
    else:
        filage=0
    driver.execute_script("arguments[0].click();", xinzeng[0])
    
    driver.switch_to.default_content()
    wait = WebDriverWait(driver, 20)
    if filage==0:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'[title="学生指导记录"]')))
        frame1 = driver.find_elements(By.CSS_SELECTOR,'[title="学生指导记录"]')[-1]
    else:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'[title="添加学生指导记录"]')))
        frame1 = driver.find_elements(By.CSS_SELECTOR,'[title="添加学生指导记录"]')[-1]
    
    driver.switch_to.frame(frame1)
    time.sleep(3) # 等待当前学生表格数据加载
    

    for index, (_, csv_row) in enumerate(student_records.iterrows()):
        week = str(csv_row['周次']) if pd.notna(csv_row['周次']) else ""
        generated_content = str(csv_row['AI扩写结果']) if pd.notna(csv_row['AI扩写结果']) else ""
        
        driver.switch_to.default_content()
        if filage==0:
            frame1 = driver.find_elements(By.CSS_SELECTOR,'[title="学生指导记录"]')[-1]
        else:
            frame1 = driver.find_elements(By.CSS_SELECTOR,'[title="添加学生指导记录"]')[-1]
        driver.switch_to.frame(frame1)
        
        wait = WebDriverWait(driver, 10) 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#submit")))
        
        # 强制等待一下表格的 AJAX 异步加载，防止出现数据还没刷出来导致获取到 0 条记录的情况
        time.sleep(3)
        
        tabelnum=driver.find_element(By.CSS_SELECTOR,"#div_talble > div > div > div > div.datagrid-view2 > div.datagrid-body")
        truenum1=tabelnum.find_elements(By.CSS_SELECTOR,"tr.datagrid-row")
        truenum=len(truenum1)

        sequence = index + 1
        
        if index < truenum:
            if config.get("only_add_new", False):
                print(f" - 第 {sequence} 次已有历史记录，根据配置跳过修改...")
                continue
                
            print(f" - 正在修改第 {sequence} 次已有历史记录...")
            row_tr = truenum1[index]
            date_str = ""
            tds = row_tr.find_elements(By.TAG_NAME, "td")
            for td in tds:
                match = re.search(r"(\d{4})[-/年.]\s*0*(\d{1,2})[-/月.]\s*0*(\d{1,2})", td.text)
                if match:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if 1 <= month <= 6 and year != 2026:
                        date_str = f"2026-{month:02d}-{day:02d}"
                    elif month == 12 and year != 2025:
                        date_str = f"2025-{month:02d}-{day:02d}"
                    break
            
            edit_btns = row_tr.find_elements(By.XPATH, ".//a[contains(text(), '修改') or contains(@title, '修改')]")
            if edit_btns:
                driver.execute_script("arguments[0].click();", edit_btns[0])
            else:
                continue
                
            driver.switch_to.default_content()
            wait.until(EC.presence_of_element_located((By.XPATH, '//iframe[contains(@title, "修改")]')))
            edit_frame = driver.find_element(By.XPATH, '//iframe[contains(@title, "修改")]')
            driver.switch_to.frame(edit_frame)
            time.sleep(1)
            
            # 填入日期
            if date_str:
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for inp in inputs:
                    val = inp.get_attribute('value')
                    if val and re.search(r"\d{4}-\d{2}-\d{2}", val):
                        js_code = """
                            arguments[0].classList.remove('textbox-prompt');
                            arguments[0].value = arguments[1];
                            var hidden = arguments[0].parentNode.querySelector('input.textbox-value');
                            if(hidden) hidden.value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        """
                        driver.execute_script(js_code, inp, date_str)
                        break
            
            # 填入文本
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,".textbox-text")))
            textboxes = driver.find_elements(By.CSS_SELECTOR,".textbox-text")
            inputcontent = None
            for tb in textboxes:
                if tb.tag_name.lower() == 'textarea' or tb.size.get('height', 0) > 40:
                    inputcontent = tb
                    break
            if not inputcontent and len(textboxes) > 1:
                inputcontent = textboxes[1]
                
            if inputcontent:
                # 使用彻底的 JS 和 EasyUI 原生方法赋值，避免不可交互元素的报错
                js_code = """
                    var val = arguments[1];
                    var input = arguments[0];
                    if(window.jQuery) {
                        var orig = window.jQuery(input).closest('.textbox').prev();
                        if(orig.length > 0) {
                            try {
                                if(orig.hasClass('combobox-f')) orig.combobox('setValue', val);
                                else if(orig.hasClass('datebox-f')) orig.datebox('setValue', val);
                                else orig.textbox('setValue', val);
                            } catch(e) {}
                        }
                    }
                    input.classList.remove('textbox-prompt');
                    input.value = val;
                    var h1 = input.parentNode.querySelector('input[type="hidden"]');
                    if(h1) { h1.value = val; h1.dispatchEvent(new Event('change', {bubbles:true})); }
                    var h2 = input.parentNode.parentNode.querySelector('input[type="hidden"]');
                    if(h2) { h2.value = val; h2.dispatchEvent(new Event('change', {bubbles:true})); }
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    input.dispatchEvent(new Event('blur', { bubbles: true }));
                """
                driver.execute_script(js_code, inputcontent, generated_content)
                time.sleep(0.5)
                
            submit_btn = driver.find_element(By.CSS_SELECTOR,"#submit_uploading")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            
        else:
            print(f" - 正在新增第 {sequence} 次指导记录...")
            tianjiabutton=driver.find_element(By.CSS_SELECTOR,"#submit")
            driver.execute_script("arguments[0].click();", tianjiabutton)
            
            driver.switch_to.default_content()
            frame1 = driver.find_elements(By.CSS_SELECTOR,'[title="添加指导记录"]')[-1]
            driver.switch_to.frame(frame1)
            wait = WebDriverWait(driver, 10) 
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,".textbox-text")))
            textboxes = driver.find_elements(By.CSS_SELECTOR,".textbox-text")
            
            inputweek = textboxes[0]
            
            # 使用彻底的 JS 和 EasyUI 原生方法赋值，避免不可交互元素的报错
            js_code = """
                var val = arguments[1];
                var input = arguments[0];
                if(window.jQuery) {
                    var orig = window.jQuery(input).closest('.textbox').prev();
                    if(orig.length > 0) {
                        try {
                            if(orig.hasClass('combobox-f')) orig.combobox('setValue', val);
                            else if(orig.hasClass('datebox-f')) orig.datebox('setValue', val);
                            else orig.textbox('setValue', val);
                        } catch(e) {}
                    }
                }
                input.classList.remove('textbox-prompt');
                input.value = val;
                var h1 = input.parentNode.querySelector('input[type="hidden"]');
                if(h1) { h1.value = val; h1.dispatchEvent(new Event('change', {bubbles:true})); }
                var h2 = input.parentNode.parentNode.querySelector('input[type="hidden"]');
                if(h2) { h2.value = val; h2.dispatchEvent(new Event('change', {bubbles:true})); }
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
            """
            driver.execute_script(js_code, inputweek, week)
            time.sleep(0.5)
            
            # 重新获取 textboxes，因为前面的 JS 可能触发了 EasyUI 重绘 DOM，导致之前的元素变为 stale
            textboxes = driver.find_elements(By.CSS_SELECTOR,".textbox-text")
            inputcontent = None
            for tb in textboxes:
                if tb.tag_name.lower() == 'textarea' or tb.size.get('height', 0) > 40:
                    inputcontent = tb
                    break
            if not inputcontent and len(textboxes) > 1:
                inputcontent = textboxes[1]
            
            if inputcontent:
                # 使用彻底的 JS 和 EasyUI 原生方法赋值，避免不可交互元素的报错
                js_code = """
                    var val = arguments[1];
                    var input = arguments[0];
                    if(window.jQuery) {
                        var orig = window.jQuery(input).closest('.textbox').prev();
                        if(orig.length > 0) {
                            try {
                                if(orig.hasClass('combobox-f')) orig.combobox('setValue', val);
                                else if(orig.hasClass('datebox-f')) orig.datebox('setValue', val);
                                else orig.textbox('setValue', val);
                            } catch(e) {}
                        }
                    }
                    input.classList.remove('textbox-prompt');
                    input.value = val;
                    var h1 = input.parentNode.querySelector('input[type="hidden"]');
                    if(h1) { h1.value = val; h1.dispatchEvent(new Event('change', {bubbles:true})); }
                    var h2 = input.parentNode.parentNode.querySelector('input[type="hidden"]');
                    if(h2) { h2.value = val; h2.dispatchEvent(new Event('change', {bubbles:true})); }
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    input.dispatchEvent(new Event('blur', { bubbles: true }));
                """
                driver.execute_script(js_code, inputcontent, generated_content)
                time.sleep(0.5)
            
            submitbutton=driver.find_element(By.CSS_SELECTOR,"#submit_uploading")
            driver.execute_script("arguments[0].click();", submitbutton)
            time.sleep(2)

    # 处理完该学生，关闭其弹窗并刷新列表
    driver.switch_to.default_content()
    close_btns = driver.find_elements(By.CSS_SELECTOR, ".panel-tool-close")
    if close_btns:
        driver.execute_script("arguments[0].click();", close_btns[-1])
    time.sleep(1)
    
    wait = WebDriverWait(driver, 10) 
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#nav > li:nth-child(5) > ul > li:nth-child(3) > a')))
    zhidao=driver.find_element(By.CSS_SELECTOR,'#nav > li:nth-child(5) > ul > li:nth-child(3) > a')
    driver.execute_script("arguments[0].click();", zhidao)
    
    wait = WebDriverWait(driver, 20) 
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'[title="指导教师提交指导记录"]')))
    frame = driver.find_element(By.CSS_SELECTOR,'[title="指导教师提交指导记录"]')
    driver.switch_to.frame(frame)
    time.sleep(2)

print("所有修改/新增任务已顺利完成！")
driver.quit()
