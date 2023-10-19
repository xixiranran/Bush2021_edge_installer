import requests
import xml.etree.ElementTree as tree
import base64
import binascii
import json
from datetime import datetime, timezone

requests.packages.urllib3.disable_warnings()

channels = {
    'stable': 'msedge-stable-win',
    'win7and8': 'msedge-stable-win7and8',
    'beta': 'msedge-beta-win',
    'dev': 'msedge-dev-win',
    'canary': 'msedge-canary-win',
}

CheckVersion = 'https://msedge.api.cdp.microsoft.com/api/v1.1/contents/Browser/namespaces/Default/names/{0}/versions/latest?action=select'
GetDownloadLink = 'https://msedge.api.cdp.microsoft.com/api/v1.1/internal/contents/Browser/namespaces/Default/names/{0}/versions/{1}/files?action=GenerateDownloadInfo'

results = {}


def check_version(appid):
    # 必须包含 UA 头，否则报错
    headers = {
        'User-Agent': 'Microsoft Edge Update/1.3.129.35;winhttp'
    }
    data = {
        'targetingAttributes': {'Updater': 'MicrosoftEdgeUpdate'}
    }
    response = requests.post(CheckVersion.format(appid), json=data, headers=headers, verify=False)

    if response.status_code == 200:
        content_id = response.json().get('ContentId')
        if content_id:
            version = content_id.get('Version')
            return version
        else:
            print("ContentId not found in the response.")
    else:
        print("Error: Unable to fetch version information. Status code:", response.status_code)

    return None


def get_download_link(appid, version):
    headers = {
        'User-Agent': 'Microsoft Edge Update/1.3.129.35;winhttp'
    }
    response = requests.post(GetDownloadLink.format(appid, version), headers=headers, verify=False)

    if response.status_code == 200:
        download_info = response.json()
        if download_info:
            # 首先按照字节大小从大到小排序
            download_info.sort(key=lambda x: x.get('SizeInBytes', 0), reverse=True)
            item = download_info[0]
            file_id = item.get('FileId', '')
            url = item.get('Url', '')
            size_in_bytes = item.get('SizeInBytes', 0)
            hashes = item.get('Hashes', {})
            sha1 = hashes.get('Sha1', '')
            sha256 = hashes.get('Sha256', '')

            return {
                '文件名': file_id,
                '下载链接': url,
                '字节大小': size_in_bytes,
                'Sha1': sha1,
                'Sha256': sha256
            }
        else:
            print("Download information not found in the response.")
    else:
        print("Error: Unable to fetch download information. Status code:", response.status_code)

    return None


def get_info(appid):
    version = check_version(appid)
    if version:
        name = appid
        info = get_download_link(appid, version)
        if info:
            info['version'] = version
            return name, info
        else:
            print("Error: Unable to obtain download information for", appid)
    else:
        print("Error: Unable to obtain version information for", appid)
    return None


def version_tuple(v):
    return tuple(map(int, (v.split("."))))


def load_json():
    global results
    with open('data.json', 'r') as f:
        results = json.load(f)


def fetch():
    for channel, appid in channels.items():
        for arch in ['x86', 'x64']:
            name, info = get_info(f'{appid}-{arch}')
            if name not in results:
                results[name] = info
            elif version_tuple(info['version']) > version_tuple(results[name]['version']):
                results[name] = info
            else:
                print("ignore", name, info['version'])


suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def replace_http_to_https():
    for name, info in results.items():
        results[name]['下载链接'] = results[name].get('下载链接', '').replace('http://msedge.b', 'https://msedge.sb')


def save_md():
    with open('readme.md', 'w') as f:
        f.write(f'# Microsoft Edge 离线安装包下载链接\n')
        f.write(f'最后检测更新时间\n')
        f.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('\n')
        f.write(f'注意\n')
        f.write(
            f'* Microsoft 直链会过期，请及时保存。\n')
        f.write(
            f'* 下载文件名可能是乱码，有需要的话请自行重命名。\n')
        f.write('\n')
        for name, info in results.items():
            f.write(f'## {name[7:].replace("win-", "").replace("-", " ")}\n')
            f.write(f'**最新版本**：{info.get("version", "")}  \n')
            f.write(f'**文件大小**：{humansize(info.get("字节大小", 0))}  \n')
            f.write(f'**文件名**：{info.get("文件名", "")}  \n')
            # f.write(f'**校验值（Sha256）**：{info.get("Sha256", "")}  \n')
            f.write(f'**下载链接**：[{info.get("下载链接", "")}]({info.get("下载链接", "")})  \n')
            f.write('\n')


def save_json():
    with open('data.json', 'w') as f:
        json.dump(results, f, indent=4)
    for k, v in results.items():
        with open(f'{k}.json', 'w') as f:
            json.dump(v, f, indent=4)


def main():
    load_json()
    fetch()
    replace_http_to_https()
    save_md()
    save_json()


main()
