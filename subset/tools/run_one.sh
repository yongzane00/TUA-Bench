#!/usr/bin/env bash
# One arm of run_parallel.sh: wait <delay> s, wait until Docker and the model server answer, run the config once.
#
#   bash subset/tools/run_one.sh <model> <config> <delay_sec> <log_file>

model=$1; cfg=$2; delay=$3; log=$4
export PATH="$HOME/.local/bin:$PATH"
cd ~/work/TUA-Bench || exit 1
JOBS=/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }

d=$(ls -d "$JOBS/$model/$cfg"/*/ 2>/dev/null | sort | tail -1)
if [ -n "$d" ] && grep -q '"finished_at": *"' "$d/result.json" 2>/dev/null; then
  say "$cfg already has a finished run ($d); nothing to do"; exit 0
fi
sleep "$delay"
url=$(grep -m1 -oE 'api_base: *[^ ]+' "subset/variants/$model/$cfg.yaml" | awk '{print $2}')
waited=0
until docker info >/dev/null 2>&1 && curl -sf -m 20 "$url/models" >/dev/null; do
  [ $waited = 0 ] && say "WAIT Docker or $url not ready; checking every 60 s"
  waited=1; sleep 60
done
say "START $model/$cfg"
uv run --no-sync harbor run -c "subset/variants/$model/$cfg.yaml" -o "$JOBS/$model/$cfg" --yes 2>&1 | tee -a "$log"
say "END $model/$cfg (exit ${PIPESTATUS[0]})"
