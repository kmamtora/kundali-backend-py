## Role

You are an expert backend architect with deep knowledge of **Prisma**, **PostgreSQL**, **FastAPI**, **SQLAlchemy 2.x**, and **Alembic**.

## Task

Read the provided `` file and generate **database table schemas** and **migration-ready models** for a **FastAPI + Alembic** backend.

## STRICT RULES (VERY IMPORTANT)

1. **DO NOT change anything** from the Prisma schema **except the **``** field type**.
2. **Table names must remain EXACTLY the same** as defined in Prisma models.
3. **Column names must remain EXACTLY the same**.
4. **Column data types must remain semantically equivalent** to Prisma types.
5. **Relations, indexes, unique constraints, defaults, nullability, enums, and cascading rules must be preserved exactly**.
6. **ONLY allowed change**:
   - Convert all primary key `id` fields to **UUID**
   - Use `UUID(as_uuid=True)` in SQLAlchemy
   - Use `uuid.uuid4()` as default
7. Do **NOT rename tables, columns, constraints, enums, or relations**.
8. Do **NOT add extra fields** like `created_at`, `updated_at`, etc unless they already exist in Prisma.

## Output Requirements

Produce the following outputs **in order**:

---

### 1. Database Table Schema (Logical View)

For each Prisma model, generate a clear table definition including:

- Table name
- Columns with data types
- Primary keys
- Foreign keys
- Indexes
- Unique constraints

(Use PostgreSQL-compatible terminology)

---

### 2. SQLAlchemy Models (FastAPI-ready)

Generate SQLAlchemy **declarative models**:

- Use `from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship`
- Use `UUID` for all `id` fields
- Preserve relationships (`one-to-one`, `one-to-many`, `many-to-many`)
- Preserve `nullable`, `unique`, `default`, and `index` attributes
- Use explicit `__tablename__`

Example style:

```python
class User(Base):
    __tablename__ = "User"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

---

### 3. Alembic Migration Script

Generate an **Alembic revision**:

- Use `op.create_table()`
- Use PostgreSQL UUID type
- Include all constraints, foreign keys, and indexes
- Ensure ordering respects foreign key dependencies

---

### 4. Prisma → SQLAlchemy Type Mapping Table

Include a mapping table such as:

| Prisma Type | PostgreSQL | SQLAlchemy |
| ----------- | ---------- | ---------- |
| String      | VARCHAR    | String     |
| Int         | INTEGER    | Integer    |
| Boolean     | BOOLEAN    | Boolean    |
| DateTime    | TIMESTAMP  | DateTime   |
| Json        | JSONB      | JSONB      |
| Enum        | ENUM       | Enum       |

---

## UUID Rules

- All `id` fields MUST be UUID
- Foreign keys referencing `id` must also be UUID
- Use `uuid.uuid4()` for defaults
- Use PostgreSQL-native UUID

---

## Assumptions

- Database: **PostgreSQL**
- ORM: **SQLAlchemy 2.x**
- Migration tool: **Alembic**
- Backend framework: **FastAPI**

---

## Input

Here is the Prisma schema:

```prisma

model User {
  id            Int            @id @default(autoincrement())
  mobileNo      String         
  otp           String
  otpExpires    DateTime       @default(now())
  isActive      Boolean        @default(true)
  createdAt     DateTime       @default(now())
  updatedAt     DateTime       @updatedAt
  followers     Follower[]     @relation("followingRelation") // Users who follow this user
  following     Follower[]     @relation("followerRelation") // Users this user follows
  messages      Message[]
  panditProfile PanditProfile?
  profile       Profile?
  ratings       Rating[]
  voiceCalls    VoiceCall[]
  wallet        Wallet[]
  rate          Rate?
}

model Profile {
  id           Int      @id @default(autoincrement())
  email        String?
  fname        String?
  lname        String?
  gender       Boolean  @default(true)
  bdate        String?
  btime        String?
  bplace       String?
  profilePic   String?
  profileVideo String?
  fcm_key      String?
  isUser       Boolean  @default(true)
  stripeCustId String?
  userId       Int?     @unique
  isActive     Boolean  @default(true)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  user         User?    @relation(fields: [userId], references: [id])
}

model PanditProfile {
  id            Int      @id @default(autoincrement())
  information   String
  isActiveChat  String   @default("Offline")
  isActiveCall  String   @default("Offline")
  isActiveLive  String   @default("Offline")
  language      String[]
  experience    String
  qualification String[]
  astrotype     String[]
  tag           String
  userId        Int?     @unique
  isActive      Boolean  @default(true)
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
  user          User?    @relation(fields: [userId], references: [id])
}

model Rate {
  id        Int      @id @default(autoincrement())
  AudioRate Int
  ChatRate  Int
  VideoRate Int
  LiveRate  Int
  userId    Int?     @unique
  isActive  Boolean? @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  user      User?    @relation(fields: [userId], references: [id])
}

model Language {
  id        Int      @id @default(autoincrement())
  name      String
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Experience {
  id        Int      @id @default(autoincrement())
  name      String
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model AstroType {
  id        Int      @id @default(autoincrement())
  name      String
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Kundali {
  id        Int      @id @default(autoincrement())
  name      String
  gender    Boolean  @default(true)
  bdate     String
  btime     String
  bplace    String
  roomName  String
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Rating {
  id        Int      @id @default(autoincrement())
  rate      Int
  comment   String
  userId    Int
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  user      User     @relation(fields: [userId], references: [id])
}

model Follower {
  id          Int @id @default(autoincrement())
  userId      Int // The user who is following
  followingId Int // The user being followed

  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  follower  User @relation("followerRelation", fields: [userId], references: [id])
  following User @relation("followingRelation", fields: [followingId], references: [id])

  @@unique([userId, followingId]) // Ensure a user follows another user only once
}

model VoiceCall {
  id         Int             @id @default(autoincrement())
  callerId   Int
  receiverId Int
  roomName   String
  startTime  DateTime        @default(now())
  endTime    DateTime?
  status     VoiceCallStatus
  isActive   Boolean         @default(true)
  userId     Int?
  createdAt  DateTime        @default(now())
  updatedAt  DateTime        @updatedAt
  User       User?           @relation(fields: [userId], references: [id])
}

model Message {
  id         Int      @id @default(autoincrement())
  senderId   Int
  receiverId Int
  content    String
  timestamp  DateTime @default(now())
  userId     Int?
  User       User?    @relation(fields: [userId], references: [id])
}

model Wallet {
  id             Int      @id @default(autoincrement())
  amount         Int
  status         String
  // rzp_orderid    String?
  // rzp_receipt    String?
  // rzp_status     String?
  // rzp_payment_id String?
  stripe_payment_intent String?
  timestamp      DateTime @default(now())
  userId         Int?
  User           User?    @relation(fields: [userId], references: [id])
}

enum VoiceCallStatus {
  INITIATE_ROOM
  CALLING
  ONGOING
  COMPLETED
  MISSED
  CANCELLED
}

```

---

## Final Check Before Answering

Before producing the output, internally verify:

- No table name changes
- No column name changes
- No datatype drift
- Only `id` converted to UUID
- make sure we create the tables in the correct order and dependencies are resolved and all the constraints are added and separate the migration files and separate the models

If any rule is violated, fix it before responding.

## Begin

