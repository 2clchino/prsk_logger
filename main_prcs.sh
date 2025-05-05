#!/usr/bin/env bash
# File: /home/chino/run_retry_pre_launch.sh
# ————————————————
LOGDIR=/home/chino/prsk_logger/logs
mkdir -p "$LOGDIR"

# YYYY-MM-DD 形式のファイル名
LOGFILE="$LOGDIR/$(date +%F).txt"

# conda 環境下でスクリプト実行。ログは追記モードで日付ファイルへ
/home/chino/miniforge3/condabin/mamba run -n prsk_logger --no-capture-output \
    python /home/chino/prsk_logger/main.py \
    >> "$LOGFILE" 2>&1