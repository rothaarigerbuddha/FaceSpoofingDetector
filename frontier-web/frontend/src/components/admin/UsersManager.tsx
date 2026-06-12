"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/input";
import {
  createUser,
  updateUserRoles,
  deleteUser,
} from "@/services/user.service";
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

type Role = { id: number; name: string };
type User = { id: number; username: string; roles: Role[] };

type Props = {
  users: User[];
  roles: Role[];
};

// ─── Inline Role-pill Multi-Select ──────────────────────────────────────────
function RoleMultiSelect({
  allRoles,
  selected,
  onChange,
}: {
  allRoles: Role[];
  selected: number[];
  onChange: (ids: number[]) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500 whitespace-nowrap">Add role:</span>
        <Select
          onValueChange={(val: string | null) => {
            if (!val) return;
            const id = parseInt(val);
            if (!isNaN(id) && !selected.includes(id)) onChange([...selected, id]);
          }}
        >
          <SelectTrigger className="text-sm h-9 flex-1">
            <SelectValue placeholder="Select…" />
          </SelectTrigger>
          <SelectContent>
            {allRoles
              .filter((r) => !selected.includes(r.id))
              .map((r) => (
                <SelectItem key={r.id} value={String(r.id)}>
                  {r.name}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>
      </div>
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.map((id) => {
            const role = allRoles.find((r) => r.id === id);
            if (!role) return null;
            return (
              <span
                key={id}
                className="bg-primary/10 text-primary text-xs px-2 py-1 rounded inline-flex items-center gap-1.5 border border-primary/20"
              >
                {role.name}
                <button
                  type="button"
                  onClick={() => onChange(selected.filter((x) => x !== id))}
                  className="text-primary/70 hover:text-primary font-bold leading-none"
                >
                  &times;
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Create User Modal ───────────────────────────────────────────────────────
function CreateUserModal({
  roles,
  onClose,
}: {
  roles: Role[];
  onClose: () => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [selectedRoles, setSelectedRoles] = useState<number[]>([]);
  const [pending, setPending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPending(true);

    const fd = new FormData();
    fd.append("username", username);
    fd.append("password", password);
    if (selectedRoles.length > 0)
      fd.append("roleIds", JSON.stringify(selectedRoles));

    const res = await createUser(fd);
    setPending(false);

    if (res.error) {
      toast.error(res.error);
    } else {
      toast.success(`User "${username}" created successfully!`);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-popover text-popover-foreground rounded-xl shadow-xl max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
        <h3 className="text-lg font-bold mb-1">Create New User</h3>
        <p className="text-xs text-muted-foreground mb-5">
          Fill out the fields below. Role assignment is optional.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-1">
              Username
            </label>
            <Input
              placeholder="e.g. johndoe"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={pending}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-foreground block mb-1">
              Password
            </label>
            <Input
              type="password"
              placeholder="Min. 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={pending}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-foreground block mb-1">
              Roles <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <RoleMultiSelect
              allRoles={roles}
              selected={selectedRoles}
              onChange={setSelectedRoles}
            />
          </div>

          {/* Errors shown via toast */}

          <div className="flex justify-end gap-2 mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={pending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={pending || !username.trim() || !password.trim()}
            >
              {pending ? "Creating..." : "Create User"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Edit Roles Modal ────────────────────────────────────────────────────────
function EditUserRolesModal({
  user,
  roles,
  onClose,
}: {
  user: User;
  roles: Role[];
  onClose: () => void;
}) {
  const [selectedRoles, setSelectedRoles] = useState<number[]>(
    user.roles.map((r) => r.id)
  );
  const [pending, setPending] = useState(false);

  const handleSave = async () => {
    setPending(true);
    const res = await updateUserRoles(user.id, selectedRoles);
    setPending(false);
    if (res.error) {
      toast.error(res.error);
    } else {
      toast.success(`Roles updated for "${user.username}"!`);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-popover text-popover-foreground rounded-xl shadow-xl max-w-sm w-full p-6 animate-in zoom-in-95 duration-200">
        <h3 className="text-lg font-bold mb-1">Edit User Roles</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Assign or revoke roles for <strong>{user.username}</strong>.
        </p>

        <div className="max-h-52 overflow-y-auto mb-5 border-y py-3 space-y-2">
          {roles.map((role) => (
            <label
              key={role.id}
              className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 p-1.5 rounded"
            >
              <input
                type="checkbox"
                checked={selectedRoles.includes(role.id)}
                onChange={(e) => {
                  if (e.target.checked)
                    setSelectedRoles([...selectedRoles, role.id]);
                  else
                    setSelectedRoles(selectedRoles.filter((id) => id !== role.id));
                }}
                className="rounded border-input text-primary focus:ring-primary"
              />
              <span>{role.name}</span>
            </label>
          ))}
          {roles.length === 0 && (
            <p className="text-sm text-muted-foreground italic">No roles available.</p>
          )}
        </div>

        {/* Errors shown via toast */}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={pending}>
            {pending ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export default function UsersManager({ users, roles }: Props) {
  const [showCreate, setShowCreate] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);

  return (
    <div className="mt-6">
      {/* Header Row */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">
          {users.length} user{users.length !== 1 ? "s" : ""} total
        </p>
        <Button onClick={() => setShowCreate(true)}>+ Create User</Button>
      </div>

      {/* Users Table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 border-b">
            <tr>
              <th className="px-4 py-3 font-medium text-foreground w-12">ID</th>
              <th className="px-4 py-3 font-medium text-foreground">Username</th>
              <th className="px-4 py-3 font-medium text-foreground">Roles</th>
              <th className="px-4 py-3 font-medium text-foreground text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-muted/50">
                <td className="px-4 py-3 text-muted-foreground">{user.id}</td>
                <td className="px-4 py-3 font-medium">{user.username}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {user.roles.length === 0 ? (
                      <span className="text-muted-foreground italic text-xs">
                        No roles
                      </span>
                    ) : (
                      user.roles.map((role) => (
                        <span
                          key={role.id}
                          className="bg-primary/10 text-primary text-xs px-2 py-0.5 rounded border border-primary/20"
                        >
                          {role.name}
                        </span>
                      ))
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-3">
                    {/* Edit */}
                    <button
                      onClick={() => setEditUser(user)}
                      className="text-blue-500 hover:text-blue-700"
                      title="Edit Roles"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M12 20h9" />
                        <path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z" />
                      </svg>
                    </button>

                    {/* Delete */}
                    <AlertDialog>
                      <AlertDialogTrigger>
                        <div
                          className="text-red-500 hover:text-red-700 cursor-pointer inline-flex"
                          title="Delete User"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M3 6h18" />
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                          </svg>
                        </div>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete User</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to permanently delete{" "}
                            <strong>{user.username}</strong>? This action cannot
                            be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={async () => {
                              const res = await deleteUser(user.id);
                              if (res?.error) toast.error(res.error);
                              else toast.success(`User "${user.username}" deleted.`);
                            }}
                            className="bg-red-500 hover:bg-red-600 text-white"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td
                  colSpan={4}
                  className="px-4 py-10 text-center text-muted-foreground text-sm italic"
                >
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {showCreate && (
        <CreateUserModal roles={roles} onClose={() => setShowCreate(false)} />
      )}
      {editUser && (
        <EditUserRolesModal
          user={editUser}
          roles={roles}
          onClose={() => setEditUser(null)}
        />
      )}
    </div>
  );
}
