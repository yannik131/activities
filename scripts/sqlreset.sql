BEGIN;
SELECT setval(pg_get_serial_sequence('"character_character_suggestions"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "character_character_suggestions";
SELECT setval(pg_get_serial_sequence('"character_character"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "character_character";
COMMIT;
