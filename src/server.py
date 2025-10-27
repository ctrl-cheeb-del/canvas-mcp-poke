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

@mcp.tool(description="Get upcoming calendar events including assignments, exams, and other events.")
async def get_calendar_events(
    canvas_url: str,
    api_token: str,
    days_ahead: int = 14
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days_ahead)
    
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "per_page": 100
    }
    
    events = await canvas.get("calendar_events", params)
    
    event_list = []
    for event in events:
        event_list.append({
            "title": event.get("title"),
            "start_at": event.get("start_at"),
            "end_at": event.get("end_at"),
            "type": event.get("type"),
            "description": event.get("description"),
            "location_name": event.get("location_name"),
            "html_url": event.get("html_url"),
            "context_code": event.get("context_code")
        })
    
    return event_list

@mcp.tool(description="Get recent announcements from your Canvas courses.")
async def get_course_announcements(
    canvas_url: str,
    api_token: str,
    days_back: int = 7
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    params = {
        "start_date": start_date.isoformat(),
        "per_page": 50
    }
    
    announcements = await canvas.get("announcements", params)
    
    announcement_list = []
    for announcement in announcements:
        announcement_list.append({
            "title": announcement.get("title"),
            "message": announcement.get("message"),
            "posted_at": announcement.get("posted_at"),
            "author": announcement.get("author", {}).get("display_name"),
            "context_code": announcement.get("context_code"),
            "html_url": announcement.get("html_url")
        })
    
    return announcement_list

@mcp.tool(description="Get your current grades for all courses or a specific course.")
async def get_grades(
    canvas_url: str,
    api_token: str,
    course_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    if course_id:
        params = {"enrollment_state": "active", "include[]": ["total_scores", "current_grading_period_scores"]}
        enrollments = await canvas.get(f"courses/{course_id}/enrollments", params)
    else:
        params = {"enrollment_state": "active", "include[]": ["total_scores", "current_grading_period_scores"]}
        enrollments = await canvas.get("users/self/enrollments", params)
    
    grades = []
    for enrollment in enrollments:
        if enrollment.get("type") == "StudentEnrollment":
            grades.append({
                "course_id": enrollment.get("course_id"),
                "current_score": enrollment.get("grades", {}).get("current_score"),
                "final_score": enrollment.get("grades", {}).get("final_score"),
                "current_grade": enrollment.get("grades", {}).get("current_grade"),
                "final_grade": enrollment.get("grades", {}).get("final_grade"),
                "unposted_current_score": enrollment.get("grades", {}).get("unposted_current_score"),
                "unposted_current_grade": enrollment.get("grades", {}).get("unposted_current_grade")
            })
    
    return grades

@mcp.tool(description="Get assignments you haven't submitted yet (missing assignments).")
async def get_missing_assignments(
    canvas_url: str,
    api_token: str
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "bucket": "missing",
        "per_page": 100
    }
    
    courses = await canvas.get("courses", {"enrollment_state": "active"})
    
    all_missing = []
    for course in courses:
        course_id = course.get("id")
        try:
            assignments = await canvas.get(f"courses/{course_id}/assignments", params)
            for assignment in assignments:
                all_missing.append({
                    "course_name": course.get("name"),
                    "course_id": course_id,
                    "assignment_id": assignment.get("id"),
                    "name": assignment.get("name"),
                    "due_at": assignment.get("due_at"),
                    "points_possible": assignment.get("points_possible"),
                    "html_url": assignment.get("html_url")
                })
        except:
            continue
    
    return all_missing

@mcp.tool(description="Get unread messages from your Canvas inbox.")
async def get_unread_messages(
    canvas_url: str,
    api_token: str
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "scope": "unread",
        "per_page": 50
    }
    
    conversations = await canvas.get("conversations", params)
    
    messages = []
    for conversation in conversations:
        messages.append({
            "id": conversation.get("id"),
            "subject": conversation.get("subject"),
            "last_message": conversation.get("last_message"),
            "last_message_at": conversation.get("last_message_at"),
            "message_count": conversation.get("message_count"),
            "participants": [p.get("name") for p in conversation.get("participants", [])],
            "context_name": conversation.get("context_name")
        })
    
    return messages

@mcp.tool(description="Get detailed information about a specific assignment including description and rubric.")
async def get_assignment_details(
    canvas_url: str,
    api_token: str,
    course_id: int,
    assignment_id: int
) -> Dict[str, Any]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "include[]": ["rubric", "rubric_assessment"]
    }
    
    assignment = await canvas.get(f"courses/{course_id}/assignments/{assignment_id}", params)
    
    return {
        "id": assignment.get("id"),
        "name": assignment.get("name"),
        "description": assignment.get("description"),
        "due_at": assignment.get("due_at"),
        "points_possible": assignment.get("points_possible"),
        "submission_types": assignment.get("submission_types", []),
        "allowed_attempts": assignment.get("allowed_attempts"),
        "grading_type": assignment.get("grading_type"),
        "html_url": assignment.get("html_url"),
        "rubric": assignment.get("rubric", []),
        "has_submitted_submissions": assignment.get("has_submitted_submissions", False)
    }

@mcp.tool(description="Check submission status for a specific assignment.")
async def get_submission_status(
    canvas_url: str,
    api_token: str,
    course_id: int,
    assignment_id: int
) -> Dict[str, Any]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "include[]": ["submission_history", "rubric_assessment"]
    }
    
    submission = await canvas.get(f"courses/{course_id}/assignments/{assignment_id}/submissions/self", params)
    
    return {
        "id": submission.get("id"),
        "assignment_id": submission.get("assignment_id"),
        "submitted_at": submission.get("submitted_at"),
        "workflow_state": submission.get("workflow_state"),
        "grade": submission.get("grade"),
        "score": submission.get("score"),
        "attempt": submission.get("attempt"),
        "late": submission.get("late"),
        "missing": submission.get("missing"),
        "excused": submission.get("excused"),
        "preview_url": submission.get("preview_url")
    }

