# FitBuddy manual QA checklist

1. Start with `python run.py`.
2. Open `/` and verify responsive landing page.
3. Sign up and verify login session.
4. Complete the fitness assessment.
5. Generate a plan with Gemini configured; if unavailable, verify the safe fallback message/plan.
6. Verify exactly seven day cards, nutrition, hydration and recovery sections.
7. Submit difficulty/energy/preferences/feedback.
8. Verify updated plan appears and original plan remains accessible.
9. Open history and verify only the signed-in user's plans appear.
10. Add progress and verify it appears in progress history.
11. Logout and verify protected pages redirect/error.
12. Create a second account and verify it cannot open the first account's plan URL.
13. Configure admin credentials and verify `/admin` is protected.
14. Verify admin sees user/plan monitoring data but never passwords.
15. Open `/docs` and test `/api/health`.


## Final verification additions

The final suite also verifies the dedicated admin login flow, the searchable food guide, admin progress monitoring, and deterministic 7-day food habits when Gemini is temporarily unavailable.


## Enhanced UI/security checks

- Public login and signup do not expose Food Guide or a separate Admin login.
- Admin credentials are entered through the normal login form and redirect to `/admin`.
- Normal users cannot see or open the Admin console.
- Food Guide is available to authenticated users and authenticated admins.
- Each generated plan has a 7-day completion checklist. Each click is saved immediately and recalculates the completion percentage.
- Admin monitoring shows the latest plan's 7-day completion state for each user.
- Feedback has a dedicated adjustment card with structured options and a clear update action.
- Food Guide includes 57 common foods/drinks with approximate serving, calorie, protein and fibre values.
