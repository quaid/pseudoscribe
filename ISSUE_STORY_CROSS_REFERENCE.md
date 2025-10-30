# GitHub Issue ↔ User Story Cross-Reference

**Date**: October 25, 2025  
**Purpose**: Complete mapping between GitHub issues and user stories

---

## 📊 Summary Statistics

- **Total User Stories in Backlog**: 43
- **Total Open GitHub Issues**: 35
- **Total Closed GitHub Issues**: 13
- **Issues Aligned**: TBD
- **Missing Issues**: TBD
- **Orphaned Issues**: TBD

---

## ✅ Verified Alignments

### Epic 3: AI Integration (9 stories)

| Story ID | Story Name | GitHub Issue | Status | Notes |
|----------|------------|--------------|--------|-------|
| AI-001 | Ollama Service Integration | #16 | ✅ Closed | Completed ~1 month ago |
| AI-002 | Model Management | #17 | ✅ Reopened | PR #85 just created |
| AI-003 | Inference Pipeline | #18 | ✅ Closed | Completed ~1 month ago |
| AI-004 | Vector Generation | #19 | ✅ Closed | Completed ~1 month ago |
| AI-005 | Similarity Search | #20 | ✅ Closed | Completed ~1 month ago |
| AI-006 | Context Ranking | #57 | 🔄 Open | Ready to start |
| AI-007 | Style Profiling | #58 | 🔄 Open | Depends on AI-001 |
| AI-008 | Style Checking | #59 | 🔄 Open | Depends on AI-007 |
| AI-009 | Style Adaptation | #61 | 🔄 Open | Depends on AI-008 |
| AI-010a | Real Embedding Generation | #62 | 🔄 Open | Split from AI-010 (3 pts) |
| AI-010b | Embedding Cache & Multi-Model | #86 | 🔄 Open | Split from AI-010 (2 pts) |

**✅ RESOLVED**: Duplicate issues #21-24 closed, using #57-59, #61  
**✅ ALIGNED**: Issues #57-59, #61 updated to match backlog (source of truth)  
**📋 NEW**: AI-010 split into AI-010a (3 pts) + AI-010b (2 pts) for 3-point max compliance

### Epic 5: VSCode Extension (7 stories)

| Story ID | Story Name | GitHub Issue | Status | Notes |
|----------|------------|--------------|--------|-------|
| VSC-001 | Command Integration | #33 | 🔄 Open | Needs work |
| VSC-002 | Custom Views | #34 | 🔄 Open | Needs work |
| VSC-003 | Input Handling | #35 | 🔄 Open | Needs work |
| VSC-004 | WebSocket Core | #36 | ✅ Closed | Completed ~1 month ago |
| VSC-005 | Live Suggestions | #37 | ✅ Closed | Completed ~1 month ago |
| VSC-006 | Collaboration | #38 | ✅ Closed | Completed ~26 days ago |
| VSC-007 | Performance Optimization | #39 | ✅ Closed | Completed ~26 days ago |

**Status**: 4 stories completed, 3 remaining

### Epic 1: Infrastructure Foundation (9 stories)

| Story ID | Story Name | GitHub Issue | Status | Notes |
|----------|------------|--------------|--------|-------|
| IF-001 | Tenant Schema Setup | #1 | ✅ Closed | Completed ~6 months ago |
| IF-002 | Tenant Configuration | #2 | 🔄 Open | Needs work |
| IF-003 | Tenant Data Isolation | #3 | 🔄 Open | Needs work |
| IF-004 | Role Management API | #4 | 🔄 Open | Needs work |
| IF-005 | Permission Assignment | #5 | 🔄 Open | Needs work |
| IF-006 | Role Hierarchy | #6 | 🔄 Open | Needs work |
| IF-007 | Vector Storage Setup | #7 | 🔄 Open | Needs work |
| IF-008 | Data Partitioning | #8 | 🔄 Open | Needs work |
| IF-009 | Backup & Recovery | #9 | 🔄 Open | Needs work |

**Status**: 1 story completed, 8 remaining

### Epic 2: Content Management (6 stories)

| Story ID | Story Name | GitHub Issue | Status | Notes |
|----------|------------|--------------|--------|-------|
| CM-001 | Version History Core | #10 | 🔄 Open | Needs work |
| CM-002 | Version Comparison | #11 | 🔄 Open | Needs work |
| CM-003 | Version Restoration | #12 | 🔄 Open | Needs work |
| CM-004 | Format Conversion | #13 | 🔄 Open | Needs work |
| CM-005 | Content Validation | #14 | 🔄 Open | Needs work |
| CM-006 | Content Analysis | #15 | 🔄 Open | Needs work |

**Status**: 0 stories completed, 6 remaining

### Epic 4: Knowledge Management (8 stories)

| Story ID | Story Name | GitHub Issue | Status | Notes |
|----------|------------|--------------|--------|-------|
| KM-001 | Vault Sync Core | #25 | ✅ Closed | Completed ~6 months ago |
| KM-002 | Markdown Processing | #26 | ✅ Closed | Completed ~6 months ago |
| KM-003 | Metadata Management | #27 | 🔄 Open | Needs work |
| KM-004 | Conflict Resolution | #28 | 🔄 Open | Needs work |
| KM-005 | Graph Core | #29 | 🔄 Open | Needs work |
| KM-006 | Graph Visualization | #30 | 🔄 Open | Needs work |
| KM-007 | Graph Search | #31 | 🔄 Open | Needs work |
| KM-008 | Graph Analytics | #32 | 🔄 Open | Needs work |

