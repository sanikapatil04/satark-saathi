# Satark Saathi - Project Context

## 1. Project Purpose
Satark Saathi is a privacy-first, voice-first scam-check application designed specifically for Indian senior citizens to protect them against digital frauds, suspicious messages, malicious links, and fraudulent visual elements.

## 2. Phase 1 Scope
Phase 1 enables senior citizen users to submit suspicious items for instant scam assessment via two primary channels: Next.js Progressive Web App (PWA) and WhatsApp bot.
Users can submit:
1. A suspicious text or message content.
2. A suspicious URL or web link.
3. A screenshot of a message, app screen, or notice.

The system processes inputs through a detection pipeline and returns:
- **GREEN**: Looks safe.
- **YELLOW**: Be careful (suspicious or unverified elements detected).
- **RED**: Scam (high risk of fraud detected).

The response includes simple, clear explanations in English, Hindi, and Marathi, accompanied by voice/TTS support.

## 3. Excluded Scope (Future Phases)
The following features belong strictly to future development phases and **MUST NOT** be implemented in Phase 1:
- Live call alerts
- Live call monitoring or listening
- Call recording
- Family Safety Circle
- Automatic family notifications

## 4. Technology Stack
- **Backend**: Python 3.12, FastAPI, PostgreSQL, SQLAlchemy 2, Alembic, Redis, Pydantic
- **ML / OCR**: Python, scikit-learn, Tesseract OCR (Transformer support reserved for future phases)
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, next-intl, PWA support
- **WhatsApp Integration**: WhatsApp Cloud API webhook service (isolated communication layer)
- **Infrastructure**: Docker, Docker Compose, Nginx, GitHub Actions
- **Testing**: pytest, Playwright
- **Code Quality**: Ruff, mypy, ESLint, Prettier

## 5. Major Folder Structure & Purpose
- `apps/api/`: Main FastAPI application handling core business services, detection pipeline, database models, repositories, and REST API endpoints.
- `apps/web/`: Next.js PWA user interface for senior citizens with multi-language and voice support.
- `apps/whatsapp-bot/`: Standalone webhook service for receiving WhatsApp user inputs and forwarding requests to `apps/api`.
- `packages/ml/`: Isolated ML package containing feature engineering, model training scripts, datasets, and inference wrappers.
- `packages/shared/`: Shared TypeScript types, constants, risk level definitions, and scam categories used across web frontend components.
- `infra/`: Nginx reverse proxy configurations, Docker container definitions, and deployment scripts.
- `docs/`: Comprehensive project documentation, architectural guidelines, API specifications, privacy rules, and ADR records.
- `.github/workflows/`: CI automation pipelines for linting, type checking, and automated testing.

## 6. Architecture Boundaries
- **Database Access**: Must be strictly encapsulated within data repository classes under `apps/api/app/repositories/`.
- **Business/Domain Logic**: Belongs exclusively inside service modules in `apps/api/app/services/` or `packages/ml/`.
- **API Endpoint Files**: Must remain thin HTTP controllers delegating request processing directly to services.
- **UI Components**: Must not contain backend business logic or database access routines.
- **OCR Service**: Encapsulated behind the dedicated API OCR service boundary (`apps/api/app/services/ocr.py`).
- **Reputation Checkers**: URL and phone number reputation checking must operate as independent, decoupled service boundaries.
- **Voice/TTS Layer**: Must be accessed exclusively through its dedicated service interface.
- **WhatsApp Bot**: Communicates with the core backend strictly via standard backend API endpoints.

## 7. Coding Conventions
- **Python**: Strict adherence to PEP 8, verified via Ruff and mypy type checking. Use async FastAPI routes and SQLAlchemy 2 async sessions.
- **TypeScript**: Strict type definitions, linted with ESLint and formatted with Prettier. No implicit `any`.
- **Service Boundaries**: Always enforce clean layer separation (Endpoints -> Services -> Repositories -> Models).

## 8. Privacy Principles
- Privacy-first by design.
- No sensitive user content or raw message payloads should be unnecessarily persisted in database storage.
- Analysis logs must sanitize personally identifiable information (PII) before storage or logging.

## 9. Supported Languages
- English (`en`)
- Hindi (`hi`)
- Marathi (`mr`)

## 10. Risk Levels
- **GREEN**: Safe / Low Risk
- **YELLOW**: Caution / Medium Risk
- **RED**: Scam / High Risk

## 11. Business Logic Isolation Rule
Business logic must be implemented **ONLY** inside the appropriate backend services (`apps/api/app/services/`) or dedicated packages (`packages/ml/`). API route handlers and frontend UI components must **NEVER** contain direct business logic, analytical heuristics, or direct DB/ML calls.
