import csv
import json
import datetime
from connect import get_conn

# ── DB init ───────────────────────────────────
def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(open("schema.sql").read())
            cur.execute(open("procedures.sql").read())
        conn.commit()
    print("Database initialized.")

# ── helpers ───────────────────────────────────
def print_table(rows, headers):
    if not rows:
        print("  (no results)")
        return
    widths = [max(len(str(h)), max(len(str(r[i])) for r in rows))
              for i, h in enumerate(headers)]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  " + "  ".join("-" * w for w in widths)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(x) if x is not None else "" for x in row]))

def input_phone_type():
    while True:
        t = input("  Phone type (home/work/mobile) [mobile]: ").strip() or "mobile"
        if t in ("home", "work", "mobile"):
            return t
        print("  Invalid type.")

def count_contacts():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM contacts")
            return cur.fetchone()[0]

# ── CRUD ──────────────────────────────────────
def add_contact():
    print("\n── Add Contact ──")
    name = input("  Name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return
    email    = input("  Email (optional): ").strip() or None
    birthday = input("  Birthday (YYYY-MM-DD, optional): ").strip() or None

    # show groups
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM groups ORDER BY name")
            groups = [r[0] for r in cur.fetchall()]
    print(f"  Groups: {', '.join(groups)}")
    group = input("  Group [Other]: ").strip() or "Other"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CALL upsert_contact(%s, %s, %s, %s)",
                        (name, email, birthday, group))
        conn.commit()
    print(f"  Contact '{name}' saved.")

    # add phones
    while True:
        phone = input("  Add phone number (or Enter to skip): ").strip()
        if not phone:
            break
        ptype = input_phone_type()
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
            conn.commit()
        print(f"  Phone {phone} added.")


def view_all():
    print("\n── All Contacts ──")
    sort_by = input("  Sort by (name/birthday/date) [name]: ").strip() or "name"
    sort_map = {
        "name":     "c.name",
        "birthday": "c.birthday",
        "date":     "c.created_at",
    }
    order = sort_map.get(sort_by, "c.name")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT c.name, c.email, c.birthday, g.name,
                       STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ') as phones
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                GROUP BY c.name, c.email, c.birthday, g.name, c.created_at
                ORDER BY {order}
            """)
            rows = cur.fetchall()
    print_table(rows, ["Name", "Email", "Birthday", "Group", "Phones"])


def search_contacts():
    print("\n── Search ──")
    query = input("  Search query: ").strip()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (query,))
            rows = cur.fetchall()
    print_table(rows, ["Name", "Email", "Birthday", "Group", "Phone", "Type"])


def filter_by_group():
    print("\n── Filter by Group ──")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM groups ORDER BY name")
            groups = [r[0] for r in cur.fetchall()]
    print(f"  Available groups: {', '.join(groups)}")
    group = input("  Group name: ").strip()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, c.email, c.birthday,
                       STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ')
                FROM contacts c
                JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                WHERE g.name ILIKE %s
                GROUP BY c.name, c.email, c.birthday
                ORDER BY c.name
            """, (group,))
            rows = cur.fetchall()
    print_table(rows, ["Name", "Email", "Birthday", "Phones"])


