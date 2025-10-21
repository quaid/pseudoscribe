#!/bin/bash
set -e

echo "🚀 Pushing all PR branches to repository..."

# Push AI-001 (Foundation)
echo "📤 Pushing AI-001 Ollama Service Integration..."
git push origin feature/AI-001

# Push VSC-004 (Style Analysis)
echo "📤 Pushing VSC-004 Advanced Style Analysis..."
git push origin feature/VSC-004-style-analysis

# Push VSC-005 (Live Suggestions)
echo "📤 Pushing VSC-005 Live Suggestions..."
git push origin feature/VSC-005-live-suggestions

# Push VSC-006 (Collaboration)
echo "📤 Pushing VSC-006 Collaboration..."
git push origin feature/VSC-006-collaboration

# Push VSC-007 (Performance)
echo "📤 Pushing VSC-007 Performance Optimization..."
git push origin feature/VSC-007-performance

echo ""
echo "✅ All PR branches pushed successfully!"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. Create PRs in your repository interface"
echo "2. Use the PR_*.md files as PR descriptions"
echo "3. Follow recommended submission sequence:"
echo "   - Phase 1: AI-001, VSC-007 (Foundation)"
echo "   - Phase 2: VSC-004, VSC-005 (Core Features)"
echo "   - Phase 3: VSC-006 (Advanced Features)"
echo ""
echo "🏆 ALL USER STORIES READY FOR PRODUCTION!"
