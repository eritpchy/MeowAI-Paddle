FROM ubuntu:20.04

RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt \
    sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list \
    && apt update && DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip \
    libgl1 libglib2.0-0 ffmpeg
RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/web/simple
RUN python3 -m pip download paddlepaddle==2.4.2 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/noavx/stable.html --no-index --no-deps \
    && pip install ./paddlepaddle-2.4.2-cp38-cp38-linux_x86_64.whl \
    && rm -f ./paddlepaddle-2.4.2-cp38-cp38-linux_x86_64.whl
ADD requirements.txt /MeowAI/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /MeowAI/requirements.txt
ADD app.tar /MeowAI
WORKDIR /MeowAI
CMD ["python3", "/MeowAI/main.py"]