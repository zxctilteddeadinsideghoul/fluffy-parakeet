# Контракты данных проекта

Статус документа: проектный контракт MVP.  
Назначение: единый источник истины для агентов, проектирующих БД, backend, API, frontend и тесты.

Связанный документ: `AGENT_DOMAIN_ENTITIES.md`.

## 1. Термины и обязательные принципы

Ключевые слова `MUST`, `MUST NOT`, `SHOULD`, `MAY` имеют нормативный смысл.

- `User` — единый тип пользователя. «Инициатор» и «получатель» — роли в конкретном взаимодействии, а не разные сущности.
- `PresenceSession` — подтверждённое временное присутствие пользователя в заведении.
- `ContactRequest` — направленный бесплатный сигнал интереса и запрос на открытие общения.
- `Connection` — зафиксированное взаимное разрешение общаться.
- `ApproachRequest` — отдельный запрос разрешения подойти лично.
- `DrinkOffer` — самостоятельное предложение напитка. Оно не является согласием на чат или личный контакт.

Система MUST считать независимыми четыре решения получателя:

1. принять сигнал интереса и открыть чат;
2. принять напиток;
3. разрешить подойти лично;
4. продолжать общение.

Принятие одного решения MUST NOT автоматически принимать другое.

## 2. Общие типы

```ts
type UUID = string;                 // UUID v7 предпочтителен
type Instant = string;              // ISO 8601 UTC: 2026-08-02T12:34:56.000Z
type LocalDate = string;            // YYYY-MM-DD
type CurrencyCode = string;         // ISO 4217, например EUR
type MinorAmount = number;          // целое >= 0, сумма в минимальных единицах валюты
type NonEmptyString = string;

type EntityRef = {
  entityType: string;
  entityId: UUID;
};

type Money = {
  amountMinor: MinorAmount;
  currency: CurrencyCode;
};

type PageRequest = {
  cursor?: string;
  limit?: number;                   // 1..100, default 20
};

type Page<T> = {
  items: T[];
  nextCursor: string | null;
};

type ResponseEnvelope<T> = {
  data: T;
};
```

Правила сериализации:

- JSON-поля API используют `camelCase`; имена колонок БД MAY использовать `snake_case`.
- Идентификаторы непрозрачны для клиента.
- Время передаётся только с часовым поясом; хранится в UTC.
- Денежные суммы MUST NOT передаваться как числа с плавающей точкой.
- Отсутствующее необязательное поле передаётся как отсутствие ключа; `null` используется только там, где явно указан.
- Все команды, создающие платёж или изменяющие его состояние, MUST принимать `idempotencyKey`.
- Все успешные HTTP-ответы MUST возвращать тело вида `ResponseEnvelope`: `{"data": <значение>}` — значение может быть DTO, `Page<T>` или примитивом. Ошибки возвращаются в конверте из раздела 7.

## 3. Перечисления

```ts
type UserStatus = "active" | "limited" | "suspended" | "deleted";
type VerificationType = "photo" | "video" | "identity";
type VerificationStatus = "pending" | "approved" | "rejected" | "expired";
type MediaModerationStatus = "pending" | "approved" | "rejected";

type AuthProvider = "email" | "yandex" | "vk";

type CommunicationGoal =
  | "dating"
  | "friends"
  | "company_tonight"
  | "networking"
  | "casual_chat";

type ApproachMode = "chat_only" | "ask_before_approach" | "may_approach";
type PresenceStatus = "active" | "hidden" | "ended" | "expired";
type PresenceVisibility = "visible" | "hidden";
type CheckInMethod = "venue_qr" | "staff" | "partner_integration";

type RequestStatus =
  | "pending"
  | "accepted"
  | "declined"
  | "expired"
  | "cancelled"
  | "blocked";

type ConnectionStatus = "active" | "closed" | "blocked";
type ConversationStatus = "active" | "closed" | "blocked";
type MessageType = "text" | "system";

type DrinkOfferStatus =
  | "payment_authorized"
  | "pending"
  | "accepted"
  | "declined"
  | "expired"
  | "cancelled"
  | "redeemed";

type PaymentStatus =
  | "created"
  | "authorization_pending"
  | "authorized"
  | "capture_pending"
  | "captured"
  | "void_pending"
  | "voided"
  | "refund_pending"
  | "refunded"
  | "failed";

type RedemptionStatus = "created" | "redeemed" | "expired" | "cancelled";
type AvailabilityStatus = "available" | "unavailable" | "archived";
type ModerationStatus = "open" | "in_review" | "resolved" | "dismissed";
type NotificationStatus = "unread" | "read";
```

