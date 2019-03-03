import os
import requests
import pymongo
from urllib.parse import urlencode           #来构造url参数的
from hashlib import md5                      #用来解析图片二进制的
from  config import *
from multiprocessing import Pool

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


#获取页面json
def get_page(offest):
    params={
            'aid':'24',
            'offest':offest,
            'format':'json',
            'keyword':'长腿美女',
            'autoload':'true',
            'count':'20',
            'en_qc': 1,
            'cur_tab':'1',
            'from':'search_tab',
            'pd':'synthesis'
            }
    url='https://www.toutiao.com/api/search/content/?aid=24&app_name=web_search&offset=0&format=json&keyword=%E9%95%BF%E8%85%BF%E7%BE%8E%E5%A5%B3&autoload=true&count=20&en_qc=1&cur_tab=1&from=search_tab&pd=synthesis' +urlencode(params)
        #用urlencode构造url中参数
    try:
        response=requests.get(url)
        if response.status_code==200:                #当请求成功时(status_code=200时)才继续下面代码
            return response.json()                   #用json方法将结果转化成JSON格式
    except requests.ConnectionError:
        return None



#提取图片url和标题
def parse_page(json):
    if json.get('data'):
        for item in json.get('data'):      #找到所需数据所处位置
            if item.get('title')==None:    #运行后发现不是每个item里都有图片链接和title，没有的直接跳过
                continue
            title=item.get('title')        #找到标题
            print(title)
            images=item.get('image_list')
            print(images)
            for image in images:
                yield{
                    'image':image.get('url'), #找到这个标题下的所以图片url 形成字典生成器
                    'title':title
                }

#实现保存图片的方法
def save_image(item):
    if not os.path.exists(item.get('title')):      #创建以标题为名称的文件夹
        os.mkdir(item.get('title'))
    try:
        response=requests.get(item.get('image'))  #访问图片的url
        if response.status_code==200:
            file_path='{0}/{1}.{2}'.format(item.get('title'),md5(response.content).hexdigest(),'jpg')
            if not os.path.exists(file_path):     #名称file_path使用其内容的md5值，可以去除重复
                with open(file_path,'wb') as f:  #访问成功后，将其二进制代码存入file_path.jpg中
                    f.write(response.content)
            else:
                print('Already Download',file_path)
    except requests.ConnectionError:
        print('Failed to save image')

def save_to_mongo(item):
    if db[MONGO_TABLE].insert(item):
        print('存储到MONGODB成功', item)
        return True
    return False


def main(offest):
    json=get_page(offest)
    for item in parse_page(json):
        print(item)
        save_image(item)
        save_to_mongo(item)


if __name__=='__main__':
    groups = [x * 20 for x in range(0, 20)]
    pool = Pool()
    pool.map(main, groups)