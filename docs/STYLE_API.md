# Style API Documentation

## Overview

The Style API provides endpoints for analyzing, comparing, adapting, and checking text styles. It helps users understand the stylistic characteristics of their writing and adapt it to match specific target styles.

## Endpoints

### 1. Analyze Style

**Endpoint:** `POST /api/style/analyze`

Analyzes the style of a text sample and returns a style profile with metrics for complexity, formality, tone, and readability.

#### Request

```json
{
  "text": "Text to analyze",
  "tenant_id": "optional-tenant-id"
}
```

#### Response

```json
{
  "complexity": 0.75,
  "formality": 0.82,
  "tone": 0.65,
  "readability": 0.90
}
```

### 2. Compare Styles

**Endpoint:** `POST /api/style/compare`

Compares the styles of two text samples and returns similarity metrics.

#### Request

```json
{
  "text1": "First text sample",
  "text2": "Second text sample"
}
```

#### Response

```json
{
  "overall": 0.78,
  "vector_similarity": 0.82,
  "characteristics_similarity": 0.75,
  "profile1": {
    "complexity": 0.75,
    "formality": 0.82,
    "tone": 0.65,
    "readability": 0.90
  },
  "profile2": {
    "complexity": 0.68,
    "formality": 0.75,
    "tone": 0.70,
    "readability": 0.85
  }
}
```

### 3. Adapt Style

**Endpoint:** `POST /api/style/adapt`

Adapts text to match a target style.

#### Request

```json
{
  "text": "Text to adapt",
  "target_style": {
    "complexity": 0.8,
    "formality": 0.9,
    "tone": 0.7,
    "readability": 0.6
  },
  "strength": 0.7
}
```

#### Response

```json
{
  "original_text": "Text to adapt",
  "adapted_text": "Adapted version of the text",
  "original_profile": {
    "complexity": 0.5,
    "formality": 0.6,
    "tone": 0.5,
    "readability": 0.8
  },
  "adapted_profile": {
    "complexity": 0.7,
    "formality": 0.8,
    "tone": 0.6,
    "readability": 0.7
  },
  "similarity": 0.85
}
```

### 4. Check Style

**Endpoint:** `POST /api/style/check`

Checks if a text matches a target style and provides improvement suggestions.

#### Request

```json
{
  "text": "Text to check",
  "target_style": {
    "complexity": 0.8,
    "formality": 0.9,
    "tone": 0.7,
    "readability": 0.6
  }
}
```

Or using a stored profile:

```json
{
  "text": "Text to check",
  "profile_id": "stored-profile-id"
}
```

#### Response

```json
{
  "consistency": 0.75,
  "matches_target": true,
  "current_profile": {
    "complexity": 0.75,
    "formality": 0.82,
    "tone": 0.65,
    "readability": 0.90
  },
  "suggestions": [
    {
      "aspect": "formality",
      "current": 0.82,
      "target": 0.9,
      "suggestion": "Consider using more formal language and avoiding contractions."
    },
    {
      "aspect": "readability",
      "current": 0.9,
      "target": 0.6,
      "suggestion": "Use more complex sentence structures and specialized vocabulary."
    }
  ]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid input (e.g., empty text)
- `404 Not Found`: Resource not found (e.g., profile_id)
- `500 Internal Server Error`: Server-side error

Error responses include a detail message explaining the issue.

## Authentication

All endpoints support multi-tenant deployments through the `X-Tenant-ID` header. If not provided, the endpoints will still work but without tenant-specific customizations.

## Example Usage

See the test script in `tests/test_style_api.py` for examples of how to use these endpoints programmatically.
