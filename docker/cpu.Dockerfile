FROM python:3.8.20-slim

RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt \
    sed -i 's@//.*.debian.org@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list.d/debian.sources \
    && apt update && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg libmagic1 libgomp1 git
RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/web/simple
# 2.4.2是最后一个支持avx版本的paddle
RUN cd /tmp && \
    python3 -m pip download paddlepaddle==2.4.2 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/noavx/stable.html --no-index --no-deps && \
    pip install paddlepaddle-2.4.2-cp38-cp38-linux_x86_64.whl && \
    rm -fv paddlepaddle-2.4.2-cp38-cp38-linux_x86_64.whl
ADD requirements.txt /MeowAI/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /MeowAI/requirements.txt
ADD app.tar /MeowAI
WORKDIR /MeowAI
CMD ["python3", "/MeowAI/main.py"]