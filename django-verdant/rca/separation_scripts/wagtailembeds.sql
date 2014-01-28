-- Rename all verdantembeds tables to wagtailembeds
ALTER TABLE verdantembeds_embed RENAME TO wagtailembeds_embed;

-- Fix app_label of core content_types
UPDATE django_content_type SET app_label = 'wagtailembeds' WHERE app_label = 'verdantembeds';

-- Update south migration history to look like we ran the new wagtailembeds migrations
DELETE FROM south_migrationhistory WHERE app_name = 'verdantembeds';
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailembeds', '0001_initial', NOW());
