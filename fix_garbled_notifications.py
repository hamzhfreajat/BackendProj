"""
Repairs notifications whose text was stored garbled ("Ø¥Ø¹Ù„Ø§Ù†Ùƒ" instead of "إعلانك").

They were written while main.py's Arabic text was damaged: the fixed parts of each
message went through the wrong encoding, while the ad titles inside them stayed
correct. Each damaged run of characters is turned back into its bytes and read
again as UTF-8; a run is only replaced when that gives clean Arabic or an emoji.

Run from the backend folder:

    python fix_garbled_notifications.py            # dry run: shows examples
    python fix_garbled_notifications.py --apply    # writes notification_text_backup_<time>.json, then updates
"""
import json
import re
import sys
import time

# Characters Windows-1252 shows for the bytes 0x80-0xFF (the five undefined ones stay as controls)
RUN = re.compile("[\u0080-ÿŒœŠšŸŽžƒˆ˜–—‘-„†-•…‰‹›€™]+")


def _bytes(run):
    out = bytearray()
    for ch in run:
        try:
            out += ch.encode("cp1252")
        except UnicodeEncodeError:
            if ord(ch) > 255:
                return None
            out.append(ord(ch))
    return bytes(out)


def repair(text):
    if not text:
        return text

    def fix(match):
        run = match.group(0)
        raw = _bytes(run)
        if raw is None:
            return run
        # A run can end in the middle of a character when the column cut the text short
        for cut in range(0, 4):
            try:
                decoded = raw[: len(raw) - cut].decode("utf-8") if cut else raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            return decoded if re.search("[؀-ۿ -\U0001faff]", decoded) else run
        return run

    return RUN.sub(fix, text)


def main():
    apply = "--apply" in sys.argv
    sys.path.append("/app")
    import models
    from database import SessionLocal

    db = SessionLocal()
    try:
        N = models.Notification
        damaged = "Ø[§£¥¢ª¨­®¯±²³´µ¶·¸¹º]|Ù[\u0080-¿„…†‡ˆ‰Š‹Œ]"
        rows = db.query(N.id, N.title, N.body).filter(N.title.op("~")(damaged) | N.body.op("~")(damaged)).all()
        plan = [(n_id, title, body, repair(title), repair(body)) for n_id, title, body in rows]
        plan = [row for row in plan if (row[1], row[2]) != (row[3], row[4])]
        still = sum(1 for row in plan if re.search("[ØÙ][\u0080-ÿ„…†‡]", f"{row[3]} {row[4]}"))
        print(f"Damaged notifications: {len(rows)} | repairable: {len(plan)} | still damaged after repair: {still}")
        seen = set()
        for n_id, title, body, new_title, new_body in plan:
            if new_title not in seen and len(seen) < 8:
                seen.add(new_title)
                print(f"  {n_id}: {new_title} | {(new_body or '')[:110]}")
        if not apply:
            print("Dry run: nothing was changed. Run again with --apply.")
            return
        db.rollback()
        name = f"notification_text_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(name, "w", encoding="utf-8") as handle:
            json.dump([{"id": r[0], "title": r[1], "body": r[2]} for r in plan], handle, ensure_ascii=False)
        print(f"Backup of the old text: {name}")
        done = 0
        for start in range(0, len(plan), 300):
            chunk = {row[0]: row for row in plan[start:start + 300]}
            for attempt in range(1, 6):
                try:
                    for item in db.query(N).filter(N.id.in_(list(chunk))).all():
                        item.title, item.body = chunk[item.id][3][:255], chunk[item.id][4]
                    db.commit()
                    done += len(chunk)
                    break
                except Exception as error:
                    db.rollback()
                    if attempt == 5:
                        raise
                    print(f"  batch at {start} failed ({type(error).__name__}), retry {attempt}")
                    time.sleep(2 * attempt)
        print(f"Repaired {done} notifications.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
