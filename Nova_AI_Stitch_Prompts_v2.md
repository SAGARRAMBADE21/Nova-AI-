# -----------------------------------------------------------
# GLOBAL DESIGN SYSTEM � QueryMind (GitBook-Inspired Theme)
# Apply this design system consistently across ALL 6 pages.
# -----------------------------------------------------------

VISUAL INSPIRATION: GitBook.com
The design should feel modern, minimal, clean, and "AI-native" �
exactly like the GitBook website. Light backgrounds, generous white
space, bold charcoal headings, and a vivid orange accent color.

--- COLOR PALETTE ---

  Page backgrounds:
    Primary:   #FFFFFF (pure white) � main page background
    Secondary: #F5F5F5 (very light warm gray) � alternate sections, cards, sidebar

  Typography colors:
    Headings:  #1A1A1A (deep charcoal/near-black)
    Body text: #666666 (medium gray)
    Labels:    #FF5925 (vivid orange) � section labels, badges, highlights

  Accent / Brand:
    Primary:   #FF5925 (orange) � badges, active nav, links, icons
    Hover:     #FF7A47 (lighter orange) � hover states

  Borders & dividers:
    #E5E7EB (very light gray) � card borders, nav separator, input outlines

  Buttons:
    Primary:   background #1A1A1A (near-black), text #FFFFFF, pill-shaped (border-radius: 999px)
    Secondary: background #F5F5F5 (light gray), text #1A1A1A, pill-shaped
    Danger:    background #FEE2E2, text #DC2626, pill-shaped
    Success:   text #16A34A (green)

--- TYPOGRAPHY ---

  Font family: "Inter" (Google Fonts) � all pages

  Sizes:
    Hero heading:    56-64px, weight 800, line-height 1.1, color #1A1A1A
    Section heading: 36-40px, weight 700, color #1A1A1A
    Card title:      20-24px, weight 600, color #1A1A1A
    Body:            16px, weight 400, line-height 1.7, color #666666
    Section label:   11-12px, weight 700, letter-spacing 0.08em, UPPERCASE, color #FF5925
    Caption/helper:  13px, color #9CA3AF

--- SHAPES & SPACING ---

  Border radius:
    Buttons:    999px (fully pill-shaped)
    Cards:      20-28px (large, soft rounded corners)
    Inputs:     12px
    Badges:     999px (pill-shaped)
    Modals:     24px

  Spacing: Generous � sections use 80-120px vertical padding
  Card padding: 28-36px inside
  Max content width: 1200px, centered

--- NAVIGATION BAR ---

  Sticky top bar � height 64px
  Background: rgba(255,255,255,0.92) with backdrop-blur(12px)
  Bottom border: 1px solid #E5E7EB
  Logo: left-aligned, bold charcoal #1A1A1A wordmark
  Nav links: center, color #666666, hover #1A1A1A
  Right side:
    "Sign In" ? ghost/text button, color #1A1A1A
    "Create Workspace" ? primary pill button (black background, white text)

--- CARDS ---

  Background: #F5F5F5
  Border: 1px solid #E5E7EB
  Border-radius: 24px
  Shadow: 0 2px 16px rgba(0,0,0,0.06) � soft, no harsh shadows
  Hover: slight lift, shadow deepens subtly

  Layout inside card:
    Section label (UPPERCASE orange) ? card title (charcoal bold) ? body (gray) ? optional CTA

--- BADGES / CHIPS ---

  Fully pill-shaped (border-radius: 999px)
  "New" / "Beta": background #FF5925, text #FFFFFF
  Status (Active): background #DCFCE7, text #16A34A
  Status (Invited): background #FEF9C3, text #854D0E
  Source chips (chat): background #F5F5F5, border 1px #E5E7EB, text #1A1A1A

