export const hasRequiredPermission = (userPermissions: string[], requiredPermissions?: string[]): boolean => {
    // If no permissions are required, everyone has access
    if (!requiredPermissions || requiredPermissions.length === 0) {
        return true;
    }
    
    // Check if the user has any of the required permissions
    return requiredPermissions.some((permission) => userPermissions.includes(permission));
};
