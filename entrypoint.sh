#!/bin/bash

source /root/google-cloud-sdk/completion.bash.inc
source /root/google-cloud-sdk/path.bash.inc
source activate v2d_data

# running parent entrypoint as well - tini
exec /usr/bin/tini -- "$@"
