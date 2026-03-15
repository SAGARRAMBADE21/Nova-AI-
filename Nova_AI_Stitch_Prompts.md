#Nova AI — Google Stitch Design Prompts
# All 6 pages ready to paste into stitch.withgoogle.com
# Use one prompt per page generation session in Stitch
# 

---

## HOW TO USE
1. Go to https://stitch.withgoogle.com
2. Sign in with Google → Click "New Project"
3. Copy ONE prompt below → paste into Stitch → Generate
4. Export as HTML → save file
5. Repeat for each page

---

## PAGE ORDER (follow this order)
0. Landing — Public marketing page (anyone can visit)
1. Onboard — Company registration (owner only, one time)
2. Login — All users login here (admin + employees)
3. Register — New employees set password (one time after invite)
4. Chat — Main interface for all logged-in users
5. Dashboard — Admin only

---
---

# 
# PAGE 0 — LANDING PAGE (paste this into Stitch)
# 

Design a public marketing landing page for "Nova AI — Enterprise AI Assistant".
This is the first page anyone sees before signing up or logging in.
It should explain whatNova AI is, who it's for, and drive companies to create a workspace.

Full page layout with these sections top to bottom:


SECTION 1 — NAVIGATION BAR (top, sticky):

- Left: "Nova AI" logo with app name
- Center links:
 "Features" | "How It Works" | "Security" | "Pricing"
- Two buttons at far right:
 "Sign In" (outlined button)
 "Create Workspace" (filled primary button) → goes to onboard.html

LOGIN DROPDOWN PANEL (opens when "Sign In" button is clicked):
A dropdown/popover panel that appears directly below the "Sign In" button in the navbar.
Panel stays open until user clicks outside or presses X.
The panel contains a compact inline login form:

 Panel header:
 - Title: "Sign In toNova AI"
 - Small "x" close button at top right of panel

 Form fields inside panel:
 - Company Join Code input (compact)
 Placeholder: "Company join code"
 Auto-uppercase as user types
 - Email Address input (compact)
 Placeholder: "Email address"
 - Password input (compact, show/hide toggle icon inside field)
 Placeholder: "Password"
 - "Remember me" checkbox (small, inline)

 Submit button: "Sign In" (full width inside panel)
 Loading state: spinner, button disabled

 On success:
 - Panel shows brief "Welcome back!" confirmation
 - Auto-redirect based on role:
 admin → dashboard.html
 others → chat.html

 Error message area below button:
 - "Invalid join code, email, or password"
 - "Not registered yet? Register first"

 Two small text links below error area:
 - "First time? Register your account" → register.html
 - "New company? Create a workspace" → onboard.html

 Divider line
 Bottom note inside panel:
 "Your session expires after 12 hours"



SECTION 2 — HERO:

Centered layout:
- Badge above heading: "Powered by GPT-4 + RAG"
- Large main heading (two lines):
 "Your Company's Private"
 "AI Assistant"
- Subheading below:
 "Nova AI gives your entire team — from employees to managers — a secure,
 private AI assistant trained on your company's own documents and data.
 No hallucinations. No data leaks. Just accurate, role-aware answers."
- Two CTA buttons side by side:
 Primary: "Create Your Workspace — Free" → goes to onboard.html
 Secondary: "See How It Works" → scrolls to how it works section
- Trust line below buttons:
 "No credit card required · Set up in 2 minutes · Your data stays private"
- Hero illustration below (or screenshot mockup of the chat interface)


SECTION 3 — SOCIAL PROOF BAR:

Full-width bar with label: "Trusted by teams at"
Row of 5–6 placeholder company logo boxes (greyscale)


SECTION 4 — FEATURES (id: features):

Section heading: "Everything your team needs"
Subheading: "One AI assistant that works across every role in your company"

