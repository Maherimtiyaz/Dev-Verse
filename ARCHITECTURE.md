# DevVerse AI - Architecture Decision Record

## Overview
DevVerse AI is a production-grade AI developer platform combining:
1. AI GitHub Twin - Developer profiling and analysis
2. AI Code Roast - Intelligent code review with personality
3. AI Open Source Matchmaker - Project recommendation engine
4. AI Hackathon Partner Finder - Teammate matching system

## Technology Choices

### Backend Stack
- **Python 3.12**: Latest stable version with improved async performance
- **FastAPI**: High-performance async framework with automatic OpenAPI docs
- **SQLAlchemy 2.0**: Modern ORM with async support and type safety
- **PostgreSQL**: Reliable RDBMS with JSONB support for flexible schemas
- **Redis**: Caching layer and Celery broker
- **Celery**: Distributed task queue for background jobs
- **LangGraph**: Agent orchestration with state management
- **Pydantic v2**: Data validation with V2 performance improvements
- **Alembic**: Database migration management

### AI/ML Stack
- **Qdrant**: Vector database for semantic search and recommendations
- **LangChain/LangGraph**: Agent framework with graph-based workflows
- **Embeddings**: Code and profile embeddings for matching algorithms

### Frontend Stack
- **Next.js 14**: App Router with Server Components
- **TypeScript**: Type safety across the stack
- **Tailwind CSS**: Utility-first styling for rapid UI development

### Infrastructure
- **Docker Compose**: Local development environment
- **Kubernetes**: Production orchestration with Kustomize
- **Helm**: Package management for K8s deployments
- **GitHub Actions**: CI/CD pipelines
- **AWS Ready**: Terraform configurations for cloud deployment

### Observability
- **OpenTelemetry**: Distributed tracing
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Structured Logging**: JSON logs with correlation IDs

## Architecture Principles

### 1. Clean Architecture
- Separation of concerns: routers → services → models
- Dependency injection for testability
- Interface-driven design

### 2. Scalability
- Async-first design throughout
- Horizontal scaling with stateless services
- Database connection pooling
- Redis caching at multiple layers

### 3. Security
- JWT authentication with refresh tokens
- OAuth 2.0 for GitHub integration
- RBAC for authorization
- Rate limiting per endpoint
- Input validation with Pydantic

### 4. Event-Driven Design
- Celery for async task processing
- Event publishing for cross-service communication
- Webhook handling for GitHub events

### 5. API Versioning
- URL-based versioning (/api/v1/, /api/v2/)
- Backward compatibility guarantees
- Deprecation strategy

## Folder Structure

```
devverse-ai/
├── backend/
│   ├── app/                  # FastAPI application
│   │   ├── v1/               # API version 1
│   │   └── v2/               # API version 2
│   ├── agents/               # LangGraph agents
│   │   ├── github_agent.py
│   │   ├── code_review_agent.py
│   │   ├── matchmaking_agent.py
│   │   ├── career_agent.py
│   │   └── project_agent.py
│   ├── core/                 # Core configuration
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── db/                   # Database setup
│   │   ├── session.py
│   │   └── base.py
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   ├── tasks/                # Celery tasks
│   ├── utils/                # Utilities
│   ├── alembic/              # Migrations
│   ├── tests/                # Test suite
│   └── main.py               # Application entry
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API clients
│   │   ├── store/            # State management
│   │   └── types/            # TypeScript types
│   └── public/
├── infrastructure/
│   ├── docker/               # Dockerfiles
│   ├── k8s/                  # Kubernetes manifests
│   ├── helm/                 # Helm charts
│   └── terraform/            # IaC
├── docker-compose.yml
└── README.md
```

## Database Schema Design

### Core Tables

**users**
- id (UUID, PK)
- email (unique)
- password_hash (nullable for OAuth users)
- github_id (unique, nullable)
- created_at
- updated_at
- last_login

**profiles**
- id (UUID, PK)
- user_id (FK → users)
- username
- full_name
- avatar_url
- bio
- location
- website
- github_username
- linkedin_url
- twitter_handle
- availability_status
- looking_for_work (boolean)
- open_to_collaboration (boolean)