--- DECORATIVE ELEMENTS ---

  Abstract 3D ribbon/wave shapes in peach-to-orange tones (#FF5925 to #FFB347)
  Place as large background decorations:
    - Top-right corner of hero section (large swooping ribbon)
    - Bottom-left corner of select alternating sections
  These ribbons provide depth and organic warmth � exactly as seen on GitBook.com

  Product mockup screenshots in browser-frame containers:
    Frame background: #FFFFFF
    Frame shadow: 0 8px 48px rgba(0,0,0,0.10)
    Frame border-radius: 16px

--- FORMS & INPUTS ---

  Background: #FFFFFF
  Border: 1.5px solid #E5E7EB
  Border-radius: 12px
  Focus border: 1.5px solid #1A1A1A
  Placeholder: #9CA3AF
  Field label: 13px, weight 600, #1A1A1A, placed above field

--- SIDEBAR (Dashboard & Chat pages) ---

  Background: #F5F5F5
  Right border: 1px solid #E5E7EB
  Active nav item: left border 2px #FF5925, text #1A1A1A, bg #EBEBEB
  Inactive nav: text #666666, hover text #1A1A1A
  Logo at top: bold charcoal

--- TABLES ---

  Header: background #F5F5F5, text #666666 uppercase small
  Rows: white background, bottom border 1px #E5E7EB
  Row hover: background #FAFAFA
  Dividers: horizontal only � no vertical grid lines

--- ICONS ---

  Style: clean line icons (Lucide / Heroicons)
  Colors: #666666 inactive, #1A1A1A active, #FF5925 accents
  Size: 18-20px inline, 32-40px on feature cards

--- OVERALL VIBE ---

  Clean � Airy � Minimal � Modern � Enterprise-grade
  Lots of breathing room and white space � no visual clutter
  Orange accent used sparingly as punctuation � not overdone
  Premium SaaS feel: professional, calm, and highly readable

# -----------------------------------------------------------
# END DESIGN SYSTEM � PAGE PROMPTS BEGIN BELOW
# -----------------------------------------------------------

---
---

#
# PAGE 0 � LANDING PAGE
#
Design a public marketing landing page for "QueryMind — Enterprise AI Assistant".
This is the first page anyone sees before signing up or logging in.

Full page layout with these sections top to bottom:


SECTION 1 — STICKY NAVIGATION BAR:

- Left: "QueryMind" logo with app name
- Center links: Features | How It Works | Security | Pricing
  (each smoothly scrolls to the corresponding section)
- Right side:
  "Sign In" button → opens the Login Dropdown Panel
  "Create Workspace" button → href="onboard.html"

LOGIN DROPDOWN PANEL (opens when "Sign In" clicked):
- Slides down below the "Sign In" button
- Panel header: "Sign In to QueryMind" + small "×" close button
- Form fields inside panel:
  1. Company Join Code  — text input, auto-uppercase as-you-type, placeholder: "Company join code e.g. ACMEXK7P12"
  2. Email Address      — email input, placeholder: "your@company.com"
  3. Password           — password input with show/hide eye toggle, placeholder: "Password"
  4. "Remember me" checkbox
- "Sign In" submit button (full width inside panel)
  Loading state: spinner + "Verifying…", button disabled
- API call: POST http://localhost:8000/join
  Body: { "join_code": "...", "email": "...", "password": "..." }
  Response: { "token": "...", "role": "...", "company_name": "..." }
- On success:
  Store token: localStorage.setItem("nova_token", response.token)
  Store role: localStorage.setItem("nova_role", response.role)
  If role == "admin" → redirect to dashboard.html
  Otherwise → redirect to chat.html
- Error messages below button:
  "Invalid join code, email, or password — please try again"
  "Account not registered yet — Register here →" (link to register.html)
- Two helper links:
  "First time? Register your account" → register.html
  "New company? Create a workspace" → onboard.html
- Note at bottom of panel: "Your session expires after 12 hours"


SECTION 2 — HERO:

Centered layout:
- Badge above heading: "Powered by GPT-4 + RAG"
- Large main heading:
  "Your Company's Private AI Assistant"
- Subheading:
  "QueryMind gives your entire team — from employees to managers — a secure, private AI assistant
  trained on your company's own documents and data. No hallucinations. No data leaks.
  Role-aware answers for every level of your organisation."
- Two CTA buttons:
  Primary: "Create Your Workspace — Free" → onboard.html
  Secondary: "See How It Works" → scrolls to #how-it-works
- Trust bar below buttons:
  "No credit card required · Set up in 2 minutes · Your data stays private"
- Hero mockup image below: a browser-frame screenshot preview of the chat interface


SECTION 3 — SOCIAL PROOF BAR:

Full-width bar: "Trusted by enterprise teams"
Row of 5–6 placeholder company logo boxes (greyscale)


SECTION 4 — FEATURES (id="features"):

Section heading: "Everything your team needs"
Subheading: "One AI assistant that works across every role in your company"

6 feature cards in a 3×2 grid. Each card: icon, title, description.

  Card 1:
  "Role-Based Access Control"
  "4 roles: Employee, Team Lead, Manager, Admin.
  Employees see only public documents. Team leads and managers access confidential data.
  Every answer is scoped to what the user is permitted to read."

  Card 2:
  "Trained on Your Documents"
  "Upload PDFs, DOCX, XLSX, CSV, TXT, JSON, XML, and Markdown files.
  Documents are chunked, embedded, and indexed into MongoDB Atlas Vector Search.
  ARIA answers only from your company's data — never guesses."

  Card 3:
  "Google Workspace Integrations"
  "Send emails via Gmail, create Calendar events, upload to Drive,
  generate Meet links, create Docs, and update Sheets — all from one chat interface."

  Card 4:
  "3-Layer Lakera Guard Security"
  "Every request passes 3 checkpoints powered by Lakera Guard:
  1. Input scan — before reaching the AI
  2. Document scan — on retrieved chunks before prompt injection
  3. Output scan — before returning the AI response"

  Card 5:
  "Human-in-the-Loop Escalation"
  "High-risk or low-confidence queries are paused and escalated automatically:
  Level 1 → Team Lead | Level 2 → Manager | Level 3 → System Admin
  30-minute SLA with audit trail."

  Card 6:
  "Admin Dashboard & LLMOps Metrics"
  "Manage users, upload documents, configure email, and track
  total queries, tokens used, security blocks, tool invocations,
  HITL escalations, error rate, and average response latency."


SECTION 5 — HOW IT WORKS (id="how-it-works"):

Section heading: "Up and running in minutes"

4-step horizontal numbered flow:

  Step 1: "Create Your Workspace"
  API: POST /onboard { company_name, admin_email, admin_password }
  "Register your company. You instantly get a unique Join Code for your team."

  Step 2: "Upload Your Documents"
  API: POST /ingest { file_path, category, db_type: 'public' | 'private' }
  "Upload company PDFs, policies, and reports. Mark each as Public (all staff) or Confidential (managers only)."

  Step 3: "Invite Your Team"
  API: POST /invite-user { email, role: 'employee' | 'manager' | 'team_lead' }
  "Add employees, managers, and team leads. They receive an invite email with the Join Code."

  Step 4: "Your Team Uses ARIA"
  API: POST /register → POST /join → POST /chat
  "Employees register once, then log in and get instant answers from your company's knowledge base."


SECTION 6 — SECURITY (id="security"):

Section heading: "Built security-first — not as an afterthought"

2-column layout:
  Left (text):
  "QueryMind applies Lakera Guard at 3 checkpoints on every single request:"
  Three rows with checkmark icons:
    ✓ Input Scan — every user message scanned before reaching the AI
    ✓ Document Scan — retrieved document chunks checked before prompt injection
    ✓ Output Scan — every AI response scanned before delivery
  "Powered by Lakera Guard — the industry standard for LLM security."

  Right (visual flow diagram):
  [User Input] → [Lakera Scan] → [MongoDB RAG] → [Lakera Scan] → [GPT-4] → [Lakera Scan] → [ARIA Response]

  4 compliance badges below:
    Role-Based Access | Prompt Injection Protection | PII Redaction | Human-in-the-Loop


SECTION 7 — PRICING (id="pricing"):

Section heading: "Simple, transparent pricing"

3 pricing cards:

  Card 1 — Starter (badge: "Most Popular"):
    Price: "Free"
    Description: "For small teams getting started with AI"
    Features: Up to 10 users · 100 documents · Public knowledge base · Google Workspace integrations · Basic metrics
    CTA: "Get Started Free" → onboard.html

  Card 2 — Pro (highlighted as recommended):
    Price: "$49/month"
    Description: "For growing companies that need more"
    Features: Up to 100 users · Unlimited documents · Public + Confidential knowledge base · HITL escalation workflows · Advanced metrics & audit logs · Priority support
    CTA: "Start Pro Trial" → onboard.html

  Card 3 — Enterprise:
    Price: "Custom"
    Description: "For large organisations with custom needs"
    Features: Unlimited users · Custom data retention · SSO & advanced security · Dedicated support · SLA guarantee · On-premise option
    CTA: "Contact Sales"


SECTION 8 — FINAL CTA BANNER:

Full-width centered section:
- Heading: "Give your team an AI assistant that actually knows your company"
- Subtext: "Set up in 2 minutes. No credit card required."
- Large CTA button: "Create Your Workspace Free" → onboard.html


FOOTER:

3 columns:
  Col 1: "QueryMind" logo + tagline: "The enterprise AI assistant built on your data."
  Col 2: Product — Features, How It Works, Security, Pricing
  Col 3: Account — Create Workspace, Sign In, Register
Bottom: "© 2025 QueryMind. All rights reserved."

---
---

#
# PAGE 1 — ONBOARD (Create Company Workspace)
#

Design a company workspace creation page for "QueryMind — Enterprise AI Assistant".
Single-column centered card layout.

Page heading: "Create Your Company Workspace"
Subtitle: "Set up your private AI assistant for your entire team"

Progress indicator at top (2 steps):
  Step 1: "Company Setup" (active)
  Step 2: "Your Join Code" (inactive — activates after success)


─── STEP 1 — CREATION FORM ───

All fields required. Show inline field-level error messages.

Fields:
1. Company Name (text input)
   Placeholder: "Acme Corporation"

2. Admin Email (email input)
   Placeholder: "admin@yourcompany.com"
   Helper text: "This becomes your login email address"

3. Password (password input with show/hide toggle)
   Placeholder: "Create a strong password"
   API minimum: 8 characters
   Live strength meter: Weak → Fair → Strong → Very Strong
   Live requirements checklist:
     ✗/✓ At least 8 characters
     ✗/✓ At least one uppercase letter
     ✗/✓ At least one number

4. Confirm Password (password input)
   Live validation: "✓ Passwords match" or "✗ Passwords do not match"

5. Checkbox: "I confirm I am authorised to create this workspace for my company"

Submit button: "Create Workspace →"
  Full width, disabled until all fields valid + checkbox ticked
  Loading state: spinner + "Creating your workspace…"

API call:
POST http://localhost:8000/onboard
Body: { "company_name": "...", "admin_email": "...", "admin_password": "..." }
Response: { "company_name": "...", "tenant_id": "...", "join_code": "...", "message": "..." }

Error handling (below submit button):
  400: "Password must be at least 8 characters"
  409: "A workspace with this company name already exists"
  500: "Something went wrong — please try again"


─── STEP 2 — JOIN CODE DISPLAY (replaces form after success) ───

Large green checkmark icon
Heading: "Your Workspace is Ready!"
Subtext: "Company: [company_name from API response]"

"Your Company Join Code" section:
- Large monospace display of join_code (e.g. ACMEXK7P12)
- "Copy Code" button → copies to clipboard → changes to "Copied!" for 2 seconds

Important notice box:
"Share this code with your team members.
They need it to register and log in to QueryMind.
Keep it safe — anyone with this code can join your workspace."

Pre-written invite message (copyable text block):
──────────────────────────
You've been invited to [Company Name] on QueryMind.

Join Code: [join_code]
1. Register at: [app url]/register.html
2. Log in at: [app url]/login.html
──────────────────────────
"Copy Invite Message" button below the block

What happens next (numbered list):
1. Share the join code with your team members
2. They visit register.html and set their password using: Join Code + email + new password
3. After registering, they log in at login.html
4. You can manage users and upload documents from your Admin Dashboard

Two buttons:
  Primary: "Go to Login →" → login.html
  Secondary: "Copy Invite Message"

Bottom link: "Already have a workspace? Sign In →" → login.html

---
---

#
# PAGE 2 — LOGIN
#

Design a login page for "QueryMind — Enterprise AI Assistant".
Used by ALL users: admin, manager, team_lead, and employee.
Redirect after login is automatic based on the role returned by the API.

Page heading: "Sign In to QueryMind"
Subheading: "Enter your company credentials to continue"


─── LOGIN FORM ───

All fields required.

1. Company Join Code (text input)
   Placeholder: "Enter your company join code"
   Auto-uppercase as user types
   Helper text: "Find this in your invite email or from your admin"

2. Email Address (email input)
   Placeholder: "your@company.com"

3. Password (password input with show/hide eye toggle)
   Placeholder: "Your password"

4. "Remember me" checkbox

"Sign In" button: full width
  Loading state: spinner + "Verifying…", button disabled

API call:
POST http://localhost:8000/join
Body: { "join_code": "...", "email": "...", "password": "..." }
Response: { "token": "...", "role": "...", "company_name": "...", "message": "..." }

On success:
  localStorage.setItem("nova_token", response.token)
  localStorage.setItem("nova_role", response.role)
  localStorage.setItem("nova_company", response.company_name)
  Toast: "Welcome back to [company_name]!"
  if role == "admin"     → redirect to dashboard.html
  else                   → redirect to chat.html

Error states (below button):
  404: "Invalid join code. Check with your admin."
  403 (not registered): "Account not set up yet — Register your account first →" (link to register.html)
  403 (email not found): "Email not found in this workspace. Contact your admin."
  401: "Incorrect password. Please try again."
  Network error: "Cannot connect to QueryMind — please check your connection"

Two helper links below error area:
  "First time? Register your account →" → register.html
  "New company? Create a workspace →" → onboard.html

---
---

#
# PAGE 3 — REGISTER (First-Time Account Setup)
#

Design a first-time account registration page for "QueryMind".
Used ONCE by non-admin users (employee / manager / team_lead) who received an invite.
The admin must have already added the user's email via the dashboard before they register.
After registering, the user logs in normally at login.html.

Page heading: "Set Up Your Account"
Subheading: "Complete your registration using your invite details"

Info banner at top of form:
"Check your invite email for your Join Code and the email address your admin used to invite you."


─── REGISTRATION FORM ───

All fields required.

1. Company Join Code (text input)
   Placeholder: "Your company join code (e.g. ACMEXK7P12)"
   Auto-uppercase as user types

2. Email Address (email input)
   Placeholder: "The email address your admin invited"
   Helper: "Must match exactly the email your admin used"

3. New Password (password input with show/hide toggle)
   Placeholder: "Create your password"
   API minimum: 8 characters
   Live requirements checklist:
     ✗/✓ At least 8 characters
     ✗/✓ At least one uppercase letter
     ✗/✓ At least one number
   Password strength meter: Weak → Fair → Strong → Very Strong

4. Confirm Password (password input)
   Live validation: "✓ Passwords match" or "✗ Passwords do not match"

"Create Account" button: full width
  Disabled until ALL fields valid + passwords match
  Loading state: "Setting up your account…"

API call:
POST http://localhost:8000/register
Body: { "join_code": "...", "email": "...", "password": "..." }
Response: { "message": "...", "role": "employee" | "manager" | "team_lead" }

On success — replace form with confirmation card:
  Large green checkmark
  "Account Created Successfully"
  "You are joining as: [Role]"
  Auto-redirect countdown: "Taking you to login in 3… 2… 1…"
  "Go to Login Now →" link

Error states (below button):
  404: "Invalid join code. Check with your admin."
  403: "This email was not invited to this workspace. Contact your admin."
  409: "Account already exists — please Sign In instead →" (link to login.html)
  400: "Password must be at least 8 characters."
  Generic: "Something went wrong — please try again"

Bottom link: "Already registered? Sign In →" → login.html

---
---

#
# PAGE 4 — CHAT INTERFACE
#

Design a full-screen AI chat interface for "QueryMind — ARIA"
(ARIA = Adaptive Retrieval Intelligence Assistant).
This is the main page for all logged-in users.

On page load:
  Read nova_token from localStorage
  If missing → redirect to login.html
  Read nova_role, nova_company from localStorage


─── LEFT SIDEBAR (fixed, full height) ───

Top:
- "QueryMind" logo + wordmark
- "New Chat" button with + icon (full sidebar width)

Conversation History (scrollable, below New Chat):
- Each item: auto-generated title from first user message + relative timestamp
  e.g. "Leave policy query — 2 hours ago"
- Hover state: shows a trash/delete icon on right
- Active conversation: highlighted
- Click → loads that conversation's messages

Divider line

Bottom section:
- User avatar (initials circle from email)
- User email (truncated if long)
- Role badge:
  Employee → badge
  Manager → badge
  Team Lead → badge
  Admin → badge
- If role == "admin": "Admin Dashboard" link → dashboard.html
- "Sign Out" button → clears localStorage, redirects to login.html


─── MAIN AREA — EMPTY STATE (no chat selected) ───

Centered vertically and horizontally:

Large greeting heading: "What can I help with today?"
Subtext: "Ask anything about your company's documents, policies, and data."

ARIA INPUT BOX (Manus-style rounded container):

  TOP SECTION — textarea:
    Multi-line, auto-expanding
    Placeholder: "Ask ARIA anything about your company…"

  BOTTOM BAR inside input box (icon row):

    Left-side icon buttons:
    - "+" attach file (document upload)
    - Plug/connector icon → opens Connectors Modal
    - Puzzle piece icon → opens tool selector

    Right-side icon buttons:
    - Stop button (stops AI mid-generation)
    - Microphone icon (voice input placeholder, no function required)
    - Send/submit button:
        Active (text present): prominent, enabled
        Inactive (empty input): grayed out, disabled

CONNECTOR STATUS BAR (directly below input box):
  Left: plug icon + text "Connect your tools to QueryMind"
    (changes to "6 tools connected" when all connected)
  Right: row of 6 small circular tool icons:
    Gmail | Google Drive | Google Docs | Google Sheets | Google Calendar | Google Meet
    Colored = connected | Gray = not connected
    Each icon clickable → opens Connectors Modal
  Far right: × dismiss button

SUGGESTION CHIPS (below connector bar):
4 rounded pill buttons:
  "What is our leave policy?"
  "Summarise the Q3 financial report"
  "Who do I contact for IT support?"
  "Draft a follow-up email to HR"
  Click any → pre-fills the textarea


─── CONNECTORS MODAL ───

Opens on: plug icon, puzzle icon, or any connector icon in the status bar.
Modal with overlay backdrop.

Modal header:
  Title: "Connectors"
  "×" close button top-right

Three tabs: [Apps] [Custom API] [Custom MCP]
  Apps is default active.
  Custom API + Custom MCP show: "Coming soon" empty state.

Search bar (full width inside modal body)

Under Apps tab — "Google Workspace" section:
6 tool cards in 2-column grid. Each card: icon | tool name | one-line description | button

  1. Gmail
     "Send emails, draft replies, and manage email threads from chat"
     Button: "Connect" → after click → "✓ Connected"

  2. Google Drive
     "Upload files, share folders, and manage company documents"
     Button: "Connect" / "✓ Connected"

  3. Google Docs
     "Create new documents and edit existing ones from chat"
     Button: "Connect" / "✓ Connected"

  4. Google Sheets
     "Push data, update rows, and log records to spreadsheets"
     Button: "Connect" / "✓ Connected"

  5. Google Calendar
     "Create events, set reminders, and invite team members"
     Button: "Connect" / "✓ Connected"

  6. Google Meet
     "Generate video call links and schedule meetings"
     Button: "Connect" / "✓ Connected"

On "Connect" click:
  Card shows: "✓ [Tool] connected — ARIA can now use this on your behalf"
  Button turns to "✓ Connected"
  Corresponding icon in connector bar becomes colored/active


─── ACTIVE CHAT STATE ───

After first message is sent:
  Messages fill the top ~80% of screen (scrollable area)
  Input box moves to bottom of screen (sticky/fixed)
  Connector status bar stays directly below input

Top bar above messages:
  Left: "ARIA — Enterprise AI Assistant" + "[Company Name] Workspace"
  Right: access level chip:
    Employee   → "Public documents only"
    Manager / Team Lead / Admin → "Public + Confidential"

User message (right-aligned bubble):
  Shows user's text

ARIA response card (left-aligned):
  During generation: animated 3-dot typing indicator

  After response — full card structure:

  a) "Answer:" — main response text (supports markdown: headers, bullet points)

  b) "Sources:" — row of clickable source chips:
     [HR Policy v2.1]  [Financial Report Q3]  [Web Search]

  c) "Confidence:" badge:
     HIGH   → green badge
     MEDIUM → yellow badge
     LOW    → red badge + italic note "(Human verification recommended)"

  d) "Actions:" section (only when tools were used):
     [Gmail icon] ✓ Email sent to hr@acme.com → "Open Gmail" link
     [Calendar icon] ✓ Event 'Team Meeting' created Friday 3PM → "View" link
     [Drive icon] ✗ Upload failed → "Retry" button

  e) "Next Step:" italic suggestion

  f) Footer action row:
     "Copy" | Thumbs up | Thumbs down | "Run a tool" button

