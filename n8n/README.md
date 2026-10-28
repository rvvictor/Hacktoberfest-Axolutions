# n8n · Hunter outreach flow

`workflows/hunter-outreach.json` is the outreach flow of the Hunter agent (IDEA.md §4 step 5, §7):

1. **Draft webhook** (POST `/webhook/hunter-outreach`) receives the AI draft from FastAPI, signed.
2. **Verify draft signature** refuses unsigned or wrongly signed drafts.
3. **Return resume URL** answers FastAPI with `resumeUrl`; the execution then pauses.
4. **Wait for human approval** resumes only when FastAPI posts the approval, which a human triggers in the UI.
5. **Verify approval signature** requires `approved_by`, checks the signature, and checks that `outreach_id` matches the draft.
6. **Mock send** does not send real email or WhatsApp. It returns `demo_data: true`.
7. **Callback to SpeedHack** calls `POST /api/hunter/outreach/{id}/callback` with a signed body. FastAPI confirms the status only after verifying it.

Opt-out is enforced before this flow: FastAPI never starts a draft for a prospect with `opt_out`.

## Signing

Both directions use HMAC-SHA256 with `N8N_WEBHOOK_SECRET`, sent in the `X-SpeedHack-Signature: sha256=<hex>` header. The signed string is the parts joined with `\n`:

| Step | Parts |
|---|---|
| draft (FastAPI to n8n) | `outreach_id`, `prospect_id`, `channel`, `sha256(body)` |
| approval (FastAPI to n8n) | `outreach_id`, `prospect_id`, `channel`, `approved_by`, `sha256(body)` |
| callback (n8n to FastAPI) | `outreach_id`, `status`, `sent_at` |

The Python side is `app/services/outreach.py` (`sign_parts`, `verify_parts`). Its tests pin the same strings.

## Import

1. In n8n, choose **Workflows → Import from file** and pick `workflows/hunter-outreach.json`.
2. Set the environment variables on the n8n instance:
   - `N8N_WEBHOOK_SECRET`: the same value as in the FastAPI `.env`. Use a new random value, never a committed one.
   - `SPEEDHACK_API_URL`: the public URL of the FastAPI backend.
3. The Code nodes read `$env`, so the instance must allow it (`N8N_BLOCK_ENV_ACCESS_IN_NODE=false`) and allow the `crypto` built-in (`NODE_FUNCTION_ALLOW_BUILTIN=crypto`).
4. Activate the workflow. In FastAPI, set `N8N_WEBHOOK_URL` to the production webhook URL. If it is unset, the same steps run in-process and the demo does not depend on n8n.

## Status

- The JSON is a hand-written export. It has not been imported into a live n8n instance: hosting n8n (Cloud or Docker) needs a human's OK.
- No real credentials exist in this repo. The secret is a placeholder read from the environment.
- Sends are mock only. Real email or WhatsApp sending is out of scope for the demo (IDEA.md §9).