6 feature cards in a 3x2 grid. Each card has: icon, title, description.

 Card 1: icon
 "Role-Based Access Control"
 "Employees see public documents only. Managers and admins access confidential data.
 Every answer is scoped to what the user is allowed to see."

 Card 2: icon
 "Trained on Your Documents"
 "Upload PDFs, Word docs, Excel files, CSVs and more.
 ARIA answers questions using only your company's actual data — never guesses."

 Card 3: icon
 "Google Workspace Integrations"
 "Send emails, create calendar events, upload to Drive, generate Meet links,
 create Docs and update Sheets — all from one chat interface."

 Card 4: icon
 "3-Layer Security with Lakera Guard"
 "Every user input, document, and AI response is scanned for prompt injections,
 jailbreaks, and data leaks before anything is processed or returned."

 Card 5: icon
 "Human-in-the-Loop Escalation"
 "High-risk or low-confidence queries are automatically escalated
 to a human reviewer — with SLA tracking and audit trail."

 Card 6: icon
 "Admin Dashboard & Analytics"
 "Manage users, upload documents, configure email, and track
 usage, latency, security blocks, and tool invocations in real time."


SECTION 5 — HOW IT WORKS (id: how-it-works):

Section heading: "Up and running in minutes"

4 steps shown as a horizontal numbered flow or vertical timeline:

 Step 1: "Create Your Workspace"
 "Register your company. You instantly get a unique Join Code for your team."

 Step 2: "Upload Your Documents"
 "Upload company PDFs, policies, reports, and files to the knowledge base.
 Mark each as Public (all staff) or Confidential (managers only)."

 Step 3: "Invite Your Team"
 "Add employees, managers, and team leads by email directly from your dashboard.
 They receive an invite email with the join code and registration link."

 Step 4: "Your Team Starts Using ARIA"
 "Employees log in and immediately get accurate answers from your company's data.
 They can also trigger Google Workspace actions directly from the chat."


SECTION 6 — SECURITY (id: security):

Section heading: "Built security-first — not as an afterthought"

2-column layout:
Left column (text):
 "Nova AI applies security at 3 checkpoints on every single request:"
 Three feature rows with checkmark icons:
 Input scan — every user message is scanned before reaching the AI
 Document scan — retrieved documents are checked before being injected into the prompt
 Output scan — every AI response is checked before being sent to the user
 "Powered by Lakera Guard — the industry standard for LLM security."

Right column: visual diagram showing the 3-checkpoint flow:
 [User Input] → [Lakera Scan] → [RAG Retrieval] → [Lakera Scan] → [LLM] → [Lakera Scan] → [Response]

Below: 4 compliance badges/icons:
 Role-Based Access | Prompt Injection Protection | PII Redaction | Human-in-the-Loop


SECTION 7 — PRICING (id: pricing):

Section heading: "Simple, transparent pricing"

3 pricing cards side by side:

 Card 1 — Starter (most popular badge):
 Price: "Free"
 Description: "Perfect for small teams getting started"
 Features list:
 Up to 10 users
 100 documents
 Public knowledge base
 Google Workspace integrations
 Basic metrics
 CTA button: "Get Started Free" → goes to onboard.html

 Card 2 — Pro (highlighted as recommended):
 Price: "$49/month"
 Description: "For growing companies that need more"
 Features list:
 Up to 100 users
 Unlimited documents
 Public + Confidential knowledge base
 HITL escalation workflows
 Advanced metrics & audit logs
 Priority support
 CTA button: "Start Pro Trial" → goes to onboard.html

 Card 3 — Enterprise:
 Price: "Custom"
 Description: "For large organizations with custom needs"
 Features list:
 Unlimited users
 Custom data retention
 SSO & advanced security
 Dedicated support
 SLA guarantee
 On-premise deployment option
 CTA button: "Contact Sales"


SECTION 8 — FINAL CTA BANNER:

Full-width centered section:
- Heading: "Give your team an AI assistant that actually knows your company"
- Subtext: "Set up in 2 minutes. No credit card required."
- Large primary button: "Create Your Workspace Free" → goes to onboard.html


FOOTER:

3 columns:
 Column 1: "Nova AI" logo + one-line description
 Column 2: Links — Features, How It Works, Security, Pricing
 Column 3: Links — Create Workspace, Sign In, Register
Bottom bar: " 2025Nova AI. All rights reserved."

---
---

# 
# PAGE 1 — ONBOARD (paste this into Stitch)
# 

Create a company workspace registration page for "Nova AI — Enterprise AI Assistant".
This page is used ONLY ONCE by the company owner to create their company workspace.

Page title: "Create Your Company Workspace"
Subtitle: "Set up your company's private AI assistant"

Progress indicator at top showing 2 steps:
Step 1: "Create Workspace" (active)
Step 2: "Your Join Code" (inactive, activates after success)

