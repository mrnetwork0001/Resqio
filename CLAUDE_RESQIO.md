# 🚨 CLAUDE_RESQIO — Persistent Project Context Directive

> **Project Name:** RESQIO  
> **Target Event:** AWS Agents for Humans Hackathon ($40,000 Cash Pool)  
> **Target Track:** Good Neighbor Agents ($5,000 Golden Agent Track / $10,000 Grand Prize)  
> **Submission Deadline:** September 15, 2026 @ 1:00 am GMT+1  
> **Primary Framework:** Strands Agents SDK (Python)  
> **Score Multiplier:** Amazon Bedrock AgentCore deployment  

---

## 📌 Core Directives for Resqio Development

1. **Master Spec Source of Truth:**  
   Always consult and align with [RESQIO_PROJECT_SPEC.md](file:///Users/mrnetwork/Test-It/RESQIO_PROJECT_SPEC.md).

2. **Technical Architecture Guidelines:**
   - **Strands Agents SDK (Mandatory):** Multi-agent coordination (`strands_grid_monitor.py`, `strands_resource_matcher.py`, `strands_volunteer_router.py`) must use the open-source **Strands Agents SDK**.
   - **AgentCore Deployment (Recommended):** Deploy background polling daemons to Amazon Bedrock AgentCore for maximum technical scoring.
   - **Background Autonomy Pattern:** Resqio runs continuously in the background and ONLY sends notifications (via WhatsApp/SMS) when a volunteer match requires human approval.

3. **Submission Requirements Checklist:**
   - Public GitHub repository with Apache 2.0 or MIT License.
   - `README.md` + Architecture Diagram.
   - Demo video (max 5 minutes, real human voiceover).
   - AWS Builder ID + (Optional) `builder.aws.com` journey post.

4. **Repository Key Files:**
   - Master Blueprint: `RESQIO_PROJECT_SPEC.md`
   - Directive File: `CLAUDE_RESQIO.md`
   - Skill Instructions: `.agents/skills/resqio-aws/SKILL.md`