Клиенты MUST сохранять совместимость с неизвестными значениями перечислений: неизвестное значение не должно приводить к падению приложения.

## 4. Контракты хранимых сущностей

Поля `createdAt` обязательны, если явно не указано обратное. Поля `updatedAt` SHOULD обновляться только при фактическом изменении.

### 4.1 Пользователь и профиль

```ts
type User = {
  id: UUID;
  status: UserStatus;
  phoneNormalized?: string;         // private
  emailNormalized?: string;         // private
  authProvider: AuthProvider | string;
  authSubject: string;               // private; unique вместе с authProvider
  birthDate?: LocalDate;             // private; наружу отдаётся age; может быть не заполнено
  createdAt: Instant;
  updatedAt: Instant;
  deletedAt: Instant | null;
};

type Profile = {
  userId: UUID;
  displayName: string;               // непустое значение требуется при visibilityEnabled = true
  gender?: string;
  bio?: string;
  communicationGoals: CommunicationGoal[];
  defaultApproachMode: ApproachMode;
  visibilityEnabled: boolean;
  createdAt: Instant;
  updatedAt: Instant;
};

type ProfilePhoto = {
  id: UUID;
  userId: UUID;
  storageKey: string;                // private
  publicUrl?: string;                // короткоживущий/проксированный URL
  position: number;                  // integer >= 0
  moderationStatus: MediaModerationStatus;
  createdAt: Instant;
  deletedAt: Instant | null;
};

type Verification = {
  id: UUID;
  userId: UUID;
  type: VerificationType;
  status: VerificationStatus;
  providerReference?: string;        // private
  rejectionReasonCode?: string;      // private
  createdAt: Instant;
  verifiedAt: Instant | null;
  expiresAt: Instant | null;
};
```

### 4.2 Заведение, меню и присутствие

```ts
type Venue = {
  id: UUID;
  name: NonEmptyString;
  address: string;                   // не используется как положение пользователя
  timezone: string;                  // IANA, например Europe/Amsterdam
  status: "active" | "inactive";
  partnerStatus: "prospect" | "pilot" | "active" | "paused";
  createdAt: Instant;
  updatedAt: Instant;
};

type VenueCheckInToken = {
  id: UUID;
  venueId: UUID;
  tokenHash: string;                 // исходный токен не хранится
  validFrom: Instant;
  validUntil: Instant;
  status: "active" | "revoked" | "expired";
  createdAt: Instant;
};

type MenuItem = {
  id: UUID;
  venueId: UUID;
  name: NonEmptyString;
  description?: string;
  price: Money;
  imageUrl?: string;
  availabilityStatus: AvailabilityStatus;
  createdAt: Instant;
  updatedAt: Instant;
};

type VenueStaff = {
  id: UUID;
  venueId: UUID;
  userId?: UUID;                    // если сотрудник входит через обычный аккаунт
  externalSubject?: string;         // private; идентификатор партнёрской системы
  role: "staff" | "manager" | "admin";
  status: "active" | "inactive";
  createdAt: Instant;
  updatedAt: Instant;
};

type PresenceSession = {
  id: UUID;
  userId: UUID;
  venueId: UUID;
  status: PresenceStatus;
  visibility: PresenceVisibility;
  approachMode: ApproachMode;        // снимок настройки на текущий визит
  checkInMethod: CheckInMethod;
  checkedInAt: Instant;
  lastHeartbeatAt: Instant;
  expiresAt: Instant;
  endedAt: Instant | null;
};
```

Инварианты:

