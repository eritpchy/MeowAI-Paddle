FROM nvidia/cuda:11.7.0-runtime-ubuntu20.04

RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt \
    sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list \
    && apt update && DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip \
    libgl1 libglib2.0-0 ffmpeg
RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/web/simple
RUN python3 -m pip install paddlepaddle-gpu==0.0.0.post117 -f https://www.paddlepaddle.org.cn/whl/linux/gpu/develop.html
ADD cudnn-linux-x86_64-8.4.1.50_cuda11.6-archive.tar.xz /usr/local/
ADD requirements.txt /MeowAI/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /MeowAI/requirements.txt
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cudnn-linux-x86_64-8.4.1.50_cuda11.6-archive/lib
RUN ln -s /usr/local/cuda-11.7/targets/x86_64-linux/lib/libcublas.so.11 /usr/lib/libcublas.so
ADD app.tar /MeowAI
WORKDIR /MeowAI
CMD ["python3", "/MeowAI/main.py"]