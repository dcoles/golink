-- Sample database
-- Run `sqlite3 database '.read sample_database.sql'` to create.

CREATE TABLE Golinks (name STRING PRIMARY KEY, url STRING);

INSERT INTO Golinks (name, url) VALUES ('google', 'https://www.google.com');
INSERT INTO Golinks (name, url) VALUES ('urlparse', 'https://docs.python.org/3/library/urllib.parse.html#url-parsing');
INSERT INTO Golinks (name, url) VALUES ('drive', 'http://drive.google.com/');
INSERT INTO Golinks (name, url) VALUES ('pylib', 'https://docs.python.org/3/library/');
INSERT INTO Golinks (name, url) VALUES ('search', 'https://www.google.com/search?q=');