TOOL CONFIRMATION FLOW (before irreversible action):
  ARIA shows: "I will use [Tool] to perform: [exact action description]"
  Preview card showing exactly what will happen
  "⚠ This action cannot be undone."
  [Confirm] [Cancel] buttons

After Confirm:
  "Executing via [Tool]…" progress indicator
  Result shown inline in response card

HITL ESCALATION BANNER (shown on ARIA response when escalated):
  "This request requires human review before proceeding.
  Request ID: [id] | Escalated to: [Team Lead / Department Manager / System Admin]
  SLA: 30 minutes | You will be notified once a decision is made."

TOOL NOT CONNECTED state:
  "Gmail is not connected. Connect it to use this feature."
  Inline "Connect Gmail" button → opens Connectors Modal

ROLE RESTRICTION state:
  "Your role (Employee) does not have access to [Tool/Data].
  Contact your admin to change your permissions."

SESSION EXPIRED state:
  Full-screen overlay: "Your session has expired — please sign in again"
  "Sign In" button → login.html

API:
POST http://localhost:8000/chat
Headers: { Authorization: "Bearer " + localStorage.getItem("nova_token") }
Body: { "prompt": "...", "session_id": "optional-uuid" }
Response: { "response": "...", "session_id": "...", "tenant_id": "...", "role": "..." }

