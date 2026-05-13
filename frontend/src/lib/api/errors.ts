export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export class UnauthorizedError extends ApiError {
  constructor(detail = "Необходима авторизация") {
    super(401, detail);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends ApiError {
  constructor(detail = "Доступ запрещён") {
    super(403, detail);
    this.name = "ForbiddenError";
  }
}

export class NotFoundError extends ApiError {
  constructor(detail = "Ресурс не найден") {
    super(404, detail);
    this.name = "NotFoundError";
  }
}

export class ServerError extends ApiError {
  constructor(detail = "Внутренняя ошибка сервера") {
    super(500, detail);
    this.name = "ServerError";
  }
}

export function throwForStatus(status: number, detail: string): never {
  if (status === 401) throw new UnauthorizedError(detail);
  if (status === 403) throw new ForbiddenError(detail);
  if (status === 404) throw new NotFoundError(detail);
  if (status >= 500) throw new ServerError(detail);
  throw new ApiError(status, detail);
}

export async function extractErrorDetail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((e: { msg: string }) => e.msg).join("; ");
    }
  } catch {
    // ignore parse error, fall through to statusText
  }
  return res.statusText || `HTTP ${res.status}`;
}
