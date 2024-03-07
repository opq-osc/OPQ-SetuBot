import httpx
from lxml import html
from pathlib import Path
import json
import hashlib

curFileDir = Path(__file__).parent.absolute()  # 当前文件路径

anime_list = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"}


def update_json_file(path, data):
    # 清空文件内容
    print(path)
    with open(path, 'w') as file:
        file.write('')

    # 更新文件内容
    with open(path, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def download_image(url, save_path):
    print(save_path)
    response = httpx.get(url, headers=headers)
    with open(save_path, "wb") as file:
        file.write(response.content)


def add_anime_info(anime_list, name, day_of_week, time, acover, tags):
    anime_info = {
        "name": name,
        "time": [day_of_week, time],
        "acover": acover,
        "tags": tags
    }

    anime_list.append(anime_info)


def get_imgurl_from_xpath(url):
    total_xpath = '//*[@id="acgs-anime-icons"]'
    try:
        with httpx.Client(follow_redirects=True,
                          headers={
                              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"}) as client:

            # 发送 HTTP 请求并获取网页内容
            response = client.get(url)

            # 确认请求成功
            response.raise_for_status()

            # 使用 lxml 解析网页内容
            tree = html.fromstring(response.content)

            # 获取当前番剧总数：
            total_number_element = tree.xpath(total_xpath)
            total_number = len(total_number_element[0])

            for i in range(1, total_number + 1):
                day_element = tree.xpath(f'//*[@id="acgs-anime-icons"]/div[{i}]')
                name_element = tree.xpath(f'//*[@id="acgs-anime-icons"]/div[{i}]/a/div[3]')
                img_element = tree.xpath(f'//*[@id="acgs-anime-list"]/div[{i}]/div[1]/div/div[2]/div/img')
                tag_element = tree.xpath(f'//*[@id="acgs-anime-list"]/div[{i}]/div[1]/div/div[3]/div[2]/div[2]/div[1]')
                time_element = tree.xpath(f'//*[@id="acgs-anime-icons"]/div[{i}]')
                get_day = day_element[0].get('weektomorrow')
                time_data = time_element[0].get('weekairtime')[1:]
                time = f"{time_data[:2]}:{time_data[2:]}"
                name = name_element[0].text_content()
                url = img_element[0].get('src')
                tag = tag_element[0].text_content()
                tags = []
                for j in range(1, len(tag_element[0]) + 1):
                    single_tag_element = tree.xpath(
                        f'//*[@id="acgs-anime-list"]/div[{i}]/div[1]/div/div[3]/div[2]/div[2]/div[1]/tags[{j}]')
                    tags.append(single_tag_element[0].text_content())
                add_anime_info(anime_list, name, get_day, time, url, tags)

    except httpx.RequestError as e:
        print("Error fetching the URL:", e)
        return None
    except Exception as ex:
        print("An error occurred:", ex)
        return None


# 替换此 URL 为你要搜索的目标网页
url_to_search = "https://acgsecrets.hk/bangumi"  # 将 URL 替换为你要搜索的目标网页

# 调用封装的函数来搜索目标元素的 src 属性值
result_ssrc = get_imgurl_from_xpath(url_to_search)

print(anime_list)

digitalConversionDict = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "日": 7,
}
b = {}

for d in anime_list:
    print(d)
    if dd := b.get(digitalConversionDict[d["time"][0]]):
        # print(dd)
        if dd.get(d["time"][1]):

            dd[d["time"][1]].append(
                {"name": d["name"], "filename": f"{hashlib.md5(d['name'].encode()).hexdigest()}.jpg",
                 "tags": d["tags"]})
            b[digitalConversionDict[d["time"][0]]] = dd
        else:
            b[digitalConversionDict[d["time"][0]]][d["time"][1]] = [
                {"name": d["name"], "filename": f"{hashlib.md5(d['name'].encode()).hexdigest()}.jpg",
                 "tags": d["tags"]}]
    else:
        b[digitalConversionDict[d["time"][0]]] = {
            d["time"][1]: [{"name": d["name"], "filename": f"{hashlib.md5(d['name'].encode()).hexdigest()}.jpg",
                            "tags": d["tags"]}]}
sorted_data = dict(sorted(b.items()))
import datetime

for k, v in sorted_data.items():
    sorted_data[k] = dict(sorted(v.items(), key=lambda x: datetime.datetime.strptime(x[0], '%H:%M')))

update_json_file(curFileDir.parent / "plugins" / "daily" / "config" / "bangumi.json", sorted_data)
for fj in anime_list:
    download_image(fj['acover'],
                   curFileDir.parent / "plugins" / "daily" / "files" / "bangumi" / f"{hashlib.md5(fj['name'].encode()).hexdigest()}.jpg")
