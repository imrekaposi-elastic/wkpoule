-- Remove all predictions (and milestone rows) for admin accounts.
-- Production: oc exec -n wkpoule-prd deploy/postgres -- psql -U wkpoule -d wkpoule -f - < scripts/delete-admin-predictions.sql

BEGIN;

DELETE FROM user_prediction_milestones
WHERE user_id IN (SELECT id FROM users WHERE is_admin = TRUE);

DELETE FROM predictions
WHERE user_id IN (SELECT id FROM users WHERE is_admin = TRUE);

COMMIT;
