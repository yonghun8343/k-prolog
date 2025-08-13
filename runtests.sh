#!/bin/bash

DIRS="child"

EXEC="./dist/k-prolog"

for dir in $DIRS; do
    if [ "$dir" = "GCD" ]; then
        PROG="최대공약수.kpl"
    elif [ "$dir" = "child" ]; then
        PROG="child.kpl"
    fi

    echo "Processing directory: $dir with program $PROG"

    for infile in "$dir"/*.inp; do
        base=$(basename "$infile" .inp)
        outfile="$dir/$base.out"

        echo "Testing $dir/$base.inp..."

        output=$($EXEC "$PROG" < "$infile")
        diff_result=$(diff -w <(echo "$output") "$outfile")

        if [ $? -eq 0 ]; then
            echo "PASS: Output matches $base.out"
        else
            echo "FAIL: Differences found for $base"
            echo "$diff_result"
        fi

        echo
    done
done