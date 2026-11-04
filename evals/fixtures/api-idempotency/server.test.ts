import { describe, expect, test } from "bun:test";
import { createHandler, type Payment } from "./server";

function request(tenant = "tenant-a", amount = 10, key = "key-1") {
  return new Request("http://localhost/payments", {
    method: "POST", headers: { "content-type": "application/json", "x-tenant-id": tenant, "idempotency-key": key },
    body: JSON.stringify({ amount }),
  });
}

describe("synthetic HTTP idempotency acceptance", () => {
  test("validates input before creating a payment", async () => {
    let calls = 0;
    const handler = createHandler(async (tenant, amount) => ({ id: String(++calls), tenant, amount }));
    expect((await handler(request("tenant-a", -1))).status).toBe(400);
    expect(calls).toBe(0);
  });

  test("replays the same tenant, key and payload without another side effect", async () => {
    let calls = 0;
    const handler = createHandler(async (tenant, amount) => ({ id: String(++calls), tenant, amount }));
    const first = await (await handler(request())).json();
    expect(await (await handler(request())).json()).toEqual(first);
    expect(calls).toBe(1);
  });

  test("isolates identical keys across tenants", async () => {
    let calls = 0;
    const handler = createHandler(async (tenant, amount) => ({ id: String(++calls), tenant, amount }));
    await handler(request("tenant-a"));
    const other = await (await handler(request("tenant-b"))).json();
    expect(other.tenant).toBe("tenant-b");
    expect(calls).toBe(2);
  });

  test("rejects changed payload for the same tenant and key", async () => {
    let calls = 0;
    const handler = createHandler(async (tenant, amount) => ({ id: String(++calls), tenant, amount }));
    await handler(request());
    expect((await handler(request("tenant-a", 20))).status).toBe(409);
    expect(calls).toBe(1);
  });

  test("coalesces concurrent identical requests before awaiting the side effect", async () => {
    let calls = 0;
    let release!: () => void;
    const gate = new Promise<void>(resolve => { release = resolve; });
    const handler = createHandler(async (tenant, amount): Promise<Payment> => {
      const id = String(++calls);
      await gate;
      return { id, tenant, amount };
    });
    let parsed = 0;
    let bothParsed!: () => void;
    const parsing = new Promise<void>(resolve => { bothParsed = resolve; });
    const observedRequest = () => {
      const value = request();
      value.json = async () => {
        if (++parsed === 2) bothParsed();
        return { amount: 10 };
      };
      return value;
    };
    const pending = [handler(observedRequest()), handler(observedRequest())];
    await parsing;
    release();
    const responses = await Promise.all(pending);
    expect(await responses[0].json()).toEqual(await responses[1].json());
    expect(calls).toBe(1);
  });

  test("rejects conflicting payload while the original effect is pending", async () => {
    let calls = 0;
    let entered!: () => void;
    let release!: () => void;
    const started = new Promise<void>(resolve => { entered = resolve; });
    const gate = new Promise<void>(resolve => { release = resolve; });
    const handler = createHandler(async (tenant, amount) => {
      const id = String(++calls);
      if (calls === 1) { entered(); await gate; }
      return { id, tenant, amount };
    });
    const original = handler(request());
    await started;
    const conflict = await handler(request("tenant-a", 20));
    release();
    await original;
    expect(conflict.status).toBe(409);
    expect(calls).toBe(1);
  });

  test("allows retry after an unsuccessful side effect", async () => {
    let calls = 0;
    const handler = createHandler(async (tenant, amount) => {
      if (++calls === 1) throw new Error("synthetic failure before effect");
      return { id: String(calls), tenant, amount };
    });
    expect((await handler(request())).status).toBe(503);
    expect((await handler(request())).status).toBe(201);
    expect(calls).toBe(2);
  });
});
