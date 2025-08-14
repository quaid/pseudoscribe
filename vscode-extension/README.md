# PseudoScribe Writer Assistant - VSCode Extension

AI-powered writing assistant that bridges ideation and content creation within VSCode.

## Features

### Command Integration (VSC-001) ✅
- **Analyze Writing Style** (`Ctrl+Shift+A` / `Cmd+Shift+A`)
  - Analyzes selected text or entire document for writing style patterns
  - Provides detailed style metrics and insights

- **Adapt Content Style** (`Ctrl+Shift+T` / `Cmd+Shift+T`)
  - Adapts selected content to match target writing style
  - Preserves meaning while transforming style characteristics

- **Connect to Service**
  - Tests and establishes connection to PseudoScribe backend service
  - Configurable service URL in settings

- **Show Style Profile**
  - Displays current user's writing style profile
  - Shows learned patterns and preferences

## Installation

### Prerequisites
- VSCode 1.74.0 or higher
- PseudoScribe backend service running (default: http://localhost:8000)

### Development Setup
```bash
cd vscode-extension
npm install
npm run compile
```

### Testing
```bash
npm test
```

## Configuration

Access settings via `File > Preferences > Settings` and search for "PseudoScribe":

- **Service URL**: Backend service endpoint (default: `http://localhost:8000`)
- **Auto Analyze**: Automatically analyze writing style as you type
- **Show Inline Hints**: Display inline style hints and suggestions

## Usage

1. **Connect to Service**: Use Command Palette (`Ctrl+Shift+P`) → "PseudoScribe: Connect to Service"
2. **Analyze Text**: Select text → Right-click → "Analyze Writing Style" or use `Ctrl+Shift+A`
3. **Adapt Style**: Select text → Right-click → "Adapt Content Style" or use `Ctrl+Shift+T`

## Architecture

### Components
- **CommandManager**: Handles command registration and execution
- **ServiceClient**: Communicates with PseudoScribe backend API
- **StatusBarManager**: Provides user feedback via status bar
- **NotificationManager**: Shows notifications and progress indicators

### BDD Test Coverage
- Command registration and availability
- Command execution with proper feedback
- Error handling and user notifications
- Service integration and communication

## Development Standards

Following Semantic Seed Venture Studio's XP-oriented development practices:
- **TDD Workflow**: Red → Green → Refactor
- **BDD Scenarios**: All features have Gherkin scenarios
- **TypeScript**: Strict typing with camelCase functions, PascalCase classes
- **Testing**: Unit, Integration, and UX tests

## API Integration

Connects to PseudoScribe backend endpoints:
- `GET /health` - Service health check
- `POST /api/style/analyze` - Style analysis
- `POST /api/style/adapt` - Content adaptation
- `GET /api/style/profile` - User style profile

## Contributing

1. Create feature branch: `feature/VSC-{id}`
2. Write BDD scenarios and failing tests
3. Implement minimum viable solution
4. Ensure all tests pass
5. Create PR with documentation updates

## License

Part of the PseudoScribe project - AI-powered writing assistance platform.
