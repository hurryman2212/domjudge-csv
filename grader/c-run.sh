#!/bin/bash
PROBLEM_DIR=$1
temp_file=/tmp/$(uuid)
gcc -mabi=sysv -flto -static -Og -o "$temp_file" -xc -
cnt=0
for input_file in "$PROBLEM_DIR"/*.in; do
    compare_file="${input_file%.in}.ans"
    if timeout 5 xargs "$temp_file" <"$input_file" | diff -EZbwB "$compare_file" - >/dev/null 2>&1; then
        cnt=$((cnt + 1))
    fi
done
rm -f "$temp_file"
echo -n "$cnt"
