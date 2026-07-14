# Output Format & Examples

The bilingual rendering spec. Console-first: ASCII separators, blockquote for source, plain text for translation. No tables.

## Template

```
🌐 <source-lang> → <target-lang>
# When source == target, replace the line above with:
# 🔍 same-language clarify mode (<lang> → <lang>)

──────────────────────────────
> <source chunk 1>          # prose chunk: > blockquote source line
<target chunk 1>            # + plain translation line beneath

> <source chunk 2>
<target chunk 2>

# Code-block chunk (whole block verbatim, NOT > blockquoted, NOT line-translated):
<gloss line (optional)>

```<lang>
<code block, verbatim>
```

...
──────────────────────────────

📝 Ghi chú
- <term> — <gloss>  [src: <url>]
⚠️ Chưa xác nhận
- <term> — <what you tried / why unsure>
```

## Rules

- One blank line between each source/translation pair.
- **Prose/list chunk**: source line in a `>` blockquote; translation as plain text beneath.
- **Code-block chunk** (fenced code, stack trace, traceback, multi-line log, JSON/YAML/TOML/`.env`/config snippet): the whole block is one chunk. Render it **verbatim inside a fenced ` ``` ` block** (keep the language tag). Do **NOT** wrap it in `>` blockquote and do **NOT** emit a per-line translation — that duplicates every line. A multi-line code block is never split into line-by-line chunks.
- Keep code, file paths, URLs, identifiers, error codes **verbatim** — never translate them. Inline comments inside code (`//`, `#`) stay verbatim too; the code must remain copy-pasteable.
- On first use of a non-obvious IT term, you may add a short gloss in parentheses: `hook (móc nối)`.
- Before a code-block chunk you may add one short Vietnamese gloss line (e.g. "Đây là component Button:") explaining what it does; skip it if surrounding prose already conveys the meaning.
- Separator width stays constant (e.g. 30 `─`). Use plain ASCII `─` is fine on modern terminals; if unsure, use `----`.
- End with **📝 Ghi chú** (Notes): verified terms + sources. Omit `⚠️ Chưa xác nhận` if none.

## Example 1 — English → Vietnamese (ticket)

Input:
> Fix the flaky test in `auth.spec.ts`. It fails intermittently because the JWT expires before the assertion runs. Increase the token TTL to 5m and add a retry.

Output:
```
🌐 English → Tiếng Việt

──────────────────────────────
> Fix the flaky test in `auth.spec.ts`.
Sửa test không ổn định (flaky) trong file `auth.spec.ts`.

> It fails intermittently because the JWT expires before the assertion runs.
Nó fail không ổn định do JWT hết hạn trước khi câu assert (kiểm tra khẳng định) chạy.

> Increase the token TTL to 5m and add a retry.
Tăng TTL (thời gian sống) của token lên 5 phút và thêm cơ chế retry (thử lại).
──────────────────────────────

📝 Ghi chú
- flaky test — test lúc pass lúc fail, không xác định  [src: https://jestjs.io/docs/flaky]
- TTL — time-to-live, thời gian sống của token  [src: https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.4]
```

## Example 2 — Mixed EN/VN + IT terms → Vietnamese

Input:
> Mình dùng Next.js App Router, nhưng khi fetch data trong Server Component thì bị `hydration error`. Lý do là client render khác server render. Fix sao?

Output:
```
🌐 Mixed (VI + EN/IT) → Tiếng Việt

──────────────────────────────
> Mình dùng Next.js App Router, nhưng khi fetch data trong Server Component thì bị `hydration error`.
Bạn đang dùng Next.js App Router, nhưng khi fetch dữ liệu trong Server Component thì gặp lỗi `hydration error`.

> Lý do là client render khác server render.
Nguyên nhân: kết quả render ở client khác với render ở server.

> Fix sao?
Cách khắc phục: đảm bảo nội dung render nhất quán giữa server và client — đừng dùng `Date.now()`, `Math.random()`, hoặc dữ liệu phụ thuộc trình duyệt trong lần render đầu; nếu cần, lấy giá trị đó trong `useEffect`.
──────────────────────────────

📝 Ghi chú
- hydration error — lỗi xảy ra khi cây DOM do server render không khớp với cây DOM do React render ở client  [src: https://react.dev/errors/hydration]
- Server Component — component chỉ chạy trên server, không gửi JS xuống client  [src: https://nextjs.org/docs/app/building-your-application/rendering]
```

## Example 3 — Vietnamese → English (direction overridden)

User said "dịch sang tiếng Anh". Input:
> Lỗi này do cache cũ, cần clear cache rồi build lại.

Output:
```
🌐 Tiếng Việt → English

──────────────────────────────
> Lỗi này do cache cũ, cần clear cache rồi build lại.
This error is caused by stale cache — you need to clear the cache and rebuild.
──────────────────────────────
```

## Example 4 — Same-language clarify mode (source == target)

Input is already Vietnamese, target defaults to Vietnamese → do not switch language. Focus on IT terms + context.

