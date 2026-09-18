// Десять отчётов одновременно: проверка НФТ «не меньше 10 параллельных отчётов».
// Запуск: k6 run -e BASE_URL=http://127.0.0.1:8000 load/k6-reports.js

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const FORMATS = ['xlsx', 'json', 'pdf', 'xls'];
// Отчёт строится в фоне, поэтому состояние опрашивается, а не читается в первом же ответе.
const POLL_ATTEMPTS = 60;

export const options = {
  scenarios: {
    reports: {
      executor: 'per-vu-iterations',
      vus: 10,
      iterations: 1,
      maxDuration: '5m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    // Отчёт строится дольше обычного запроса, поэтому порог свой.
    'http_req_duration{name:report}': ['p(95)<30000'],
  },
};

export default function () {
  const options = {
    headers: { 'X-Dev-User': 'alina.denisova@example.com', 'Content-Type': 'application/json' },
    tags: { name: 'report' },
  };
  const body = JSON.stringify({ format: FORMATS[__VU % FORMATS.length] });

  const created = http.post(`${BASE_URL}/api/v1/reports`, body, options);
  check(created, { 'задание принято': (r) => r.status === 202 });

  const id = created.json('id');
  if (!id) return;

  const poll = { headers: options.headers, tags: { name: 'poll' } };
  let status = 'queued';
  for (let attempt = 0; attempt < POLL_ATTEMPTS; attempt++) {
    const state = http.get(`${BASE_URL}/api/v1/reports/${id}`, poll);
    status = state.json('status');
    if (status === 'done' || status === 'failed') break;
    sleep(1);
  }
  check({ status: status }, { 'отчёт дошёл до done': (r) => r.status === 'done' });
}
