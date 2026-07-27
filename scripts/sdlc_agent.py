import os
import json
import logging
import asyncio
import urllib.request
import aiocron
import datetime
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.triggers import TriggerContext

logging.basicConfig(level=logging.INFO)

POSTHOG_API_KEY = os.environ.get('POSTHOG_API_KEY')
PROJECT_ID = os.environ.get('POSTHOG_PROJECT_ID', '489528')
LINEAR_API_KEY = os.environ.get('LINEAR_API_KEY')

def fetch_telemetry_data(days_back: int = 1) -> str:
    """Fetches the latest telemetry errors from PostHog for the given number of days back.
    
    Returns a JSON string containing the most frequent errors.
    """
    logging.info(f"Fetching telemetry data for the last {days_back} days...")
    q_str = f"""
    SELECT properties.error_category, properties.error_message, count() as n
    FROM events 
    WHERE timestamp >= toStartOfDay(now())-toIntervalDay({days_back}) 
    AND event='tool_executed' 
    AND properties.error_category IN ('InitError', 'ADCExpired', 'IAMError', 'APIError', 'SchemaHallucination')
    GROUP BY properties.error_category, properties.error_message 
    ORDER BY n DESC 
    LIMIT 20
    """

    req = urllib.request.Request(
        f'https://us.posthog.com/api/projects/{PROJECT_ID}/query/',
        data=json.dumps({"query": {"kind": "HogQLQuery", "query": q_str}}).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {POSTHOG_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'ga4-report/1.0'
        }
    )
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        results = data.get('results', [])
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error fetching telemetry: {str(e)}"

def create_linear_issue(title: str, description: str, due_date: str = None) -> str:
    """Creates a new issue in Linear (or logs to a local file if no API key is present) for the human maintainer to review.
    
    Args:
        title: A short summary of the issue (e.g. "Skill Fix: Prevent guessing 'conversions' metric" or "[Validation] SUR-168")
        description: A detailed description of the error data, validation plan, or reasoning.
        due_date: Optional ISO 8601 date string (e.g. '2026-07-30') for scheduling validation tickets.
    """
    if not LINEAR_API_KEY:
        # Fallback to local markdown file if no Linear key is provided
        logging.info("LINEAR_API_KEY not set. Writing issue to local backlog.md")
        with open("backlog.md", "a") as f:
            f.write(f"\n## [DRAFT] {title} (Due: {due_date})\n{description}\n---\n")
        return f"Drafted issue locally to backlog.md: {title}"

    team_id = os.environ.get('LINEAR_TEAM_ID')
    if not team_id:
        return "Error: LINEAR_TEAM_ID environment variable is missing, cannot create Linear issue."

    query = """
    mutation IssueCreate($title: String!, $description: String!, $teamId: String!, $dueDate: TimelessDate) {
      issueCreate(input: {
        title: $title,
        description: $description,
        teamId: $teamId,
        dueDate: $dueDate
      }) {
        success
        issue {
          id
          url
        }
      }
    }
    """
    
    variables = {
        "title": title,
        "description": description,
        "teamId": team_id
    }
    if due_date:
        variables["dueDate"] = due_date

    req = urllib.request.Request(
        'https://api.linear.app/graphql',
        data=json.dumps({"query": query, "variables": variables}).encode('utf-8'),
        headers={
            'Authorization': LINEAR_API_KEY,
            'Content-Type': 'application/json'
        }
    )
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        if data.get('data', {}).get('issueCreate', {}).get('success'):
            url = data['data']['issueCreate']['issue']['url']
            return f"Successfully created Linear issue: {url}"
        return f"Failed to create Linear issue: {data}"
    except Exception as e:
        return f"Exception while creating Linear issue: {str(e)}"

def get_due_validation_tickets() -> str:
    """Fetches unresolved Linear issues titled '[Validation]...' that are due today or earlier."""
    if not LINEAR_API_KEY:
        return "No LINEAR_API_KEY set."
    
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    
    query = """
    query {
      issues(filter: { 
        title: { startsWith: "[Validation]" }
      }) {
        nodes {
          id
          title
          description
          dueDate
          completedAt
          canceledAt
        }
      }
    }
    """
    
    req = urllib.request.Request(
        'https://api.linear.app/graphql',
        data=json.dumps({"query": query}).encode('utf-8'),
        headers={'Authorization': LINEAR_API_KEY, 'Content-Type': 'application/json'}
    )
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        nodes = data.get('data', {}).get('issues', {}).get('nodes', [])
        
        due_tickets = []
        for n in nodes:
            if n.get('completedAt') or n.get('canceledAt'):
                continue
            due_date = n.get('dueDate')
            if due_date and due_date <= today:
                due_tickets.append({
                    "id": n.get('id'),
                    "title": n.get('title'),
                    "description": n.get('description')
                })
        return json.dumps(due_tickets, indent=2)
    except Exception as e:
        return f"Exception while fetching due validation tickets: {str(e)}"

def add_linear_comment(issue_id: str, body: str) -> str:
    """Adds a comment to an existing Linear issue by its ID (e.g. 'SUR-168')."""
    if not LINEAR_API_KEY:
        return f"Local fallback: Commented on {issue_id}: {body}"
        
    query = """
    mutation CommentCreate($issueId: String!, $body: String!) {
      commentCreate(input: { issueId: $issueId, body: $body }) {
        success
      }
    }
    """
    variables = {"issueId": issue_id, "body": body}
    
    req = urllib.request.Request(
        'https://api.linear.app/graphql',
        data=json.dumps({"query": query, "variables": variables}).encode('utf-8'),
        headers={'Authorization': LINEAR_API_KEY, 'Content-Type': 'application/json'}
    )
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        success = data.get('data', {}).get('commentCreate', {}).get('success')
        return f"Successfully commented on {issue_id}" if success else f"Failed: {data}"
    except Exception as e:
        return f"Exception while commenting on Linear issue: {str(e)}"

