import os
import json
import gradio as gr
from dotenv import load_dotenv
from gemma_engine import GemmaEngine
from database import (
    insert_report, update_report_analysis, get_report,
    get_all_reports, get_stats, search_reports,
    update_report_status
)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY", "")
gemma = GemmaEngine(api_key) if api_key else None

SEVERITY_COLORS = {
    "Critical": "#dc2626",
    "High": "#ea580c",
    "Medium": "#ca8a04",
    "Low": "#16a34a",
    "Pending": "#6b7280",
}

SEVERITY_BADGE = {
    "Critical": '<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:4px;font-weight:bold">CRITICAL</span>',
    "High": '<span style="background:#ea580c;color:white;padding:2px 8px;border-radius:4px;font-weight:bold">HIGH</span>',
    "Medium": '<span style="background:#ca8a04;color:white;padding:2px 8px;border-radius:4px;font-weight:bold">MEDIUM</span>',
    "Low": '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:4px;font-weight:bold">LOW</span>',
    "Pending": '<span style="background:#6b7280;color:white;padding:2px 8px;border-radius:4px">PENDING</span>',
}


def submit_report(title, reporter, org, description, steps, language):
    if not title or not description:
        return gr.update(value="Title and description are required."), "", get_stats_display()

    report_id = insert_report(title, reporter, org, description, steps, language)

    if not gemma:
        return (
            f"Report #{report_id} saved. Add GOOGLE_API_KEY for AI analysis.",
            "",
            get_stats_display()
        )

    full_text = f"{title}\n\n{description}"
    if steps:
        full_text += f"\n\nSteps to reproduce:\n{steps}"

    try:
        analysis = gemma.full_analysis(full_text)
        update_report_analysis(report_id, analysis)
        result = format_analysis(analysis)
        return result, f"Report #{report_id} submitted and analyzed.", get_stats_display()
    except Exception as e:
        return f"Report #{report_id} saved. Analysis error: {str(e)}", "", get_stats_display()


def format_analysis(analysis: dict) -> str:
    severity = analysis.get("severity", {})
    category = analysis.get("category", {})
    fix = analysis.get("fix", {})
    risk = analysis.get("risk", {})
    translation = analysis.get("translation", {})

    output = "# Gemma 4 AI Analysis\n\n"

    if translation.get("confidence"):
        output += f"**Language Detection:** {translation.get('confidence')} confidence\n\n"

    sev = severity.get("severity", "Unknown")
    badge = SEVERITY_BADGE.get(sev, "")
    output += f"## Severity: {badge}\n"
    output += f"**Score:** {severity.get('score', 'N/A')}/10\n"
    output += f"**Reasoning:** {severity.get('reasoning', 'N/A')}\n\n"

    output += f"## Category\n"
    output += f"**Type:** {category.get('primary_category', 'N/A')}\n"
    output += f"**OWASP Top 10:** {category.get('owasp_top10', 'N/A')}\n"
    output += f"**Attack Vector:** {category.get('attack_vector', 'N/A')}\n\n"

    output += f"## Risk Assessment\n"
    output += f"**Risk Score:** {risk.get('risk_score', 'N/A')}/100\n"
    output += f"**Exploitability:** {risk.get('exploitability', 'N/A')}\n"
    output += f"**Business Impact:** {risk.get('business_impact', 'N/A')}\n"
    output += f"**Urgency:** {risk.get('remediation_urgency', 'N/A')}\n\n"

    output += f"## Suggested Fix\n"
    output += f"**Root Cause:** {fix.get('root_cause', 'N/A')}\n\n"
    code = fix.get("code_fix", "N/A")
    output += f"**Code Fix:**\n```\n{code}\n```\n\n"
    practices = fix.get("best_practices", [])
    if practices:
        output += "**Best Practices:**\n"
        for p in practices:
            output += f"- {p}\n"
    output += f"\n**Testing:** {fix.get('testing', 'N/A')}\n"

    return output


def get_stats_display() -> str:
    stats = get_stats()
    return f"""
    | Metric | Count |
    |--------|-------|
    | Total Reports | {stats['total']} |
    | Critical | {stats['critical']} |
    | High | {stats['high']} |
    | Medium | {stats['medium']} |
    | Low | {stats['low']} |
    | Open | {stats['open']} |
    """


def get_dashboard():
    reports = get_all_reports()
    if not reports:
        return "No reports yet. Submit one to get started!"

    html = '<div style="font-family:sans-serif">'

    for r in reports:
        sev = r.get("severity", "Pending")
        badge = SEVERITY_BADGE.get(sev, "")
        status = r.get("status", "Open")
        status_color = "#16a34a" if status == "Open" else "#6b7280"

        html += f"""
        <div style="border:1px solid #333;border-radius:8px;padding:16px;margin:8px 0;background:#1a1a2e">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <h3 style="margin:0;color:#e0e0e0">#{r['id']} - {r['title']}</h3>
                <div>{badge} <span style="background:{status_color};color:white;padding:2px 6px;border-radius:4px;font-size:12px">{status}</span></div>
            </div>
            <p style="color:#aaa;margin:8px 0"><strong>Reporter:</strong> {r['reporter']} | <strong>Org:</strong> {r.get('organization', 'N/A')} | <strong>Category:</strong> {r.get('category', 'N/A')}</p>
            <p style="color:#ccc;margin:4px 0">{r['description'][:200]}{'...' if len(r['description']) > 200 else ''}</p>
            <p style="color:#888;font-size:12px">Risk Score: {r.get('risk_score', 0)}/100 | OWASP: {r.get('owasp_top10', 'N/A')}</p>
        </div>
        """

    html += "</div>"
    return html


