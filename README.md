# Canvas Learning MCP Server

An MCP server for integrating with [Canvas Learning Management System](https://www.instructure.com/canvas) using the Canvas API.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ctrl-cheeb-del/canvas-mcp-poke)

## Features

This MCP server provides tools to interact with Canvas LMS:

- **get_upcoming_assignments** - Get assignments due within the next N days across all courses
- **get_todos** - Get your Canvas todo list (assignments needing attention)
- **get_dashboard_courses** - Get your active Canvas courses
- **get_course_assignments** - Get assignments for a specific course (upcoming, past, or undated)

## Setup

### Get Your Canvas API Token

1. Log into your Canvas instance (e.g., `https://canvas.instructure.com` or your school's Canvas URL)
2. Go to Account → Settings
3. Scroll down to "Approved Integrations"
4. Click "+ New Access Token"
5. Enter a purpose (e.g., "MCP Server") and set an expiration date (optional)
6. Copy the generated token - **you won't be able to see it again!**

### Local Development

Fork the repo, then run:

```bash
git clone <your-repo-url>
cd canvas-mcp-poke
conda create -n canvas-mcp python=3.13
conda activate canvas-mcp
pip install -r requirements.txt
```

### Test

```bash
python src/server.py
# then in another terminal run:
npx @modelcontextprotocol/inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using "Streamable HTTP" transport (NOTE THE `/mcp`!).

When testing tools, you'll need to provide:
- **canvas_url**: Your Canvas instance URL (e.g., `https://canvas.instructure.com`)
- **api_token**: Your Canvas API token from the setup step above

## Usage Examples

### Get Upcoming Assignments

```python
# Get assignments due in the next 7 days
get_upcoming_assignments(
    canvas_url="https://canvas.instructure.com",
    api_token="your-token-here",
    days_ahead=7
)
```

### Get Todos

```python
# Get your Canvas todo list
get_todos(
    canvas_url="https://canvas.instructure.com",
    api_token="your-token-here"
)
```

### Get Active Courses

```python
# Get your active courses
get_dashboard_courses(
    canvas_url="https://canvas.instructure.com",
    api_token="your-token-here"
)
```

### Get Course Assignments

```python
# Get upcoming assignments for a specific course
get_course_assignments(
    canvas_url="https://canvas.instructure.com",
    api_token="your-token-here",
    course_id=12345,
    bucket="upcoming"  # or "past", "undated"
)
```

## Deployment

### Option 1: One-Click Deploy
Click the "Deploy to Render" button above.

### Option 2: Manual Deployment
1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Render will automatically detect the `render.yaml` configuration

Your server will be available at `https://your-service-name.onrender.com/mcp` (NOTE THE `/mcp`!)

## Poke Setup

You can connect your MCP server to Poke at [poke.com/settings/connections](https://poke.com/settings/connections).

**Important**: When configuring the connection in Poke, you'll need to specify how to pass your Canvas credentials. Since tools require `canvas_url` and `api_token` parameters, you can either:
- Pass them with each tool call
- Store them in environment variables and modify the tools to read from env vars

To test the connection explicitly, ask Poke something like:
```
Tell the subagent to use the "Canvas" integration's "get_upcoming_assignments" tool with canvas_url="https://your-canvas.edu" and api_token="your-token"
```

If you run into persistent issues of Poke not calling the right MCP (e.g., after you've renamed the connection), you may send `clearhistory` to Poke to delete all message history and start fresh.

## Security Notes

⚠️ **Never commit your Canvas API token to version control!**

- Use environment variables for production deployments
- Tokens grant full access to your Canvas account
- Set expiration dates on tokens when possible
- Rotate tokens regularly

## Canvas API Documentation

For more details on the Canvas API:
- [Canvas LMS REST API Documentation](https://canvas.instructure.com/doc/api/)
- [Canvas API Live Documentation](https://canvas.instructure.com/doc/api/live) - Interactive API explorer

## Customization

Add more Canvas tools by decorating async functions with `@mcp.tool`:

```python
@mcp.tool(description="Get submissions for an assignment")
async def get_assignment_submissions(
    canvas_url: str,
    api_token: str,
    course_id: int,
    assignment_id: int
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    submissions = await canvas.get(
        f"courses/{course_id}/assignments/{assignment_id}/submissions"
    )
    return submissions
```

Common Canvas API endpoints you might want to add:
- `/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions` - Assignment submissions
- `/api/v1/courses/{course_id}/quizzes` - Course quizzes
- `/api/v1/courses/{course_id}/discussion_topics` - Discussion topics
- `/api/v1/users/self/courses` - All courses (not just dashboard)
- `/api/v1/calendar_events` - Calendar events
