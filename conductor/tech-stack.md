# Technology Stack: Schedule AI

## Frontend
- **Framework:** React (v19) with TypeScript. Use modern, functional components and hooks for state management.
- **Build Tool:** Vite. Fast development and optimized production builds for the React application.
- **Styling:** Tailwind CSS (v4). Utility-first CSS framework for rapid and responsive UI development.
- **Visualization:** Cytoscape.js and Dagre layout for interactive and automated prerequisite tree rendering.

## Backend
- **Framework:** Python (v3.12) with FastAPI. High-performance web framework for building APIs and handling complex business logic.
- **Database:** libSQL (SQLite/Turso) with SQLAlchemy as the ORM for structured data storage and querying.
- **AI/ML Integration:** Google GenAI, Groq, LangChain, and LangGraph for advanced natural language processing and agentic workflows.
- **Web Scraping:** Playwright, Firecrawl, and BeautifulSoup4 for harvesting course data, GE requirements, and instructor ratings.

## Infrastructure & Tools
- **Package Management:** `uv` for Python and `npm` for the frontend.
- **Testing:** `pytest` for backend testing.
- **Deployment:** Container-ready architecture for deployment to cloud platforms (e.g., Vercel for frontend, Fly.io or Render for backend).

## Project Structure
- `server/`: FastAPI backend application and API endpoints.
- `frontend/`: React frontend application.
- `sjsu-data-retrival/`: Scrapers, database schema, and data loading scripts.
