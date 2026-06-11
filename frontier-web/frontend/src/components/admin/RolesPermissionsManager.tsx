"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/input";
import { createRole, createPermission, deleteRole, deletePermission, updateRolePermissions } from "@/services/admin.service";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = {
  roles: any[];
  permissions: any[];
};

export default function RolesPermissionsManager({ roles, permissions }: Props) {
  // Create Role State
  const [roleName, setRoleName] = useState("");
  const [newRolePerms, setNewRolePerms] = useState<number[]>([]);
  const [isRolePending, setIsRolePending] = useState(false);

  // Edit Role State
  const [editingRoleId, setEditingRoleId] = useState<number | null>(null);
  const [editRolePerms, setEditRolePerms] = useState<number[]>([]);
  const [isEditPending, setIsEditPending] = useState(false);

  // Create Permission State
  const [permName, setPermName] = useState("");
  const [isPermPending, setIsPermPending] = useState(false);

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRolePending(true);
    
    const formData = new FormData();
    formData.append("name", roleName);
    if (newRolePerms.length > 0) {
      formData.append("permissionIds", JSON.stringify(newRolePerms));
    }
    
    const res = await createRole(formData);
    if (res.error) {
      toast.error(res.error);
    } else {
      toast.success(`Role "${roleName}" created!`);
      setRoleName("");
      setNewRolePerms([]);
    }
    setIsRolePending(false);
  };

  const handleCreatePermission = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsPermPending(true);
    
    const formData = new FormData();
    formData.append("name", permName);
    
    const res = await createPermission(formData);
    if (res.error) {
      toast.error(res.error);
    } else {
      toast.success(`Permission "${permName}" created!`);
      setPermName("");
    }
    setIsPermPending(false);
  };

  const handleSaveEditRole = async () => {
    if (editingRoleId === null) return;
    setIsEditPending(true);
    const res = await updateRolePermissions(editingRoleId, editRolePerms);
    setIsEditPending(false);
    if (res.error) {
      toast.error(res.error);
    } else {
      toast.success("Role permissions updated!");
      setEditingRoleId(null);
      setEditRolePerms([]);
    }
  };

  const startEditingRole = (role: any) => {
    setEditingRoleId(role.id);
    setEditRolePerms(role.permissions?.map((p: any) => p.id) || []);
  };

  return (
    <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8 relative">
      {/* Roles Section */}
      <div className="bg-card text-card-foreground p-6 rounded-lg shadow-sm border flex flex-col h-full">
        <h2 className="text-xl font-bold mb-4">Roles</h2>
        
        <form onSubmit={handleCreateRole} className="mb-6 flex flex-col gap-3">
          <div className="flex gap-2">
            <Input 
              placeholder="New role name (e.g., Moderator)" 
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              disabled={isRolePending}
              className="flex-1"
            />
            <Button type="submit" disabled={isRolePending || !roleName.trim()}>
              {isRolePending ? "Creating..." : "Create Role"}
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Optional Permissions:</span>
            <Select
                onValueChange={(val: string | null) => {
                  if (!val) return;
                  const id = parseInt(val);
                  if (!isNaN(id) && !newRolePerms.includes(id)) {
                    setNewRolePerms([...newRolePerms, id]);
                  }
                }}
              >
                <SelectTrigger className="w-[160px] text-sm h-8">
                  <SelectValue placeholder="+ Add..." />
                </SelectTrigger>
                <SelectContent>
                  {permissions
                    .filter((p) => !newRolePerms.includes(p.id))
                    .map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        {p.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
          </div>

          {newRolePerms.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-1">
              {newRolePerms.map(id => {
                const p = permissions.find(x => x.id === id);
                if(!p) return null;
                return (
                  <span key={id} className="bg-primary/10 text-primary text-xs px-2 py-1 rounded inline-flex items-center gap-1.5 border border-primary/20">
                    {p.name}
                    <button type="button" onClick={() => setNewRolePerms(prev => prev.filter(x => x !== id))} className="text-primary/70 hover:text-primary font-bold leading-none">
                      &times;
                    </button>
                  </span>
                )
              })}
            </div>
          )}
          
          {/* Errors shown via toast */}
        </form>
        
        <div className="overflow-y-auto max-h-[400px] flex-1 border rounded-lg">
            <table className="w-full text-sm text-left border-collapse">
                <thead className="bg-muted/50 border-b sticky top-0">
                    <tr>
                        <th className="px-4 py-3 font-medium text-foreground">ID</th>
                        <th className="px-4 py-3 font-medium text-foreground">Role Name</th>
                        <th className="px-4 py-3 font-medium text-foreground text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y relative">
                    {roles.map(role => (
                        <tr key={role.id} className="hover:bg-muted/50">
                            <td className="px-4 py-3 text-muted-foreground w-12">{role.id}</td>
                            <td className="px-4 py-3 font-medium">
                                {role.name}
                                <div className="text-xs font-normal text-muted-foreground mt-0.5">
                                    {role.permissions?.length || 0} permissions
                                </div>
                            </td>
                            <td className="px-4 py-3 text-right">
                                <div className="flex justify-end gap-2">
                                    <button 
                                      onClick={() => startEditingRole(role)}
                                      className="text-blue-500 hover:text-blue-700" 
                                      title="Edit Permissions">
                                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"></path></svg>
                                    </button>
                                    <AlertDialog>
                                      <AlertDialogTrigger>
                                        <div className="text-red-500 hover:text-red-700 cursor-pointer inline-flex" title="Delete Role">
                                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                                        </div>
                                      </AlertDialogTrigger>
                                      <AlertDialogContent>
                                        <AlertDialogHeader>
                                          <AlertDialogTitle>Delete Role</AlertDialogTitle>
                                          <AlertDialogDescription>Are you sure you want to delete the role "{role.name}"? This action cannot be undone and will remove it from all users.</AlertDialogDescription>
                                        </AlertDialogHeader>
                                        <AlertDialogFooter>
                                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                                          <AlertDialogAction onClick={async () => {
                                              const res = await deleteRole(role.id);
                                              if (res?.error) toast.error(res.error);
                                              else toast.success(`Role "${role.name}" deleted.`);
                                            }} className="bg-red-500 hover:bg-red-600 text-white">Delete</AlertDialogAction>
                                        </AlertDialogFooter>
                                      </AlertDialogContent>
                                    </AlertDialog>
                                </div>
                            </td>
                        </tr>
                    ))}
                    {roles.length === 0 && (
                        <tr>
                            <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground text-sm">No roles found</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
      </div>

      {/* Edit Role Overlay (Absolute centered inside parent container) */}
      {editingRoleId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-popover text-popover-foreground rounded-xl shadow-xl max-w-sm w-full p-6 animate-in zoom-in-95 duration-200">
            <h3 className="text-lg font-bold mb-1">Edit Role Permissions</h3>
            <p className="text-xs text-muted-foreground mb-4">Select the permissions this role should have.</p>
            
            <div className="max-h-60 overflow-y-auto mb-6 pr-2 space-y-2 border-y py-3">
              {permissions.map(p => (
                <label key={p.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 p-1.5 rounded">
                  <input 
                    type="checkbox" 
                    checked={editRolePerms.includes(p.id)} 
                    onChange={(e) => {
                      if (e.target.checked) setEditRolePerms([...editRolePerms, p.id]);
                      else setEditRolePerms(editRolePerms.filter(id => id !== p.id));
                    }}
                    className="rounded border-input text-primary focus:ring-primary"
                  />
                  <span>{p.name}</span>
                </label>
              ))}
              {permissions.length === 0 && <p className="text-sm text-muted-foreground italic">No system permissions exist yet.</p>}
            </div>
            
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingRoleId(null)} disabled={isEditPending}>Cancel</Button>
              <Button onClick={handleSaveEditRole} disabled={isEditPending}>
                {isEditPending ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Permissions Section */}
      {/* <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex flex-col h-full">
        <h2 className="text-xl font-bold mb-4">Permissions</h2>
        
        <form onSubmit={handleCreatePermission} className="flex gap-2 mb-6">
          <Input 
            placeholder="New permission (e.g., posts.publish)" 
            value={permName}
            onChange={(e) => setPermName(e.target.value)}
            disabled={isPermPending}
            className="flex-1"
          />
          <Button type="submit" disabled={isPermPending || !permName.trim()}>
            {isPermPending ? "Creating..." : "Create"}
          </Button>
        </form>
        
        <div className="overflow-y-auto max-h-[400px] flex-1 border rounded-lg">
            <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 border-b sticky top-0">
                    <tr>
                        <th className="px-4 py-3 font-medium text-gray-700">ID</th>
                        <th className="px-4 py-3 font-medium text-gray-700">Permission Name</th>
                        <th className="px-4 py-3 font-medium text-gray-700 text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y">
                    {permissions.map(perm => (
                        <tr key={perm.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-gray-500 w-12">{perm.id}</td>
                            <td className="px-4 py-3 font-medium">{perm.name}</td>
                            <td className="px-4 py-3 text-right">
                                <AlertDialog>
                                  <AlertDialogTrigger>
                                    <div className="text-red-500 hover:text-red-700 cursor-pointer inline-flex" title="Delete Permission">
                                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                                    </div>
                                  </AlertDialogTrigger>
                                  <AlertDialogContent>
                                    <AlertDialogHeader>
                                      <AlertDialogTitle>Delete Permission</AlertDialogTitle>
                                      <AlertDialogDescription>Are you sure you want to delete "{perm.name}"? It will be immediately removed from all roles that possess it.</AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                                      <AlertDialogAction onClick={async () => {
                                          const res = await deletePermission(perm.id);
                                          if (res?.error) toast.error(res.error);
                                          else toast.success(`Permission "${perm.name}" deleted.`);
                                        }} className="bg-red-500 hover:bg-red-600 text-white">Delete</AlertDialogAction>
                                    </AlertDialogFooter>
                                  </AlertDialogContent>
                                </AlertDialog>
                            </td>
                        </tr>
                    ))}
                    {permissions.length === 0 && (
                        <tr>
                            <td colSpan={3} className="px-4 py-8 text-center text-gray-500 text-sm">No permissions found</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
      </div> */}
    </div>
  );
}
