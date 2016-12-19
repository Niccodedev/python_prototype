-- Table: admin_bdys_201611.locality_bdys_display_web
DROP TABLE IF EXISTS admin_bdys_201611.locality_bdys_display_web;

CREATE TABLE admin_bdys_201611.locality_bdys_display_web
(
  gid integer NOT NULL,
  locality_pid character varying(16) NOT NULL,
  locality_name character varying(100) NOT NULL,
  postcode character(4),
  state character varying(3) NOT NULL,
  locality_class character varying(50) NOT NULL,
  address_count integer NOT NULL,
  street_count integer NOT NULL,
  geom geometry(MultiPolygon,900913) NOT NULL,
  CONSTRAINT localities_bdys_display_web_pk PRIMARY KEY (locality_pid)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE admin_bdys_201611.locality_bdys_display_web
  OWNER TO postgres;

CREATE INDEX localities_bdys_display_web_geom_idx
  ON admin_bdys_201611.locality_bdys_display_web
  USING gist
  (geom);
ALTER TABLE admin_bdys_201611.locality_bdys_display_web CLUSTER ON localities_bdys_display_web_geom_idx;


INSERT INTO admin_bdys_201611.locality_bdys_display_web
SELECT gid, locality_pid, locality_name, postcode, state, locality_class, address_count, street_count, ST_Transform(geom, 900913)
    FROM admin_bdys_201611.locality_bdys_display;

