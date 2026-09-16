// Нагрузка на рабочий день КАМа и руководителя: радар, списки, карточка, заметка.
// Запуск: k6 run -e BASE_URL=http://127.0.0.1:8000 load/k6-main.js
// Стенд поднимается с AUTH_MODE=dev, поэтому пользователь передаётся заголовком X-Dev-User.

import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const USERS = [
  'anna.smirnova@example.com',
  'mikhail.volkov@example.com',
  'roman.kovalev@example.com',
  'alina.denisova@example.com',
];

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '2m', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // Порог из НФТ: девяносто пятый процентиль меньше секунды.
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

function headers() {
  const email = USERS[__VU % USERS.length];
  return { headers: { 'X-Dev-User': email, 'Content-Type': 'application/json' } };
}

export default function () {
  const options = headers();

  group('радар', () => {
    const signals = http.get(`${BASE_URL}/api/v1/signals?page_size=50`, options);
    check(signals, { 'сигналы отданы': (r) => r.status === 200 });
    const summary = http.get(`${BASE_URL}/api/v1/signals/summary`, options);
    check(summary, { 'матрица отдана': (r) => r.status === 200 });
  });

  let interactionId = null;
  group('список и карточка', () => {
    const list = http.get(`${BASE_URL}/api/v1/interactions?page_size=50`, options);
    check(list, { 'список отдан': (r) => r.status === 200 });
    const items = list.json('items') || [];
    if (items.length > 0) {
      interactionId = items[__VU % items.length].id;
      const card = http.get(`${BASE_URL}/api/v1/interactions/${interactionId}`, options);
      check(card, { 'карточка отдана': (r) => r.status === 200 });
    }
  });

  group('заметка', () => {
    if (interactionId === null) return;
    const note = http.post(
      `${BASE_URL}/api/v1/interactions/${interactionId}/notes`,
      JSON.stringify({ text: `Нагрузочная заметка VU ${__VU}` }),
      options,
    );
    check(note, { 'заметка сохранена': (r) => r.status === 201 });
  });

  group('аналитика', () => {
    const rating = http.get(`${BASE_URL}/api/v1/analytics/rating`, options);
    check(rating, { 'рейтинг посчитан': (r) => r.status === 200 });
  });

  sleep(1);
}