STEP 1 FORM (all fields required):
- Company Name input
- Admin Email input (this becomes their login email)
- Password input with show/hide toggle
 Live requirements checklist shown below:
 Minimum 8 characters
 At least one uppercase letter
 At least one number
 Password strength meter: Weak / Fair / Strong / Very Strong
- Confirm Password input (live mismatch validation)
- Checkbox: "I confirm I am authorized to create this workspace"

Submit button: "Create Workspace" (full width, prominent)
Button disabled until all fields valid and checkbox checked.
Loading state text: "Creating your workspace..."

On API success — replace form with STEP 2 card:
- Large green checkmark icon
- Heading: "Your Workspace is Ready!"
- "Company: [Company Name]"
- Section: "Your Company Join Code"
 Large monospace bold display of the join code (e.g. ACMEXK7P12)
 "Copy Code" button with clipboard icon
 Copied confirmation: changes to "Copied!" for 2 seconds
- Important notice box:
 "Share this code with your employees.
 They need it to register and log in toNova AI."
- Pre-written shareable message with its own "Copy Message" button:
 "You have been invited to [Company Name] onNova AI.
 Join Code: [code]
 Register at: [app url]/register"
- What happens next (numbered steps):
 1. Share the join code with your team members
 2. They register using: Join Code + their email + a new password
 3. Log in to your Admin Dashboard to upload documents and manage your team
- Two buttons:
 Primary: "Go to Login" → goes to login.html
 Secondary: "Copy Invite Message" → copies the pre-written message above

Error handling (shown below submit button):
- "Something went wrong — please try again"
- "Company name is already taken"
- Field-level validation error messages

Bottom link (below form):
"Already have a workspace? Sign In" → links to login.html

---
---

# 
# PAGE 2 — LOGIN (paste this into Stitch)
# 

Create a login page for "Nova AI — Enterprise AI Assistant".
This is the single login page for ALL users: admins, managers, team leads, and employees.
Everyone uses the same page — after login, redirect is based on their role.

Page title: "Sign In toNova AI"
Subtitle: "Enter your company credentials to continue"

Login form:
- Company Join Code input (required)
 Placeholder: "Enter your company join code"
 Auto uppercases as user types
 Helper text below: "Find this in your invite email or from your admin"
- Email Address input (required, email type)
- Password input (required) with show/hide password toggle
- "Remember me" checkbox (keeps token for longer session)

Submit button: "Sign In" (full width, prominent)
Loading state: spinner with "Verifying..."

On success:
- Brief toast notification: "Welcome back!"
- Redirect logic (automatic, based on JWT role):
 role = admin → redirect to dashboard.html
 role = manager or team_lead → redirect to chat.html
 role = employee → redirect to chat.html

Error states shown below submit button:
- "Invalid join code, email, or password — please try again"
- "Account not registered yet — you need to set your password first"
 with link "Register here" → goes to register.html
- "Network error — cannot connect toNova AI"

Two secondary links below error area:
1. "First time here? Register your account" → goes to register.html
 (for employees who just received their invite email)