@mcp.tool(description="Get course modules and their content structure.")
async def get_course_modules(
    canvas_url: str,
    api_token: str,
    course_id: int
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "include[]": ["items"]
    }
    
    modules = await canvas.get(f"courses/{course_id}/modules", params)
    
    module_list = []
    for module in modules:
        items = []
        for item in module.get("items", []):
            items.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "type": item.get("type"),
                "html_url": item.get("html_url"),
                "position": item.get("position")
            })
        
        module_list.append({
            "id": module.get("id"),
            "name": module.get("name"),
            "position": module.get("position"),
            "unlock_at": module.get("unlock_at"),
            "state": module.get("state"),
            "items": items
        })
    
    return module_list

@mcp.tool(description="Get active discussion topics from your courses.")
async def get_discussions(
    canvas_url: str,
    api_token: str,
    course_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    if course_id:
        discussions = await canvas.get(f"courses/{course_id}/discussion_topics")
    else:
        courses = await canvas.get("courses", {"enrollment_state": "active"})
        all_discussions = []
        for course in courses[:5]:
            try:
                course_discussions = await canvas.get(f"courses/{course.get('id')}/discussion_topics")
                for disc in course_discussions[:3]:
                    disc["course_name"] = course.get("name")
                    all_discussions.append(disc)
            except:
                continue
        discussions = all_discussions
    
    discussion_list = []
    for discussion in discussions:
        discussion_list.append({
            "id": discussion.get("id"),
            "title": discussion.get("title"),
            "message": discussion.get("message"),
            "posted_at": discussion.get("posted_at"),
            "discussion_type": discussion.get("discussion_type"),
            "unread_count": discussion.get("unread_count"),
            "html_url": discussion.get("html_url"),
            "course_name": discussion.get("course_name")
        })
    
    return discussion_list

@mcp.tool(description="Get upcoming quizzes from your courses.")
async def get_quizzes(
    canvas_url: str,
    api_token: str,
    course_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    if course_id:
        quizzes = await canvas.get(f"courses/{course_id}/quizzes")
    else:
        courses = await canvas.get("courses", {"enrollment_state": "active"})
        all_quizzes = []
        for course in courses:
            try:
                course_quizzes = await canvas.get(f"courses/{course.get('id')}/quizzes")
                for quiz in course_quizzes:
                    quiz["course_name"] = course.get("name")
                    quiz["course_id"] = course.get("id")
                    all_quizzes.append(quiz)
            except:
                continue
        quizzes = all_quizzes
    
    quiz_list = []
    for quiz in quizzes:
        quiz_list.append({
            "id": quiz.get("id"),
            "title": quiz.get("title"),
            "description": quiz.get("description"),
            "due_at": quiz.get("due_at"),
            "lock_at": quiz.get("lock_at"),
            "unlock_at": quiz.get("unlock_at"),
            "points_possible": quiz.get("points_possible"),
            "question_count": quiz.get("question_count"),
            "time_limit": quiz.get("time_limit"),
            "html_url": quiz.get("html_url"),
            "course_name": quiz.get("course_name"),
            "course_id": quiz.get("course_id")
        })
    
    return quiz_list

@mcp.tool(description="Get your Canvas notifications.")
async def get_notifications(
    canvas_url: str,
    api_token: str
) -> List[Dict[str, Any]]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "per_page": 50
    }
    
    try:
        activity_stream = await canvas.get("users/self/activity_stream", params)
        
        notifications = []
        for item in activity_stream:
            notifications.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "message": item.get("message"),
                "type": item.get("type"),
                "created_at": item.get("created_at"),
                "html_url": item.get("html_url"),
                "context_type": item.get("context_type")
            })
        
        return notifications
    except:
        return []

@mcp.tool(description="Get the syllabus for a specific course.")
async def get_course_syllabus(
    canvas_url: str,
    api_token: str,
    course_id: int
) -> Dict[str, Any]:
    canvas = CanvasAPI(canvas_url, api_token)
    
    params = {
        "include[]": ["syllabus_body"]
    }
    
    course = await canvas.get(f"courses/{course_id}", params)
    
    return {
        "course_id": course.get("id"),
        "course_name": course.get("name"),
        "course_code": course.get("course_code"),
        "syllabus_body": course.get("syllabus_body"),
        "start_at": course.get("start_at"),
        "end_at": course.get("end_at"),
        "time_zone": course.get("time_zone")
    }

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