def close_linear_issue(issue_id: str) -> str:
    """Marks a Linear issue as 'Done' (Completed)."""
    if not LINEAR_API_KEY:
        return f"Local fallback: Closed {issue_id}"
        
    state_query = """
    query {
      workflowStates {
        nodes {
          id
          type
        }
      }
    }
    """
    req_state = urllib.request.Request(
        'https://api.linear.app/graphql',
        data=json.dumps({"query": state_query}).encode('utf-8'),
        headers={'Authorization': LINEAR_API_KEY, 'Content-Type': 'application/json'}
    )
    
    try:
        res_state = urllib.request.urlopen(req_state)
        state_data = json.loads(res_state.read().decode('utf-8'))
        done_state_id = None
        for state in state_data.get('data', {}).get('workflowStates', {}).get('nodes', []):
            if state.get('type') == 'completed':
                done_state_id = state.get('id')
                break
                
        if not done_state_id:
            return "Error: Could not find a 'completed' workflow state."
            
        update_query = """
        mutation IssueUpdate($id: String!, $stateId: String!) {
          issueUpdate(id: $id, input: { stateId: $stateId }) {
            success
          }
        }
        """
        req_update = urllib.request.Request(
            'https://api.linear.app/graphql',
            data=json.dumps({"query": update_query, "variables": {"id": issue_id, "stateId": done_state_id}}).encode('utf-8'),
            headers={'Authorization': LINEAR_API_KEY, 'Content-Type': 'application/json'}
        )
        res_update = urllib.request.urlopen(req_update)
        update_data = json.loads(res_update.read().decode('utf-8'))
        success = update_data.get('data', {}).get('issueUpdate', {}).get('success')
        return f"Successfully closed {issue_id}" if success else f"Failed: {update_data}"
    except Exception as e:
        return f"Exception while closing Linear issue: {str(e)}"

def create_cron_trigger(cron_expr: str):
    """Creates a trigger that runs on a cron schedule."""
    async def trigger_fn(ctx: TriggerContext):
        logging.info(f"Cron trigger active for: {cron_expr}")
        queue = asyncio.Queue()
        
        @aiocron.crontab(cron_expr)
        async def on_cron():
            await queue.put(True)

        while True:
            await queue.get()
            logging.info("Cron triggered! Sending instruction to agent.")
            await ctx.send(
                "Good morning! It is 9:00 AM. Please run the 3-stage SDLC loop:\n"
                "1. REPORT: Fetch the telemetry data for the last 1 day. Ignore all environmental 'SETUP BLOCKED' errors. "
                "For any real bugs or SchemaHallucinations, draft a Linear issue. You MUST embed a 'Validation Plan' in the ticket description that explicitly defines the Primary Metric, Nth-Order Metrics, and the Time Horizon required for future validation.\n"
                "2. SCHEDULE: Check recently closed bugs (e.g. from the past 24-48 hours). For each, schedule a `[Validation]` ticket by reading its Validation Plan Time Horizon, and set the dueDate accordingly using create_linear_issue.\n"
                "3. VALIDATE: Use `get_due_validation_tickets` to fetch `[Validation]` tickets due today. Execute their Validation Plan queries, comment the impact assessment onto the original parent bug ticket using `add_linear_comment`, and then close the `[Validation]` ticket using `close_linear_issue`."
            )
            
    return trigger_fn


async def main():
    config = LocalAgentConfig(
        system_instructions=(
            "You are the Telemetry-Driven AI SDLC Analyst for the google-analytics-mcp project. "
            "Your job is to run autonomously and continuously improve the agent by analyzing daily PostHog telemetry and tracking validation impact. "
            "CRITICAL RULES: "
            "1. You MUST ignore any errors containing '[SETUP BLOCKED]' (e.g. InitError, ADCExpired, IAMError). These are environmental and cannot be fixed in code. "
            "2. You MUST focus entirely on 'SchemaHallucination' errors (LLM guessing bad fields) and actual Python unhandled exceptions (e.g., 'APIError: can only concatenate str to str'). "
            "3. For every actionable new bug, draft a Linear issue. YOU MUST embed a 'Validation Plan' inside the ticket description stating the Primary Metric (the error disappearing), Nth-Order Metrics (what else might break), and Time Horizon (how many days to wait for stats significance). "
            "4. When bugs are closed, schedule a `[Validation]` ticket assigned to yourself, setting its `dueDate` based on the defined Time Horizon. "
            "5. Execute due `[Validation]` tickets by checking telemetry over the time horizon, commenting the impact on the parent ticket, and closing the validation ticket. "
            "Do not attempt to fix the code yourself until the human approves the Linear issue."
        ),
        tools=[fetch_telemetry_data, create_linear_issue, get_due_validation_tickets, add_linear_comment, close_linear_issue],
        triggers=[create_cron_trigger("0 9 * * *")]  # Runs every day at 9:00 AM
    )

    logging.info("Starting SDLC Agent. It will wait for 9:00 AM everyday to execute.")
    async with Agent(config) as agent:
        # Keep the event loop running forever so the cron trigger remains active
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
