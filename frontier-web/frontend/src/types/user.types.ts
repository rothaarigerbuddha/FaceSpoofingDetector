
// Reflects the actual JWT claims returned by the backend
// JWT contains: name (= username), role (one per assigned role)
export interface UserInfo {
  username: string;
  roles: string[];  // e.g. ["Admin", "Editor"]
}