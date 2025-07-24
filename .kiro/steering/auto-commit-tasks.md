---
inclusion: always
---

# Auto-Commit Task Completion Rule

## Purpose
This rule ensures that changes are automatically committed to git whenever a task or subtask in the project is completed.

## Guidelines

1. After completing any task or subtask from the spec's tasks.md file:
   - Stage all changes related to the completed task
   - Create a descriptive commit message that includes:
     - The task/subtask number and title
     - A brief description of what was implemented
     - Any relevant notes about the implementation

2. Commit format:
   ```
   Task [TASK_NUMBER]: [TASK_TITLE]

   - Implemented [FEATURE/COMPONENT]
   - [ADDITIONAL DETAILS IF NECESSARY]
   ```

3. For subtasks, include the parent task number:
   ```
   Task [PARENT_TASK].[SUBTASK_NUMBER]: [SUBTASK_TITLE]

   - Implemented [FEATURE/COMPONENT]
   - [ADDITIONAL DETAILS IF NECESSARY]
   ```

4. Always verify that all changes related to the task are included in the commit.

5. Keep commits focused on the specific task that was completed.

## Example

After completing task 2.1 "Implement User Authentication":
```
git add [files related to authentication]
git commit -m "Task 2.1: Implement User Authentication

- Added JWT authentication flow
- Created login and registration endpoints
- Implemented token validation middleware"
```

## Importance
Following this rule ensures:
- Clear tracking of task completion
- Easier code review process
- Better project history
- Ability to revert specific task implementations if needed
