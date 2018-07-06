-- Sample database
-- Run `sqlite3 database '.read sample_database.sql'` to create.

CREATE TABLE IF NOT EXISTS Golinks (name VARCHAR PRIMARY KEY, url VARCHAR NOT NULL, owner VARCHAR);

INSERT OR REPLACE INTO Golinks (name, url) VALUES ('golink', 'https://github.com/dcoles/golink');
INSERT OR REPLACE INTO Golinks (name, url) VALUES ('google', 'https://www.google.com');
INSERT OR REPLACE INTO Golinks (name, url) VALUES ('urlparse', 'https://docs.python.org/3/library/urllib.parse.html#url-parsing');
INSERT OR REPLACE INTO Golinks (name, url) VALUES ('drive', 'http://drive.google.com/');
INSERT OR REPLACE INTO Golinks (name, url) VALUES ('pylib', 'https://docs.python.org/3/library/');
INSERT OR REPLACE INTO Golinks (name, url) VALUES ('search', 'https://www.google.com/search?q=');