ARIA response parsing: The "response" field returns structured markdown:
  **Answer:** [text]
  **Sources:** [list]
  **Confidence:** [HIGH/MEDIUM/LOW]
  **Actions:** [tool results, if any]
  **Next Step:** [suggestion]
Parse and render each section as a distinct block inside the response card.

---
---

#
# PAGE 5 — ADMIN DASHBOARD
#

Design a full-screen admin dashboard for "QueryMind".
Only accessible if nova_role == "admin" (check localStorage on page load; if not admin → redirect to chat.html).
Full sidebar + tabbed main content area layout.


─── LEFT SIDEBAR (fixed, full height) ───

Top: "QueryMind" logo

Navigation items (click switches main content area):
  1. Overview      (default active)
  2. Users
  3. Documents
  4. Email Settings
  5. Metrics

Divider

Bottom:
  - Admin user avatar (initials circle)
  - Admin email
  - "Admin" role badge
  - "Go to Chat" link → chat.html
  - "Sign Out" button → clears localStorage, redirects to login.html


─── TAB 1: OVERVIEW (default) ───

4 stat cards in a row:
  1. "Total Users"          — count + breakdown: "X employees · X managers · X team leads"
  2. "Documents Ingested"   — count + "X public · X confidential"
  3. "Active Sessions"      — live count with pulsing indicator
  4. "Avg Response Time"    — number in milliseconds

