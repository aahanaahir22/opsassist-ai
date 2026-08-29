import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("launch → investigate → simulate → approve → execute → verify", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Launch guided incident/i }).click();
  await expect(page.getByText(/Root-cause hypotheses/i)).toBeVisible();
  await page.getByRole("tab", { name: /Digital twin/i }).click();
  await page.getByRole("button", { name: /Simulate action/i }).click();
  await page.getByRole("button", { name: /Review & approve/i }).click();
  await page.getByRole("button", { name: /Sign approval/i }).click();
  await page.getByRole("button", { name: /Execute in simulator/i }).click();
  await expect(page.getByRole("button", { name: /Recovery verified/i })).toBeVisible({ timeout: 10_000 });
  await page.getByRole("tab", { name: /Postmortem/i }).click();
  await expect(page.getByText(/VERIFIED RECOVERY/i)).toBeVisible();
});

test("critical accessibility rules pass", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).analyze();
  const severe = results.violations.filter((item) => item.impact === "critical" || item.impact === "serious");
  expect(severe).toEqual([]);
});
