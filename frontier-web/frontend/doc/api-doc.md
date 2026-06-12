# FrontierWeb — Detailed API Reference

## Overview

| Property | Value |
|---|---|
| **Base URL (dev)** | `http://localhost:5160` |
| **Default content type** | `application/json` |
| **Auth mechanism** | JWT Bearer (`Authorization: Bearer <token>`) |
| **Database** | SQLite (`blog.db` in project root) |
| **Token algorithm** | HMAC-SHA256 |
| **Token expiry** | 8 hours |
| **CORS allowed origins** | `http://localhost:5173` |

---

## Shared Object Schemas

These objects appear in multiple endpoint responses.

### `PermissionResponse`
```json
{
  "id": 1,            // int — auto-generated primary key
  "name": "posts.read" // string — unique permission name
}
```

### `RoleResponse`
```json
{
  "id": 1,
  "name": "Admin",
  "permissions": [ PermissionResponse, ... ]  // all permissions assigned to this role
}
```

### `UserResponse`
```json
{
  "id": 1,
  "username": "admin",  // password is NEVER returned
  "roles": [ RoleResponse, ... ]  // full role + permission tree
}
```

### `PostObject`
```json
{
  "id": 1,
  "title": "Hello, world!",
  "slug": "hello-world",
  "content": "Full post body...",
  "notes": "Internal note visible in admin",
  "author": "admin",
  "image": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "published": true,
  "createdAtUtc": "2026-06-02T16:12:00Z",
  "updatedAtUtc": "2026-06-02T16:12:00Z"
}
```

### `Paged<T>`
```json
{
  "items": [ PostObject, ... ],
  "total": 42,     // total records matching query (before pagination)
  "page": 1,       // current page (1-indexed)
  "pageSize": 10   // items per page
}
```

---

## Authentication

### How JWT Works in This API

1. Call `POST /auth/login` with credentials.
2. Receive an `access_token` (JWT).
3. On subsequent requests to protected routes, send the header:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### JWT Token Claims

The token contains:

| Claim | Value |
|-------|-------|
| `name` (`ClaimTypes.Name`) | The username |
| `role` (`ClaimTypes.Role`) | One entry **per role** assigned to the user |
| `iss` | `BlogApi` |
| `aud` | `BlogApiClients` |
| `exp` | 8 hours from issue time |

### JWT Configuration (`appsettings.Development.json`)

```json
{
  "Auth": {
    "Issuer": "BlogApi",
    "Audience": "BlogApiClients",
    "Key": "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
  }
}
```

> ⚠️ The key must be changed before any production deployment.

### Password Hashing

Passwords are hashed using **PBKDF2-SHA256** with:
- 16-byte random salt
- 100,000 iterations
- 32-byte output key

Stored format: `base64(salt):base64(hash)`. Passwords are **never stored or returned in plain text**.

---

## Endpoints

---

## 1. Auth

### `POST /auth/login`

Authenticates a user and returns a signed JWT token.

**Auth required:** ❌ No  
**Route:** `POST /auth/login`

#### Request Body

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `username` | string | ✅ | — | Case-sensitive |
| `password` | string | ✅ | — | Plain text, verified against PBKDF2 hash |

```json
// Request
{
  "username": "admin",
  "password": "admin123"
}
```

#### Responses

| Status | When |
|--------|------|
| `200 OK` | Credentials are valid |
| `401 Unauthorized` | User not found **or** password mismatch |

> Note: Both "user not found" and "wrong password" return the same `401` — no distinction is exposed to prevent username enumeration.

```json
// 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...",
  "token_type": "Bearer",
  "expires_in": 28800   // seconds (= 8 hours)
}

// 401 Unauthorized — empty body
```

---

## 2. Posts

> ⚠️ **Authorization note:** `POST`, `PUT`, and `DELETE` routes have `[Authorize(Policy = "AdminOnly")]` commented out. They are currently **open to all callers** without authentication.

**`AdminOnly` policy** requires the JWT role claim to contain `"Admin"`.

---

### `GET /posts`

Returns a paginated, optionally filtered list of posts.

**Auth required:** ❌ No  
**Route:** `GET /posts`

#### Query Parameters

