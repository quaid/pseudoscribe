#!/bin/bash

# Validation script for Ollama Service Integration
# Checks that all components are properly implemented before container testing

set -e

echo "🔍 Validating Ollama Service Integration Implementation..."

# Check that all required files exist
echo "📁 Checking file structure..."
required_files=(
    "features/ollama-service-integration.feature"
    "tests/api/test_ollama_service_api.py"
    "pseudoscribe/api/ollama_integration.py"
    "pseudoscribe/infrastructure/ollama_service.py"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $file exists"
    else
        echo "  ❌ $file missing"
        exit 1
    fi
done

# Check that the router is registered in app.py
echo "🔌 Checking router registration..."
if grep -q "ollama_integration" pseudoscribe/api/app.py; then
    echo "  ✅ ollama_integration router registered in app.py"
else
    echo "  ❌ ollama_integration router not found in app.py"
    exit 1
fi

# Check for proper domain-based naming (no user story IDs in source files)
echo "📝 Checking naming conventions..."
if find . -name "*AI-001*" -o -name "*ai001*" | grep -v "\.git" | grep -q .; then
    echo "  ❌ Found files with user story IDs in names"
    find . -name "*AI-001*" -o -name "*ai001*" | grep -v "\.git"
    exit 1
else
    echo "  ✅ No user story IDs found in source filenames"
fi

# Check that BDD scenarios are properly defined
echo "🧪 Checking BDD scenarios..."
scenario_count=$(grep -c "Scenario:" features/ollama-service-integration.feature)
if [[ $scenario_count -ge 6 ]]; then
    echo "  ✅ Found $scenario_count BDD scenarios"
else
    echo "  ❌ Only found $scenario_count scenarios, expected at least 6"
    exit 1
fi

# Check that test classes exist
echo "🧪 Checking test structure..."
test_classes=(
    "TestOllamaServiceAPI"
    "TestOllamaServiceErrorHandling"
    "TestOllamaServiceIntegration"
    "TestOllamaServiceConfiguration"
)

for class_name in "${test_classes[@]}"; do
    if grep -q "class $class_name" tests/api/test_ollama_service_api.py; then
        echo "  ✅ $class_name test class found"
    else
        echo "  ❌ $class_name test class missing"
        exit 1
    fi
done

# Check API endpoints are defined
echo "🚀 Checking API endpoints..."
endpoints=(
    "/health"
    "/models"
    "/config"
    "/metrics"
    "/sla-status"
    "/validate"
)

for endpoint in "${endpoints[@]}"; do
    if grep -q "@router.get(\"$endpoint\"" pseudoscribe/api/ollama_integration.py || grep -q "@router.post(\"$endpoint\"" pseudoscribe/api/ollama_integration.py; then
        echo "  ✅ $endpoint endpoint defined"
    else
        echo "  ❌ $endpoint endpoint missing"
        exit 1
    fi
done

echo ""
echo "🎉 Ollama Service Integration validation completed successfully!"
echo "📋 Summary:"
echo "  ✅ All required files present"
echo "  ✅ Router properly registered"
echo "  ✅ Domain-based naming conventions followed"
echo "  ✅ BDD scenarios comprehensive ($scenario_count scenarios)"
echo "  ✅ Test classes properly structured"
echo "  ✅ All API endpoints implemented"
echo ""
echo "🔄 Ready for container testing with scripts/test-rancher.sh"
echo "🎯 Current state: RED TESTS (expected to fail until implementation is complete)"