Recent Activity feed below:
Label: "Recent Activity"
Timeline list of last 10 events (icon + description + relative timestamp):
  "john@acme.com invited as Employee — 2 hours ago"
  "Q3_Report.pdf ingested (Confidential) — 5 hours ago"
  "maria@acme.com registered and activated account — Yesterday"
  "HITL escalation: salary query escalated to Manager — 2 days ago"
  "Invite email sent to dev@acme.com — 3 days ago"


─── TAB 2: USERS ───

Page heading: "Team Members" + count badge: "X members"

─ INVITE NEW USER FORM ─

Heading: "Invite New Team Member"
Inline fields:
  Email Address input — placeholder: "colleague@yourcompany.com"
  Role dropdown: Employee | Manager | Team Lead
    (Admin is NOT in the dropdown — admin is only created via /onboard)
  "Send Invite" button

API call:
POST http://localhost:8000/invite-user
Headers: { Authorization: "Bearer " + nova_token }
Body: { "email": "...", "role": "..." }

On success — confirmation box:
  "✓ Invite sent to john@acme.com
  Role: Employee
  They will receive an email with the join code and registration instructions.
  Email delivery: [sent / skipped — configure Gmail via Email Settings]"

On error:
  409: "This email is already a member of this workspace"
  403: "Only admins can invite users"

