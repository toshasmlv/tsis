-- ── Pattern search (from Practice 8, extended to email + phones table) ──────
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    grp      VARCHAR,
    phone    VARCHAR,
    type     VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.name, c.email, c.birthday,
        g.name AS grp,
        p.phone, p.type
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE
        c.name  ILIKE '%' || p_query || '%'
     OR c.email ILIKE '%' || p_query || '%'
     OR p.phone ILIKE '%' || p_query || '%';
END;
$$ LANGUAGE plpgsql;

-- ── Upsert contact (from Practice 8) ─────────────────────────────────────
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_name     VARCHAR,
    p_email    VARCHAR DEFAULT NULL,
    p_birthday DATE    DEFAULT NULL,
    p_group    VARCHAR DEFAULT 'Other'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INTEGER;
BEGIN
    SELECT id INTO v_group_id FROM groups WHERE name = p_group;
    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group) RETURNING id INTO v_group_id;
    END IF;

    IF EXISTS (SELECT 1 FROM contacts WHERE name = p_name) THEN
        UPDATE contacts
        SET email    = COALESCE(p_email,    email),
            birthday = COALESCE(p_birthday, birthday),
            group_id = v_group_id
        WHERE name = p_name;
    ELSE
        INSERT INTO contacts (name, email, birthday, group_id)
        VALUES (p_name, p_email, p_birthday, v_group_id);
    END IF;
END;
$$;

-- ── Add phone to existing contact ─────────────────────────────────────────
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;
    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);
END;
$$;

-- ── Move contact to group (create group if not exists) ────────────────────
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INTEGER;
BEGIN
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name) RETURNING id INTO v_group_id;
    END IF;
    UPDATE contacts SET group_id = v_group_id WHERE name = p_contact_name;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;
END;
$$;

-- ── Paginated query (from Practice 8) ────────────────────────────────────
CREATE OR REPLACE FUNCTION get_contacts_page(p_limit INT, p_offset INT)
RETURNS TABLE(
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    grp      VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.name, c.email, c.birthday, g.name AS grp
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    ORDER BY c.name
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ── Delete by name or phone (from Practice 8) ────────────────────────────
CREATE OR REPLACE PROCEDURE delete_contact(p_value VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    -- try delete by name
    DELETE FROM contacts WHERE name = p_value;
    IF NOT FOUND THEN
        -- try delete by phone
        DELETE FROM contacts
        WHERE id IN (
            SELECT contact_id FROM phones WHERE phone = p_value
        );
    END IF;
END;
$$;

-- ── Bulk insert with phone validation (from Practice 8) ───────────────────
CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names  VARCHAR[],
    p_phones VARCHAR[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i       INT;
    v_phone VARCHAR;
    v_name  VARCHAR;
BEGIN
    FOR i IN 1..array_length(p_names, 1) LOOP
        v_name  := p_names[i];
        v_phone := p_phones[i];
        -- validate phone: must be digits, +, -, spaces only
        IF v_phone ~ '^[0-9\+\-\s\(\)]{7,20}$' THEN
            CALL upsert_contact(v_name);
            IF v_phone IS NOT NULL AND v_phone <> '' THEN
                CALL add_phone(v_name, v_phone, 'mobile');
            END IF;
        ELSE
            RAISE NOTICE 'Invalid phone for %: %', v_name, v_phone;
        END IF;
    END LOOP;
END;
$$;