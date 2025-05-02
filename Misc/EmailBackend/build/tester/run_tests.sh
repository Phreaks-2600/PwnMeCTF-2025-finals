#!/bin/bash
echo "[+] Running vulnerability patch tests against the live app..."

# Wait for app to be ready
curl -s "${API_BASE_URL}/api" || { echo "App not reachable."; exit 1; }

# Run Jest or Curl-based integration tests
npm test > log_output.txt 2> test_output.txt

# Extract the "Test Suites:" summary line
summary_suites_line=$(grep "^Test Suites:" test_output.txt)

# Extract passed and failed suite counts
passed=$(echo "$summary_suites_line" | grep -oP '\d+(?= passed)')
failed=$(echo "$summary_suites_line" | grep -oP '\d+(?= failed)')

echo -e "\n[+] Test Suites Summary:"
echo "✅ Passed: $passed"
echo "❌ Failed: $failed"

# If tests failed, list the failed test file names
if [ "$failed" -gt 0 ]; then
  echo -e "\n[!] Failed Test Files:"
  grep "^FAIL" test_output.txt | awk '{print $2}'
  echo -e "\n❌ Some tests failed. Try again."
else
  echo -e "\n✅ All tests passed! Here's your flag: ${FLAG}"
fi
