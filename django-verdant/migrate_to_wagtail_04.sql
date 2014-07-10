DELETE FROM south_migrationhistory WHERE migration = '0003_create_page_view_restriction';

ALTER TABLE wagtailcore_site DROP CONSTRAINT core_site_hostname_uniq;
ALTER TABLE "wagtailcore_site" ADD CONSTRAINT "wagtailcore_site_hostname_29d2c7f94ac026_uniq" UNIQUE ("hostname", "port");
ALTER TABLE "wagtailcore_pagerevision" ADD COLUMN "approved_go_live_at" timestamp with time zone NULL;
ALTER TABLE "wagtailcore_page" ADD COLUMN "go_live_at" timestamp with time zone NULL;
ALTER TABLE "wagtailcore_page" ADD COLUMN "expire_at" timestamp with time zone NULL;
ALTER TABLE "wagtailcore_page" ADD COLUMN "expired" boolean NOT NULL;

INSERT INTO south_migrationhistory(app_name, migration, applied) VALUES ('wagtailcore', '0003_auto__del_unique_site_hostname__add_unique_site_hostname_port', now());
INSERT INTO south_migrationhistory(app_name, migration, applied) VALUES ('wagtailcore', '0004_fields_for_scheduled_publishing', now());
INSERT INTO south_migrationhistory(app_name, migration, applied) VALUES ('wagtailcore', '0005_create_page_view_restriction', now());