─ SEARCH AND FILTER BAR ─
  Search by email (text input)
  Filter by role: All | Employee | Manager | Team Lead
  Filter by status: All | Active | Invited

─ USERS TABLE ─
Columns: Email | Role (badge) | Status (badge) | Date Added | Action

Role badge styles:
  Employee  → labeled badge
  Manager   → labeled badge
  Team Lead → labeled badge

Status badge styles:
  Active  → "Active"  (user has registered and can log in)
  Invited → "Invited" (email sent, not yet registered)

Action column:
  "Remove" button → confirmation dialog:
    "Are you sure you want to remove [email] from this workspace?
    This action cannot be undone."
    [Confirm Remove] [Cancel]


─── TAB 3: DOCUMENTS ───

Page heading: "Knowledge Base"

─ UPLOAD DOCUMENT PANEL ─

Drag-and-drop file upload area:
  Center text: "Drag & drop files here, or click to browse"
  Below: "Supported formats: PDF, DOCX, XLSX, CSV, TXT, JSON, XML, MD"
  After file selected: show filename + file size + remove button

Category text input:
  Placeholder: "Category (e.g. HR, Finance, Legal, IT, Compliance)"

Database selection (two radio buttons):
  ○ Public Database
    "Accessible to all employees, managers, team leads, and admins"
  ○ Confidential Database
    "Accessible to managers, team leads, and admins only — hidden from employees"

