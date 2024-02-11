# RelinkMateriaGenerator-WEBUI

## 简介

碧蓝幻想：Relink（Granblue Fantasy: Relink）的因子生成器。

## 项目截图

![](/screenshot/1.png)

## 环境要求

- python (version 3.11.x)

## 安装使用

1. clone 本项目

   ```bash
    git clone https://github.com/X-Zero-L/RelinkMateriaGenerator-WEBUI.git"
    ```

2. 将[Nylib](https://github.com/nyaoouo/NyLib)项目下的nylib文件夹复制到本项目根目录下。

3. 安装依赖

   ```bash
    pip install -r requirements.txt
    ```
    
4. 运行

   ```bash
    python main.py
   ```

5. 生成因子
- 打开游戏并载入你的存档，浏览器访问 `http://127.0.0.1:8848/`进行因子生成。

## 致谢
核心代码来自于 @nyaoouo 的 [gist代码片段](https://gist.github.com/nyaoouo/c32b8c93e4505eb393b75df2e0ecd23b)。

## 注意

- 本项目仅供学习交流使用，不得用于商业用途。
- 本项目不提供任何形式的技术支持，使用本项目所造成的一切后果由使用者自行承担。
- 若出现dll not found的情况，请把`C:\users\你的用户名\AppData\Local\Programs\Python\Python311\Lib\site-packages\pywin32_system32\`目录下的两个dll复制到system32目录下。