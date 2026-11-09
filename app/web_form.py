"""HTML веб-формы. Вынесено отдельно, чтобы не мешать разметку и логику."""

FORM_PAGE = """<!doctype html>
<html lang="ru">
<meta charset="utf-8">
<title>Черновик карточки товара - КИП</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font: 15px/1.5 -apple-system, Segoe UI, Roboto, sans-serif; margin: 0 auto;
         max-width: 900px; padding: 24px 16px; color: #1b1b1b; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  p.sub { color: #666; margin: 0 0 20px; }
  textarea { width: 100%; height: 300px; font: 13px/1.45 ui-monospace, Menlo, monospace;
             padding: 10px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 6px; }
  button { margin-top: 12px; padding: 9px 18px; font-size: 15px; border: 0;
           border-radius: 6px; background: #1b5e9b; color: #fff; cursor: pointer; }
  button[disabled] { background: #9bb4c9; cursor: default; }
  pre { background: #f6f6f6; padding: 14px; border-radius: 6px; white-space: pre-wrap;
        word-wrap: break-word; }
  .err { color: #a11; white-space: pre-wrap; }
  .muted { color: #666; font-size: 13px; }
</style>
<h1>Черновик карточки товара для B2B-магазина КИП</h1>
<p class="sub">Вставьте JSON о приборе. Модель: <code>{{model}}</code>.
Технические значения берутся только из входных данных.</p>

<form id="f">
  <textarea id="src" spellcheck="false">{
  "name": "Манометр показывающий ТМ-510Р.00 (0-2,5 МПа) G1/2",
  "manufacturer": "РОСМА",
  "specs": {
    "диапазон измерений": "0-2,5 МПа",
    "присоединение": "G1/2",
    "диаметр корпуса": "100 мм"
  },
  "description": "Манометр предназначен для измерения избыточного давления неагрессивных к медным сплавам жидкостей, пара и газа."
}</textarea>
  <button id="go" type="submit">Собрать карточку</button>
  <span id="state" class="muted"></span>
</form>

<div id="out"></div>

<script>
const form = document.getElementById('f');
const out = document.getElementById('out');
const state = document.getElementById('state');
const go = document.getElementById('go');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  out.innerHTML = '';
  let payload;
  try {
    payload = JSON.parse(document.getElementById('src').value);
  } catch (err) {
    out.innerHTML = '<p class="err">Некорректный JSON: ' + err.message + '</p>';
    return;
  }
  go.disabled = true;
  state.textContent = ' запрос к модели, обычно 10-40 секунд...';
  try {
    const resp = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await resp.json();
    if (!resp.ok) {
      out.innerHTML = '<p class="err">Ошибка ' + resp.status + ': ' +
        (data.error || JSON.stringify(data)) + '</p>';
    } else {
      const pre = document.createElement('pre');
      pre.textContent = data.markdown;
      out.appendChild(pre);
    }
  } catch (err) {
    out.innerHTML = '<p class="err">Сервис недоступен: ' + err.message + '</p>';
  } finally {
    go.disabled = false;
    state.textContent = '';
  }
});
</script>
</html>
"""
