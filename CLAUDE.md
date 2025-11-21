# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based desktop application for analyzing source code using Large Language Models (LLMs) through Ollama. The application generates call graphs, performs code analysis, synthesizes results, and provides an interactive dashboard with analytics. It's built using Flet for the GUI and follows an MVC architecture pattern.

## Common Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama service (required)
ollama serve
# Pull a model (e.g., codellama)
ollama pull codellama

# Run the application
python main.py
```

### Development Setup
```bash
# Create necessary directories (done automatically on first run)
mkdir -p storage/data storage/temp storage/export log explicabilidade inspecao modules/auth middleware
```

### Database Management
The application uses SQLite databases located in `storage/`:
- `storage/analise.db` - Analysis results
- `storage/analytics.db` - System metrics
- `storage/users.json` - User authentication data

## Architecture Overview

### MVC Pattern
Each module follows strict MVC separation:
- **Model**: Handles data and business logic (e.g., `AnaliseModel`, `SinteseModel`)
- **View**: Manages UI components using Flet (e.g., `AnaliseViewManager`, component cards)
- **Controller**: Coordinates between Model and View (e.g., `AnaliseController`)

### Module Structure
```
modules/
├── analise/      # Core code analysis module with thread support
├── sintese/      # Graph synthesis module
├── grafo/        # Graph visualization and network analysis
├── dashboard/    # Analytics dashboard with RAG capabilities
└── auth/         # User authentication system
```

### Key Services
- **OllamaService**: Handles communication with Ollama API
- **NotificationService**: Centralized notification system
- **DatabaseService**: SQLite database operations
- **BaseController**: Unified operation lifecycle management and UI coordination
- **UnifiedTimingService**: Centralized timing and metrics collection

### Storage Architecture
All persistent data is stored in the `storage/` directory:
- Analysis results are saved as JSON in `storage/data/`
- Temporary files during processing go to `storage/temp/`
- User exports are stored in `storage/export/`

## Development Guidelines

### Working with Modules
When modifying a module:
1. Maintain MVC separation - don't mix business logic in view components
2. Use the notification service for user feedback
3. Store analysis results in the appropriate storage location
4. Follow the existing pattern for controller initialization

### Adding New Features
1. Create a new module following the MVC pattern if needed
2. Register the module in `main.py`
3. Add the tab to the main interface
4. Ensure proper cleanup in `_cleanup_modules()`

### Threading Considerations
- Background operations are managed through BaseController lifecycle
- Always call `finish_operation()` in cleanup methods
- Use thread-safe operations when accessing shared data
- Callback system handles thread-to-UI communication automatically

### UI Development
- Views are built using Flet components
- Each module has reusable components in `view/components/`
- Cards are the primary UI pattern (e.g., `ConfigCard`, `ExecutionCard`)
- Maintain consistent styling and spacing

### Error Handling
- All modules use the centralized logging system
- Log errors with appropriate context
- Use notifications for user-facing errors
- Implement graceful degradation when Ollama is unavailable

## Important Implementation Details

### Authentication Flow
1. User authentication is required before accessing modules
2. Session data is stored in `auth_controller`
3. Modules receive auth controller reference after login

### Module Integration
- Dashboard controller integrates with graph controller for RAG analytics
- Analysis results flow: Analysis → Storage → Graph → Dashboard
- Controllers communicate through shared models and services

### Background Processing
- Long-running operations use BaseController with async execution
- Progress updates are sent through callback system
- Results are automatically saved to storage with detailed timing metrics
- UnifiedTimingService tracks effective analysis time excluding pauses

### Ollama Integration
- Models are fetched dynamically from Ollama service
- Timeout is set to 1200 seconds for long analyses
- Fallback to CLI if API is unavailable

## Testing
Currently, the project does not have formal unit tests. When adding tests:
- Place them in a `tests/` directory
- Test controllers and models separately from views
- Mock OllamaService for testing without LLM dependency

## Documentation Standards (Atualizado em 2025-11-19)

### Docstring Requirements
All Python modules and classes must follow these documentation standards:

#### Module Documentation
- Every module must have a comprehensive docstring at the top
- Include purpose, main features, and usage examples
- List key classes and their responsibilities
- Document any dependencies or requirements

#### Class Documentation
- Every class must have a detailed docstring
- Include purpose, attributes, and usage examples
- Document initialization parameters
- Note any important behaviors or side effects

#### Method Documentation
- Every public method must have a docstring
- Include purpose, parameters, return values, and examples
- Document exceptions that may be raised
- Note any important implementation details

#### Documentation Format
```python
"""
Module Purpose - Brief one-line summary

Detailed description of the module's purpose, functionality,
and key features. Include usage examples when appropriate.

Main Features:
- Feature 1 description
- Feature 2 description
- Feature 3 description

Dependencies:
- List external dependencies
- Note version requirements if applicable

Example:
    >>> from module import Class
    >>> instance = Class(param1, param2)
    >>> result = instance.method()
"""

class ExampleClass:
    """
    Brief description of the class purpose.

    Detailed description including responsibilities, usage patterns,
    and any important implementation notes.

    Attributes:
        attr1 (type): Description of attribute 1
        attr2 (type): Description of attribute 2

    Example:
        >>> instance = ExampleClass(param1="value")
        >>> result = instance.process()
    """

    def method_name(self, param1: type, param2: type) -> return_type:
        """
        Brief description of the method purpose.

        Args:
            param1 (type): Description of parameter 1
            param2 (type): Description of parameter 2

        Returns:
            return_type: Description of return value

        Raises:
            ExceptionType: Description of when this exception is raised

        Note:
            Any important implementation details or side effects
        """
```

### Recent Documentation Updates (2025-11-19)
- ✅ Updated `OllamaService` with comprehensive class and method docstrings
- ✅ Enhanced `DatabaseService` documentation with detailed examples
- ✅ Added proper module documentation for `main.py`
- ✅ Improved `ViewManager` classes with complete documentation
- ✅ Standardized docstring format across services
- ✅ Added type hints and return documentation to key methods