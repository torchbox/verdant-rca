-- Rename all core tables to wagtailcore
ALTER TABLE core_grouppagepermission RENAME TO wagtailcore_grouppagepermission;
ALTER TABLE core_page RENAME TO wagtailcore_page;
ALTER TABLE core_pagerevision RENAME TO wagtailcore_pagerevision;
ALTER TABLE core_site RENAME TO wagtailcore_site;

-- Fix app_label of core content_types
UPDATE django_content_type SET app_label = 'wagtailcore' WHERE app_label = 'core';

-- Update south migration history to look like we ran the new wagtailcore migrations
DELETE FROM south_migrationhistory WHERE app_name = 'core';
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailcore', '0001_initial', NOW());
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailcore', '0002_initial_data', NOW());
