import json

import codecs
import sys
# import queue
import threading

import requests
import time
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

availability_url = 'https://reserve.cdn-apple.com/CN/zh_CN/reserve/iPhone/availability.json'
choose_iphone_url = 'https://reserve.cdn-apple.com/CN/zh_CN/reserve/iPhone/availability?channel=1&store={0}&partNumber={1}'
x = PrettyTable(['时间', '预约', '状态'])
x.align = 'c'
x.padding_width = 3
leancloud_app_id = 'pnnejv58vui1q50cny3epjib9wzniv34qx5l31exdhv0eq04'
leancloud_app_key = '7e935r6rh2nlq09opz0gj91sjqmnx3vbravm0zbow3mgefh6'
sms_to_phone = '106550218370001'
phone_number = '13143332278'
'''
中国移动： 10657516068401
中国电信： 106590210056601
中国联通： 106550218370001
'''


# 获取商店的代码
def store_name_to_code(store_name):
    f = codecs.open('%s/store.json' % sys.path[0], 'r', encoding='UTF-8')
    stores = f.read()
    store_json = json.loads(stores)
    store_kv = dict()
    for store in store_json['stores']:
        store_kv[store['storeCity'] + store['storeName']] = store['storeNumber']
    f.close()
    return store_kv[store_name], store_name


# 获取手机的型号
def phone_name_to_code(phone_name, phone_storage, phone_color):
    f = codecs.open('%s/phone.json' % sys.path[0], 'r', encoding='UTF-8')
    phone_json = f.read()
    phone_versions = json.loads(phone_json)
    model_kv = dict()
    for phone_version in phone_versions['skus']:
        model_kv[phone_version['productDescription']] = phone_version['part_number']

    if phone_name == '7':
        version = 'iPhone 7 '
    else:
        version = 'iPhone 7 Plus '
    phone_storage += 'GB '
    phone_color += '色'
    iphone_str = version + phone_storage + phone_color
    model = model_kv[iphone_str]
    f.close()
    return model, iphone_str


# 执行线程
def append_thread_task():
    f = codecs.open('%s/config.txt' % sys.path[0], 'r', encoding='UTF-8')
    threads = []
    for task in f.readlines():
        task = task.strip('\n').split(',')
        t = threading.Thread(target=start, args=(task,))
        threads.append(t)
    f.close()
    return threads


# 执行监控任务
# def fetch_phone_func(q):
#     # while True:
#     #     try:
#     #         task = q.get_nowait().strip('\n').split(',')
#     #         i = q.qsize()
#     #     except:
#     #         break
#     start(task)


# 具体执行
def start(task):
    store_name = task[0]
    version = task[1]
    storage = task[2]
    color = task[3]
    account = task[4]
    password = task[5]
    # print(store_name_to_code(store_name))
    search_phone(store_name_to_code(store_name), phone_name_to_code(version, storage, color), account, password)


# 监控
def search_phone(store_code_and_name, phone_code_and_name, account, password):
    while True:
        try:

            availability = requests.get(availability_url).text

        except:
            print('超时')
            continue
        availability_json = json.loads(availability)
        if availability_json[store_code_and_name[0]][phone_code_and_name[0]] == 'NONE' or \
                        availability_json[store_code_and_name[0]][
                            phone_code_and_name[0]] == 'none':
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), store_code_and_name[1], phone_code_and_name[1],
                  '无货')
        else:
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), store_code_and_name[1], phone_code_and_name[1],
                  '有货有货有货有货有货有货有货有货')
            open_url(store_code_and_name[0], phone_code_and_name[0], account, password)
            break


def open_url(store_code, phone_code, account, password):
    driver = webdriver.Chrome()
    driver.get(choose_iphone_url.format(store_code, phone_code))
    driver.find_element_by_name('submit').click()

    # 开始登录
    try:
        WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.ID, 'appIdKey'))
        )
    finally:
        pass
    driver.switch_to.frame(0)
    email_elem = driver.find_element_by_id('appleId')
    password_elem = driver.find_element_by_id('pwd')
    email_elem.send_keys(account)
    password_elem.send_keys(password)
    password_elem.send_keys(Keys.RETURN)

    # 开始预约
    try:
        WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[@id='smsForm']/div[2]/div[1]/p[1]/strong"))
        )
    finally:
        pass
    msg_content = driver.find_element_by_xpath("//*[@id='smsForm']/div[2]/div[1]/p[1]/strong").text
    header = {'X-LC-Id': leancloud_app_id,
              'X-LC-Key': leancloud_app_key,
              'Content-Type': 'application/json'}
    data = '{' + '"data":' + '{' + '"action":"com.edanelx.push","alert":"{0}","title":"{1}"'.format(msg_content,
                                                                                                    sms_to_phone) + '}' + '}'
    r = requests.post('https://leancloud.cn/1.1/push', headers=header, data=data)
    print(r.text)
    phone_elem = driver.find_element_by_xpath("//*[@id='phoneNumber']")
    phone_elem.send_keys(phone_number)
    time.sleep(1000)  # 测试使用


if __name__ == '__main__':
    for t1 in append_thread_task():
        t1.start()
