import pptxgen from "pptxgenjs";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

// Корень репозитория — от расположения скрипта, а не с машины автора.
const ROOT = fileURLToPath(new URL("../..", import.meta.url)).replace(/\/$/, "");
// Число операций и путей берём из контракта: цифра на слайде не устареет вместе с API.
const CONTRACT = readFileSync(`${ROOT}/contracts/openapi.yaml`, "utf8");
const OPERATIONS = (CONTRACT.match(/^\s+operationId:/gm) ?? []).length;
const PATHS = (CONTRACT.match(/^  \/\S*:$/gm) ?? []).length;
// «1 тест», «3 теста», «332 теста», «116 операций».
const plural = (n, one, few, many) => {
  const tail = n % 100;
  if (tail >= 11 && tail <= 14) return `${n} ${many}`;
  if (n % 10 === 1) return `${n} ${one}`;
  if (n % 10 >= 2 && n % 10 <= 4) return `${n} ${few}`;
  return `${n} ${many}`;
};
// Тесты — функции test_* бэкенда; параметризованные варианты pytest считает отдельно, их больше.
const TESTS = readdirSync(`${ROOT}/backend/tests`)
  .filter((name) => name.startsWith("test_") && name.endsWith(".py"))
  .map((name) => readFileSync(`${ROOT}/backend/tests/${name}`, "utf8"))
  .reduce((total, text) => total + (text.match(/^(async )?def test_/gm) ?? []).length, 0);
const SHOT = (name) => `${ROOT}/backend/app/help/images/${name}.png`;
const DIAGRAM = (n) => `${ROOT}/docs/architecture/images/diagram-${n}.png`;

// Палитра взята из самого продукта: тёмная навигация, оранжевое действие, фиолетовое выделение.
const NAVY = "1B2140";
const INK = "232634";
const MUTED = "6B7280";
const LIGHT = "F3F4F8";
const ORANGE = "E8590C";
const VIOLET = "6D4AFF";
const WHITE = "FFFFFF";

const HEAD = "Cambria";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Команда «Радар вузов»";
pres.title = "Радар вузов — кейс №6 ЛЦТ 2026";

const W = 13.3;
const H = 7.5;
const M = 0.7;

function titled(slide, title, subtitle) {
  slide.addText(title, {
    x: M, y: 0.45, w: W - 2 * M, h: 0.8,
    fontFace: HEAD, fontSize: 32, bold: true, color: INK, isTextBox: true, margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: M, y: 1.22, w: W - 2 * M, h: 0.45,
      fontFace: BODY, fontSize: 14, color: MUTED, isTextBox: true, margin: 0,
    });
  }
}

function card(slide, { x, y, w, h, fill = WHITE }) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.12, fill: { color: fill },
    line: { color: "E3E6EF", width: 1 },
    shadow: { type: "outer", angle: 90, blur: 10, offset: 2, color: "AAB0C0", opacity: 0.25 },
  });
}

