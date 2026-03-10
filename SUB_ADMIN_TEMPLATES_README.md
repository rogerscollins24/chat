# Sub-admin Lead Info & Shared Templates

## Objective
Capture lead metadata (device, city) inside the session view and give every agent access to a shared bank of up to five reusable message templates. Teams should be able to add/remove templates from the backend so agents see consistent canned replies without duplicating work. The UI also removes the third auto-suggestion button (per latest requirements) and wires the lead info into the sidebar context.

## Backend Changes
1. New `MessageTemplate` model in `backend/models.py` stores template text plus timestamps. It is shared across agents and persisted in Postgres/SQLite via SQLAlchemy.
2. Added three REST endpoints in `backend/main.py`:
   - `GET /api/templates` returns all templates (ordered most recent first). Authentication is required via bearer token.
   - `POST /api/templates` saves a template after trimming whitespace; rejects empty text and enforces a cap of five templates.
   - `DELETE /api/templates/{template_id}` removes a template if it exists.
   Each of these endpoints reuses the existing `security` scheme and calls `get_current_agent` to keep consistent session checks.
3. Updated Pydantic schemas (`backend/schemas.py`) to expose `MessageTemplateCreate` and `MessageTemplateResponse`, letting the frontend validate payloads and responses.

## Frontend Tasks
1. In `src/services/api.ts`, add typings for the new template endpoints and wire them to the auth-aware `fetch` helper (reuse the authenticated header helper). Provide functions for listing templates, saving a new one, and deleting by ID.
2. Adjust `SuperAdminDashboard.tsx` (and any shared sidebar components) to:
   - Render the sub-admin lead info panel with device and city metadata extracted from `session.metadata` (`metadata.device`, `metadata.location?.city`).
   - Replace the third auto-suggestion button with the new template picker (shown in a readonly list or dropdown).
   - Allow agents to click a template to add it into the compose box without copying text manually.
3. Manage template state globally (hooks or context) so agents see updates after adding/removing templates. The UI should enforce the five-template cap (disable save when limit reached and show a helper message).
4. Ensure the shared templates UI is accessible from `App.tsx`'s routing (inside the super-admin/sub-admin view) so new panels load only for authorized roles.

## Testing & Verification
- Backend: Run `pytest backend/test_postgresql_backend.py` to cover new persistence logic, or manually hit the new endpoints using the same JWT header super-admin credentials to ensure CRUD works and the five-template ceiling is enforced.
- Frontend: Start the Vite dev server (`npm run dev`) and log in as a super-admin/sub-admin to confirm templates load, delete, and that the lead sidebar correctly shows device/city metadata.

## Notes
- Template texts are trimmed server-side; the frontend should avoid sending duplicates by checking if a modal text already exists (optional but recommended).
- Templates are shared across all agents, so the UI should refresh `GET /api/templates` after mutations. Strategies include invalidating cache on save/delete or using `useEffect` with a dependency on the last update time.
- The third suggestion button used to prefill text; it should now route users through the template list without mentioning the prior shortcut.
