#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import pathlib
import logging
import requests
import traceback
import subprocess
from utils.douyu import DouYu
from utils.huya import HuYa
from utils.bilibili import BiliBili
from flask import Flask, send_from_directory
from flask_apscheduler import APScheduler
from xmltv import xmltv_helpers
from xmltv.models.xmltv import Tv, Channel

'''
自定义配置信息
'''
listen_host = "" #监听服务IP地址
listen_port = 33401 #监听服务端口号
plex_tuner = {
    "bin": pathlib.Path("./bin/plex-tuner").absolute(), #编译好的plex-tuner路径
    "id": "iptv",
    "tuner_count": 9,
    "listen": "0.0.0.0:33400",
    "ffmpeg": "/opt/homebrew/bin/ffmpeg",#ffmpeg地址
    "channel": "http://127.0.0.1:%s/plex/channel" % listen_port
}
#网络直播源
common_channel = [
    {"platform":"bilibili","id":"bilibili-test", "name":"B站自习室", "uid": "25389123" },
    # {"platform":"douyu","id":"douyu-test", "name":"xxx", "uid":"111"},
    # {"platform":"huya","id":"huya-test", "name":"xxx", "uid": "222"},
]
#IPTV单播源，示例为浙江电信IPTV源，键值（ID）与name 需要与51zmt的xml文件对应，便于Plex自动关联频道
tv_channel = {
    '1': {'name':'CCTV1','url':'http://115.233.40.247/PLTV/88888913/224/3221228078/10000100000000060000000002460690_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV1.png'},
    '2': {'name':'CCTV2','url':'http://115.233.40.247/PLTV/88888913/224/3221228083/10000100000000060000000002633372_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV2.png'},
    '3': {'name':'CCTV3','url':'rtsp://115.233.40.247/PLTV/88888913/224/3221229136/10000100000000060000000005809121_0.smil','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV3.png'},
    '4': {'name':'CCTV4','url':'http://115.233.40.247/PLTV/88888913/224/3221227806/10000100000000060000000000304159_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV4.png'},
    '5': {'name':'CCTV5','url':'http://115.233.40.247/PLTV/88888913/224/3221229114/10000100000000060000000005809143_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV5.png'},
    '6': {'name':'CCTV5+','url':'http://115.233.40.247/PLTV/88888913/224/3221229201/52583204.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV5+.png'},
    '7': {'name':'CCTV6','url':'rtsp://115.233.40.247/PLTV/88888913/224/3221229161/10000100000000060000000005809142_0.smil','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV6.png'},
    '8': {'name':'CCTV7','url':'http://115.233.40.247/PLTV/88888913/224/3221228093/10000100000000060000000002633385_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV7.png'},
    '9': {'name':'CCTV8','url':'rtsp://115.233.40.247/PLTV/88888913/224/3221229157/10000100000000060000000005809141_0.smil','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV8.png'},
    '10': {'name':'CCTV9','url':'http://115.233.40.247/PLTV/88888913/224/3221228112/10000100000000060000000002633384_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV9.png'},
    '11': {'name':'CCTV10','url':'http://115.233.40.247/PLTV/88888913/224/3221228131/10000100000000060000000002633383_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV10.png'},
    '13': {'name':'CCTV12','url':'http://115.233.40.247/PLTV/88888913/224/3221228130/10000100000000060000000002633382_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV12.png'},
    '14': {'name':'CCTV13','url':'http://115.233.40.247/PLTV/88888913/224/3221229154/52628615.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV13.png'},
    '15': {'name':'CCTV14','url':'http://115.233.40.247/PLTV/88888913/224/3221228088/10000100000000060000000002633381_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV14.png'},
    '16': {'name':'CCTV15','url':'http://115.233.40.247/PLTV/88888913/224/3221227993/10000100000000060000000000794054_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/CCTV/CCTV15.png'},
    '27': {'name':'湖南卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221227983/10000100000000060000000000794037_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/hunan.png'},
    '28': {'name':'浙江卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221228012/10000100000000060000000000794032_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/zhejiang.png'},
    '29': {'name':'江苏卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221228067/10000100000000060000000001063212_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/jiangsu.png'},
    '31': {'name':'北京卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221228080/10000100000000060000000001063209_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/beijing.png'},
    '31': {'name':'东方卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221228140/10000100000000060000000002670196_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/dongfang.png'},
    '32': {'name':'安徽卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221228120/10000100000000060000000002242150_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/anhui.png'},
    '33': {'name':'广东卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221228011/10000100000000060000000000794034_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/guangdong.png'},
    '38': {'name':'山东卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221227978/10000100000000060000000000794036_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/shandong.png'},
    '40': {'name':'重庆卫视','url':'http://115.233.40.247/PLTV/88888913/224/3221229061/10000100000000060000000004835834_0.smil/index.m3u8?fmt=ts2hls','icon':'http://epg.51zmt.top:8000/tb1/ws/chongqing.png'}
} 

#4,15
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler('logs/service.log'),
                              logging.StreamHandler()])
class Config(object):
    SCHEDULER_API_ENABLED = False

app = Flask(__name__)
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def check_m3u8_url(channel):
    try:
        if not channel["url"]: return False
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        res = requests.get(channel["url"],timeout=7, headers=headers).status_code
        return res == 200
    except:
        return False

