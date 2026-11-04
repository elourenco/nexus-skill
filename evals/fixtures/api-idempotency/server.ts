export type Payment = { id: string; tenant: string; amount: number };
export type CreatePayment = (tenant: string, amount: number) => Promise<Payment>;

// Intentionally defective evaluation starting point. No real payments or external I/O.
export function createHandler(createPayment: CreatePayment) {
  const completed = new Map<string, Payment>();
  return async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/payments") {
      return Response.json({ error: "not found" }, { status: 404 });
    }
    const tenant = request.headers.get("x-tenant-id");
    const key = request.headers.get("idempotency-key");
    let body: unknown;
    try { body = await request.json(); }
    catch { return Response.json({ error: "invalid JSON" }, { status: 400 }); }
    const amount = (body as { amount?: unknown } | null)?.amount;
    if (!tenant || !key || typeof amount !== "number" || !Number.isFinite(amount) || amount <= 0) {
      return Response.json({ error: "invalid input" }, { status: 400 });
    }
    const cached = completed.get(key);
    if (cached) return Response.json(cached, { status: 201 });
    try {
      const payment = await createPayment(tenant, amount);
      completed.set(key, payment);
      return Response.json(payment, { status: 201 });
    } catch {
      return Response.json({ error: "temporary failure" }, { status: 503 });
    }
  };
}

if (import.meta.main) {
  let sequence = 0;
  const fetch = createHandler(async (tenant, amount) => ({ id: `synthetic-${++sequence}`, tenant, amount }));
  Bun.serve({ hostname: "127.0.0.1", port: Number(Bun.env.PORT ?? 3000), fetch });
}
