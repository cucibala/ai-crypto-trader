#!/bin/bash

echo "正在配置conda环境..."

# 配置conda使用清华源
echo "配置conda清华源..."
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --set show_channel_urls yes

# 创建新的conda环境
echo "创建conda环境..."
conda env create -f environment.yml

# 激活环境
echo "激活环境..."
conda activate ai-crypto-trader

echo "环境配置完成！"
echo "请使用 'conda activate ai-crypto-trader' 来激活环境" 