2. "New company? Create a workspace" → goes to onboard.html
 (for company owners who haven't set up yet)

---
---

# 
# PAGE 3 — REGISTER (paste this into Stitch)
# 

Create a first-time account setup page for "Nova AI".
This page is for new employees who received an invite email from their admin.
They use it ONCE to set their password. After this they use the normal login page.

Page title: "Set Up Your Account"
Subtitle: "Complete your registration using your invite details"

Info banner at top of form:
"Check your invite email for your Join Code and
 the email address your admin used to invite you."

Registration form (all fields required):
- Company Join Code input (auto-uppercase as user types)
 Validation: 12 uppercase letters displayed as entered
- Email Address input
 Note: "Must match the email your admin invited"
- New Password input with show/hide toggle
 Live requirements checklist shown below field:
 Minimum 8 characters
 At least one uppercase letter
 At least one number
 Password strength meter: Weak / Fair / Strong / Very Strong
- Confirm Password input
 Live validation: shows "Passwords match " or "Passwords do not match "

Submit button: "Create Account"
Disabled until ALL fields are valid and passwords match.
Loading state: "Setting up your account..."

On success — show confirmation card (replace form):
- " Account Created Successfully"
- "You are joining as: [Role]" (e.g. Employee, Manager)
- "Company: [Company Name]"
- Auto-redirect countdown: "Taking you to login in 3 seconds..."
- "Go to Login Now" link

Error states (below submit button):
- "This email was not invited to this workspace"
- "Invalid join code — check with your admin"
- "Account already exists — please log in instead" with "Sign In" link
- "Passwords do not match"
- "Password does not meet requirements"

Bottom link:
"Already registered? Sign In" → links to login.html

---
---

# 
# PAGE 4 — CHAT INTERFACE (paste this into Stitch)
# 

Design a full-screen AI chat interface for "Nova AI — ARIA"
(Adaptive Retrieval Intelligence Assistant).
Modeled exactly after Manus AI's layout with the connector tools bar.


LEFT SIDEBAR (persistent):

- "Nova AI" logo at very top
- "New Chat" button with + icon
- Conversation history list (below New Chat):
 Each entry: auto-generated title from first message + timestamp
 Hover state: delete icon appears on right side
- Divider line
- Bottom section:
 - Logged-in user's email
 - Role badge: Employee / Manager / Team Lead / Admin
 - If role is admin: "Admin Dashboard" shortcut link
 - "Sign Out" button


MAIN AREA — EMPTY STATE (new or no chat selected):

Centered vertically and horizontally:

Large heading: "What can I do for you?"

Below heading — CHAT INPUT BOX (Manus-style):
Rounded rectangle container with two inner sections:

 TOP SECTION — textarea input:
 - Large multi-line expandable text area
 - Placeholder: "Assign a task or ask anything"
 - Auto-grows in height as user types

 BOTTOM BAR inside the input box (icon row):
 Left side icons (small, icon-button style):
 - "+" button → attach a file (to upload/ingest a document)
 - Plug/connector icon → opens Connectors panel modal
 - Puzzle piece icon → opens tool action selector

 Right side icons:
 - Pause/stop button (to stop AI response mid-generation)
 - Microphone icon (voice input, UI placeholder)
 - Send button (arrow-up icon)
 Active state: colored/prominent when text is entered
 Inactive state: grayed out when input is empty

BELOW THE INPUT BOX — Connector status bar:
A thin bar directly beneath the input box showing:
 Left side: plug icon + text "Connect your tools toNova AI"
 (changes to "6 tools connected" when all connected)
 Right side: row of 6 small circular tool icons:
 Gmail icon | Google Calendar icon | Google Drive icon |
 Google Docs icon | Google Sheets icon | Google Meet icon
 Colored = connected, gray = not connected
 Each icon clickable → opens Connectors panel
 Far right: "x" to dismiss bar

Below the connector bar — 4 suggestion chips:
"What is our leave policy?"
"Summarize the Q3 financial report"
"Who do I contact for IT support?"
"Draft a follow-up email to the HR team"


CONNECTORS PANEL (modal popup):
Opens when user clicks plug icon or any tool icon in the connector bar.

White modal with overlay background.

Modal header:
- Title: "Connectors"
- "x" close button at top right

Three tabs: Apps | Custom API | Custom MCP
(Apps is default active, others show "Coming soon")

Search bar (full width inside modal body)

Under Apps tab:
Section label: "Google Workspace"
6 tool cards in 2-column grid. Each card:
 Tool icon (colored) | Tool name | One-line description | Connect or Connected button

 Card 1: Gmail "M" icon
 "Gmail"
 "Send emails, draft replies, and manage email threads directly from chat"
 Button: "Connect" → changes to "Connected " after linking

 Card 2: Google Drive triangle icon
 "Google Drive"
 "Upload files, share folders, and manage company documents"
 Button: "Connect" / "Connected "

 Card 3: Google Docs page icon
 "Google Docs"
 "Create new documents and edit existing ones from chat"
 Button: "Connect" / "Connected "

 Card 4: Google Sheets grid icon
 "Google Sheets"
 "Push data, update rows, and log records to spreadsheets"
 Button: "Connect" / "Connected "

 Card 5: Google Calendar icon
 "Google Calendar"
 "Create events, set reminders, and invite team members"
 Button: "Connect" / "Connected "

 Card 6: Google Meet video icon
 "Google Meet"
 "Generate video call links and schedule meetings"
 Button: "Connect" / "Connected "

On "Connect" click:
 - Card shows: " [Tool] connected — ARIA can now use this on your behalf"
 - Button becomes "Connected " in green
 - Corresponding icon in connector bar becomes colored/active

Custom API tab: "Coming soon — connect any REST API endpoint" (empty state)
Custom MCP tab: "Coming soon — connect Model Context Protocol tools" (empty state)


ACTIVE CHAT STATE (after first message sent):

Layout shifts:
- Messages fill top 80% of screen (scrollable)
- Input box moves to bottom of screen (fixed)
- Connector bar stays just below input box at bottom

Top bar appears above messages:
- "ARIA — Enterprise AI Assistant"
- "[Company Name] Workspace"
- Access level shown: "Access: Public documents only"
 or "Access: Public + Confidential documents" (for manager/admin)

User message (right-aligned):
- Shows user's text

ARIA response card (left-aligned):
During generation: animated typing dots
After response — full card with:
 a) Answer text (formatted, supports bullet points, headers)
 b) Sources section: "Sources:" label + clickable chips
 [HR Policy v2.1] [Employee Handbook] [Web Search]
 c) Confidence line:
 "Confidence: HIGH" in green
 "Confidence: MEDIUM" in yellow
 "Confidence: LOW" in red + "(Human verification recommended)"
 d) Tool Actions section (shown when tools were triggered by ARIA):
 Each action on its own line:
 [Gmail icon] Email sent to hr@acme.com → "Open Gmail" link
 [Calendar icon] Event 'Team Meeting' created Friday 3PM → "View" link
 [Drive icon] Upload failed → "Retry" button
 e) "Next Step:" in italic (ARIA's follow-up suggestion)
 f) Bottom action row:
 "Copy" | [thumbs up] | [thumbs down] | "Run a tool" button (opens Connectors panel)

