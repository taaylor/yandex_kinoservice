CREATE TABLE IF NOT EXISTS rating (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL,
  film_id uuid NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  score smallint CHECK (
    score BETWEEN 1
    AND 10
  )
);
CREATE UNIQUE INDEX IF NOT EXISTS rating_user_id_film_id_idx ON rating (film_id, user_id);
CREATE INDEX IF NOT EXISTS rating_user_id_idx ON rating (user_id);
CREATE INDEX IF NOT EXISTS rating_film_id_idx ON rating (film_id);
CREATE TYPE mood AS ENUM ('NOTWATCHED', 'WATCHED');
CREATE TABLE IF NOT EXISTS bookmark (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL,
  film_id uuid NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  comment TEXT CHECK (
    char_length(comment) IS NULL
    OR (
      char_length(comment) >= 5
      AND char_length(comment) <= 500
    )
  ),
  status mood NOT NULL DEFAULT 'NOTWATCHED'
);
CREATE UNIQUE INDEX IF NOT EXISTS bookmark_user_id_film_id_idx ON bookmark (film_id, user_id);
CREATE INDEX IF NOT EXISTS bookmark_user_id_idx ON bookmark (user_id);
CREATE INDEX IF NOT EXISTS bookmark_film_id_idx ON bookmark (film_id);