@scheduler.task('cron', id='update_xmltv', day='*', hour='*/8', minute='0', second='0')
def update_xmltv():
    '''刷新电视指南，每8小时更新一次'''
    logging.info("更新TV频道EPG信息.")
    try:
        io = requests.get("http://epg.51zmt.top:8000/cc.xml",timeout=100)
        with open("./config/origin.xml","wb") as f: f.write(io.content)
        xml_data = xmltv_helpers.serialize_xml_from_file(pathlib.Path("./config/origin.xml"), Tv)
        channel_list = []
        programme_list = []
        for x in xml_data.channel:
            if x.id in tv_channel.keys():
                x.icon = tv_channel[x.id]['icon']
                channel_list.append(x)
        for x in xml_data.programme:
            if x.channel in tv_channel.keys(): programme_list.append(x)
        #追加自定义频道
        for x in common_channel:
            ch = Channel()
            ch.id = x["id"]
            ch.display_name = x["name"]
            ch.icon = "http://%s:%s/assets/%s" % (listen_host, listen_port, x["platform"])
            channel_list.append(ch)
        xml_generate = Tv()
        xml_generate.channel = channel_list
        xml_generate.programme = programme_list
        xmltv_helpers.write_file_from_xml(pathlib.Path("./config/tv.xml"), xml_generate)
        modify_content = open(pathlib.Path("./config/tv.xml")).read().replace('<icon>','<icon src="').replace('</icon>','" />')
        os.remove(pathlib.Path("./config/origin.xml"))
        open(pathlib.Path("./config/tv.xml"),"w+").write(modify_content)
    except:
        logging.error(traceback.format_exc())

@scheduler.task('cron', id='update_channel', day='*', hour='*', minute='*/10', second='0')
def update_channel():
    '''每10分钟判断一次网络直播URL'''
    channels = []
    try:
        channel_list = json.loads(open(pathlib.Path("./config/channel.json"),"r").read())
        mem_channel = {}
        for i in channel_list:
            mem_channel[i["id"]]= i
    except:
        mem_channel = {}
    #ThirdParty
    cursor = 0
    for i in common_channel:
        item = {"type": "bilibili", "icon": "", "name": i["name"], "id": i["id"], "url": "22757083" } #随便找一个24h的源，避免Plex TV客户端加载不到源导致卡死
        if mem_channel.__contains__(i["id"]) and check_m3u8_url(mem_channel[i["id"]]):
            channels.append(mem_channel[i["id"]])
            continue
        if i["platform"] == "douyu":
            real_url = None
            try:
                real_url = DouYu(i["uid"]).get_real_url()
            except:
                logging.error(traceback.format_exc())
            if real_url:
                item["type"] = "hls"
                item["url"] = real_url[-1]
                logging.info("更新频道源%s 地址:%s" % (item["name"],item["url"]))
                cursor += 1
            channels.append(item)
        elif i["platform"] == "huya":
            real_url = HuYa(i["uid"], 1463993859134, 1).get_real_url()
            if real_url:
                item["type"] = "hls"
                item["url"] = real_url[0]
                logging.info("更新频道源%s 地址:%s" % (item["name"],item["url"]))
                cursor += 1
            channels.append(item)
        elif i["platform"] == "bilibili":
            try:
                real_url = BiliBili(i["uid"]).get_real_url()
            except:
                real_url = None
            if real_url:
                item["type"] = "hls"
                item["url"] = real_url["http_hls_ts_avc"]
                logging.info("更新频道源%s 地址:%s" % (item["name"],item["url"]))
                cursor += 1
            channels.append(item)
        else:
            logging.error("不支持的平台: %s" % item["platform"])
    open(pathlib.Path("./config/channel.json"),"w+").write(json.dumps(channels,indent=2,ensure_ascii=False))
    logging.info("更新直播地址完成，共%s个频道，%s个频道流发生变化" % (len(channels),cursor))

def update_xteve():
    code = "#EXTM3U\n"
    for x in tv_channel.keys():
        code += '#EXTINF:-1 tvg-id="%s" tvg-name="%s",%s\n%s\n' % (x,tv_channel[x]["name"],tv_channel[x]["name"],tv_channel[x]["url"])
    open(pathlib.Path("./config/xteve.m3u"),"w+").write(code)
    logging.info("xteve直播源m3u列表生成.")

def init():
    update_xteve()
    update_xmltv()
    update_channel()
    plex_tuner_path = plex_tuner["bin"]
    config_path = pathlib.Path("./config/config.json")
    del plex_tuner["bin"]
    open(config_path,"w+").write(json.dumps(plex_tuner,indent=2,ensure_ascii=False))
    subprocess.Popen([plex_tuner_path,"-c",config_path.absolute()],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logging.info("Plex-Tuner进程启动.")

@app.errorhandler(404)
def page_not_found(error):
    return '404 not found.'

@app.route('/plex/tv.xml', methods=['GET'])
def xmltv():
    #直播指南
    return send_from_directory('config','tv.xml')

@app.route('/plex/channel', methods=['GET'])
def channel():
    #plex-tuner 直播源
    return send_from_directory('config','channel.json')

@app.route('/xteve.m3u', methods=['GET'])
def m3u():
    #xTeVe 电视源
    return send_from_directory('config','xteve.m3u')

@app.route('/assets/<site>', methods=['GET'])
def assets(site):
    if site in ["bilibili","douyu","huya"]:
        return send_from_directory('assets',site+'.png')
    else:
        return

if __name__ == '__main__':
    init()
    app.run(host='0.0.0.0', port=listen_port, threaded=True, debug=False)