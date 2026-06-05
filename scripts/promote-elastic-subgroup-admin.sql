-- Promote imre.kaposi to admin in the Elastic subgroup.
-- Production: oc exec -n wkpoule-prd deploy/postgres -- psql -U wkpoule -d wkpoule -f - < scripts/promote-elastic-subgroup-admin.sql

BEGIN;

UPDATE subgroup_members sm
SET role = 'admin'
FROM subgroups sg, users u
WHERE sm.subgroup_id = sg.id
  AND sm.user_id = u.id
  AND lower(sg.name) = 'elastic'
  AND lower(u.username) = 'imre.kaposi';

COMMIT;
