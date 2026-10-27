import requests
B = "http://localhost:8088"
a = requests.Session()
def ver(nombre, r):
    try: n = r.json().get("count")
    except Exception: n = "-"
    print(f"{nombre:<38} → {r.status_code} (registros: {n})")
ver("anónimo lista datasets", a.get(f"{B}/api/v1/dataset/?q=(page_size:100)"))
ver("anónimo lista bases de datos", a.get(f"{B}/api/v1/database/"))
ver("anónimo tablas base curricular (db2)", a.get(f"{B}/api/v1/database/2/tables/?q=(schema_name:public)"))
ver("anónimo esquemas db1", a.get(f"{B}/api/v1/database/1/schemas/"))
ver("anónimo dashboard 1", a.get(f"{B}/api/v1/dashboard/1"))
for cid in (8, 12, 5):
    r = a.get(f"{B}/api/v1/chart/{cid}/data/")
    filas = r.json()["result"][0].get("rowcount") if r.ok else "-"
    print(f"anónimo datos gráfico {cid:<23} → {r.status_code} (filas: {filas})")
print(f"{'página pública del tablero':<38} → {a.get(f'{B}/superset/dashboard/1/?standalone=true').status_code}")
r = a.put(f"{B}/api/v1/chart/8", json={"slice_name": "x"})
print(f"{'anónimo intenta editar gráfico':<38} → {r.status_code}")
