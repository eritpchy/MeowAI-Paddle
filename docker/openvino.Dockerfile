FROM openvino/ubuntu20_dev:2024.0.0
USER root
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt \
    sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list \
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
RUN pip install paddle2onnx==1.3.1 onnxruntime-openvino==1.16.0
RUN sed -i 's/sess_options=config/sess_options=config, providers=args.onnx_providers/g' /usr/local/lib/python3.8/dist-packages/paddleclas/deploy/utils/predictor.py
USER openvino
ADD download-models.sh /tmp/
RUN bash /tmp/download-models.sh
RUN find /home/openvino/.paddleocr/whl/ -type d | grep infer | xargs -I {} \
        paddle2onnx --model_dir {} \
        --model_filename inference.pdmodel \
        --params_filename inference.pdiparams \
        --save_file {}/model.onnx \
        --opset_version 14 \
        --enable_onnx_checker True;
RUN find /home/openvino/.paddleclas/inference_model/ -type d | grep infer | xargs -I {} \
        paddle2onnx --model_dir {} \
        --model_filename inference.pdmodel \
        --params_filename inference.pdiparams \
        --save_file {}/inference.onnx \
        --opset_version 14 \
        --enable_onnx_checker True;
ADD app.tar /MeowAI
WORKDIR /MeowAI
CMD ["python3", "/MeowAI/main.py"]