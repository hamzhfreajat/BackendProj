import re

with open('telemetry_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

friction_code = """
    # Friction Metrics for User
    rage_taps_query = text('''
        SELECT 
          screen,
          metadata_json->>'location' as location,
          metadata_json->>'target_name' as target
        FROM telemetry_events
        WHERE event_name = 'rage_tap'
          AND metadata_json->>'location' IS NOT NULL
          AND screen IS NOT NULL 
          AND screen != ''
          AND user_id = :uid
        LIMIT 500;
    ''')
    rage_taps_results = db.execute(rage_taps_query, {"uid": user_id_str}).fetchall()
    rage_taps_data = []
    for r in rage_taps_results:
        try:
            x_str, y_str = r.location.split(',')
            rage_taps_data.append({"screen": r.screen, "x": float(x_str.strip()), "y": float(y_str.strip()), "target": r.target})
        except:
            pass

    dead_clicks_query = text('''
        SELECT screen, metadata_json->>'x_pos' as x, metadata_json->>'y_pos' as y
        FROM telemetry_events
        WHERE event_name = 'dead_click' AND metadata_json->>'x_pos' IS NOT NULL AND screen IS NOT NULL AND screen != '' AND user_id = :uid
        LIMIT 500;
    ''')
    dead_clicks_results = db.execute(dead_clicks_query, {"uid": user_id_str}).fetchall()
    dead_clicks_data = []
    for r in dead_clicks_results:
        try:
            dead_clicks_data.append({"screen": r.screen, "x": float(r.x), "y": float(r.y)})
        except:
            pass

    form_abandoned_query = text('''
        SELECT metadata_json->>'form_name' as form, metadata_json->>'last_active_field' as field, COUNT(*) as count
        FROM telemetry_events WHERE event_name = 'form_abandoned' AND user_id = :uid GROUP BY 1, 2 ORDER BY count DESC LIMIT 50;
    ''')
    form_abandoned_results = db.execute(form_abandoned_query, {"uid": user_id_str}).fetchall()
    form_abandoned_data = [{"form_field": f"{r.form} ({r.field})", "count": r.count} for r in form_abandoned_results]

    u_turns_query = text('''
        SELECT COALESCE(screen, 'Unknown') as screen, COUNT(*) as count
        FROM telemetry_events WHERE event_name = 'u_turn' AND user_id = :uid GROUP BY 1 ORDER BY count DESC LIMIT 50;
    ''')
    u_turns_results = db.execute(u_turns_query, {"uid": user_id_str}).fetchall()
    u_turns_data = [{"screen": r.screen, "count": r.count} for r in u_turns_results]

    friction_metrics = {
        "rage_taps": rage_taps_data,
        "dead_clicks": dead_clicks_data,
        "form_abandonment": form_abandoned_data,
        "u_turns": u_turns_data
    }
"""

# Wait, `telemetry_router.py` returns {"sankey": {"nodes": nodes, "links": links}}?
# Let's check exactly what telemetry_router.py returns for get_user_sankey.
content = content.replace('    return {"sankey": {"nodes": nodes, "links": links}}', friction_code + '\n    return {"sankey": {"nodes": nodes, "links": links}, "friction_metrics": friction_metrics}')

with open('telemetry_router.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched telemetry_router.py")
