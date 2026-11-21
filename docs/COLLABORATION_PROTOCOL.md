# Codex and Grok collaboration

Samir owns the project. Codex coordinates engineering, reviews, and leads the
editable frontend. Grok leads bots/backend implementation, reviews Codex's work
and supplies independent recommendations. Both agree integration contracts. Either assistant
can be wrong; tests, source evidence and trade-offs guide the choice.

## Discussion format
For each substantial choice, the issue contains:
1. Problem and requirement IDs.
2. Grok's independent proposal before reading a preferred answer when practical.
3. Codex's proposal or review and questions.
4. Alternatives with complexity, latency, reliability, observability and cost.
5. A bounded experiment or independently derived test that distinguishes them.
6. Outcome: ACCEPTED, REVISE, BLOCKED or INCONCLUSIVE.
7. Decision record and exact affected commit.

Grok should actively identify weaknesses in Codex's starter. Codex must answer
Grok's substantive objections and adopt the stronger supported design when warranted.
Avoid consensus based only on two assistants agreeing.
After two unresolved discussion rounds, define the missing test or record the
decision as open. Consult Samir for material scope, spending or risk choices.

## Work loop
- Issue: concrete scope, owner, interfaces and acceptance tests.
- Branch: `grok/<task>` or `codex/<task>`.
- PR: requirement mapping, actual commands, evidence and remaining limits.
- Review: comments tied to the exact commit; do not approve unseen later changes.
- Revision: reply to each finding with a fix or evidence-based explanation.
- Record: update the requirements matrix and decision register.
- Merge only through the agreed stage workflow and available repository controls.

Claim an issue before editing shared contracts. Both parties must agree changes
to public contracts before parallel dependent work. Do not rewrite each other's
branches or silently change financial logic to satisfy a test.
Codex owns M14 implementation in apps/dashboard/. Grok provides UI critique,
backend capabilities and realistic data/error examples, and proposes frontend
changes through the relevant issue/PR. See docs/FRONTEND_HANDOFF.md.

## Identity and permissions
A comment begins with `Actor: Grok` or `Actor: Codex`, followed by `Reviewed commit:`.
These are descriptive labels, not authenticated independent accounts.
If both assistants use Samir's GitHub identity, GitHub may treat both as one actor.
Do not claim formal independent approval, create fake reviewer accounts, or
bypass self-review/branch protection restrictions. Use transparent review comments,
test evidence and an owner-controlled merge where required by GitHub.

No repository sharing to outside people or public publication is included.
Exchange secrets, tokens, cookies and account passwords do not belong in issues,
source files, prompts, screenshots or logs.

## Trigger and delivery
This package does not configure autonomous messaging or schedules.
A comment appearing in GitHub is not proof that the other assistant saw it.
For supervised handoffs, send the other assistant the issue or PR link and ask it
to review the latest commit/comments. It reads and replies through GitHub when
its tools and repository access permit.
A future automatic bridge needs separate verification of authentication, duplicate
suppression, branch/commit targeting, bounded retries, usage limits and response
delivery. Do not promise permanent monitoring from an ordinary chat.

## Engineering acceptance
A task is accepted for its stated behavior, with relevant passing tests and
recorded limits. Financial authority remains conventional software.
No assistant can activate live orders or paid services under the setup instruction.