| Param | Type | Required | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `q` | string | ❌ | — | — | Searches `Title`, `Content`, and `Slug` (case-insensitive via SQLite) |
| `page` | int | ❌ | `1` | Min clamped to `1` | Page number |
| `pageSize` | int | ❌ | `10` | Clamped to `1–100` | Items per page |
| `published` | bool? | ❌ | `true` | `true`, `false`, or omit | If omitted defaults to `true`. To return **all** posts regardless of status, pass no value or use `null` via a custom client |

#### Ordering

Results are ordered **descending by `createdAtUtc`** (newest first).

#### Example Requests

```
GET /posts
GET /posts?q=hello
GET /posts?page=2&pageSize=5
GET /posts?published=false
GET /posts?q=world&page=1&pageSize=3&published=true
```

#### Response — `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "title": "Hello, world!",
      "slug": "hello-world",
      "content": "This is your first post.",
      "notes": "Internal note",
      "author": "admin",
      "image": "abc123.jpg",
      "published": true,
      "createdAtUtc": "2026-06-02T16:12:00Z",
      "updatedAtUtc": "2026-06-02T16:12:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10
}
```

---

### `GET /posts/{idOrSlug}`

Fetches a single post by its numeric ID or URL slug.

**Auth required:** ❌ No  
**Route:** `GET /posts/{idOrSlug}`

#### Path Parameters

| Param | Type | Notes |
|-------|------|-------|
| `idOrSlug` | string | If the value can be parsed as an integer, it is looked up as an ID. Otherwise it is matched as a `slug`. |

#### Examples

```
GET /posts/1
GET /posts/hello-world
```

#### Responses

| Status | When |
|--------|------|
| `200 OK` | Post found |
| `404 Not Found` | No post matches the given ID or slug |

```json
// 200 OK
{
  "id": 1,
  "title": "Hello, world!",
  "slug": "hello-world",
  "content": "This is your first post.",
  "notes": "Internal note",
  "author": "admin",
  "image": "abc123.jpg",
  "published": true,
  "createdAtUtc": "2026-06-02T16:12:00Z",
  "updatedAtUtc": "2026-06-02T16:12:00Z"
}
```

---

### `POST /posts`

Creates a new blog post.

**Auth required:** ⚠️ Should be `AdminOnly` — currently disabled  
**Route:** `POST /posts`

#### Request Body

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `title` | string | ✅ | max 200 chars | Trimmed before save |
| `slug` | string | ✅ | max 200 chars, **globally unique** | Trimmed before save. Used as the URL identifier |
| `content` | string | ✅ | — | Full post body (HTML or Markdown — server stores as-is) |
| `notes` | string | ✅ | — | Internal notes, not intended for public display |
| `author` | string | ✅ | max 200 chars | Display name of the author |
| `image` | string | ✅ | — | Filename returned from `POST /uploads` |
| `published` | bool | ❌ | — | Default `true`. Set to `false` to save as draft |

```json
// Request
{
  "title": "My New Post",
  "slug": "my-new-post",
  "content": "<h1>Hello</h1><p>Post body...</p>",
  "notes": "Remember to review before sharing",
  "author": "admin",
  "image": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "published": true
}
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `201 Created` | Post saved successfully | Full `PostObject` |
| `409 Conflict` | Another post already uses the same slug | Error string |

```json
// 201 Created
{
  "id": 2,
  "title": "My New Post",
  "slug": "my-new-post",
  "content": "<h1>Hello</h1><p>Post body...</p>",
  "notes": "Remember to review before sharing",
  "author": "admin",
  "image": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "published": true,
  "createdAtUtc": "2026-06-02T16:45:00Z",
  "updatedAtUtc": "2026-06-02T16:45:00Z"
}

// 409 Conflict
"Slug must be unique."
```

> `Location` response header: `GET /posts/2`

---

### `PUT /posts/{id}`

Updates an existing post. Only fields that are supplied are applied — `null`/omitted fields are ignored.

**Auth required:** ⚠️ Should be `AdminOnly` — currently disabled  
**Route:** `PUT /posts/{id}`

#### Path Parameters

| Param | Type | Notes |
|-------|------|-------|
| `id` | int | The numeric post ID |

