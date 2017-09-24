
# zhihu-crawler
一个简单的知乎爬虫，通过 API 获取信息。API 则是通过手动分析知乎网站网络交互过程获取。


## 文件结构及用途


| 文件名 | 用途
| :--- | :---
| cookies/ | 存放 cookie 文件，用于登录知乎，cookie 文件可有多个，以登录多个帐号，轮换使用
| cpfiles/ | 保存备份的 id_dict.txt 和 id_queue.txt 的文件夹
| data/ | 存放获取到的数据文件
| out/ | 存放保存有程序输出信息的文件
| state/ | 存放保存有程序运行状态信息的文件
| state/error_ids.txt | 保存爬取时出现错误的用户 id
| state/id_dict.txt | 保存当前已爬取过的用户 id 列表
| state/id_queue.txt | 保存待爬取的用户 id 队列
| state/x.txt | 文件中有一个数字，标志着该使用哪一个 json 文件登录
| cp_files.py | 每爬完 100 个用户，便将 id_dict.txt 和 id_queue.txt 备份一下
| get_url.py | 给定 url ，使用代理，下载内容并返回
| proxy_pool.py | 维护一个代理池，提供代理
| run_zhihu_crawler.bat| 批处理文件，调用爬虫主程序，Windows 用。
| run_zhihu_crawler.sh| 批处理文件，调用爬虫主程序，Linux 用。
| zh_api.py| 给定用户 id ，获取用户的各种信息
| zh_crawler.py| 爬虫主程序，爬 100 个用户后退出
| zhihu_client.py| 可用于登录帐号并生成保存有 cookie 的 json 文件

## 运行方法
以下所用 python 均为 python 2，假定在 Windows 环境下。

- 若未安装 requests 库，需运行以下命令安装

```bash
    pip install requests
```
     
- 第一次使用，需在 `cmd` 中输入以下命令，以生成 cookie 的 json 文件。若要登录多个账户，可再运行此命令生成其他 cookie 。  

```bash
    python zhihu_client.py
```

- 爬取速度
    - 账户数少而爬取数据过快时，帐号可能会被知乎暂时封掉，需要打开网站输入验证码登录才能解封。  
    - 用多个账户轮流登录爬取可以避免被封。目前的默认爬取速度，大概需要10个账户轮流。  
    - 可通过修改 zh_crawler.py 第 184 行开始定义的几个参数修改爬取速度  

- 第一次运行前，需 state/id_queue.txt 中存储有待爬取的队列。
    
以后每次运行时，运行以下两条命令即可

- 在 `cmd` 中输入以下命令  

```bash
    python cp_files.py
```

- 另开一个 `cmd` 输入以下命令  

```bash
    run_zhihu_crawler.bat
```

## 查看数据


- data 文件夹中有一个 `indent_chinese.py`
- 在 data 文件夹中打开 `cmd`
- 运行类似如下的命令
```bash
    python indent_chinese.py data_2017-09-23-23-55-59.txt
```
可在 indent 文件夹下生成一个 `data_2017-09-23-23-55-59_indent_chinese.txt` 文件。  
用 sublime-text 或 notepad++ 打开该文件，可看到该文件的内容。


## 说明
zhihu_client.py 使用 [7sDream](https://github.com/7sDream) 的项目 [zhihu-py3](https://github.com/7sDream/zhihu-py3) 中的代码，原项目以 MIT License 发布。

## 联系方式
邮箱: [maxuewei1995@126.com](mailto:maxuewei1995@126.com)  
Github: [@maxuewei2](https://github.com/maxuewei2)
