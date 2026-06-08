import os
import json
import urllib.request
import urllib.error
import pandas as pd
import re
import time

# 防止 Python 和 ChromeDriver 通信走代理
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

# 读取配置文件
config = {}
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception as e:
    print("读取 config.json 失败，请检查配置文件格式！", e)
    exit(1)

def generate_record_content(sequence, template_content, topic_name):
    API_KEY = config.get("deepseek_api_key", "")
    BASE_URL = "https://api.deepseek.com/chat/completions" 
    MODEL = "deepseek-chat"

    if not API_KEY:
        return f"【第{sequence}次指导】\n{template_content}\n学生已理解指导内容，后续将按要求改进。"

    # 更新提示词，融入学生毕设题目
    prompt = f"你是一个毕业设计指导老师。这是对学生的第 {sequence} 次指导，该学生的毕设题目是：【{topic_name}】。\n原本的指导记录模板是：'{template_content}'。\n请你结合该学生的毕设题目，对模板内容进行简易的润色扩写，使其看起来真实自然。字数要求在50字以内，直接输出最终的指导内容，不要包含多余的废话。"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的毕业设计指导老师。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        req = urllib.request.Request(BASE_URL, headers=headers, data=json.dumps(data).encode('utf-8'))
        response = urllib.request.urlopen(req, timeout=15)
        result = json.loads(response.read().decode('utf-8'))
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"调用 AI 接口失败: {e}")
        return template_content

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

df = pd.read_csv('指导记录模板.csv', header=None, encoding='utf-8')
df = df.dropna(how='all') # 去除可能存在的纯空行
cishu = len(df)

info = driver.find_element(By.XPATH,'//div[1]/div[3]/div/div[1]/div[2]/div[2]')
student_rows = info.find_elements(By.TAG_NAME,"tr")
total_students = len(student_rows)
print(f"当前页面共发现 {total_students} 名学生！")

results = []

for s_index in range(total_students):
    info = driver.find_element(By.XPATH,'//div[1]/div[3]/div/div[1]/div[2]/div[2]')
    student = info.find_elements(By.TAG_NAME,"tr")[s_index]
    
    student_name = "未知姓名"
    topic_name = "未知题目"
    tds = student.find_elements(By.TAG_NAME, "td")
    for td in tds:
        field = td.get_attribute("field")
        if field == "学生姓名":
            student_name = td.text.strip()
        elif field == "名称":
            topic_name = td.text.strip()
            
    topic = f"{student_name} - {topic_name}"
    
    print(f"正在为学生 [{topic}] 生成 AI 扩写记录...")
    
    for index, xlsrow in df.iterrows():
        if index >= cishu:
            break
        content = str(xlsrow[0]) if pd.notna(xlsrow[0]) else ""
        week = str(xlsrow[1]) if pd.notna(xlsrow[1]) else ""
        sequence = index + 1
        
        print(f"   - 调用 AI 生成第 {sequence} 次...")
        generated_content = generate_record_content(sequence, content, topic_name)
        
        results.append({
            "学生序号": s_index,
            "学生标识": topic,
            "周次": week,
            "原始模板": content,
            "AI扩写结果": generated_content
        })

# 导出到 CSV
out_df = pd.DataFrame(results)
out_df.to_csv('各学生指导记录_待审核.csv', index=False, encoding='utf-8-sig')

print("\n全部 AI 生成完毕！已导出为 各学生指导记录_待审核.csv")
print("请打开此 CSV 文件核对并修改，确认无误后运行第二步脚本。")
driver.quit()
