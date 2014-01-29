-- Rename all verdantembeds tables to wagtailembeds
ALTER TABLE verdantredirects_redirect RENAME TO wagtailredirects_redirect;

-- Fix app_label of core content_types
UPDATE django_content_type SET app_label = 'wagtailredirects' WHERE app_label = 'verdantredirects';

-- Update south migration history to look like we ran the new wagtailembeds migrations
DELETE FROM south_migrationhistory WHERE app_name = 'verdantredirects';
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailredirects', '0001_initial', NOW());
