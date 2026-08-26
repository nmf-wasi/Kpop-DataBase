
for f in ["users", "idols", "songs", "groups", "albums"]:
    print(f"app.include_router({f}.router, prefix='/api/{f}', tags=['{f}'])") 