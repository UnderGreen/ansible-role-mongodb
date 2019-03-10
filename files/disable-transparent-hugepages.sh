#!/bin/bash

if [ -d /sys/kernel/mm/transparent_hugepage ]; then
    thp_path=/sys/kernel/mm/transparent_hugepage
else
    return 0
fi

echo 'never' > ${thp_path}/enabled
echo 'never' > ${thp_path}/defrag
