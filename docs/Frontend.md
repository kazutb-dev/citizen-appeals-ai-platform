# Frontend

## Stack

- React 18
- TypeScript
- Vite
- TanStack Query
- React Router
- Tailwind CSS
- Recharts
- Framer Motion
- react-i18next

## User Surfaces

- requester portal for appeal submission and status tracking
- operator and analyst workspace for intake and review
- admin tools for agent settings, knowledge base, and integrations
- dashboards, monitoring, and geographic visualization

## Frontend Conventions

- all network access goes through `src/api/`
- role gating is centralized in auth route guards
- empty states are preferred over synthetic fallback data
- localization must keep Russian and Kazakh flows intact
- maps must preserve operational usability on desktop and mobile
