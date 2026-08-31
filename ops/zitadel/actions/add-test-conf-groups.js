/**
 * Add test-conf.de access groups to OIDC tokens from ZITADEL project roles.
 *
 * Installation:
 * - Replace CHANGE_ME_ACCESS_PROJECT_ID with the ID of the project that owns
 *   the roles below.
 * - Create a ZITADEL Actions V1 Action named `addTestConfGroups`; its name must
 *   match this function name.
 * - Attach it to the Complement Token flow's Pre Userinfo creation trigger.
 */
function addTestConfGroups(ctx, api) {
  // Replace this when installing the Action in a fresh ZITADEL instance.
  const accessProjectId = "CHANGE_ME_ACCESS_PROJECT_ID";

  const stagingAccess = "staging-access";
  const observabilityAccess = "observability-access";
  const observabilityAdmin = "observability-admin";

  const groups = [];

  function addGroup(group) {
    if (!groups.includes(group)) {
      groups.push(group);
    }
  }

  if (
    ctx.v1.user === undefined ||
    ctx.v1.user.grants === undefined ||
    ctx.v1.user.grants.count === 0 ||
    !Array.isArray(ctx.v1.user.grants.grants)
  ) {
    api.v1.claims.setClaim("groups", groups);
    return;
  }

  ctx.v1.user.grants.grants.forEach((grant) => {
    const projectId = String(grant.projectId ?? grant.projectID ?? "");

    if (projectId !== accessProjectId) {
      return;
    }

    const roles = Array.isArray(grant.roles) ? grant.roles : [];

    roles.forEach((role) => {
      if (role === stagingAccess) {
        addGroup(stagingAccess);
        addGroup(observabilityAccess);
      }

      if (role === observabilityAccess) {
        addGroup(observabilityAccess);
      }

      if (role === observabilityAdmin) {
        addGroup(observabilityAccess);
        addGroup(observabilityAdmin);
      }
    });
  });

  api.v1.claims.setClaim("groups", groups);
}