function badge(slide, { x, y, text, color = VIOLET }) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: 0.42, h: 0.42, fill: { color } });
  slide.addText(text, {
    x, y, w: 0.42, h: 0.42, align: "center", valign: "middle",
    fontFace: BODY, fontSize: 13, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
}

function bullets(slide, items, { x, y, w, size = 14 }) {
  slide.addText(
    items.map((text, index) => ({
      text,
      options: { bullet: true, breakLine: index !== items.length - 1, paraSpaceAfter: 8 },
    })),
    { x, y, w, h: 0.4 * items.length + 0.4, fontFace: BODY, fontSize: size, color: INK, isTextBox: true, margin: 0 },
  );
}

function picture(slide, path, { x, y, w, h }) {
  // sizing: contain вписывает картинку в рамку и не растягивает — у схем и снимков разные пропорции.
  if (existsSync(path)) slide.addImage({ path, x, y, w, h, sizing: { type: "contain", w, h } });
}

// 1. Титул
{
  const slide = pres.addSlide();
  slide.background = { color: NAVY };
  slide.addText("Радар вузов", {
    x: M, y: 2.2, w: W - 2 * M, h: 1.2,
    fontFace: HEAD, fontSize: 54, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
  slide.addText("CRM контроля взаимодействия ИТ Школы Ростелекома с вузами", {
    x: M, y: 3.4, w: 8.6, h: 0.9,
    fontFace: BODY, fontSize: 20, color: "C9CEE4", isTextBox: true, margin: 0,
  });
  slide.addText("Кейс №6 · ЛЦТ 2026", {
    x: M, y: 4.45, w: 6, h: 0.5,
    fontFace: BODY, fontSize: 16, color: ORANGE, bold: true, isTextBox: true, margin: 0,
  });
  slide.addText(`Работающий прототип: ${plural(OPERATIONS, "операция", "операции", "операций")} API, ${plural(TESTS, "тест", "теста", "тестов")}, демо-стенд на 351 записи`, {
    x: M, y: 5.6, w: 9.5, h: 0.5,
    fontFace: BODY, fontSize: 13, color: "8E97B8", italic: true, isTextBox: true, margin: 0,
  });
  slide.addNotes("Здравствуйте. Мы сделали CRM для ИТ Школы Ростелекома: она ведёт работу с вузами от первого контакта до занятий и сама показывает, где работа встала.");
}

// 2. Проблема
{
  const slide = pres.addSlide();
  titled(slide, "Работа есть, а картины нет", "Так выглядит процесс, пока он живёт в таблицах");
  const stats = [
    ["96", "вузов в работе", "у каждого — свои программы и продукты"],
    ["14", "этапов пути", "от поиска контактов до контроля занятий"],
    ["0", "сигналов тревоги", "просрочку замечают, когда уже поздно"],
  ];
  stats.forEach(([value, label, note], index) => {
    const x = M + index * 4.05;
    card(slide, { x, y: 2.1, w: 3.75, h: 2.3 });
    slide.addText(value, {
      x: x + 0.3, y: 2.3, w: 3.1, h: 0.9,
      fontFace: HEAD, fontSize: 44, bold: true, color: index === 2 ? ORANGE : VIOLET, isTextBox: true, margin: 0,
    });
    slide.addText(label, {
      x: x + 0.3, y: 3.18, w: 3.1, h: 0.35,
      fontFace: BODY, fontSize: 15, bold: true, color: INK, isTextBox: true, margin: 0,
    });
    slide.addText(note, {
      x: x + 0.3, y: 3.55, w: 3.15, h: 0.7,
      fontFace: BODY, fontSize: 12, color: MUTED, isTextBox: true, margin: 0,
    });
  });
  bullets(slide, [
    "Отчёт за период собирают руками, и каждый раз по-своему",
    "Договор, лицензия и обучение живут в разных файлах",
    "Заявки с сайта и данные из LMS никуда не приходят сами",
  ], { x: M, y: 4.75, w: W - 2 * M });
  slide.addNotes("Задача не в том, чтобы завести ещё одну таблицу, а в том, чтобы система сама показывала, где работа встала.");
}

// 3. Решение
{
  const slide = pres.addSlide();
  titled(slide, "Радар: экран, с которого начинается день", "Записи, которые требуют внимания сегодня — с причиной и сроком");
  picture(slide, SHOT("radar"), { x: 6.3, y: 1.75, w: 6.3, h: 4.28, rounding: true });
  bullets(slide, [
    "Четыре сигнала: просрочка этапа, истекающая лицензия, отсутствие документа, простой",
    "Сигнал открывается и закрывается сам — ничего не нужно помечать руками",
    "У каждого сигнала видно числа, по которым он построен",
    "Пороги задаёт администратор, а не разработчик",
  ], { x: M, y: 2.0, w: 5.3, size: 15 });
  slide.addNotes("Это первый экран КАМа. Шесть записей из трёхсот пятидесяти — те, где сегодня нужно что-то сделать.");
}

// 4. Процесс
{
  const slide = pres.addSlide();
  titled(slide, "Путь взаимодействия виден целиком", "Карточка записи: этап, сроки, требования и история");
  picture(slide, SHOT("card"), { x: M, y: 1.8, w: 6.5, h: 4.42, rounding: true });
  const points = [
    ["Этап и норма", "46 дней на этапе при норме 14 — это и есть сигнал"],
    ["Требования перехода", "нет подписанного договора — система не пустит дальше и скажет почему"],
    ["Возврат назад", "процесс бюрократический: у каждого шага вперёд есть обратный"],
    ["История только дозаписью", "триггер базы запрещает изменить прошлое"],
  ];
  points.forEach(([head, text], index) => {
    const y = 1.95 + index * 1.15;
    badge(slide, { x: 7.5, y, text: String(index + 1) });
    slide.addText(head, {
      x: 8.05, y: y - 0.04, w: 4.4, h: 0.32,
      fontFace: BODY, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0,
    });
    slide.addText(text, {
      x: 8.05, y: y + 0.28, w: 4.5, h: 0.7,
      fontFace: BODY, fontSize: 12, color: MUTED, isTextBox: true, margin: 0,
    });
  });
  slide.addNotes("Правила перехода проверяет сервер, а не интерфейс: кнопку можно спрятать, но обойти правило нельзя.");
}

// 5. Радар — четыре сигнала
{
  const slide = pres.addSlide();
  titled(slide, "Четыре сигнала и ни одного ручного статуса", "Правила и пороги — в настройках администратора");
  const signals = [
    ["Просрочка этапа", "дней на этапе больше нормы", "medium / high"],
    ["Истекает лицензия", "до конца лицензии 60 дней и меньше", "medium / high"],
    ["Нет документа", "этап требует документ, прошла половина нормы", "medium"],
    ["Простой", "нет переходов, заметок и файлов", "low / medium"],
  ];
  signals.forEach(([name, rule, severity], index) => {
    const y = 1.95 + index * 1.15;
    card(slide, { x: M, y, w: 11.9, h: 0.95, fill: index % 2 ? LIGHT : WHITE });
    slide.addText(name, {
      x: M + 0.35, y: y + 0.12, w: 3.3, h: 0.35,
      fontFace: BODY, fontSize: 15, bold: true, color: INK, isTextBox: true, margin: 0,
    });
    slide.addText(rule, {
      x: M + 3.8, y: y + 0.12, w: 5.6, h: 0.6,
      fontFace: BODY, fontSize: 13, color: MUTED, isTextBox: true, margin: 0,
    });
    slide.addText(severity, {
      x: 10.6, y: y + 0.12, w: 1.9, h: 0.35, align: "right",
      fontFace: BODY, fontSize: 13, bold: true, color: ORANGE, isTextBox: true, margin: 0,
    });
  });
  slide.addText("Пересчёт идёт сразу после действия и полностью раз в сутки: запись получает сигнал сама, просто потому что прошло время.", {
    x: M, y: 6.6, w: 11.9, h: 0.5,
    fontFace: BODY, fontSize: 12, color: MUTED, italic: true, isTextBox: true, margin: 0,
  });
  slide.addNotes("Ни один сигнал не ставится руками — иначе он врёт ровно в тот момент, когда нужен.");
}

// 6. Рейтинг
{
  const slide = pres.addSlide();
  titled(slide, "Рейтинг, который можно объяснить", "Заявки, обучающиеся и потоки — с вкладом каждой метрики");
  card(slide, { x: M, y: 1.9, w: 6.1, h: 3.5 });
  slide.addText("score = Σ(вес × нормированное значение) / Σ(вес)", {
    x: M + 0.35, y: 2.15, w: 5.4, h: 0.4,
    fontFace: BODY, fontSize: 14, bold: true, color: VIOLET, isTextBox: true, margin: 0,
  });
  bullets(slide, [
    "Нормирование внутри направления: маленькое направление не проигрывает большому",
    "Сумма вкладов равна баллу — видно, из чего он сложился",
    "Нет метрики за период — строка помечается неполной, а не проваливается вниз",
    "Никаких внешних LLM: результат воспроизводим и проверяем",
  ], { x: M + 0.35, y: 2.65, w: 5.4, size: 13 });
  card(slide, { x: 7.2, y: 1.9, w: 5.4, h: 3.5, fill: LIGHT });
  slide.addText("Ручной приоритет", {
    x: 7.55, y: 2.15, w: 4.7, h: 0.4,
    fontFace: BODY, fontSize: 15, bold: true, color: INK, isTextBox: true, margin: 0,
  });
  slide.addText("«В этом году продвигаем ИИ» — это решение человека, а не вывод из данных.", {
    x: 7.55, y: 2.6, w: 4.7, h: 0.7,
    fontFace: BODY, fontSize: 13, color: MUTED, isTextBox: true, margin: 0,
  });
  bullets(slide, [
    "Курс можно поднять вручную: приоритет 0–100",
    "Порядок показа меняется, балл и место — нет",
    "Изменение пишется в журнал аудита",
  ], { x: 7.55, y: 3.4, w: 4.7, size: 13 });
  slide.addText("Так видно, где расчёт, а где решение: рейтинг остаётся объяснимым.", {
    x: M, y: 5.65, w: 11.9, h: 0.5,
    fontFace: BODY, fontSize: 13, color: INK, italic: true, isTextBox: true, margin: 0,
  });
  slide.addNotes("Жюри прямо спрашивало про ручные приоритеты. Мы их сделали, но не дали им подменить расчёт.");
}

// 7. B2B и B2C
{
  const slide = pres.addSlide();
  titled(slide, "Вузы и частные лица — разные процессы", "Группа контрагентов определяет путь записи");
  const groups = [
    ["Вузы (B2B)", VIOLET, ["14 этапов из ТЗ", "договор, лицензия, передача материалов", "обучение преподавателей и ведение занятий"]],
    ["Частные лица (B2C)", ORANGE, ["свой короткий путь: заявка → оплата → занятия", "контрагент — человек или организация", "продукт может быть не нужен"]],
  ];
  groups.forEach(([name, color, items], index) => {
    const x = M + index * 6.15;
    card(slide, { x, y: 2.0, w: 5.75, h: 3.1 });
    slide.addShape(pres.ShapeType.roundRect, {
      x: x + 0.35, y: 2.3, w: 2.6, h: 0.42, rectRadius: 0.1, fill: { color },
    });
    slide.addText(name, {
      x: x + 0.35, y: 2.3, w: 2.6, h: 0.42, align: "center", valign: "middle",
      fontFace: BODY, fontSize: 13, bold: true, color: WHITE, isTextBox: true, margin: 0,
    });
    bullets(slide, items, { x: x + 0.35, y: 2.95, w: 5.0, size: 13 });
  });
  slide.addText("Администратор заводит новые группы сам: у каждой свой процесс, свои нормы и свой радар.", {
    x: M, y: 5.4, w: 11.9, h: 0.5,
    fontFace: BODY, fontSize: 13, color: MUTED, isTextBox: true, margin: 0,
  });
  slide.addNotes("Это ответ на вопрос жюри про B2C: не отдельная система, а группа контрагентов со своим процессом.");
}

// 8. Интеграции
{
  const slide = pres.addSlide();
  titled(slide, "Обмен в обе стороны", "CRM — ядро процесса, а не ещё один справочник");

  const boxes = [
    { x: M, label: "LMS", note: "обучающиеся, потоки", color: LIGHT, text: INK },
    { x: 5.0, label: "Радар вузов", note: "очередь обмена в той же транзакции", color: NAVY, text: WHITE },
    { x: 9.3, label: "Сайт ИТ Школы", note: "заявки абитуриентов", color: LIGHT, text: INK },
  ];
  boxes.forEach(({ x, label, note, color, text }) => {
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 2.3, w: 3.3, h: 1.6, rectRadius: 0.14, fill: { color },
      line: { color: color === NAVY ? NAVY : "D8DCE8", width: 1 },
    });
    slide.addText(label, {
      x: x + 0.25, y: 2.5, w: 2.8, h: 0.45,
      fontFace: BODY, fontSize: 17, bold: true, color: text, isTextBox: true, margin: 0,
    });
    slide.addText(note, {
      x: x + 0.25, y: 2.95, w: 2.85, h: 0.8,
      fontFace: BODY, fontSize: 12, color: color === NAVY ? "B9C0DC" : MUTED, isTextBox: true, margin: 0,
    });
  });

  const arrows = [
    { x: 4.05, y: 2.65, w: 0.85, flip: false, label: "метрики" },
    { x: 4.05, y: 3.35, w: 0.85, flip: true, label: "документ" },
    { x: 8.35, y: 2.65, w: 0.85, flip: true, label: "заявки" },
    { x: 8.35, y: 3.35, w: 0.85, flip: false, label: "документ" },
  ];
  arrows.forEach(({ x, y, w, flip, label }) => {
    slide.addShape(pres.ShapeType.rightArrow, {
      x, y, w, h: 0.26, fill: { color: flip ? ORANGE : VIOLET }, flipH: flip,
    });
    slide.addText(label, {
      x: x - 0.15, y: y + 0.27, w: 1.15, h: 0.25, align: "center",
      fontFace: BODY, fontSize: 9, color: MUTED, isTextBox: true, margin: 0,
    });
  });

  bullets(slide, [
    "Заявка сама находит запись по вузу, программе и продукту; не нашлась — ждёт человека",
    "Обратно уходит документ radar-vuzov/interaction@1: статус, ответственный, файлы, ключи связей",
    "Отметка об отправке пишется в одной транзакции с изменением: откатилась — отправлять нечего",
    "Получатель недоступен — повтор по расписанию, работа КАМа не ждёт",
  ], { x: M, y: 4.5, w: 11.9, size: 14 });
  slide.addNotes("Полная схема связей со всеми участниками — в сопроводительной документации, здесь только суть обмена.");
}

// 9. Архитектура
{
  const slide = pres.addSlide();
  titled(slide, "Из чего это собрано", "Один сервер, docker compose, наружу только 80 и 443");

  const layers = [
    ["Вход", ["nginx — TLS, статика", "Keycloak 26 — вход и роли"], VIOLET],
    ["Приложение", ["api — FastAPI, uvicorn", "worker — arq, тот же образ"], ORANGE],
    ["Состояние", ["PostgreSQL 16", "Redis 7", "MinIO (S3)"], NAVY],
  ];
  layers.forEach(([name, items, color], index) => {
    const x = M + index * 4.05;
    card(slide, { x, y: 2.0, w: 3.75, h: 2.6 });
    slide.addShape(pres.ShapeType.roundRect, {
      x: x + 0.3, y: 2.25, w: 1.75, h: 0.4, rectRadius: 0.1, fill: { color },
    });
    slide.addText(name, {
      x: x + 0.3, y: 2.25, w: 1.75, h: 0.4, align: "center", valign: "middle",
      fontFace: BODY, fontSize: 12, bold: true, color: WHITE, isTextBox: true, margin: 0,
    });
    items.forEach((item, line) => {
      slide.addText(item, {
        x: x + 0.3, y: 2.85 + line * 0.42, w: 3.2, h: 0.38,
        fontFace: BODY, fontSize: 13, color: INK, isTextBox: true, margin: 0,
      });
    });
  });

  card(slide, { x: M, y: 4.8, w: 11.9, h: 0.95, fill: LIGHT });
  slide.addText("Резервные копии раз в сутки: дамп базы и зеркало файлов из MinIO — в один том, с проверкой восстановления", {
    x: M + 0.35, y: 5.0, w: 11.2, h: 0.55,
    fontFace: BODY, fontSize: 13, color: INK, isTextBox: true, margin: 0,
  });

  bullets(slide, [
    "Приложение без состояния: масштабируется копиями за тем же nginx",
    "Очереди захватываются арендой и SKIP LOCKED — вторая копия воркера не отправит то же дважды",
    "Swagger на /api/docs, контракт в репозитории, расхождение ловит CI",
  ], { x: M, y: 5.95, w: 11.9, size: 13 });
  slide.addNotes("Схема программно-аппаратной архитектуры целиком — в документации; здесь три слоя и то, что масштабируется.");
}

// 10. Нагрузка
{
  const slide = pres.addSlide();
  titled(slide, "Нагрузка измерена, а не обещана", "k6 на данных стенда: 299 записей, 96 вузов, 10 548 метрик");
  const rows = [
    ["50 пользователей", "386,59 мс", "порог 1 с ✓", "0 ошибок из 21 048"],
    ["100 пользователей", "1,15 с", "упирается база", "0 ошибок из 24 996"],
    ["300 пользователей", "1,87 с", "четыре копии API", "0 ошибок из 40 872"],
    ["10 отчётов разом", "204 мс", "все доходят до done", "полный цикл до 4,3 с"],
  ];
  rows.forEach(([label, value, note, errors], index) => {
    const y = 1.95 + index * 1.1;
    card(slide, { x: M, y, w: 11.9, h: 0.92, fill: index === 0 ? "EEF6EE" : WHITE });
    slide.addText(label, { x: M + 0.35, y: y + 0.12, w: 3.2, h: 0.35, fontFace: BODY, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0 });
    slide.addText(value, { x: M + 3.6, y: y + 0.1, w: 2.0, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: index === 0 ? "2C6E32" : INK, isTextBox: true, margin: 0 });
    slide.addText(note, { x: M + 5.7, y: y + 0.15, w: 3.0, h: 0.35, fontFace: BODY, fontSize: 12, color: MUTED, isTextBox: true, margin: 0 });
    slide.addText(errors, { x: M + 8.8, y: y + 0.15, w: 2.7, h: 0.35, align: "right", fontFace: BODY, fontSize: 12, color: MUTED, isTextBox: true, margin: 0 });
  });
  slide.addText("Система не отказывает, а замедляется: узкое горлышко — база (420 % CPU против 6 % у Redis). План на 300+: разнести базу и приложение, PgBouncer, копии API и воркера, реплика для чтения.", {
    x: M, y: 6.45, w: 11.9, h: 0.7,
    fontFace: BODY, fontSize: 12, color: INK, isTextBox: true, margin: 0,
  });
  slide.addNotes("Важнее самой цифры то, что на всех ступенях ноль ошибок: замедление лечится железом, отказ пришлось бы чинить.");
}

// 11. Безопасность
{
  const slide = pres.addSlide();
  titled(slide, "152-ФЗ — не абзац в документе", "Меры, у каждой из которых есть место в коде и тест");
  const measures = [
    ["Права проверяет сервер", "чужая запись — «не найдено», а не «нет прав»; тест на каждом методе"],
    ["Персональные данные шифруются", "почта и телефон — Fernet; в списке адрес показан сокращённо"],
    ["Просмотр ПДн пишется в аудит", "видно, кто и когда открывал контакт; журнал только дозаписью"],
    ["История не переписывается", "триггер базы запрещает UPDATE и DELETE переходов"],
    ["Секреты — только в окружении", "в базе хранится имя переменной, а не сам токен"],
    ["Зависимости проверяются", "pip-audit и gitleaks в CI; известных уязвимостей нет"],
  ];
  measures.forEach(([head, text], index) => {
    const column = index % 2;
    const row = Math.floor(index / 2);
    const x = M + column * 6.15;
    const y = 1.95 + row * 1.55;
    card(slide, { x, y, w: 5.75, h: 1.35, fill: LIGHT });
    slide.addText(head, { x: x + 0.35, y: y + 0.18, w: 5.0, h: 0.35, fontFace: BODY, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0 });
    slide.addText(text, { x: x + 0.35, y: y + 0.58, w: 5.05, h: 0.65, fontFace: BODY, fontSize: 12, color: MUTED, isTextBox: true, margin: 0 });
  });
  slide.addNotes("Аттестуется контур заказчика, но архитектуру и меры смотрят уже сейчас — поэтому у каждой меры есть ссылка на код.");
}

// 12. Итог
{
  const slide = pres.addSlide();
  slide.background = { color: NAVY };
  slide.addText("Что готово", {
    x: M, y: 0.8, w: 5.6, h: 0.6,
    fontFace: HEAD, fontSize: 28, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
  const done = [
    "Процесс, радар, отчёты, рейтинг, интеграции, уведомления",
    `${plural(OPERATIONS, "операция", "операции", "операций")} на ${plural(PATHS, "пути", "путях", "путях")} API, контракт, ${plural(TESTS, "тест", "теста", "тестов")}, 46 таблиц`,
    "Руководства внутри продукта, диаграммы, разбор соответствия ТЗ",
    "Демо-стенд на 351 записи поднимается одной командой",
  ];
  slide.addText(
    done.map((text, index) => ({ text, options: { bullet: true, breakLine: index !== done.length - 1, paraSpaceAfter: 10 } })),
    { x: M, y: 1.6, w: 5.6, h: 3.0, fontFace: BODY, fontSize: 14, color: "D7DBEC", isTextBox: true, margin: 0 },
  );
  slide.addText("Что дальше", {
    x: 7.0, y: 0.8, w: 5.6, h: 0.6,
    fontFace: HEAD, fontSize: 28, bold: true, color: ORANGE, isTextBox: true, margin: 0,
  });
  const next = [
    "Развернуть стенд: сервер и домен — единственное, чего нельзя закрыть кодом",
    "Подключить оставшиеся экраны интерфейса по готовой постановке",
    "Снять скриншоты новых экранов во встроенное руководство",
  ];
  slide.addText(
    next.map((text, index) => ({ text, options: { bullet: true, breakLine: index !== next.length - 1, paraSpaceAfter: 10 } })),
    { x: 7.0, y: 1.6, w: 5.6, h: 3.0, fontFace: BODY, fontSize: 14, color: "D7DBEC", isTextBox: true, margin: 0 },
  );
  slide.addText("Репозиторий, документация и демо-стенд — по ссылке из заявки", {
    x: M, y: 5.6, w: 11.9, h: 0.5,
    fontFace: BODY, fontSize: 14, color: "8E97B8", italic: true, isTextBox: true, margin: 0,
  });
  slide.addText("Спасибо. Готовы показать вживую любой сценарий.", {
    x: M, y: 6.2, w: 11.9, h: 0.6,
    fontFace: HEAD, fontSize: 20, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
  slide.addNotes("Здесь честно: стенда нет, потому что нет сервера. Всё остальное работает и проверяется командами из репозитория.");
}

await pres.writeFile({ fileName: `${ROOT}/docs/РадарВузов-презентация.pptx` });
console.log("готово");
