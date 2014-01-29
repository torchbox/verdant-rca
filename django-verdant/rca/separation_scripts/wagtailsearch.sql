-- Rename all verdantsearch tables to wagtailsearch
ALTER TABLE verdantsearch_query RENAME TO wagtailsearch_query;
ALTER TABLE verdantsearch_querydailyhits RENAME TO wagtailsearch_querydailyhits;
ALTER TABLE verdantsearch_editorspick RENAME TO wagtailsearch_editorspick;
ALTER TABLE verdantsearch_searchtest RENAME TO wagtailsearch_searchtest;
ALTER TABLE verdantsearch_searchtestchild RENAME TO wagtailsearch_searchtestchild;

-- Fix app_label of verdantimages content_types
UPDATE django_content_type SET app_label = 'wagtailsearch' WHERE app_label = 'verdantsearch';

-- Update south migration history to look like we ran the new wagtailsearch migrations
DELETE FROM south_migrationhistory WHERE app_name = 'verdantsearch';
INSERT INTO south_migrationhistory (app_name, migration, applied) VALUES ('wagtailsearch', '0001_initial', NOW());