- для одного `userId` существует не более одной сессии со статусом `active` или `hidden`;
- видим только пользователь с `User.status = active`, валидной верификацией, `PresenceSession.status = active`, `visibility = visible` и `Profile.visibilityEnabled = true`;
- API MUST NOT раскрывать координаты, столик, `lastHeartbeatAt` или историю посещений;
- завершённая сессия MUST NOT возвращаться в выдаче присутствующих;
- политика удаления/обезличивания завершённых сессий задаётся отдельно и MUST быть реализована фоновым процессом.

### 4.3 Интерес, связь, чат и личный подход

```ts
type ContactRequest = {
  id: UUID;
  senderUserId: UUID;
  recipientUserId: UUID;
  senderPresenceId: UUID;
  recipientPresenceId: UUID;
  venueId: UUID;
  status: RequestStatus;
  message?: string;                  // если разрешено продуктовой политикой
  createdAt: Instant;
  respondedAt: Instant | null;
  expiresAt: Instant;
};

type Connection = {
  id: UUID;
  userAId: UUID;
  userBId: UUID;
  venueId: UUID;
  sourceRequestId: UUID;
  status: ConnectionStatus;
  createdAt: Instant;
  closedAt: Instant | null;
};

type Conversation = {
  id: UUID;
  connectionId: UUID;
  status: ConversationStatus;
  createdAt: Instant;
  closedAt: Instant | null;
};

type ConversationMember = {
  conversationId: UUID;
  userId: UUID;
  lastReadMessageId: UUID | null;
  mutedAt: Instant | null;
  leftAt: Instant | null;
};

type Message = {
  id: UUID;
  conversationId: UUID;
  senderUserId: UUID;
  type: MessageType;
  body: string;
  createdAt: Instant;
  deletedAt: Instant | null;
};

type ApproachRequest = {
  id: UUID;
  requesterUserId: UUID;
  recipientUserId: UUID;
  requesterPresenceId: UUID;
  recipientPresenceId: UUID;
  connectionId?: UUID;
  venueId: UUID;
  status: RequestStatus;
  createdAt: Instant;
  respondedAt: Instant | null;
  expiresAt: Instant;
};
```

Инварианты:

- `senderUserId != recipientUserId` и `requesterUserId != recipientUserId`;
- обе сессии запроса должны быть действующими и относиться к одному `venueId`;
- повторный `ContactRequest` от того же отправителя к тому же получателю в рамках `recipientPresenceId` запрещён независимо от результата первого запроса;
- принятие `ContactRequest` атомарно создаёт одну `Connection`, одну `Conversation` и двух `ConversationMember`;
- сообщение может отправить только действующий участник активного разговора;
- разрешение `may_approach` действует только в рамках текущей сессии присутствия получателя;
- режим `chat_only` запрещает создание `ApproachRequest`; режим `ask_before_approach` требует принятого запроса; `may_approach` является явным разрешением в пределах текущего визита, но не раскрывает местоположение.

### 4.4 Напиток, платёж и выдача

```ts
type DrinkOffer = {
  id: UUID;
  senderUserId: UUID;
  recipientUserId: UUID;
  senderPresenceId: UUID;
  recipientPresenceId: UUID;
  venueId: UUID;
  menuItemId: UUID;
  connectionId?: UUID;
  status: DrinkOfferStatus;
  itemNameSnapshot: string;
  priceSnapshot: Money;
  createdAt: Instant;
  respondedAt: Instant | null;
  expiresAt: Instant;
};

type Payment = {
  id: UUID;
  drinkOfferId: UUID;
  payerUserId: UUID;
  amount: Money;
  provider: string;
  providerReference?: string;        // private
  idempotencyKey: string;
  status: PaymentStatus;
  createdAt: Instant;
  authorizedAt: Instant | null;
  capturedAt: Instant | null;
  voidedAt: Instant | null;
  refundedAt: Instant | null;
  failureCode?: string;
};

type Redemption = {
  id: UUID;
  drinkOfferId: UUID;
  codeHash: string;                  // private; исходный код не хранится
  status: RedemptionStatus;
  expiresAt: Instant;
  redeemedAt: Instant | null;
  venueStaffId: UUID | null;
  createdAt: Instant;
};
```

Инварианты:

