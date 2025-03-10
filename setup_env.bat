@echo off
echo 正在配置conda环境...

REM 配置conda使用清华源
echo 配置conda清华源...
call conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
call conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
call conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
call conda config --set show_channel_urls yes

REM 创建新的conda环境
echo 创建conda环境...
call conda env create -f environment.yml

REM 激活环境
echo 激活环境...
call conda activate ai-crypto-trader

echo 环境配置完成！
echo 请使用 'conda activate ai-crypto-trader' 来激活环境
pause 