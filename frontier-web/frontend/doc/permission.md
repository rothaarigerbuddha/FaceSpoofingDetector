# FrontierWeb API Documentation

> Base URL: `http://localhost:5160`  
> Content-Type: `application/json`

---

## Permissions

### `GET /permissions`

List all permissions.

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Array of permission objects |

```json
// 200 OK
[
  { "id": 1, "name": "posts.read" },
  { "id": 2, "name": "posts.write" },
  { "id": 3, "name": "users.manage" }
]
```

---

### `GET /permissions/{id}`

Get a single permission by ID.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | Permission ID |

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Permission object |
| `404 Not Found` | Permission with given ID does not exist |

```json
// 200 OK
{ "id": 1, "name": "posts.read" }
```

---

### `POST /permissions`

Create a new permission.

**Request body**

| Field | Type   | Required | Constraints      |
|-------|--------|----------|------------------|
| `name`| string | ✅       | max 100 chars    |

```json
// Request body
{ "name": "posts.delete" }
```

**Responses**

| Status | Description |
|--------|-------------|
| `201 Created` | Permission created, returns new object |
| `409 Conflict` | Permission with that name already exists |

```json
// 201 Created
{ "id": 4, "name": "posts.delete" }

// 409 Conflict
"A permission with this name already exists."
```

---

### `DELETE /permissions/{id}`

Delete a permission by ID.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | Permission ID |

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `204 No Content` | Permission deleted successfully |
| `404 Not Found` | Permission with given ID does not exist |

---

## Roles

### `GET /roles`

List all roles with their assigned permissions.

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Array of role objects |

```json
// 200 OK
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

Get a single role by ID.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | Role ID |

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Role object with permissions |
| `404 Not Found` | Role with given ID does not exist |

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

Create a new role.

**Request body**

| Field | Type   | Required | Constraints   |
|-------|--------|----------|---------------|
| `name`| string | ✅       | max 50 chars  |

```json
// Request body
{ "name": "Editor" }
```

**Responses**

| Status | Description |
|--------|-------------|
| `201 Created` | Role created, returns new object |
| `409 Conflict` | Role with that name already exists |

```json
// 201 Created
{
  "id": 2,
  "name": "Editor",
  "permissions": []
}

// 409 Conflict
"A role with this name already exists."
```

---

### `PUT /roles/{id}/permissions`

Replace the full set of permissions assigned to a role.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | Role ID |

**Request body**

| Field           | Type  | Required | Description                       |
|-----------------|-------|----------|-----------------------------------|
| `permissionIds` | int[] | ✅       | Array of permission IDs to assign |

```json
// Request body
{ "permissionIds": [1, 2, 3] }
```

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Updated role with new permissions |
| `404 Not Found` | Role with given ID does not exist |
| `409 Conflict` | One or more permission IDs are invalid |

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
```

---

### `DELETE /roles/{id}`

Delete a role by ID.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | Role ID |

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `204 No Content` | Role deleted successfully |
| `404 Not Found` | Role with given ID does not exist |

---

## Users

### `GET /users`

List all users with their assigned roles (and nested permissions).

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Array of user objects |

```json
// 200 OK
[
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
]
```

---

### `GET /users/{id}`

Get a single user by ID.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | User ID |

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | User object with roles |
| `404 Not Found` | User with given ID does not exist |

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

Create a new user (optionally assign roles at creation).

**Request body**

| Field      | Type   | Required | Constraints                         |
|------------|--------|----------|-------------------------------------|
| `username` | string | ✅       | max 100 chars                       |
| `password` | string | ✅       | min 6 chars, max 100 chars          |
| `roleIds`  | int[]  | ❌       | Array of role IDs to assign at creation |

```json
// Request body
{
  "username": "johndoe",
  "password": "secret123",
  "roleIds": [1]
}
```

**Responses**

| Status | Description |
|--------|-------------|
| `201 Created` | User created, returns new object (password is never returned) |
| `409 Conflict` | Username already taken |

```json
// 201 Created
{
  "id": 2,
  "username": "johndoe",
  "roles": [
    {
      "id": 1,
      "name": "Admin",
      "permissions": []
    }
  ]
}

// 409 Conflict
"A user with this username already exists."
```

---

### `PUT /users/{id}/roles`

Replace the full set of roles assigned to a user.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | User ID |

**Request body**

| Field     | Type  | Required | Description                  |
|-----------|-------|----------|------------------------------|
| `roleIds` | int[] | ✅       | Array of role IDs to assign  |

```json
// Request body
{ "roleIds": [1, 2] }
```

**Responses**

| Status | Description |
|--------|-------------|
| `200 OK` | Updated user with new roles |
| `404 Not Found` | User with given ID does not exist |
| `409 Conflict` | One or more role IDs are invalid |

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

### `DELETE /users/{id}`

Delete a user by ID.

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id`  | int  | User ID |

**Request body:** none

**Responses**

| Status | Description |
|--------|-------------|
| `204 No Content` | User deleted successfully |
| `404 Not Found` | User with given ID does not exist |