- позиция меню должна принадлежать `venueId` предложения и быть доступной при создании;
- сумма и название копируются в snapshot и не меняются вслед за меню;
- сумма `Payment.amount` должна совпадать с `DrinkOffer.priceSnapshot`;
- принятое предложение напитка MUST NOT создавать `Connection`, `Conversation` или `ApproachRequest`;
- блокировка до выдачи запрещает дальнейшее прямое взаимодействие, но финансовое завершение обрабатывается по отдельной политике возвратов;
- одна операция выдачи может успешно погасить `Redemption` только один раз.

Рекомендуемый, но ещё не окончательно утверждённый поток оплаты:

```text
authorize -> send offer -> accept -> redeem -> capture
                         -> decline/expire -> void
```

### 4.5 Безопасность и модерация

```ts
type Block = {
  id: UUID;
  blockerUserId: UUID;
  blockedUserId: UUID;
  reasonCode?: string;               // private
  createdAt: Instant;
};

type ReportTargetType =
  | "profile"
  | "message"
  | "contact_request"
  | "approach_request"
  | "drink_offer"
  | "venue_behavior";

type Report = {
  id: UUID;
  reporterUserId: UUID;
  reportedUserId: UUID;
  targetType: ReportTargetType;
  targetId?: UUID;
  category: string;
  comment?: string;                  // private, sensitive
  status: ModerationStatus;
  createdAt: Instant;
};

type ModerationCase = {
  id: UUID;
  reportedUserId: UUID;
  status: ModerationStatus;
  priority: "low" | "normal" | "high" | "urgent";
  assignedModeratorId: UUID | null;
  createdAt: Instant;
  resolvedAt: Instant | null;
};

type ModerationAction = {
  id: UUID;
  caseId: UUID;
  type: "warn" | "limit" | "suspend" | "ban" | "dismiss";
  reason: string;
  startsAt: Instant;
  expiresAt: Instant | null;
  createdAt: Instant;
};
```

Создание `Block` MUST атомарно:

- скрыть пользователей друг от друга;
- перевести незавершённые запросы между ними в `blocked`;
- закрыть доступ к существующему чату;
- запретить новые запросы и предложения;
- не уведомлять заблокированного о личности, причине или факте блокировки.

`Report` и `Block` независимы: клиент MAY отправить только блокировку, только жалобу или обе команды.

### 4.6 Уведомления, устройства и события

```ts
type Device = {
  id: UUID;
  userId: UUID;
  pushToken: string;                 // private, encrypted at rest
  platform: "ios" | "android" | "web";
  status: "active" | "revoked";
  lastSeenAt: Instant;
  createdAt: Instant;
};

type Notification = {
  id: UUID;
  userId: UUID;
  type: string;
  entityType: string;
  entityId: UUID;
  status: NotificationStatus;
  safePayload: Record<string, unknown>;
  createdAt: Instant;
  readAt: Instant | null;
};

type DomainEvent<T = Record<string, unknown>> = {
  id: UUID;
  eventType: string;
  eventVersion: number;
  actorUserId: UUID | null;
  entityType: string;
  entityId: UUID;
  occurredAt: Instant;
  traceId: string;
  payload: T;
};
```

События не должны содержать точные координаты, токены, платёжные реквизиты, полный текст сообщений и иные данные, не нужные потребителю события.

## 5. Публичные DTO

Хранимые модели MUST NOT отдаваться клиенту напрямую. Все успешные ответы возвращаются внутри конверта `{"data": <DTO>}` (раздел 2); схемы ниже описывают значение поля `data`.

```ts
type AuthResponseDto = {
  userId: UUID;
  isNewUser: boolean;                // true — аккаунт создан только что
};

type MyProfileDto = {
  id: UUID;
  displayName: string;
  age: number | null;
  gender?: string;
  bio?: string;
  communicationGoals: CommunicationGoal[];
  defaultApproachMode: ApproachMode;
  photos: Array<{
    id: UUID;
    url: string;
    position: number;
    moderationStatus: MediaModerationStatus;
  }>;
  verification: { isVerified: boolean };
};

type VisibleProfileDto = {
  userId: UUID;
  presenceId: UUID;
  venueId: UUID;
  displayName: string;
  age: number | null;
  gender?: string;
  bio?: string;
  communicationGoals: CommunicationGoal[];
  approachMode: ApproachMode;
  photos: Array<{ id: UUID; url: string; position: number }>;
  isVerified: boolean;
  availableActions: Array<"contact" | "drink" | "ask_to_approach">;
};
```

