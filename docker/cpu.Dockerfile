FROM ubuntu:22.04

RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt \
    sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list \
    && apt update && DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip \
    libgl1 libglib2.0-0 ffmpeg libmagic1
RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/web/simple
RUN python3 -m pip install paddlepaddle==2.6.2 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
ADD requirements.txt /MeowAI/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /MeowAI/requirements.txt
ADD app.tar /MeowAI
WORKDIR /MeowAI
CMD ["python3", "/MeowAI/main.py"]