import buildbot.www.authz.roles as bb_roles


class DeveloperRoleIfConnected(bb_roles.RolesFromBase):
    """Sets the 'developer' role to all authenticated users."""
    def getRolesFromUser(self, userDetails):
        roles = []
        if 'email' in userDetails:
            roles.append('developer')
        return roles
