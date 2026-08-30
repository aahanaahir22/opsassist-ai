import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: { steady: { executor: "constant-vus", vus: 20, duration: "60s" } },
  thresholds: { http_req_failed: ["rate<0.01"], http_req_duration: ["p(95)<750"] },
};

const base = __ENV.API_BASE_URL || "http://localhost:8000/api/v1";
export default function workflowLoad() {
  const response = http.get(`${base}/health`);
  check(response, { "health is 200": (value) => value.status === 200 });
  sleep(0.25);
}