**github_repositories**
- id (UUID, PK)
- user_id (FK → users)
- repo_id (GitHub ID)
- name
- full_name
- description
- language
- stars_count
- forks_count
- private
- archived
- created_at
- updated_at
- last_synced

**skills**
- id (UUID, PK)
- name (unique)
- category (language, framework, tool, domain)
- parent_skill_id (FK → skills, nullable)

**user_skills**
- user_id (FK → users)
- skill_id (FK → skills)
- proficiency_level (1-5)
- years_experience
- last_used
- PRIMARY KEY (user_id, skill_id)

**projects**
- id (UUID, PK)
- name
- description
- github_url
- organization
- technologies (JSONB)
- difficulty_level (beginner/intermediate/advanced)
- status (active/completed/archived)
- embedding (vector)
- created_at
- updated_at

**matches**
- id (UUID, PK)
- user_id (FK → users)
- target_type (project/user)
- target_id (UUID)
- score (float)
- match_reason (text)
- status (pending/accepted/rejected)
- created_at

**code_reviews**
- id (UUID, PK)
- user_id (FK → users)
- repository_url
- review_type (architecture/security/performance/roast)
- findings (JSONB)
- roast_mode (boolean)
- status (pending/completed/failed)
- created_at
- completed_at

**contributions**
- id (UUID, PK)
- user_id (FK → users)
- project_id (FK → projects)
- type (pr/issue/comment)
- url
- description
- accepted (boolean)
- created_at

**notifications**
- id (UUID, PK)
- user_id (FK → users)
- type
- title
- message
- read (boolean)
- created_at

**hackathon_teams**
- id (UUID, PK)
- name
- project_idea
- max_members
- current_members (int)
- status (forming/complete/disbanded)
- created_at

**team_members**
- team_id (FK → hackathon_teams)
- user_id (FK → users)
- role
- joined_at
- PRIMARY KEY (team_id, user_id)

## Agent Architecture

### GithubAgent
- **Purpose**: Analyze GitHub profiles and repositories
- **Tools**: GitHub API client, language analyzer, commit pattern analyzer
- **Output**: Developer DNA (skills, strengths, weaknesses, style)
- **State**: User context, repository list, analysis results

### CodeReviewAgent
- **Purpose**: Multi-agent code review system
- **Sub-agents**: 
  - ArchitectureReviewer
  - SecurityReviewer
  - PerformanceReviewer
  - RoastGenerator
- **Tools**: AST parser, security scanner, complexity analyzer
- **Output**: Structured review with actionable feedback

### MatchmakingAgent
- **Purpose**: Match developers with projects and teammates
- **Tools**: Vector similarity search, skill graph, compatibility scorer
- **Output**: Ranked recommendations with explanations

### CareerAgent
- **Purpose**: Personalized learning and career guidance
- **Tools**: Skill gap analyzer, learning resource finder, trend analyzer
- **Output**: Learning roadmap and recommendations

### ProjectRecommendationAgent
- **Purpose**: Suggest open source contributions
- **Tools**: Issue analyzer, difficulty estimator, interest matcher
- **Output**: Curated issue list with contribution guide

## Security Considerations

1. **Authentication**: JWT with short-lived access tokens + refresh tokens
2. **OAuth**: GitHub OAuth with PKCE flow
3. **Authorization**: Role-based access control (RBAC)
4. **Rate Limiting**: Per-user and per-endpoint limits via Redis
5. **Input Validation**: Pydantic models for all inputs
6. **Secrets Management**: Environment variables, never hardcoded
7. **CORS**: Strict origin policies
8. **HTTPS**: Enforced in production

## Next Steps (Phase 1)

1. Set up Docker Compose for local development
2. Implement database models with SQLAlchemy
3. Create Alembic migration configuration
4. Build authentication system (JWT + OAuth)
5. Set up basic API structure with versioning
6. Configure logging and observability basics

---

**Decision Date**: 2025
**Status**: Approved for Phase 1 Implementation
**Author**: CTO/Lead Engineer