Tool confirmation flow (before ARIA executes a tool):
ARIA shows: "I will use [Tool] for this. Please review before I proceed:"
Preview card: shows exactly what action will be taken
Two buttons: "Confirm" | "Cancel"
Note: "This action cannot be undone"

After confirmation:
Progress: "Executing via [Tool]..."
Result shown inline in response card.

HITL escalation banner (shown conditionally on ARIA response):
"Warning: This action requires manager approval before executing.
 Request ID: [id] | Your manager has been notified within 30 minutes."
Yellow/amber warning band.

Tool not connected state (when ARIA tries to use a tool that isn't linked):
ARIA shows: "Warning: Gmail is not connected. Connect it to use this feature."
Inline "Connect Gmail" button inside the response card.
Clicking it opens the Connectors panel.

Role restriction state (if employee tries to use a restricted tool):
"Your current role (Employee) cannot use [Tool].
 Contact your admin to change your permissions."

Session expired state:
Full screen overlay: "Your session has expired — please sign in again"
"Sign In" button

---
---

# 
# PAGE 5 — ADMIN DASHBOARD (paste this into Stitch)
# 

Design a full-screen admin dashboard for "Nova AI".
Only users with the admin role see this page after login.
Full sidebar + tabbed main content area layout.


LEFT SIDEBAR (persistent):

- "Nova AI" logo at top
- Navigation items (clicking each switches main content):
 1. Overview (home icon) — default active
 2. Users (people icon)
 3. Documents (file icon)
 4. Email Settings (mail icon)
 5. Metrics (chart icon)
- Divider
- Bottom:
 - Admin email
 - "Admin" role badge
 - "Go to Chat" link (admin can also use ARIA chat)
 - "Sign Out" button


TAB 1: OVERVIEW (default view):

4 metric stat cards in a row:
- "Total Users" — count number + breakdown text "X employees, X managers, X team leads"
- "Documents Ingested" — count + "X public, X confidential"
- "Active Sessions" — live count of users currently using ARIA
- "Avg Response Time" — number in milliseconds

Recent Activity feed (below cards):
Label: "Recent Activity"
Timeline list of last 10 events:
 "John invited as Employee — 2 hours ago"
 "Q3_Report.pdf ingested (Confidential) — 5 hours ago"
 "Maria registered and activated account — Yesterday"
 "HITL escalation: salary query — 2 days ago"


TAB 2: USERS:

Section heading: "Team Members"
Total count badge: "6 members"

INVITE NEW USER form at top:
- Email Address input
- Role dropdown: Employee / Manager / Team Lead
 (Admin is not in dropdown — admin created via Onboarding only)
- "Send Invite" button
- On success: green confirmation box:
 " Invite sent to john@acme.com
 They will receive an email with the join code and registration instructions."
- On error:
 "This email is already a member of this workspace"

Search and filter bar (above users table):
- Search by email input
- Filter by role dropdown: All / Employee / Manager / Team Lead
- Filter by status: All / Active / Invited

Users table with columns:
Email | Role (badge) | Status | Date Added | Action

 Role badge styles:
 Employee = gray badge
 Manager = blue badge
 Team Lead = purple badge

 Status badge:
 Active = green ("registered and can log in")
 Invited = yellow ("email sent, not registered yet")

 Action column:
 "Remove" button → shows confirmation dialog:
 "Are you sure you want to remove [email] from this workspace?
 This cannot be undone."
 Confirm / Cancel buttons in dialog.


TAB 3: DOCUMENTS:

Section heading: "Knowledge Base"

UPLOAD DOCUMENT panel at top:
- Drag-and-drop file upload area
 Center text: "Drag & drop files here or click to browse"
 Below: "Supported formats: PDF, DOCX, XLSX, CSV, TXT, JSON, XML, MD"
 After file selected: show filename + file size
- Category text input (e.g. HR, Finance, Legal, IT, Compliance)
- Database selection as two radio buttons:
 Public Database
 Description: "Accessible to all employees, managers, and admins"
 Confidential Database
 Description: "Accessible to managers and admins only — hidden from employees"
- "Upload & Ingest" button (full width)
- Progress bar during upload and ingestion
- On success: green result card:
  "Success: HR_Policy_2024.pdf ingested successfully
  14 document chunks indexed into Public database
  Category: HR"
- On Lakera security block: red result card:
  "Blocked: Document blocked by security scan
  This document was flagged and not ingested.
  Reason: contains restricted or sensitive content"
- On unsupported format error:
  "Error: Unsupported file format. Please use PDF, DOCX, XLSX, CSV, TXT, JSON, XML, or MD"

INGESTED DOCUMENTS table below (read-only):
Columns: Filename | Category | Database | Chunks | Uploaded By | Date Ingested


TAB 4: EMAIL SETTINGS:

Section heading: "Email Configuration"
Purpose text:
"When you invite team members,Nova AI will send them an invite email
 FROM your Gmail account with the join code and registration instructions."

Current status card (shown at top):
If configured: "Configured: Email configured — invites will be sent from admin@gmail.com"
If not configured: "Not configured: Email not configured — invite emails will not be sent to new users"

Setup guide (expandable/collapsible section):
Title: "How to get your Gmail App Password"
Steps shown as numbered list:
 Step 1: Go to myaccount.google.com
 Step 2: Click Security → Enable 2-Step Verification (if not already)
 Step 3: Go to App Passwords
 Step 4: Create one named "Nova AI" and copy the 16-character password
 Step 5: Paste it below in the App Password field

Configuration form:
- Gmail Address input
- App Password input (masked by default, show/hide toggle)
 Validation: exactly 16 non-space characters
 Helper text: "The 16-character password you got from Google App Passwords"
- "Save Email Settings" button
- On success: "Success: Email settings saved successfully"
- On failure: "Error: Failed — check your Gmail address and App Password"

Test email section (below save button):
- "Send Test Email" button — sends test email to admin's own address
- On success: "Success: Test email delivered to admin@gmail.com — check your inbox"
- On failure: "Error: Test failed — please verify your credentials and try again"


TAB 5: METRICS:

Section heading: "System Performance & Usage"
Date range filter buttons in top right: Today | Last 7 Days | Last 30 Days

Metric cards grid (2 rows of 3):
- "Total Queries" — total number of chat messages sent
- "Total Tokens Used" — total OpenAI tokens consumed
- "Security Blocks" — breakdown: X prompt injection, X PII, X jailbreak attempts
- "Tool Invocations" — total plugin actions triggered
- "HITL Escalations" — times a human reviewer was notified
- "Error Rate" — percentage of failed requests
- "Average Latency" — ms per response

Charts section below cards:
- Queries over time: line chart matching selected date range
- Confidence distribution: pie chart with HIGH / MEDIUM / LOW segments
- Tool usage breakdown: bar chart showing which plugins were used most
- Security events: bar chart showing types of blocks over time

Empty state (if no data yet):
"No data yet — start using ARIA to see metrics here"
```

