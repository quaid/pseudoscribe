#!/bin/bash
set -e

echo "🧪 Running Ollama tests in batches to avoid hanging issues..."

# Function to run a test class and capture results
run_test_class() {
    local test_class=$1
    local class_name=$2
    echo "📋 Testing $class_name..."
    
    if kubectl exec deployment/api -- python -m pytest "$test_class" -v --tb=short; then
        echo "✅ $class_name: PASSED"
        return 0
    else
        echo "❌ $class_name: FAILED"
        return 1
    fi
}

# Initialize counters
total_classes=0
passed_classes=0
failed_classes=0

echo "🚀 Starting batch test execution..."

# Test Ollama Service API
total_classes=$((total_classes + 1))
if run_test_class "tests/api/test_ollama_service_api.py::TestOllamaServiceAPI" "TestOllamaServiceAPI"; then
    passed_classes=$((passed_classes + 1))
else
    failed_classes=$((failed_classes + 1))
fi

# Test Ollama Error Handling
total_classes=$((total_classes + 1))
if run_test_class "tests/api/test_ollama_service_api.py::TestOllamaServiceErrorHandling" "TestOllamaServiceErrorHandling"; then
    passed_classes=$((passed_classes + 1))
else
    failed_classes=$((failed_classes + 1))
fi

# Test Ollama Configuration
total_classes=$((total_classes + 1))
if run_test_class "tests/api/test_ollama_service_api.py::TestOllamaServiceConfiguration" "TestOllamaServiceConfiguration"; then
    passed_classes=$((passed_classes + 1))
else
    failed_classes=$((failed_classes + 1))
fi

# Test Performance API
total_classes=$((total_classes + 1))
if run_test_class "tests/api/test_vsc007_performance_optimization.py::TestPerformanceAPI" "TestPerformanceAPI"; then
    passed_classes=$((passed_classes + 1))
else
    failed_classes=$((failed_classes + 1))
fi

echo ""
echo "📊 BATCH TEST RESULTS:"
echo "Total test classes: $total_classes"
echo "Passed: $passed_classes"
echo "Failed: $failed_classes"
echo "Success rate: $(( passed_classes * 100 / total_classes ))%"

if [ $failed_classes -eq 0 ]; then
    echo "🎉 ALL TEST CLASSES PASSED!"
    exit 0
else
    echo "⚠️  Some test classes failed"
    exit 1
fi
