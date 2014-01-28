-- Rename all verdantimages tables to wagtailimages
ALTER TABLE verdantimages_image RENAME TO wagtailimages_image;
ALTER TABLE verdantimages_filter RENAME TO wagtailimages_filter;
ALTER TABLE verdantimages_rendition RENAME TO wagtailimages_rendition;

-- Fix app_label of verdantimages content_types
UPDATE django_content_type SET app_label = 'wagtailimages' WHERE app_label = 'verdantimages';

-- Update south migration history to look like we ran the new wagtailimages migrations
DELETE FROM south_migrationhistory WHERE app_name = 'verdantimages';
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailimages', '0001_initial', NOW());
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailimages', '0002_initial_data', NOW());
