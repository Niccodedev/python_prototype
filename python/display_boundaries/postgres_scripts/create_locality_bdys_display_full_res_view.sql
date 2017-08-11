CREATE VIEW admin_bdys_201705.vw_locality_bdys_display_full_res AS
SELECT loc.gid,
       loc.locality_pid,
       loc.locality_name,
       loc.postcode, state,
       loc.locality_class,
       loc.address_count,
       loc.street_count,
       bdy.geom
  FROM admin_bdys_201705.locality_bdys_display as loc
  INNER JOIN admin_bdys_201705.locality_bdys_display_full_res as bdy
  ON loc.locality_pid = bdy.locality_pid;

select Count(*) from admin_bdys_201705.vw_locality_bdys_display_full_res; -- 15587

select Count(*) from admin_bdys_201705.locality_bdys_display; -- 15587

select Count(*) from admin_bdys_201705.locality_bdys_display_full_res; -- 15587