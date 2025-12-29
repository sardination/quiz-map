-- 02 Add active flag to pubs

ALTER TABLE pub ADD COLUMN active INTEGER NOT NULL DEFAULT 1;