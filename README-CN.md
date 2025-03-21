# MeowAI

![GitHub release (release name instead of tag name)](https://img.shields.io/github/v/release/charlie-captain/MeowAI?include_prereleases)
![GitHub last commit](https://img.shields.io/github/last-commit/charlie-captain/MeowAI)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/charlie-captain/MeowAI)
![Docker Stars](https://img.shields.io/docker/stars/charliecaptain/meowai-image)
![GitHub Repo stars](https://img.shields.io/github/stars/charlie-captain/MeowAI)
![GitHub](https://img.shields.io/github/license/charlie-captain/MeowAI)

使用Yolov5离线检测图片并在Synology Photos上对图片添加标签，支持识别80种场景

## 原理

通过Synology API获取图片缩略图，使用离线yolov5模型识别并对图片添加标签，支持图片和视频

## 使用方法

### Shell (推荐)

1. git clone repository
2. install requirements.txt
    ```
   pip3 install -r requirements.txt
   pip3 install -r yolov5/requirements.txt
   pip3 install torch torchvision
   ```
3. run py
   ```
    user="xxx" \
    pwd="xxx" \
    mode="xxx" \
    exclude_class="[\"cat\"]" \
    ip="192.168.5.1:5000" \
    python3 main.py
    ```

### Docker 

Docker将比上面的 shell 命令运行更久，因为它会永远监控新照片，并且可以在开机时运行启动Docker

1. 拉取镜像
    ```
    //arm64 [600MB]
    docker pull charliecaptain/meowai-image:latest-arm-linux

    //x86-64 [2G]
    docker pull charliecaptain/meowai-image:latest
    ```

2. 运行Docker容器

   ```shell
    docker run -it
            --name meowai \
            -e user="xxx" \
            -e pwd="xxx" \
            -e mode="person" \
            -e exclude_class="[\"cat\",\"dog\"]" \
            -e model='yolov5s6' \
            --network host \
            meowai_image
    ```

### Synology DSM

运行在Synology上会占用大量CPU，请谨慎使用

1. 下载镜像, 一般选latest(x86-64)
   ![picture 1](images/1679625127031.png)

2. 启动容器
   ![picture 2](images/1679625615970.png)

   ![picture 3](images/1679625687135.png)


### 参数说明

| 参数          | 说明                                                  | 例子               | 必选                            |
| ------------- | ----------------------------------------------------- | ------------------ |-------------------------------|
| user          | 登录用户名                                            | -                  | true                          |
| pwd           | 登录密码                                              | -                  | true                          |
| ip            | Nas的地址:端口                                        | 0.0.0.0:5000       | false(default 127.0.0.1:5000) |
| mode          | 个人文件夹还是共享文件夹                              | "person" or"share" | false(default person)         |
| exclude_class | 排除识别的场景(80种), 具体看src/detect/detect_dict.py | ['cat','dog']      | false(default [])             |
| model         | 模型数据集                                            | yolov5m6           | false(default yolov5m6)       |
| lang          | 标签语言                                              | zh(中文)/en(英文)  | false(default en)             |

#### 模型选择

Yolov5的预训练的模型都可以选择，程序会自动下载到环境中。

直接运行python文件则可以运行更大的模型，因为GPU参与运算，速度会比Docker容器快很多。

Docker中运行最好是yolov5s6，平均2秒左右识别速度。

## 开发

目前使用的是yolov5m6.pt数据模型，可以更换更大的数据模型，更多详情请看[Yolov5-Github](https://github.com/ultralytics/yolov5).

### 构建Docker镜像

1. 安装Docker
2. 克隆项目
3. 修改代码
4. 构建Docker镜像
    ```shell
    chmod 777 ./build.sh
    ./build.sh
    ```

## Q&A

### 如何清除所有已经识别的标签
```shell
user="xxx" pwd="xxx" mode="xxx" exclude_class="[\"dog\"]" python3 src/util/util.py
```

## Thanks

https://github.com/zeichensatz/SynologyPhotosAPI

## License

```
MIT License

Copyright (c) 2023 Charlie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```