## Plex-Live

一个小工具，快速生成xteve配置与plex可解析icon的节目指南，使用plex随处观看电视IPTV与斗鱼、虎牙、Bilibili等自定义网络直播间

工具解决的场景见[博客文章](https://le4f.net/plex-live/)

#### 依赖

- [Plex Tuner](https://github.com/xbugio/plex-tuner)
- [xTeVe](https://github.com/xteve-project/xTeVe)
- [FFmpeg](https://ffmpeg.org/)

由于网络直播间流地址变化频繁，使用xTeVe难以有效跟踪，使用一款Go开发的轻量Plex直播模拟项目Plex Tuner进行HLS流播放，而IPTV单播流（RTSP/HLS）测试该项目暂无法播放，使用更常见的xTeVe接入。

解析直播间地址引用了 [real-url-proxy-server](https://github.com/rain-dl/real-url-proxy-server) 项目

#### 使用

*   编译plex-tuner、安装ffmpeg
*   参考注释定义web.py配置
*   运行后，如果使用xTeVe观看IPTV直播，选择PMS类型，m3u文件地址使用 http://listen_host:listen_port/xteve.m3u
*   Plex节目指南使用 http://listen_host:listen_port/plex/tv.xml
