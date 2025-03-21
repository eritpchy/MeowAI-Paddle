#!/bin/bash
set -e
echo "import paddle;paddle.disable_signal_handler();from paddleocr import PaddleOCR;PaddleOCR(use_gpu=False,lang='ch')" | python3
echo "import paddle;paddle.disable_signal_handler();from paddleclas import PaddleClas;PaddleClas(use_gpu=False,model_name='PPHGNet_small_ssld', debug=False, show_log=False)" | python3