def search_by_email():
    print("\n── Search by Email ──")
    query = input("  Email pattern: ").strip()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, c.email, g.name
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                WHERE c.email ILIKE %s
                ORDER BY c.name
            """, (f"%{query}%",))
            rows = cur.fetchall()
    print_table(rows, ["Name", "Email", "Group"])


def paginated_view():
    print("\n── Browse Pages ──")
    page_size = 5
    total     = count_contacts()
    if total == 0:
        print("  No contacts.")
        return
    page = 0
    while True:
        offset = page * page_size
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_contacts_page(%s, %s)",
                            (page_size, offset))
                rows = cur.fetchall()
        total_pages = (total + page_size - 1) // page_size
        print(f"\n  Page {page+1} of {total_pages}")
        print_table(rows, ["Name", "Email", "Birthday", "Group"])
        cmd = input("  [n]ext / [p]rev / [q]uit: ").strip().lower()
        if cmd == "n" and page < total_pages - 1:
            page += 1
        elif cmd == "p" and page > 0:
            page -= 1
        elif cmd == "q":
            break


def update_contact():
    print("\n── Update Contact ──")
    name = input("  Contact name to update: ").strip()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
            row = cur.fetchone()
    if not row:
        print(f"  Contact '{name}' not found.")
        return
    contact_id = row[0]

    print("  What to update?")
    print("  1. Email")
    print("  2. Birthday")
    print("  3. Group")
    print("  4. Add phone")
    print("  5. Move to group")
    choice = input("  Choice: ").strip()

    with get_conn() as conn:
        with conn.cursor() as cur:
            if choice == "1":
                email = input("  New email: ").strip()
                cur.execute("UPDATE contacts SET email = %s WHERE name = %s",
                            (email, name))
            elif choice == "2":
                bday = input("  New birthday (YYYY-MM-DD): ").strip()
                cur.execute("UPDATE contacts SET birthday = %s WHERE name = %s",
                            (bday, name))
            elif choice == "3":
                group = input("  New group: ").strip()
                cur.execute("CALL move_to_group(%s, %s)", (name, group))
            elif choice == "4":
                phone = input("  Phone number: ").strip()
                ptype = input_phone_type()
                cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
            elif choice == "5":
                group = input("  Group name: ").strip()
                cur.execute("CALL move_to_group(%s, %s)", (name, group))
        conn.commit()
    print("  Updated.")


def delete_contact():
    print("\n── Delete Contact ──")
    value = input("  Enter name or phone number: ").strip()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CALL delete_contact(%s)", (value,))
        conn.commit()
    print(f"  Deleted '{value}' (if existed).")


# ── CSV import/export ─────────────────────────
def import_csv():
    print("\n── Import CSV ──")
    path = input("  CSV file path [contacts.csv]: ").strip() or "contacts.csv"
    imported = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name     = row.get("name", "").strip()
                phone    = row.get("phone", "").strip()
                ptype    = row.get("type", "mobile").strip() or "mobile"
                email    = row.get("email", "").strip() or None
                birthday = row.get("birthday", "").strip() or None
                group    = row.get("group", "Other").strip() or "Other"
                if not name:
                    continue
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("CALL upsert_contact(%s, %s, %s, %s)",
                                    (name, email, birthday, group))
                        if phone:
                            cur.execute("CALL add_phone(%s, %s, %s)",
                                        (name, phone, ptype))
                    conn.commit()
                imported += 1
        print(f"  Imported {imported} contacts.")
    except FileNotFoundError:
        print(f"  File '{path}' not found.")


# ── JSON import/export ────────────────────────
def export_json():
    print("\n── Export to JSON ──")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, c.email,
                       c.birthday::text,
                       g.name as grp
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                ORDER BY c.name
            """)
            contacts = cur.fetchall()

            result = []
            for name, email, birthday, group in contacts:
                cur.execute("""
                    SELECT phone, type FROM phones
                    WHERE contact_id = (SELECT id FROM contacts WHERE name = %s)
                """, (name,))
                phones = [{"phone": p, "type": t} for p, t in cur.fetchall()]
                result.append({
                    "name":     name,
                    "email":    email,
                    "birthday": birthday,
                    "group":    group,
                    "phones":   phones,
                })

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"contacts_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  Exported {len(result)} contacts to '{path}'.")


def import_json():
    print("\n── Import from JSON ──")
    path = input("  JSON file path: ").strip()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"  File '{path}' not found.")
        return

    for entry in data:
        name = entry.get("name", "").strip()
        if not name:
            continue

        # check duplicate
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
                exists = cur.fetchone()

        if exists:
            choice = input(f"  '{name}' already exists. [s]kip / [o]verwrite? ").strip().lower()
            if choice != "o":
                continue

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL upsert_contact(%s, %s, %s, %s)", (
                    name,
                    entry.get("email"),
                    entry.get("birthday"),
                    entry.get("group", "Other"),
                ))
                # re-add phones
                cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
                cid = cur.fetchone()[0]
                cur.execute("DELETE FROM phones WHERE contact_id = %s", (cid,))
                for ph in entry.get("phones", []):
                    cur.execute("CALL add_phone(%s, %s, %s)",
                                (name, ph.get("phone"), ph.get("type","mobile")))
            conn.commit()
        print(f"  '{name}' imported.")


# ── main menu ─────────────────────────────────
def main():
    print("Initializing database...")
    init_db()

    while True:
        print("""
╔══════════════════════════════╗
║       PHONE BOOK MENU        ║
╠══════════════════════════════╣
║  1. Add contact              ║
║  2. View all contacts        ║
║  3. Search (name/phone/email)║
║  4. Filter by group          ║
║  5. Search by email          ║
║  6. Browse pages             ║
║  7. Update contact           ║
║  8. Delete contact           ║
║  9. Import from CSV          ║
║ 10. Export to JSON           ║
║ 11. Import from JSON         ║
║  0. Exit                     ║
╚══════════════════════════════╝""")
        choice = input("  Choice: ").strip()

        actions = {
            "1": add_contact,
            "2": view_all,
            "3": search_contacts,
            "4": filter_by_group,
            "5": search_by_email,
            "6": paginated_view,
            "7": update_contact,
            "8": delete_contact,
            "9": import_csv,
            "10": export_json,
            "11": import_json,
        }

        if choice == "0":
            print("Bye!")
            break
        elif choice in actions:
            try:
                actions[choice]()
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()