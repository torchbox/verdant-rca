-- Rename all verdantdocs tables to wagtaildocs
ALTER TABLE verdantdocs_document RENAME TO wagtaildocs_document;

-- Fix app_label of core content_types
UPDATE django_content_type SET app_label = 'wagtaildocs' WHERE app_label = 'verdantdocs';

-- Update south migration history to look like we ran the new wagtaildocs migrations
DELETE FROM south_migrationhistory WHERE app_name = 'verdantdocs';
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtaildocs', '0001_initial', NOW());
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtaildocs', '0002_initial_data', NOW());