#### Request Body (all fields optional)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `title` | string? | max 200 chars | Ignored if `null` or empty |
| `slug` | string? | max 200 chars, **globally unique** | Trimmed; must not match any **other** post's slug |
| `content` | string? | — | Ignored if `null` |
| `notes` | string? | — | Ignored if `null` |
| `author` | string? | max 200 chars | Ignored if `null` |
| `image` | string? | — | Ignored if `null` |
| `published` | bool? | — | Ignored if `null` |

```json
// Request — partial update (only title and published changed)
{
  "title": "Updated Title",
  "published": false
}

// Request — full update
{
  "title": "Updated Title",
  "slug": "updated-slug",
  "content": "New content",
  "notes": "Updated notes",
  "author": "editor",
  "image": "new-image.jpg",
  "published": false
}
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | Post updated | Full updated `PostObject` |
| `404 Not Found` | No post with given ID | Empty body |
| `409 Conflict` | New slug is already used by another post | Error string |

```json
// 200 OK
{
  "id": 2,
  "title": "Updated Title",
  "slug": "my-new-post",
  "content": "<h1>Hello</h1><p>Post body...</p>",
  "notes": "Remember to review before sharing",
  "author": "admin",
  "image": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "published": false,
  "createdAtUtc": "2026-06-02T16:45:00Z",
  "updatedAtUtc": "2026-06-02T17:00:00Z"
}

// 409 Conflict
"Slug must be unique."
```

---

### `DELETE /posts/{id}`

Deletes a post permanently.

**Auth required:** ⚠️ Should be `AdminOnly` — currently disabled  
**Route:** `DELETE /posts/{id}`

#### Path Parameters

| Param | Type | Notes |
|-------|------|-------|
| `id` | int | The numeric post ID |

#### Responses

| Status | When |
|--------|------|
| `204 No Content` | Deleted successfully |
| `404 Not Found` | No post with given ID |

---

## 3. Uploads

### `POST /uploads`

Uploads an image file to the server's static files directory. Returns a filename to be stored in a post's `image` field.

**Auth required:** ⚠️ Should be `AdminOnly` — currently disabled  
**Route:** `POST /uploads`  
**Content-Type:** `multipart/form-data`

#### Form Data

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | file | ✅ | Any file. Must not be empty (`Length > 0`) |

#### Behavior

- A **UUID v4 filename** is generated: `{Guid.NewGuid()}{original extension}`
- File is saved to: `wwwroot/images/posts/<filename>`
- Directory is auto-created if it does not exist
- The **original filename is discarded** — only the extension is preserved

#### Accessing Uploaded Images

Images are served as static files:

```
GET http://localhost:5160/images/posts/<filename>
```

For example, if the upload returns `{ "url": "abc123.jpg" }`, the full image URL is:
```
http://localhost:5160/images/posts/abc123.jpg
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | File uploaded | `{ "url": "<filename>" }` |
| `400 Bad Request` | No file sent or file is empty | Error string |

```json
// 200 OK
{
  "url": "550e8400-e29b-41d4-a716-446655440000.jpg"
}

// 400 Bad Request
"No file uploaded."
```

---

## 4. Permissions

Permissions are simple named capabilities (e.g. `posts.read`, `users.manage`) that can be assigned to roles.

> There is **no authorization** on any permission endpoints.

---

### `GET /permissions`

Returns all permissions, ordered alphabetically by name.

**Route:** `GET /permissions`

#### Response — `200 OK`

```json
[
  { "id": 1, "name": "posts.read" },
  { "id": 2, "name": "posts.write" },
  { "id": 3, "name": "users.manage" }
]
```

---

### `GET /permissions/{id}`

Returns a single permission.

**Route:** `GET /permissions/{id}`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int |

#### Responses

| Status | When |
|--------|------|
| `200 OK` | Found |
| `404 Not Found` | No permission with that ID |

```json
// 200 OK
{ "id": 1, "name": "posts.read" }
```

---

### `POST /permissions`

Creates a new permission.

**Route:** `POST /permissions`

#### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ | max 100 chars; trimmed; **globally unique** |

```json
// Request
{ "name": "posts.delete" }
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `201 Created` | Created | `PermissionResponse` |
| `409 Conflict` | Name already exists | Error string |

```json
// 201 Created
{ "id": 4, "name": "posts.delete" }

