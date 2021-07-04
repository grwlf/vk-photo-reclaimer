export CWD=`pwd`
export PYTHONPATH="$CWD/src:$PYTHONPATH"
export MYPYPATH="$PYTHONPATH"
alias ipython="sh $CWD/ipython.sh"
# 1980 workaround https://github.com/NixOS/nixpkgs/issues/270#issuecomment-467583872
export SOURCE_DATE_EPOCH=315532800

runjupyter() {
  jupyter-notebook --ip 0.0.0.0 --port 8888 \
    --NotebookApp.token='' --NotebookApp.password='' "$@" --no-browser
}
alias jupyter=runjupyter
