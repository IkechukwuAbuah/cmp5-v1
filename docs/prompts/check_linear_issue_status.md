# Check Linear Issue Status Prompt

## Purpose
Verify if a specific Linear issue has been addressed or completed by checking its current status and task completion.

## Prompt Template

```
Check the status of Linear issue [ISSUE_ID] to determine if it has been addressed:

1. Retrieve the issue details using the Linear API
2. Check the current status (Backlog, In Progress, Done, etc.)
3. Review task completion progress in the description
4. Analyze recent updates or comments
5. Provide a summary of:
   - Current status
   - Completion percentage
   - Any blockers or dependencies
   - Next steps if incomplete
6. When marked complete, capture evidence (files, tests) and update Linear with a status/comment.

Issue to check: [ISSUE_URL_OR_ID]
```

## Example Usage

```
Check the status of Linear issue EFLP-212 to determine if it has been addressed:

1. Retrieve the issue details using the Linear API
2. Check the current status (Backlog, In Progress, Done, etc.)
3. Review task completion progress in the description
4. Analyze recent updates or comments
5. Provide a summary of:
   - Current status
   - Completion percentage
   - Any blockers or dependencies
   - Next steps if incomplete

Issue to check: https://linear.app/abuah/issue/EFLP-212/phase-33-core-implementation-models-and-services-t018-t034
```

## Expected Output Format

```
Issue Status Report:
- Issue ID: [ID]
- Title: [Title]
- Current Status: [Status]
- Progress: [X/Y tasks completed]
- Last Updated: [Date]
- Assignee: [Name]
- Completion Status: [Addressed/Not Addressed/Partially Addressed]
- Evidence Collected: [Key files, test results, notes]
- Next Actions: [List of recommended actions]
```

## Follow-up Checklist

- Note the repository evidence that confirms completion (e.g., `backend/src/localisation/en.py`).
- Update `tasks.md` with the verified task status.
- Post a Linear comment summarising the verification and, if appropriate, move the issue to Done.