Input:
> Server return 500, log báo `SQLSTATE 23505` lúc insert user mới. Sao lại vậy?

Output:
```
🔍 same-language clarify mode (Tiếng Việt → Tiếng Việt)

──────────────────────────────
> Server return 500, log báo `SQLSTATE 23505` lúc insert user mới. Sao lại vậy?
Server trả về lỗi 500 (lỗi phía server). Log ghi mã `SQLSTATE 23505` — đây là lỗi vi phạm ràng buộc duy nhất (unique violation), tức bạn đang insert một user có giá trị trùng với bản ghi đã tồn tại (thường là trường unique như email hoặc username). Nguyên nhân khả năng cao: dữ liệu trùng hoặc chưa kiểm tra tồn tại trước khi insert.
──────────────────────────────

📝 Ghi chú
- SQLSTATE 23505 — vi phạm ràng buộc unique / primary key  [src: https://www.postgresql.org/docs/current/errcodes-appendix.html]
- HTTP 500 — lỗi chung phía server, bản thân nó không cho biết nguyên nhân gốc  [src: https://datatracker.ietf.org/doc/html/rfc9110#name-500-internal-server-error]
```

Note: the source language is preserved; value comes from clarifying terms, adding context, and citing docs — not from switching language.

## Example 5 — List input (bullets stripped, same bilingual chunk format)

List input uses the SAME format as prose: each list item becomes one chunk. Strip the bullet/number marker — no `-`, no `*`, no `→`. Just `>`-quoted source line + plain translation line.

Input:
```
I have a few questions to clarify before creating the MR.

* Please check the attached API response schema.
* There is no **Transaction ID** value in the **Company Identity Card** section. How should we handle this?
* The `registration_date` is currently returned as `1950-11-04`, while the UI expects `15 Jul 2025, 5:35 PM`.
```

Output:
```
🌐 English → Tiếng Việt

────────────────────────────
> I have a few questions to clarify before creating the MR.
Tôi có vài câu hỏi cần làm rõ trước khi tạo MR (Merge Request — yêu cầu gộp code).

> Please check the attached API response schema.
Mình có đính kèm schema (cấu trúc dữ liệu) của API response — bạn xem giúp nhé.

> There is no **Transaction ID** value in the **Company Identity Card** section. How should we handle this?
Trong phần **Company Identity Card** không có giá trị **Transaction ID**. Nên xử lý thế nào?

> The `registration_date` is currently returned as `1950-11-04`, while the UI expects `15 Jul 2025, 5:35 PM`.
Hiện tại `registration_date` trả về định dạng `1950-11-04`, trong khi UI kỳ vọng dạng `15 Jul 2025, 5:35 PM`.
────────────────────────────

📝 Ghi chú
- MR (Merge Request) — yêu cầu gộp nhánh (GitLab; tương đương PR bên GitHub)
- schema — cấu trúc (tên field + kiểu dữ liệu) của dữ liệu API trả về
```

Rules:
- Bullet markers are stripped; each item becomes a plain `>`-quoted source line + plain translation line.
- Never use `-`, `*`, `+`, `1.`, or `→` in the output.
- Keep `**bold**` and `` `code` `` spans; keep identifiers verbatim.
- One source item → one source line + one translation line.

## Example 6 — Input contains a code block (rendered verbatim, never duplicated)

A code block is one atomic chunk. Render the **whole block verbatim inside a fenced ` ``` ` block** — do NOT `>`-blockquote it, do NOT emit a per-line translation (that would duplicate every line). Optionally precede it with a short Vietnamese gloss line.

Input:
```
Translate this: Here's the confirm button. Use this:

<Button
  variant="primary"
  size="large"
  sx={{ marginTop: '32px', borderRadius: '100%' }}
>
  Confirm & Proceed
</Button>

It should sit at the top of the modal.
```

Output:
```
🌐 English → Tiếng Việt

────────────────────────────
> Here's the confirm button. Use this:
Đây là nút confirm (xác nhận). Dùng như sau:

Đây là component Button:

```jsx
<Button
  variant="primary"
  size="large"
  sx={{ marginTop: '32px', borderRadius: '100%' }}
>
  Confirm & Proceed
</Button>
```

> It should sit at the top of the modal.
Nó nên nằm ở đầu modal (hộp thoại nổi).
────────────────────────────

📝 Ghi chú
- MUI sx prop — prop nhận object style động cho component  [src: https://mui.com/system/the-sx-prop/]
```

Rules:
- The JSX block is rendered **once**, verbatim, fenced with `jsx` tag. No line is repeated.
- Prose around the code still uses the `>` blockquote + translation pair.
- The optional gloss line ("Đây là component Button:") is plain text, not `>`-quoted.
- Inline comments inside code (none here) would stay verbatim — never translated in place.

## Long Input

If input is long (a full doc section or multi-paragraph issue):
1. First line: a one-line structural summary.
2. Then render chunks grouped under light headings (`##`) matching the source's structure.
3. If output risks being truncated, stop at a clean boundary and offer to continue.