**Status**: 2 stories completed, 6 remaining

### Epic 6: Enterprise Features (3 stories)

| Story ID | Story Name | GitHub Issue | Status | Notes |
|----------|------------|--------------|--------|-------|
| ENT-001 | Usage Tracking | #40 | 🔄 Open | Needs work |
| ENT-002 | Performance Monitoring | #41 | 🔄 Open | Needs work |
| ENT-003 | Analytics Dashboard | #42 | 🔄 Open | Needs work |

**Status**: 0 stories completed, 3 remaining

---

## 🚨 Issues Requiring Action

### 1. Duplicate Issue IDs (CRITICAL)

**Problem**: AI-006 through AI-009 have duplicate GitHub issues

| Story | Old Issue (6 months) | New Issue (1 month) | Recommended Action |
|-------|---------------------|---------------------|-------------------|
| AI-006 Context Ranking | #21 | #57 | Close #21, keep #57 |
| AI-007 Style Profiling | #22 | #58 | Close #22, keep #58 |
| AI-008 Style Checking | #23 | #59 | Close #23, keep #59 |
| AI-009 Style Adaptation | #24 | #61 | Close #24, keep #61 |

**Rationale**: Newer issues (1 month old) are more recent and likely more accurate. Old issues (6 months) should be closed as duplicates.

### 2. Mystery Issue

| Issue | Title | Problem |
|-------|-------|---------|
| #62 | [AI-010] Implement Product... | No AI-010 story exists in backlog! |

**Action**: Check if this is a typo or new story. If new, add to backlog. If typo, correct issue number.

### 3. Closed Issue #60

| Issue | Title | Problem |
|-------|-------|---------|
| #60 | [DB-001] Enhance VectorStore | No DB-001 story in backlog |

**Action**: Verify if this was a one-off task or should be added to backlog.

---

## 📋 Recommended Actions

### Immediate (High Priority)

1. **Close Duplicate Issues**
   ```bash
   gh issue close 21 --comment "Duplicate of #57 - closing older issue"
   gh issue close 22 --comment "Duplicate of #58 - closing older issue"
   gh issue close 23 --comment "Duplicate of #59 - closing older issue"
   gh issue close 24 --comment "Duplicate of #61 - closing older issue"
   ```

2. **Investigate AI-010**
   ```bash
   gh issue view 62
   # Determine if this should exist or be renumbered
   ```

3. **Verify DB-001**
   ```bash
   gh issue view 60
   # Check if this should be in backlog
   ```

### Short Term (This Sprint)

4. **Update Issue Labels**
   - Ensure all issues have proper epic labels
   - Add status labels (in-progress, blocked, etc.)
   - Add priority labels

5. **Link PRs to Issues**
   - Verify all closed issues have corresponding PRs
   - Ensure PR #85 properly closes #17

6. **Create Missing Issues**
   - None identified yet (all backlog stories have issues)

---

## 📊 Progress by Epic

### Epic 1: Infrastructure Foundation
- **Progress**: 1/9 (11%)
- **Completed**: IF-001
- **In Progress**: None identified
- **Remaining**: IF-002 through IF-009

### Epic 2: Content Management
- **Progress**: 0/6 (0%)
- **Completed**: None
- **In Progress**: None identified
- **Remaining**: CM-001 through CM-006

### Epic 3: AI Integration
- **Progress**: 6/9 (67%)
- **Completed**: AI-001 through AI-005, AI-002 (in PR)
- **In Progress**: AI-002 (PR #85)
- **Remaining**: AI-006 through AI-009

### Epic 4: Knowledge Management
- **Progress**: 2/8 (25%)
- **Completed**: KM-001, KM-002
- **In Progress**: None identified
- **Remaining**: KM-003 through KM-008

### Epic 5: VSCode Extension
- **Progress**: 4/7 (57%)
- **Completed**: VSC-004 through VSC-007
- **In Progress**: None identified
- **Remaining**: VSC-001 through VSC-003

### Epic 6: Enterprise Features
- **Progress**: 0/3 (0%)
- **Completed**: None
- **In Progress**: None identified
- **Remaining**: ENT-001 through ENT-003

---

## 🎯 Overall Project Status

- **Total Stories**: 43
- **Completed**: 13 (30%)
- **In Progress**: 1 (2%)
- **Remaining**: 29 (68%)

### Velocity Insights
- **Recent completions**: VSC-004 through VSC-007, AI-001 through AI-005
- **Current sprint**: AI-002 (PR #85)
- **Suggested next**: AI-006 through AI-009 (complete AI Integration epic)

---

## ✅ Action Plan

### Phase 1: Cleanup (Today)
- [ ] Close duplicate issues #21-24
- [ ] Investigate issue #62 (AI-010)
- [ ] Verify issue #60 (DB-001)
- [ ] Update issue labels

### Phase 2: Alignment (This Week)
- [ ] Ensure all open issues have clear acceptance criteria
- [ ] Link all closed issues to their PRs
- [ ] Update backlog with any new stories
- [ ] Archive obsolete issues

### Phase 3: Planning (Next Sprint)
- [ ] Prioritize remaining AI Integration stories
- [ ] Plan VSCode Extension completion
- [ ] Assess Infrastructure Foundation priorities

---

**Status**: 🔄 **CLEANUP IN PROGRESS**  
**Next**: Execute Phase 1 actions