// 409 Conflict
"Permission name must be unique."
```

> `Location` response header: `GET /permissions/4`

---

### `DELETE /permissions/{id}`

Deletes a permission. **Cascade:** The permission is also removed from all roles that had it assigned (via DB cascade delete on `RolePermissions`).

**Route:** `DELETE /permissions/{id}`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int |

#### Responses

| Status | When |
|--------|------|
| `204 No Content` | Deleted |
| `404 Not Found` | No permission with that ID |

---

## 5. Roles

Roles group permissions together and can be assigned to users.

> There is **no authorization** on any role endpoints.

---

### `GET /roles`

Returns all roles (with their permissions), ordered alphabetically by name.

**Route:** `GET /roles`

#### Response — `200 OK`

```json
[
  {
    "id": 1,
    "name": "Admin",
    "permissions": [
      { "id": 1, "name": "posts.read" },
      { "id": 2, "name": "posts.write" },
      { "id": 3, "name": "users.manage" }
    ]
  }
]
```

---

### `GET /roles/{id}`

Returns a single role with its permissions.

**Route:** `GET /roles/{id}`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int |

#### Responses

| Status | When |
|--------|------|
| `200 OK` | Found |
| `404 Not Found` | No role with that ID |

```json
// 200 OK
{
  "id": 1,
  "name": "Admin",
  "permissions": [
    { "id": 1, "name": "posts.read" }
  ]
}
```

---

### `POST /roles`

Creates a new role (starts with no permissions — assign them separately).

**Route:** `POST /roles`

#### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ | max 50 chars; trimmed; **globally unique** |

```json
// Request
{ "name": "Editor" }
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `201 Created` | Created | `RoleResponse` (with empty `permissions` array) |
| `409 Conflict` | Name already exists | Error string |

```json
// 201 Created
{
  "id": 2,
  "name": "Editor",
  "permissions": []
}

// 409 Conflict
"Role name must be unique."
```

> `Location` response header: `GET /roles/2`

---

### `PUT /roles/{id}/permissions`

**Replaces** the full set of permissions for a role. This is a **full replacement**, not an append — any permissions not in the new list will be removed.

**Route:** `PUT /roles/{id}/permissions`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int — Role ID |

#### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `permissionIds` | int[] | ✅ | Must all exist. Duplicates are de-duplicated automatically |

```json
// Request — assign permissions 1, 2, 3
{ "permissionIds": [1, 2, 3] }

// Request — remove all permissions from the role
{ "permissionIds": [] }
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | Updated | Full updated `RoleResponse` |
| `404 Not Found` | Role ID doesn't exist | Empty body |
| `409 Conflict` | One or more permission IDs don't exist | Error string |

```json
// 200 OK
{
  "id": 1,
  "name": "Admin",
  "permissions": [
    { "id": 1, "name": "posts.read" },
    { "id": 2, "name": "posts.write" },
    { "id": 3, "name": "users.manage" }
  ]
}

// 409 Conflict — if permission IDs 99 and 100 don't exist
"Unknown permission ids: 99, 100."
```

---

### `DELETE /roles/{id}`

Deletes a role. **Cascade:** The role is also removed from all users that had it assigned (via DB cascade delete on `UserRoles`).

**Route:** `DELETE /roles/{id}`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int |

#### Responses

| Status | When |
|--------|------|
| `204 No Content` | Deleted |
| `404 Not Found` | No role with that ID |

---

## 6. Users

Users have a username, a hashed password, and are assigned one or more roles. The full role + permission tree is always returned in user responses.

> There is **no authorization** on any user endpoints.

---

### `GET /users`

Returns all users with their roles, ordered alphabetically by username.

**Route:** `GET /users`

#### Response — `200 OK`

```json
[
  {
    "id": 1,
    "username": "admin",
    "roles": [
      {
        "id": 1,
        "name": "Admin",
        "permissions": [
          { "id": 1, "name": "posts.read" },
          { "id": 2, "name": "posts.write" },
          { "id": 3, "name": "users.manage" }
        ]
      }
    ]
  }
]
```

---

### `GET /users/{id}`

Returns a single user with their full role + permission tree.

**Route:** `GET /users/{id}`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int |

#### Responses

| Status | When |
|--------|------|
| `200 OK` | Found |
| `404 Not Found` | No user with that ID |

```json
// 200 OK
{
  "id": 1,
  "username": "admin",
  "roles": [
    {
      "id": 1,
      "name": "Admin",
      "permissions": [
        { "id": 1, "name": "posts.read" }
      ]
    }
  ]
}
```

---

### `POST /users`

Creates a new user and optionally assigns roles at creation time.

**Route:** `POST /users`

#### Request Body

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `username` | string | ✅ | max 100 chars; trimmed; **globally unique** | Case-sensitive when logging in |
| `password` | string | ✅ | min 6 chars, max 100 chars | Hashed via PBKDF2-SHA256 before storage. Never returned |
| `roleIds` | int[]? | ❌ | Must all exist; duplicates removed | Roles assigned at creation. Omit for a role-less user |

```json
// Request — with roles
{
  "username": "johndoe",
  "password": "mypassword123",
  "roleIds": [1]
}

