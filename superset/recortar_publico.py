"""Deja el rol Public de Superset en solo lectura de los datasets del tablero público (ID 1)."""
import json
import sys

from ss_api import BASE, Superset

ss = Superset()
roles = {r["name"]: r["id"] for r in ss.s.get(f"{BASE}/api/v1/security/roles/?q=(page_size:50)").json()["result"]}
rid = roles["Public"]
actuales = ss.s.get(f"{BASE}/api/v1/security/roles/{rid}/permissions/").json()["result"]
json.dump(actuales, open("/tmp/public_role_respaldo.json", "w"), indent=1)

# Lo que un visitante anónimo no necesita para ver el tablero
QUITAR = {
    ("all_database_access", "all_database_access"), ("all_datasource_access", "all_datasource_access"),
    ("can_csv", "Superset"), ("can_export", "Chart"), ("can_export", "Dashboard"), ("can_export", "Theme"),
    ("can_export_as_example", "Dashboard"), ("can_export_streaming_csv", "SQLLab"),
    ("can_write", "Chart"), ("can_write", "Dashboard"), ("can_write", "Tag"), ("can_write", "Theme"),
    ("menu_access", "Datasets"),
}
conservar = [p["id"] for p in actuales if (p["permission_name"], p["view_menu_name"]) not in QUITAR]
quitados = sorted(f"{p['permission_name']} on {p['view_menu_name']}" for p in actuales
                  if (p["permission_name"], p["view_menu_name"]) in QUITAR)

graficos = ss.get("chart/", page_size=200, columns=["id", "datasource_id", "dashboards.id"])["result"]
ds_tablero = sorted({c["datasource_id"] for c in graficos if any(d["id"] == 1 for d in c.get("dashboards", []))})
todos, page = [], 0
while True:
    rr = ss.s.get(f"{BASE}/api/v1/security/permissions-resources/",
                  params={"q": json.dumps({"page_size": 100, "page": page})}).json()
    todos += rr["result"]
    page += 1
    if len(todos) >= rr["count"] or not rr["result"]:
        break
acceso_ds = [x["id"] for x in todos if x["permission"]["name"] == "datasource_access"
             and any(x["view_menu"]["name"].endswith(f"(id:{d})") for d in ds_tablero)]

nuevos = sorted(set(conservar) | set(acceso_ds))
print(f"Public: {len(actuales)} → {len(nuevos)} permisos")
print(f"Se quitan ({len(quitados)}):", "; ".join(quitados))
print(f"Se agrega datasource_access a los datasets del tablero 1: {ds_tablero}")
if "--aplicar" in sys.argv:
    r = ss.s.post(f"{BASE}/api/v1/security/roles/{rid}/permissions", json={"permission_view_menu_ids": nuevos})
    print("aplicado:", r.status_code, r.text[:150])
else:
    print("SIMULACIÓN (use --aplicar)")