`VisibleProfileDto` MUST NOT содержать `birthDate`, контакты, точные координаты, столик, время последнего heartbeat, историю заведений и причины модерационных ограничений.

## 6. Контракты команд

```ts
type RegisterCommand = {
  authProvider: AuthProvider;
  authSubject: string;               // email для провайдера "email"; subject у OAuth-провайдера
  email?: string;                    // привязывается к emailNormalized, когда доступна
};

type UpdateMyProfileCommand = {
  displayName: string;               // непустое значение при visibilityEnabled = true
  gender?: string;
  bio?: string;
  birthDate?: LocalDate;             // наружу отдаётся только age
  communicationGoals: CommunicationGoal[];
  defaultApproachMode: ApproachMode;
  visibilityEnabled: boolean;
};

type DeleteProfilePhotoCommand = {
  photoId: UUID;
};

type CheckInCommand = {
  venueToken: string;
  visibility: PresenceVisibility;
  approachMode: ApproachMode;
};

type SendContactRequestCommand = {
  recipientPresenceId: UUID;
  message?: string;
};

type RespondToRequestCommand = {
  decision: "accept" | "decline";
};

type SendApproachRequestCommand = {
  recipientPresenceId: UUID;
};

type SendDrinkOfferCommand = {
  recipientPresenceId: UUID;
  menuItemId: UUID;
  idempotencyKey: string;
};

type RedeemDrinkCommand = {
  redemptionCode: string;
  idempotencyKey: string;
};

type CreateBlockCommand = {
  blockedUserId: UUID;
  reasonCode?: string;
};

type CreateReportCommand = {
  reportedUserId: UUID;
  targetType: ReportTargetType;
  targetId?: UUID;
  category: string;
  comment?: string;
  alsoBlock: boolean;
};
```

Загрузка фото — отдельный multipart-командный поток (`POST /me/profile/photos`, поле `file`). Сервер сохраняет файл в хранилище, создаёт `ProfilePhoto` с `storageKey`, короткоживущим `publicUrl`, `position = max(1 + max(position))` и `moderationStatus`. Удаление — команда `DeleteProfilePhotoCommand` (soft-delete через `deletedAt`). Политика модерации (кто и когда одобряет) задаётся отдельно; в development-окружении загруженные фото получают статус `approved` для локальной разработки.

Общие проверки команд:

- аутентифицированный пользователь берётся из серверного контекста, а не из `actorUserId` тела;
- владение ресурсом и переход состояния проверяются на сервере;
- отправитель и получатель не совпадают;
- между пользователями нет блока ни в одном направлении;
- обе требуемые сессии действуют в одном заведении;
- применяются rate limit и ограничения для новых/ограниченных аккаунтов;
- повтор команды с тем же `idempotencyKey` возвращает прежний результат, а не выполняет действие повторно.

## 7. Контракт ошибок

```ts
type ApiError = {
  error: {
    code: string;
    message: string;                 // безопасный локализуемый текст
    traceId: string;
    details?: Record<string, unknown>;
  };
};
```

Минимальный набор кодов:

| Код | HTTP | Значение |
|---|---:|---|
| `AUTH_REQUIRED` | 401 | Требуется вход |
| `FORBIDDEN` | 403 | Действие недоступно без раскрытия причины |
| `VERIFICATION_REQUIRED` | 403 | Нужна верификация |
| `ACTIVE_PRESENCE_REQUIRED` | 409 | Нет действующей сессии присутствия |
| `NOT_SAME_VENUE` | 409 | Участники не находятся в одном заведении |
| `ALREADY_EXISTS` | 409 | Учётная запись с таким идентификатором уже существует |
| `INVALID_STATE_TRANSITION` | 409 | Переход состояния невозможен |
| `REQUEST_ALREADY_EXISTS` | 409 | Повторный запрос в рамках визита запрещён |
| `OFFER_EXPIRED` | 409 | Предложение истекло |
| `MENU_ITEM_UNAVAILABLE` | 409 | Позиция недоступна |
| `RATE_LIMITED` | 429 | Превышен лимит действий |
| `PAYMENT_FAILED` | 402 | Платёжная операция не завершена |
| `NOT_FOUND` | 404 | Ресурс отсутствует либо намеренно скрыт |