"Upload & Ingest" button (full width)
  Progress bar shown during upload and ingestion

API call:
POST http://localhost:8000/ingest
Headers: { Authorization: "Bearer " + nova_token }
Body: { "file_path": "...", "category": "...", "db_type": "public" | "private" }

Result states:
  Success:
    "✓ HR_Policy_2024.pdf ingested successfully
    14 document chunks indexed into Public database
    Category: HR"

  Security blocked (Lakera Guard flagged the document):
    "🚫 Document blocked by security scan
    This document was flagged and not ingested.
    Reason: contains restricted or sensitive content (Lakera Guard)"

  Unsupported format:
    "⚠ Unsupported file format.
    Please use: PDF, DOCX, XLSX, CSV, TXT, JSON, or MD"

  Server error:
    "✗ Ingestion failed — please try again"

─ INGESTED DOCUMENTS TABLE (read-only) ─
Columns: Filename | Category | Database | Chunks | Uploaded By | Date Ingested


─── TAB 4: EMAIL SETTINGS ───

Page heading: "Email Configuration"
Purpose text:
"When you invite team members, QueryMind sends them invitation emails FROM your Gmail account,
containing the join code and registration instructions."

─ STATUS CARD ─
If configured:
  "✓ Configured — invites sent from admin@gmail.com"