def view_report(report_id):
    r = get_report(int(report_id))
    if not r:
        return "Report not found."

    output = f"# Report #{r['id']}\n\n"
    output += f"**Title:** {r['title']}\n"
    output += f"**Reporter:** {r['reporter']}\n"
    output += f"**Organization:** {r.get('organization', 'N/A')}\n"
    output += f"**Status:** {r['status']}\n"
    output += f"**Created:** {r['created_at']}\n\n"
    output += f"## Description\n{r['description']}\n\n"

    if r.get("steps_to_reproduce"):
        output += f"## Steps to Reproduce\n{r['steps_to_reproduce']}\n\n"

    fix = json.loads(r.get("fix_suggestion", "{}"))
    if fix:
        output += format_analysis({
            "severity": {"severity": r["severity"], "score": r["severity_score"]},
            "category": {"primary_category": r["category"], "owasp_top10": r["owasp_top10"]},
            "fix": fix,
            "risk": json.loads(r.get("risk_analysis", "{}")),
        })

    return output


def search_dashboard(query):
    reports = search_reports(query)
    if not reports:
        return "No reports found."

    html = '<div style="font-family:sans-serif">'
    for r in reports:
        sev = r.get("severity", "Pending")
        badge = SEVERITY_BADGE.get(sev, "")
        html += f"""
        <div style="border:1px solid #333;border-radius:8px;padding:12px;margin:6px 0;background:#1a1a2e">
            <h4 style="margin:0;color:#e0e0e0">#{r['id']} - {r['title']} {badge}</h4>
            <p style="color:#aaa;font-size:13px;margin:4px 0">{r.get('category', 'N/A')} | {r.get('reporter', 'N/A')}</p>
        </div>
        """
    html += "</div>"
    return html


CUSTOM_CSS = """
.main-title { text-align:center; color:#e0e0e0; margin-bottom:0 }
.subtitle { text-align:center; color:#aaa; margin-top:0 }
"""

with gr.Blocks(title="BugHunter PK - AI-Powered Bug Bounty Platform") as app:
    gr.Markdown("# BugHunter PK", elem_classes="main-title")
    gr.Markdown("AI-Powered Bug Bounty Platform for Pakistan | Powered by Gemma 4", elem_classes="subtitle")

    with gr.Tabs():
        with gr.Tab("Submit Report"):
            with gr.Row():
                with gr.Column(scale=1):
                    title = gr.Textbox(label="Vulnerability Title", placeholder="e.g., SQL Injection in Login Form")
                    reporter = gr.Textbox(label="Your Name / Handle", placeholder="e.g., security_researcher")
                    org = gr.Dropdown(
                        label="Target Organization",
                        choices=[
                            "University of the Punjab",
                            "Lahore University of Management Sciences",
                            "COMSATS University",
                            "National University of Sciences & Technology",
                            "LUMS",
                            "Fast-NUCES",
                            "IBA Karachi",
                            "Habib University",
                            "Jazz (PTCL)",
                            "Telenor Pakistan",
                            "Zong",
                            "Daraz",
                            "FoodPanda",
                            "Other"
                        ],
                        allow_custom_value=True,
                    )
                    language = gr.Radio(
                        label="Report Language",
                        choices=["English", "Urdu"],
                        value="English",
                    )

                with gr.Column(scale=2):
                    description = gr.Textbox(
                        label="Vulnerability Description",
                        lines=5,
                        placeholder="Describe the vulnerability in detail... (can be in Urdu or English)",
                    )
                    steps = gr.Textbox(
                        label="Steps to Reproduce",
                        lines=4,
                        placeholder="1. Go to login page\n2. Enter ' OR 1=1 -- in username\n3. Click login\n4. Access granted without credentials",
                    )

            submit_btn = gr.Button("Submit & Analyze with Gemma 4", variant="primary", size="lg")
            submit_status = gr.Markdown()
            analysis_output = gr.Markdown()
            stats_after_submit = gr.Markdown(value=get_stats_display())

            submit_btn.click(
                fn=submit_report,
                inputs=[title, reporter, org, description, steps, language],
                outputs=[analysis_output, submit_status, stats_after_submit],
            )

        with gr.Tab("Dashboard"):
            gr.Markdown("## Live Dashboard")
            stats_display = gr.Markdown(value=get_stats_display())
            dashboard_html = gr.HTML(value=get_dashboard())
            refresh_btn = gr.Button("Refresh Dashboard", variant="secondary")
            refresh_btn.click(fn=get_dashboard, outputs=[dashboard_html])

        with gr.Tab("View Report"):
            report_id_input = gr.Number(label="Report ID", value=1, precision=0)
            view_btn = gr.Button("Load Report", variant="secondary")
            report_view = gr.Markdown()
            view_btn.click(fn=view_report, inputs=[report_id_input], outputs=[report_view])

        with gr.Tab("Search"):
            search_input = gr.Textbox(label="Search", placeholder="Search by title, description, or category...")
            search_btn = gr.Button("Search", variant="secondary")
            search_results = gr.HTML()
            search_btn.click(fn=search_dashboard, inputs=[search_input], outputs=[search_results])


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=True, theme=gr.themes.Soft(), css=CUSTOM_CSS)
