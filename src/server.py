#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import httpx
from fastmcp import FastMCP

mcp = FastMCP("Canvas Learning MCP Server")

class CanvasAPI:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v1/{endpoint}"
            response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()

@mcp.tool(description="Get upcoming assignments from Canvas. Returns assignments due within the specified number of days ahead.")
async def get_upcoming_assignments(
    canvas_url: str,
    api_token: str,
    days_ahead: int = 7
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days_ahead)
    
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "filter": ""
    }
    
    items = await canvas.get("planner/items", params)
    
    assignments = []
    for item in items:
        if item.get("plannable_type") == "assignment":
            plannable = item.get("plannable", {})
            assignments.append({
                "title": plannable.get("title"),
                "due_at": plannable.get("due_at"),
                "points_possible": plannable.get("points_possible"),
                "course_id": item.get("course_id"),
                "assignment_id": plannable.get("id"),
                "html_url": item.get("html_url")
            })
    
    return assignments

@mcp.tool(description="Get your Canvas todo list. Returns assignments and tasks that need attention.")
async def get_todos(
    canvas_url: str,
    api_token: str
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    todos = await canvas.get("users/self/todo")
    
    todo_list = []
    for todo in todos:
        assignment = todo.get("assignment", {})
        todo_list.append({
            "assignment_name": assignment.get("name"),
            "due_at": assignment.get("due_at"),
            "course_id": assignment.get("course_id"),
            "assignment_id": assignment.get("id"),
            "type": todo.get("type"),
            "needs_grading_count": todo.get("needs_grading_count", 0),
            "html_url": assignment.get("html_url")
        })
    
    return todo_list

@mcp.tool(description="Get your active Canvas courses from the dashboard.")
async def get_dashboard_courses(
    canvas_url: str,
    api_token: str
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    cards = await canvas.get("dashboard/dashboard_cards")
    
    courses = []
    for card in cards:
        courses.append({
            "id": card.get("id"),
            "course_code": card.get("course_code"),
            "short_name": card.get("shortName"),
            "name": card.get("originalName"),
            "href": card.get("href")
        })
    
    return courses

@mcp.tool(description="Get assignments for a specific Canvas course.")
async def get_course_assignments(
    canvas_url: str,
    api_token: str,
    course_id: int,
    bucket: str = "upcoming"
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "bucket": bucket,
        "order_by": "due_at"
    }
    
    assignments = await canvas.get(f"courses/{course_id}/assignments", params)
    
    assignment_list = []
    for assignment in assignments:
        assignment_list.append({
            "id": assignment.get("id"),
            "name": assignment.get("name"),
            "description": assignment.get("description"),
            "due_at": assignment.get("due_at"),
            "points_possible": assignment.get("points_possible"),
            "submission_types": assignment.get("submission_types", []),
            "html_url": assignment.get("html_url"),
            "has_submitted_submissions": assignment.get("has_submitted_submissions", False)
        })
    
    return assignment_list

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting Canvas MCP server on {host}:{port}")
    
    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