// Request — no roles (simple user)
{
  "username": "viewer",
  "password": "viewpass1"
}
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `201 Created` | User created | `UserResponse` — password never included |
| `409 Conflict` | Username already exists **or** a role ID is invalid | Error string |

```json
// 201 Created
{
  "id": 2,
  "username": "johndoe",
  "roles": [
    {
      "id": 1,
      "name": "Admin",
      "permissions": [
        { "id": 1, "name": "posts.read" },
        { "id": 2, "name": "posts.write" },
        { "id": 3, "name": "users.manage" }
      ]
    }
  ]
}

// 409 Conflict — duplicate username
"Username must be unique."

// 409 Conflict — bad role IDs
"Unknown role ids: 99, 100."
```

> `Location` response header: `GET /users/2`

---

### `PUT /users/{id}/roles`

**Replaces** the full set of roles assigned to a user. This is a **full replacement**, not an append — roles not in the new list will be removed.

**Route:** `PUT /users/{id}/roles`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int — User ID |

#### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `roleIds` | int[] | ✅ | Must all exist. Duplicates de-duplicated automatically |

```json
// Request — assign roles 1 and 2
{ "roleIds": [1, 2] }

// Request — remove all roles from user
{ "roleIds": [] }
```

#### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | Updated | Full updated `UserResponse` |
| `404 Not Found` | User ID doesn't exist | Empty body |
| `409 Conflict` | One or more role IDs don't exist | Error string |

```json
// 200 OK
{
  "id": 1,
  "username": "admin",
  "roles": [
    {
      "id": 1,
      "name": "Admin",
      "permissions": [
        { "id": 1, "name": "posts.read" },
        { "id": 2, "name": "posts.write" },
        { "id": 3, "name": "users.manage" }
      ]
    }
  ]
}

// 409 Conflict
"Unknown role ids: 99."
```

---

### `DELETE /users/{id}`

Permanently deletes a user and all their role assignments.

**Route:** `DELETE /users/{id}`

#### Path Parameters

| Param | Type |
|-------|------|
| `id` | int |

#### Responses

| Status | When |
|--------|------|
| `204 No Content` | Deleted |
| `404 Not Found` | No user with that ID |

---

## Default Seed Data

The project auto-seeds on startup (via `DataSeeder.SeedAsync`) if the database is empty.

| Resource | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |
| Role | `Admin` |
| Permissions | `posts.read`, `posts.write`, `users.manage` |
| Sample post | Title: "Hello, world!" · Slug: `hello-world` |

> ⚠️ The seeder is marked `// TESTING ONLY — TODO: REMOVE`. **Change or remove these credentials before deploying.**

---

## Error Reference

| Error message | HTTP Status | Trigger |
|---|---|---|
| `"Slug must be unique."` | `409` | `POST /posts` or `PUT /posts/{id}` with a duplicate slug |
| `"Permission name must be unique."` | `409` | `POST /permissions` with a duplicate name |
| `"Role name must be unique."` | `409` | `POST /roles` with a duplicate name |
| `"Username must be unique."` | `409` | `POST /users` with a duplicate username |
| `"Unknown permission ids: X, Y."` | `409` | `PUT /roles/{id}/permissions` with non-existent permission IDs |
| `"Unknown role ids: X, Y."` | `409` | `POST /users` or `PUT /users/{id}/roles` with non-existent role IDs |
| `"No file uploaded."` | `400` | `POST /uploads` with no file or zero-length file |
| *(empty body)* | `401` | `POST /auth/login` with wrong username or password |
| *(empty body)* | `404` | Any `GET /{id}`, `PUT`, or `DELETE` on a non-existent resource |
