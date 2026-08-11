import { expect, type Page, test } from "@playwright/test";

const username = process.env.E2E_ADMIN_USERNAME ?? "admin";
const password = process.env.E2E_ADMIN_PASSWORD ?? "choose-a-local-demo-password";

async function signIn(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Deception Overview" })).toBeVisible();
}

test("protects the console and authenticates an analyst", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await signIn(page);
  await expect(page.getByText("Events (24h)")).toBeVisible();
});

test("runs the deterministic demo and opens its investigation", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Demo Lab" }).click();
  await page.getByRole("button", { name: "Run safe scenario" }).click();

  await expect(page).toHaveURL(/\/investigations\//, { timeout: 15_000 });
  await expect(page.getByRole("heading", { name: "Attack investigation" })).toBeVisible();
  await expect(page.getByText("198.51.100.42").first()).toBeVisible();
  await expect(page.getByText(/T1059/).first()).toBeVisible();
});
