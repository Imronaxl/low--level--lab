#!/bin/bash
# Запуск всех тестов и проверка качества кода
set -e

cd "$(dirname "$0")"

echo "=== Ruff Lint ==="
ruff check src/ tools/

echo ""
echo "=== Unit Tests ==="
python -m pytest tests/unit/ -v

echo ""
echo "=== Compile and Run Programs ==="
for prog in hello test_simple cat; do
    echo "--- $prog ---"
    python tools/compile.py "programs/$prog.alg" -o "/tmp/${prog}_test.bin" 2>/dev/null
    if [ "$prog" = "cat" ]; then
        echo -n "Test" > /tmp/_test_in.txt
        python tools/run.py "/tmp/${prog}_test.bin" /tmp/_test_in.txt 2>&1 | grep "Output:" -A2
    else
        python tools/run.py "/tmp/${prog}_test.bin" 2>&1 | grep "Output:" -A2
    fi
done

echo ""
echo "=== All tests passed! ==="
