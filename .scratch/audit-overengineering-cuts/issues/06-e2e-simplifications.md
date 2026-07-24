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

**Status:** ready-for-agent

- [ ] `signInTutor` helper used everywhere; ~55 lines removed
- [ ] vite-startup spec/server/script deleted
- [ ] run.sh single cleanup path
- [ ] One serve script covers both ports
- [ ] `bun run test:e2e` passes
- [ ] One commit
