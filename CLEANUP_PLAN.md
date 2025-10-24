# 🧹 **CODEBASE CLEANUP PLAN**

## 📋 **Files to Rename/Remove**

### **Test Files (Rename to descriptive names):**
- `tests/api/test_vsc004_style_analysis.py` → `tests/api/test_style_analysis.py`
- `tests/api/test_vsc005_live_suggestions.py` → `tests/api/test_live_suggestions.py`
- `tests/api/test_vsc006_collaboration.py` → `tests/api/test_collaboration.py`
- `tests/api/test_vsc007_performance_optimization.py` → `tests/api/test_performance.py`

### **Feature Files (Rename to descriptive names):**
- `features/VSC-004-advanced-extension-features.feature` → `features/style-analysis.feature`
- `features/VSC-005-live-suggestions.feature` → `features/live-suggestions.feature`
- `features/VSC-006-collaboration.feature` → `features/collaboration.feature`
- `features/VSC-007-performance-optimization.feature` → `features/performance.feature`

### **Documentation Files (Remove PR docs, keep technical specs):**
- `PR_AI-001.md` → **REMOVE** (temporary PR documentation)
- `PR_VSC-004.md` → **REMOVE** (temporary PR documentation)
- `PR_VSC-005.md` → **REMOVE** (temporary PR documentation)
- `PR_VSC-006.md` → **REMOVE** (temporary PR documentation)
- `PR_VSC-007.md` → **REMOVE** (temporary PR documentation)
- `docs/VSC-004-technical-specification.md` → `docs/style-analysis-specification.md`

### **Test Endpoint Files (Remove - duplicates):**
- `test_vsc004_endpoints.py` → **REMOVE** (duplicate testing)
- `test_vsc005_endpoints.py` → **REMOVE** (duplicate testing)
- `test_vsc006_endpoints.py` → **REMOVE** (duplicate testing)

### **Scripts to Update References:**
- `scripts/test-full-suite.sh` - Update test file paths
- Any other scripts referencing the old names

## 🎯 **Execution Order:**
1. Rename test files and update imports
2. Rename feature files
3. Rename documentation files
4. Remove temporary PR files
5. Remove duplicate test files
6. Update script references
7. Test everything works
8. Commit cleanup changes