If not configured:
  "⚠ Not configured — invite emails will not be sent to new users"

─ SETUP GUIDE (expandable section) ─
  Title: "How to get your Gmail App Password" [expand/collapse]
  Numbered steps:
    1. Go to myaccount.google.com
    2. Click Security → Enable 2-Step Verification (if not already)
    3. Go to App Passwords
    4. Create a new App Password named "QueryMind"
    5. Copy the 16-character password and paste it below

─ CONFIGURATION FORM ─
  Gmail Address input — placeholder: "admin@gmail.com"
  App Password input (masked, show/hide toggle):
    Placeholder: "16-character app password"
    Validation: exactly 16 non-space characters
    Helper: "The 16-char password from Google App Passwords — NOT your normal Gmail password"
  "Save Email Settings" button

API call:
POST http://localhost:8000/email-config
Headers: { Authorization: "Bearer " + nova_token }
Body: { "sender_email": "...", "sender_password": "..." }

Results:
  Success: "✓ Email settings saved. Invites will now be sent from admin@gmail.com"
  Error:   "✗ Failed — check your Gmail address and App Password"

─ TEST EMAIL SECTION ─
  "Send Test Email" button — sends a test email to the admin's own address
  Success: "✓ Test email delivered to admin@gmail.com — check your inbox"
  Failure: "✗ Test failed — verify your credentials and try again"


─── TAB 5: METRICS ───

Page heading: "System Performance & Usage"
Date range filter buttons (top right): [Today] [Last 7 Days] [Last 30 Days]

API call:
GET http://localhost:8000/metrics
Headers: { Authorization: "Bearer " + nova_token }

─ METRIC CARDS GRID ─
Each card: large number + label + icon

  1. "Total Queries"       — total chat messages sent
  2. "Total Tokens Used"   — total OpenAI tokens consumed
  3. "Security Blocks"     — breakdown: X prompt injection · X PII · X jailbreak
  4. "Tool Invocations"    — total Google Workspace plugin actions triggered
  5. "HITL Escalations"    — number of human review escalations triggered
  6. "Error Rate"          — percentage of failed requests
  7. "Avg Latency"         — milliseconds per AI response

─ CHARTS SECTION ─
  1. Queries over time: line chart (based on selected date range)
  2. Confidence distribution: donut chart — HIGH / MEDIUM / LOW segments
  3. Tool usage breakdown: bar chart — which Google Workspace plugins used most
  4. Security events: bar chart — prompt injection / PII / jailbreak types over time

Empty state (if no data returned):
  "No data yet — start using ARIA to see metrics here"


─── GLOBAL NOTES FOR ALL PAGES ───

Token handling (on every authenticated page):
  1. Read nova_token from localStorage
  2. If missing → redirect to login.html
  3. Attach to all API calls: Authorization: "Bearer " + nova_token
  4. If any API returns 401 → show "Session expired" overlay → redirect to login.html

API base URL: http://localhost:8000

Roles returned by POST /join:
  "admin"     → access: dashboard.html + chat.html
  "manager"   → access: chat.html (public + confidential docs)
  "team_lead" → access: chat.html (public + confidential docs)
  "employee"  → access: chat.html (public docs only)

ARIA response structure (from POST /chat → "response" field):
  **Answer:** [main response]
  **Sources:** [cited sources]
  **Confidence:** [HIGH / MEDIUM / LOW]
  **Actions:** [tool results, if any]
  **Next Step:** [follow-up suggestion]
Parse and render each section as a distinct labelled block inside the ARIA message card.
