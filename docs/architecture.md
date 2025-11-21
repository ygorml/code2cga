# Code2CGA Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [MVC Architecture Pattern](#mvc-architecture-pattern)
3. [Module Structure](#module-structure)
4. [Service Layer Architecture](#service-layer-architecture)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Storage Architecture](#storage-architecture)
7. [Threading Model](#threading-model)
8. [Component Interactions](#component-interactions)
9. [Security Architecture](#security-architecture)
10. [Performance Architecture](#performance-architecture)

## System Overview

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Flet UI Components]
        Tabs[Main Application Tabs]
    end

    subgraph "Module Layer"
        Auth[Authentication Module]
        Analise[Analysis Module]
        Sintese[Synthesis Module]
        Grafo[Graph Module]
        Dashboard[Dashboard Module]
    end

    subgraph "Service Layer"
        Ollama[Ollama Service]
        DB[Database Service]
        Notif[Notification Service]
        Timing[Unified Timing Service]
    end

    subgraph "Core Layer"
        Base[Base Controller]
        ViewMngr[View Manager]
    end

    subgraph "External Systems"
        OllamaAPI[Ollama API]
        SQLite[(SQLite Databases)]
        FileSystem[File System]
    end

    UI --> Tabs
    Tabs --> Auth
    Tabs --> Analise
    Tabs --> Sintese
    Tabs --> Grafo
    Tabs --> Dashboard

    Auth --> Base
    Analise --> Base
    Sintese --> Base
    Grafo --> Base
    Dashboard --> Base

    Base --> Ollama
    Base --> DB
    Base --> Notif
    Base --> Timing

    Ollama --> OllamaAPI
    DB --> SQLite
    Timing --> FileSystem
```

## MVC Architecture Pattern

```mermaid
graph LR
    subgraph "View Layer"
        ViewComp[View Components]
        Cards[Reusable Cards]
        Managers[View Managers]
    end

    subgraph "Controller Layer"
        Controllers[Controllers]
        BaseCtrl[Base Controller]
        Lifecycle[Operation Lifecycle]
    end

    subgraph "Model Layer"
        Models[Data Models]
        Business[Business Logic]
        Validation[Data Validation]
    end

    ViewComp --> Controllers
    Controllers --> ViewComp
    Controllers --> Models
    Models --> Controllers

    Controllers --> BaseCtrl
    BaseCtrl --> Lifecycle
```

### Module MVC Structure

```mermaid
graph TB
    subgraph "Module: Analysis"
        AView[Analise View Manager]
        AComp[Components]
        ACtrl[Analise Controller]
        AModel[Analise Model]
    end

    subgraph "Module: Synthesis"
        SView[Sintese View Manager]
        SComp[Components]
        SCtrl[Sintese Controller]
        SModel[Sintese Model]
    end

    subgraph "Module: Graph"
        GView[Grafo View Manager]
        GComp[Components]
        GCtrl[Grafo Controller]
        GModel[Grafo Model]
    end

    subgraph "Module: Dashboard"
        DView[Dashboard View Manager]
        DComp[Components]
        DCtrl[Dashboard Controller]
        DModel[Dashboard Model]
    end

    AView --> AComp
    AComp --> ACtrl
    ACtrl --> AModel
    AModel --> ACtrl
    ACtrl --> AView

    SView --> SComp
    SComp --> SCtrl
    SCtrl --> SModel
    SModel --> SCtrl
    SCtrl --> SView

    GView --> GComp
    GComp --> GCtrl
    GCtrl --> GModel
    GModel --> GCtrl
    GCtrl --> GView

    DView --> DComp
    DComp --> DCtrl
    DCtrl --> DModel
    DModel --> DCtrl
    DCtrl --> DView
```

## Module Structure

```mermaid
graph TD
    subgraph "Main Application"
        Main[main.py]
        App[Code2CGA App]
    end

    subgraph "Authentication Module"
        AuthCtrl[Auth Controller]
        AuthView[Login View]
        UserMgmt[User Management]
    end

    subgraph "Analysis Module"
        AnaliseCtrl[Analysis Controller]
        CodeAnalysis[Code Analysis Engine]
        ThreadMngr[Thread Manager]
        ProgressTrack[Progress Tracking]
    end

    subgraph "Synthesis Module"
        SinteseCtrl[Synthesis Controller]
        GraphSynth[Graph Synthesis]
        DataProcess[Data Processing]
    end

    subgraph "Graph Module"
        GrafoCtrl[Graph Controller]
        NetworkAn[Network Analysis]
        Visualization[Graph Visualization]
        CommDetect[Community Detection]
    end

    subgraph "Dashboard Module"
        DashboardCtrl[Dashboard Controller]
        RAG[RAG Analytics]
        Metrics[Metrics Display]
        Storytell[Storytelling]
    end

    Main --> App
    App --> AuthCtrl
    App --> AnaliseCtrl
    App --> SinteseCtrl
    App --> GrafoCtrl
    App --> DashboardCtrl

    AuthCtrl --> AuthView
    AnaliseCtrl --> CodeAnalysis
    SinteseCtrl --> GraphSynth
    GrafoCtrl --> NetworkAn
    DashboardCtrl --> RAG
```

## Service Layer Architecture

```mermaid
graph TB
    subgraph "Core Services"
        BaseCtrl[Base Controller]
        Timing[Unified Timing Service]
        Notif[Notification Service]
    end

    subgraph "External Services"
        OllamaSrv[Ollama Service]
        DBService[Database Service]
        FileService[File Service]
    end

    subgraph "Service Interfaces"
        APIInterface[Ollama API Interface]
        DBInterface[SQLite Interface]
        FileSystem[File System Interface]
    end

    BaseCtrl --> OllamaSrv
    BaseCtrl --> DBService
    BaseCtrl --> Timing
    BaseCtrl --> Notif

    OllamaSrv --> APIInterface
    DBService --> DBInterface
    FileService --> FileSystem

    Timing --> FileService
    Notif --> BaseCtrl
```

## Data Flow Architecture

```mermaid
flowchart TD
    subgraph "Input Phase"
        UserInput[User Input]
        FileUpload[File Upload]
        Config[Configuration]
    end

    subgraph "Processing Phase"
        Validation[Data Validation]
        Analysis[Code Analysis]
        Synthesis[Graph Synthesis]
        Metrics[Metrics Calculation]
    end

    subgraph "Storage Phase"
        TempData[Temporary Storage]
        PermanentData[Permanent Storage]
        Cache[Cache Layer]
    end

    subgraph "Output Phase"
        Visualization[Data Visualization]
        Export[Export Functionality]
        Reports[Report Generation]
    end

    UserInput --> Validation
    FileUpload --> Validation
    Config --> Validation

    Validation --> Analysis
    Analysis --> Synthesis
    Synthesis --> Metrics

    Analysis --> TempData
    Synthesis --> PermanentData
    Metrics --> Cache

    TempData --> Visualization
    PermanentData --> Export
    Cache --> Reports
```

### Analysis Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as UI Components
    participant Controller as Analysis Controller
    participant Model as Analysis Model
    participant Ollama as Ollama Service
    participant DB as Database
    participant Storage as File System

    User->>UI: Select files and configure
    UI->>Controller: Start analysis
    Controller->>Model: Validate input
    Model->>Controller: Validation result

    alt Valid input
        Controller->>Model: Initialize analysis
        Controller->>Ollama: Process code
        Ollama-->>Controller: Analysis results
        Controller->>Model: Store results
        Model->>DB: Save to database
        Model->>Storage: Save to files
        Controller->>UI: Update progress
        UI->>User: Show completion
    else Invalid input
        Controller->>UI: Show error
        UI->>User: Display validation error
    end
```

## Storage Architecture

```mermaid
graph TB
    subgraph "Storage Root"
        StorageRoot[storage/]
    end

    subgraph "Data Storage"
        Data[storage/data/]
        JSONFiles[*.json analysis files]
        Results[Analysis results]
    end

    subgraph "Temporary Storage"
        Temp[storage/temp/]
        ProcessTemp[Processing files]
        CacheTemp[Cache files]
    end

    subgraph "Export Storage"
        Export[storage/export/]
        UserExports[User exports]
        Reports[Generated reports]
    end

    subgraph "Database Storage"
        DBFiles[storage/*.db]
        AnaliseDB[analise.db]
        AnalyticsDB[analytics.db]
        UsersFile[users.json]
    end

    StorageRoot --> Data
    StorageRoot --> Temp
    StorageRoot --> Export
    StorageRoot --> DBFiles

    Data --> JSONFiles
    Data --> Results

    Temp --> ProcessTemp
    Temp --> CacheTemp

    Export --> UserExports
    Export --> Reports

    DBFiles --> AnaliseDB
    DBFiles --> AnalyticsDB
    DBFiles --> UsersFile
```

## Threading Model

```mermaid
graph TB
    subgraph "Main Thread"
        MainUI[Main UI Thread]
        EventLoop[Flet Event Loop]
    end

    subgraph "Background Threads"
        AnalysisThread[Analysis Thread]
        SynthesisThread[Synthesis Thread]
        GraphThread[Graph Processing Thread]
    end

    subgraph "Thread Management"
        BaseController[Base Controller]
        Lifecycle[Operation Lifecycle]
        CallbackSystem[Callback System]
    end

    subgraph "Thread Safety"
        ThreadSafeOps[Thread-Safe Operations]
        Locks[Resource Locks]
        Queues[Message Queues]
    end

    MainUI --> EventLoop
    EventLoop --> BaseController

    BaseController --> AnalysisThread
    BaseController --> SynthesisThread
    BaseController --> GraphThread

    BaseController --> Lifecycle
    Lifecycle --> CallbackSystem

    CallbackSystem --> ThreadSafeOps
    ThreadSafeOps --> Locks
    ThreadSafeOps --> Queues
```

## Component Interactions

```mermaid
graph LR
    subgraph "UI Components"
        TabView[Tab Navigation]
        Cards[Component Cards]
        Dialogs[Dialog Boxes]
    end

    subgraph "State Management"
        AppState[Application State]
        Session[Session Data]
        Preferences[User Preferences]
    end

    subgraph "Event Handling"
        Events[UI Events]
        Handlers[Event Handlers]
        Callbacks[Async Callbacks]
    end

    subgraph "Communication"
        Notifications[User Notifications]
        Logging[System Logging]
        Metrics[Performance Metrics]
    end

    TabView --> Cards
    Cards --> Dialogs

    Cards --> Events
    Events --> Handlers
    Handlers --> Callbacks

    Handlers --> AppState
    AppState --> Session
    Session --> Preferences

    Callbacks --> Notifications
    Callbacks --> Logging
    Callbacks --> Metrics
```

## Security Architecture

```mermaid
graph TB
    subgraph "Authentication Layer"
        Login[Login System]
        SessionMgmt[Session Management]
        PasswordHash[Password Hashing]
    end

    subgraph "Authorization Layer"
        Permissions[Permission System]
        AccessControl[Access Control]
        UserRoles[User Roles]
    end

    subgraph "Data Protection"
        InputValidation[Input Validation]
        DataSanitization[Data Sanitization]
        ErrorHandling[Error Handling]
    end

    subgraph "External Security"
        APIAuth[API Authentication]
        NetworkSec[Network Security]
        FilePermissions[File Permissions]
    end

    Login --> SessionMgmt
    SessionMgmt --> PasswordHash

    SessionMgmt --> Permissions
    Permissions --> AccessControl
    AccessControl --> UserRoles

    AccessControl --> InputValidation
    InputValidation --> DataSanitization
    DataSanitization --> ErrorHandling

    ErrorHandling --> APIAuth
    APIAuth --> NetworkSec
    NetworkSec --> FilePermissions
```

## Performance Architecture

```mermaid
graph TB
    subgraph "Performance Monitoring"
        TimingService[Unified Timing Service]
        MetricsCollection[Metrics Collection]
        PerformanceLog[Performance Logging]
    end

    subgraph "Optimization Strategies"
        AsyncProcessing[Async Processing]
        ResourcePooling[Resource Pooling]
        LazyLoading[Lazy Loading]
    end

    subgraph "Caching Layer"
        ResultCache[Result Cache]
        ModelCache[Model Cache]
        SessionCache[Session Cache]
    end

    subgraph "Resource Management"
        MemoryManagement[Memory Management]
        ThreadPooling[Thread Pooling]
        ConnectionPooling[Connection Pooling]
    end

    TimingService --> MetricsCollection
    MetricsCollection --> PerformanceLog

    PerformanceLog --> AsyncProcessing
    AsyncProcessing --> ResourcePooling
    ResourcePooling --> LazyLoading

    LazyLoading --> ResultCache
    ResultCache --> ModelCache
    ModelCache --> SessionCache

    SessionCache --> MemoryManagement
    MemoryManagement --> ThreadPooling
    ThreadPooling --> ConnectionPooling
```

## Directory Structure

```
code2cga/
├── main.py                     # Application entry point
├── core/                       # Core framework components
│   ├── base_controller.py      # Base controller with lifecycle management
│   └── view_manager_template.py # Template for view managers
├── modules/                    # Functional modules
│   ├── analise/               # Code analysis module
│   │   ├── controller.py      # Analysis controller
│   │   ├── model.py           # Analysis model
│   │   └── view/              # View layer
│   │       ├── view_manager.py
│   │       └── components/    # Reusable UI components
│   ├── sintese/              # Graph synthesis module
│   │   ├── controller.py      # Synthesis controller
│   │   ├── model.py           # Synthesis model
│   │   └── view/              # View layer
│   ├── grafo/                # Graph visualization module
│   │   ├── controller.py      # Graph controller
│   │   ├── model.py           # Graph model
│   │   └── view/              # View layer
│   ├── dashboard/            # Analytics dashboard
│   │   ├── controller.py      # Dashboard controller
│   │   ├── model.py           # Dashboard model
│   │   └── view/              # View layer
│   └── auth/                 # Authentication module
│       ├── controller.py      # Auth controller
│       └── view/              # Login view
├── services/                   # Support services
│   ├── ollama_service.py      # Ollama integration
│   ├── notification_service.py # Notification system
│   ├── database_service.py    # Database operations
│   └── unified_timing_service.py # Timing and metrics
├── storage/                    # Persistent data storage
│   ├── analise.db             # SQLite: Analysis results
│   ├── analytics.db           # SQLite: System metrics
│   ├── users.json             # User authentication
│   ├── data/                  # JSON analysis files
│   ├── temp/                  # Temporary files
│   └── export/                # User exports
├── log/                        # Application logs
├── explicabilidade/            # Explainability artifacts
├── inspecao/                   # Inspection files
└── docs/                       # Documentation
```

## Key Design Principles

1. **Modularity**: Each module is self-contained with clear boundaries
2. **Separation of Concerns**: MVC pattern ensures clean separation
3. **Async Processing**: Long-running operations don't block UI
4. **Centralized Services**: Shared services reduce duplication
5. **Event-Driven**: UI responds to events through callbacks
6. **Thread Safety**: Proper synchronization for concurrent operations
7. **Resource Management**: Efficient use of memory and connections
8. **Extensibility**: Easy to add new modules and features

This architecture documentation provides a comprehensive view of the Code2CGA system using Mermaid diagrams to visualize various aspects of the system's structure, data flow, and interactions. The diagrams follow the actual implementation patterns found in the codebase and illustrate the relationships between components, modules, and services.