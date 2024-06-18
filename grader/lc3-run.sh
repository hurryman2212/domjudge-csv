#!/bin/bash
PROBLEM_DIR=$1
temp_file=/tmp/$(uuid)
cat >"$temp_file"
cnt=0
for input_file in "$PROBLEM_DIR"/*.in; do
    compare_file="${input_file%.in}.ans"
    if timeout 5 "$PROBLEM_DIR"/"$(basename "$PROBLEM_DIR")" "$temp_file" --print-output <"$input_file" | diff -EZbwB "$compare_file" - >/dev/null 2>&1; then
        cnt=$((cnt + 1))
    fi
done
rm -f "$temp_file"
echo -n "$cnt"