Для блокировки и приватных ограничений API SHOULD предпочитать нейтральные `FORBIDDEN`/`NOT_FOUND`, чтобы не раскрывать состояние другого пользователя.

## 8. Событийные контракты

Минимальный набор событий первого релиза:

```text
presence.started.v1
presence.visibility_changed.v1
presence.ended.v1
presence.expired.v1
contact_request.created.v1
contact_request.accepted.v1
contact_request.declined.v1
connection.created.v1
message.created.v1
approach_request.created.v1
approach_request.accepted.v1
drink_offer.created.v1
drink_offer.accepted.v1
drink_offer.declined.v1
drink_offer.expired.v1
drink_offer.redeemed.v1
payment.authorized.v1
payment.captured.v1
payment.voided.v1
user.blocked.v1
report.created.v1
```

Пример:

```json
{
  "id": "0198...",
  "eventType": "contact_request.accepted.v1",
  "eventVersion": 1,
  "actorUserId": "0198...",
  "entityType": "contact_request",
  "entityId": "0198...",
  "occurredAt": "2026-08-02T12:34:56.000Z",
  "traceId": "req_...",
  "payload": {
    "connectionId": "0198...",
    "conversationId": "0198...",
    "venueId": "0198..."
  }
}
```

Потребители MUST использовать сочетание `eventType` + `eventVersion`. Изменение смысла или удаление поля требует новой версии события.

## 9. Ограничения БД и конкурентность

Минимально необходимые ограничения:

```text
UNIQUE active PresenceSession per userId
UNIQUE (senderUserId, recipientUserId, recipientPresenceId) on ContactRequest
UNIQUE sourceRequestId on Connection
UNIQUE connectionId on Conversation
UNIQUE (conversationId, userId) on ConversationMember
UNIQUE (blockerUserId, blockedUserId) on Block
UNIQUE drinkOfferId on Payment
UNIQUE drinkOfferId on Redemption
UNIQUE (provider, providerReference) where providerReference is not null
UNIQUE (payerUserId, idempotencyKey) on Payment
CHECK actor != recipient on directed interactions
CHECK amountMinor >= 0
```

Принятие запроса, блокировка, погашение напитка и переходы платежа MUST использовать транзакцию и/или compare-and-set по текущему статусу. Повторная параллельная команда должна завершаться идемпотентно.

## 10. Политика хранения и чувствительность

| Категория | Примеры | Правило |
|---|---|---|
| Публичная в текущем заведении | имя, возраст, фото, цели общения | только видимым пользователям того же заведения |
| Приватная | дата рождения, контакты, auth subject | только владельцу и служебным процессам |
| Чувствительная | жалобы, причины модерации, provider reference | строгий служебный доступ и аудит |
| Эфемерная | heartbeat, QR-токены, presence | короткий срок хранения |
| Финансовая | суммы, статусы, ссылки провайдера | хранение по юридической и бухгалтерской политике |

История посещений не является продуктовой функцией и MUST NOT предоставляться пользователям. Сроки удаления, юридическое основание обработки и требования к платёжным данным требуют отдельного решения.

## 11. Неутверждённые решения (`TBD`)

Агенты MUST NOT молча фиксировать следующие пункты как решённые:

1. Можно ли предложить напиток до принятого `ContactRequest`.
2. Момент списания: принятие предложения или фактическая выдача.
3. Способ подтверждения выдачи: код, QR, интерфейс сотрудника или POS.
4. Время жизни `PresenceSession` без heartbeat.
5. Срок хранения/обезличивания завершённых сессий.
6. Допустимо ли прикладывать текст к первому сигналу интереса.
7. Является ли `may_approach` достаточным разрешением или всегда нужен `ApproachRequest`.
8. Нужен ли взаимный «лайк» вместо принятия направленного запроса.

До решения этих вопросов реализации SHOULD использовать конфигурацию или изолированную доменную политику, а не размазывать условную логику по контроллерам и интерфейсу.
