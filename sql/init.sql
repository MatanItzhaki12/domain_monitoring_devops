CREATE TABLE users (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username varchar NOT NULL UNIQUE,
  password varchar NOT NULL,
  created_at timestamp NOT NULL DEFAULT now()
);

CREATE TABLE domains (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  domain varchar NOT NULL UNIQUE,
  status varchar NOT NULL DEFAULT 'pending',
  ssl_issuer varchar DEFAULT 'N/A',
  ssl_expiration varchar DEFAULT 'N/A',
  last_check timestamp
);

CREATE TABLE aux_users_domains (
  user_id integer NOT NULL,
  domain_id integer NOT NULL,
  PRIMARY KEY (user_id, domain_id)
);

CREATE INDEX index_aux_domains_user 
ON aux_users_domains (domain_id, user_id);

ALTER TABLE aux_users_domains 
ADD CONSTRAINT fk_aux_users_domains_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE aux_users_domains 
ADD CONSTRAINT fk_aux_users_domains_domain 
FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE;
