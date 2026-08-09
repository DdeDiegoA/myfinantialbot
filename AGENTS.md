# MyFinancialBot
> Project initialized with protto.

## Build & Test
- Build: `echo 'TODO: add build command'`
- Test: `echo 'TODO: add test command'`
- Lint: `echo 'TODO: add lint command'`
- Typecheck: `echo 'TODO: add typecheck command'`

## Architecture
- docs/ — documentation
- .opencode/ — agent configuration

## Gotchas
- `lib/detect.sh` uses POSIX tools (no jq/python). Keep it dependency-free.
- `collect_skills` emits newline-separated names; consume with while-read.
- Backup files use `.bak.<timestamp>`; clean them up before committing.

## Environment
- Required: `bash >= 4.0`
- Optional: `git graphify`

## Available Skills
- Invoke skills with their trigger description. Add personal skills here as needed.
- See `docs/skills.md` for the list detected by protto.

## Docs
- `docs/architecture/` — high-level design and structure
- `docs/specs/` — feature specifications (speckit output)
- `docs/design-system/` — UI/UX and visual direction
- `docs/context.md` — current state and decisions
- `docs/decisions.md` — architectural decision log
- `docs/skills.md` — skills available to this project

## Post-Setup
- Run `protto analyze` to import graphify output or bootstrap it.

## Suggested Post-Setup Workflow

- **`agent-delegation`**: Delega tareas aisladas con agent-delegation
- **`architecture-diagram`**: Diagrama la arquitectura con architecture-diagram
- **`arxiv`**: Busca papers relevantes en arxiv
- **`business-opportunity`**: Valida oportunidad de negocio con business-opportunity
- **`excalidraw`**: Crea wireframes con excalidraw
- **`graphify`**: Genera el knowledge graph del proyecto: ejecuta al inicio y tras cada tarea
- **`grill-me`**: Valida el plan con /grill-me antes de implementar
- **`llm-council`**: Usa llm-council para validar decisiones de arquitectura
- **`naming`**: Usa naming para validar nombres de proyecto/módulos
- **`open-design-integration`**: Integra Open Design para diseño visual iterativo
- **`plan`**: Genera un plan de acción detallado con /plan
- **`proyecto-lean`**: Usa proyecto-lean como orquestador para proyectos multi-fase
- **`requesting-code-review`**: Configura code review pre-commit con requesting-code-review
- **`speckit-clarify`**: Usa /speckit-clarify si el spec tiene ambigüedades
- **`speckit-plan`**: Usa /speckit-plan para generar el plan de implementación
- **`speckit-specify`**: Usa /speckit-specify para crear el spec.md del proyecto
- **`vault-governance`**: Captura decisiones en el vault con vault-governance
- **`youtube-content`**: Investiga contenido relevante en YouTube con youtube-content
