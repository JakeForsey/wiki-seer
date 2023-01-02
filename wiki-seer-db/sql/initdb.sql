CREATE USER writer WITH PASSWORD 'writer';
CREATE USER reader WITH PASSWORD 'reader';
CREATE TABLE page_views (title TEXT, date DATE, page_views INTEGER NOT NULL, PRIMARY KEY (title, date));
GRANT ALL PRIVILEGES ON TABLE page_views TO writer;
GRANT ALL PRIVILEGES ON TABLE page_views TO reader;
