"""
get_codes.py  —  View all companies, join codes, and optionally reset a password.
Usage:
  python get_codes.py              # list all companies
  python get_codes.py --reset      # interactively reset a password
"""
import sys
sys.path.insert(0, 'enterprise_ai')
from dotenv import load_dotenv
load_dotenv('enterprise_ai/.env')
from db.mongodb import get_mongodb_client

client, db = get_mongodb_client()

# ── Fetch all companies ───────────────────────────────────────────────────────
companies = list(db['companies'].find({}, {'company_name': 1, 'join_code': 1, 'admin_email': 1, 'tenant_id': 1, '_id': 0}))

if not companies:
    print("No companies found.")
    sys.exit()

print("\n" + "="*55)
print("  Nova AI — Company Workspaces")
print("="*55)

for i, c in enumerate(companies, 1):
    tenant_id = c.get('tenant_id', '')
    # Check if admin user has a password set
    admin_email = c.get('admin_email', '')
    user = db['users'].find_one({'tenant_id': tenant_id, 'email': admin_email}, {'password_hash': 1, '_id': 0})
    pwd_status = "✓ Password set" if (user and user.get('password_hash')) else "✗ No password set"

    print(f"\n  [{i}] {c.get('company_name')}")
    print(f"      Join Code : {c.get('join_code')}")
    print(f"      Admin     : {admin_email}")
    print(f"      Password  : {pwd_status}")

print("\n" + "="*55)

# ── Optional: reset a password ────────────────────────────────────────────────
if '--reset' in sys.argv:
    print("\nReset a password")
    company_num = int(input("Enter company number to reset: ")) - 1
    c = companies[company_num]
    tenant_id = c.get('tenant_id', '')

    users = list(db['users'].find({'tenant_id': tenant_id}, {'email': 1, 'role': 1, '_id': 0}))
    print("\nUsers in this workspace:")
    for j, u in enumerate(users, 1):
        print(f"  [{j}] {u['email']}  ({u.get('role', '?')})")

    user_num = int(input("Enter user number to reset: ")) - 1
    email = users[user_num]['email']
    new_password = input(f"New password for {email}: ")

    if len(new_password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    import bcrypt
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db['users'].update_one(
        {'tenant_id': tenant_id, 'email': email},
        {'$set': {'password_hash': hashed, 'status': 'active'}}
    )
    print(f"\n✓ Password reset for {email}. You can now login.")
