# 06 — E2E simplifications

**What to build:** Four cuts, one commit:
1. Hoist the copy-pasted tutor magic-link sign-in flow (10 sites across specs)
   into one `e2e/helpers.ts` `signInTutor(page)`; replace all inline copies
   (`tutor-timezone.spec.ts` already has the right local shape).
2. Delete `e2e/vite-startup.spec.ts`, its third webServer in
   `playwright.config.ts`, and the `serve:e2e:development-frontend` script —
   it tests Vite, not the product.
3. `e2e/run.sh`: cleanup runs twice (trap + explicit + `trap - EXIT`) — keep the
   trap, end with `exit "${status}"`.
4. Merge `serve:frontend` and `serve:e2e:frontend` into one script with a port
   default (`${E2E_FRONTEND_PORT:-7310}`).

**Blocked by:** 04, 05 (shares spec files)

**Status:** resolved

- [x] `signInTutor` helper used everywhere; ~55 lines removed
- [x] vite-startup spec/server/script deleted
- [x] run.sh single cleanup path
- [x] One serve script covers both ports
- [x] `bun run test:e2e` passes
- [x] One commit

## Answer

1. `e2e/helpers.ts` `signInTutor(page)` (returns the CSRF token) replaced 9
   inline copies across `tutor-authentication`, `login-request`,
   `critical-journey`, and `tutor-timezone` (which delegates so it keeps its
   Tokyo-timezone context). The first test in `tutor-authentication.spec.ts`
   keeps its inline flow — it asserts the intermediate screens, so it *is* the
   sign-in flow test.
2. `vite-startup.spec.ts`, the third webServer, and
   `serve:e2e:development-frontend` deleted (plus
   `E2E_DEVELOPMENT_FRONTEND_PORT` in `run.sh`).
3. `run.sh` keeps only the EXIT trap and ends with `exit "${status}"`.
4. `serve:e2e:frontend` merged into `serve:frontend` with
   `${E2E_FRONTEND_PORT:-7310}`; `playwright.config.ts` updated. README has no
   references to these scripts. 18/18 e2e pass. Commit `1699b45`.
